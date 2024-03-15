from generate import gen_all
from asset_manager import CustomAssetManager
import json
from pathlib import Path
from const import *


def main(custom_data):
    meta = custom_data.get("_meta")
    if meta is None or meta.get("id") is None:
        raise Exception("Invalid custom data!")
    custom_data_id = meta.get("id")
    asset_manager = CustomAssetManager(custom_data_id)

    with open(f"{DATA_PATH}/en/abilities.json", "r", encoding="utf-8") as file:
        abilities_data = json.load(file)

    out_path = f"./custom/generated/{custom_data_id}"
    Path(out_path).mkdir(parents=True, exist_ok=True)
    gen_all(data, "units", out_path, asset_manager, abilities_data)
    gen_all(data, "attachments", out_path, asset_manager, abilities_data)


if __name__ == "__main__":
    with open("./custom/data/cmon-leaks.json", "r", encoding="utf-8") as cd:
        data = json.load(cd)
    main(data)
