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
    asset_manager = CustomAssetManager(custom_data_id)

    abilities_data = {}

    for abilities_data_path in [f"{DATA_PATH}/en/abilities.json", f"./custom/data/{custom_data_id}-abilities.json"]:
        if os.path.exists(abilities_data_path):
            with open(abilities_data_path, "r", encoding="utf-8") as file:
                _abilities_data = json.load(file)
                abilities_data.update(_abilities_data)

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

            Path("./custom/portraits/round").mkdir(parents=True, exist_ok=True)
            path_round = f"./custom/portraits/{custom_data_id}/round/{object_id}.png"
            if not os.path.exists(path_round):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_round = ImageSaver(path_round)
                circle = Circle({})
                cropper_circle = ImageCropper(loader, saver_round, circle)
                cropper_circle.create_ui()

            Path("./custom/portraits/square").mkdir(parents=True, exist_ok=True)
            path_square = f"./custom/portraits/{custom_data_id}/square/{object_id}.jpg"
            if not os.path.exists(path_square):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_square = ImageSaver(path_square)
                square = Square({})
                cropper_square = ImageCropper(loader, saver_square, square)
                cropper_square.create_ui()

            Path("./custom/portraits/standees").mkdir(parents=True, exist_ok=True)
            path_standee = f"./custom/portraits/{custom_data_id}/standees/{object_id}.jpg"
            if not os.path.exists(path_standee):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_standee = ImageSaver(path_standee)
                rectangle = Rectangle({"aspect": 0.7})
                cropper_standee = ImageCropper(loader, saver_standee, rectangle)
                cropper_standee.create_ui()


if __name__ == "__main__":
    with open("./custom/data/cmon-leaks.json", "r", encoding="utf-8") as cd:
        leaks_data = json.load(cd)
    main(leaks_data, False)
    with open("./custom/data/tully.json", "r", encoding="utf-8") as cd:
        tully_data = json.load(cd)
    main(tully_data, False)
