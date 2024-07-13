import os.path

from generate import gen_all
from asset_manager import CustomAssetManager, get_path_or_dialogue
from image_cropper import *
import json
from pathlib import Path
from const import *


def main(custom_data, skip_portrait=True):
    meta = custom_data.get("_meta")
    if meta is None or meta.get("id") is None:
        raise Exception("Invalid custom data!")
    custom_data_id = meta.get("id")
    language = meta.get("language", "en")
    asset_manager = CustomAssetManager(custom_data_id)

    with open(f"{DATA_PATH}/{language}/abilities.json", "r", encoding="utf-8") as file:
        abilities_data = json.load(file)

    for key, val in custom_data.get("abilities", {}).items():
        abilities_data[key] = val

    out_path = f"./custom/generated/{custom_data_id}"
    Path(out_path).mkdir(parents=True, exist_ok=True)
    gen_all(custom_data, "units", out_path, asset_manager, abilities_data)
    gen_all(custom_data, "attachments", out_path, asset_manager, abilities_data)
    gen_all(custom_data, "ncus", out_path, asset_manager, None)
    gen_all(custom_data, "tactics", out_path, asset_manager, None)

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
