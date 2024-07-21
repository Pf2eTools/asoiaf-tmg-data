import os.path

from generate import Generator, load_json
from generate_utils import TextRenderer
from generate_tactics import ImageGeneratorTactics
from generate_units import ImageGeneratorUnits
from generate_ncus import ImageGeneratorNCUs
from generate_attachments import ImageGeneratorAttachments
from asset_manager import CustomAssetManager, get_path_or_dialogue
from image_cropper import *
import json
from pathlib import Path
from const import *


def main(path, skip_portrait=True):
    json_data = load_json(path)

    meta = json_data.get("_meta")
    if meta is None or meta.get("id") is None:
        raise Exception("Invalid custom data!")
    custom_data_id = meta.get("id")
    language = meta.get("language", "en")
    asset_manager = CustomAssetManager(custom_data_id)
    text_renderer = TextRenderer(asset_manager)
    ig_tactics = ImageGeneratorTactics(asset_manager, text_renderer)
    ig_units = ImageGeneratorUnits(asset_manager, text_renderer)
    ig_ncus = ImageGeneratorNCUs(asset_manager, text_renderer)
    ig_attachments = ImageGeneratorAttachments(asset_manager, text_renderer)

    generator = Generator(
        ig_tactics,
        ig_units,
        ig_ncus,
        ig_attachments,
        overwrite=False,
        get_path=None,
        filter_data=None,
    )

    with open(f"{DATA_PATH}/{language}/abilities.json", "r", encoding="utf-8") as file:
        abilities_data = json.load(file)

    for key, val in json_data.get("abilities", {}).items():
        abilities_data[key] = val

    out_path = f"./custom/generated/{custom_data_id}"
    Path(out_path).mkdir(parents=True, exist_ok=True)

    if skip_portrait:
        return

    for key in ["units", "attachments", "ncus"]:
        for data_object in custom_data[key]:
            object_id = data_object.get("id")
            path = None

            Path(f"./custom/portraits/{custom_data_id}/round").mkdir(parents=True, exist_ok=True)
            path_round = f"./custom/portraits/{custom_data_id}/round/{object_id}.png"
            if not os.path.exists(path_round):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_round = ImageSaver(path_round)
                circle = Circle({})
                cropper_circle = ImageCropper(loader, saver_round, circle)
                cropper_circle.create_ui()

            Path(f"./custom/portraits/{custom_data_id}/square").mkdir(parents=True, exist_ok=True)
            path_square = f"./custom/portraits/{custom_data_id}/square/{object_id}.jpg"
            if not os.path.exists(path_square):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_square = ImageSaver(path_square)
                square = Square({})
                cropper_square = ImageCropper(loader, saver_square, square)
                cropper_square.create_ui()

            Path(f"./custom/portraits/{custom_data_id}/standees").mkdir(parents=True, exist_ok=True)
            path_standee = f"./custom/portraits/{custom_data_id}/standees/{object_id}.jpg"
            if not os.path.exists(path_standee):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_standee = ImageSaver(path_standee)
                rectangle = Rectangle({"aspect": 0.7})
                cropper_standee = ImageCropper(loader, saver_standee, rectangle)
                cropper_standee.create_ui()


if __name__ == "__main__":
    with open("./custom/data/brew.json", "r", encoding="utf-8") as cd:
        leaks_data = json.load(cd)
    main(leaks_data, True)
