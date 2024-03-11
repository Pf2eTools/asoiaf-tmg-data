import json
from pathlib import Path
from asset_manager import AssetManager
from generate_tactics import generate_tactics
from generate_units import generate_unit, generate_unit_back
from generate_ncus import generate_ncu, generate_ncu_back
from generate_attachments import generate_attachment, generate_attachment_back
from const import *


def gen_all(all_data, key, basepath, asset_manager, abilities_data):
    if len(TYPES_FILTER) and key not in TYPES_FILTER:
        return
    for data in all_data.get(key, []):
        data_id = data.get("id")
        name = data.get("name")
        subname = data.get("subname")
        statistics = data.get("statistics")
        fluff = data.get("fluff", {})
        if len(ID_FILTER) and data_id not in ID_FILTER:
            continue
        outpath = f'{basepath}/{data["id"]}.jpg'
        if (not Path(outpath).exists() or not AMEND) and "cardface" in CARDSIDE_FILTER:
            if key == "tactics":
                gen = generate_tactics(asset_manager, name, statistics).convert("RGB")
            elif key == "units":
                gen = generate_unit(asset_manager, data_id, name, subname, statistics, abilities_data).convert("RGB")
            elif key == "attachments":
                gen = generate_attachment(asset_manager, data_id, name, subname, statistics, abilities_data).convert("RGB")
            elif key == "ncus":
                gen = generate_ncu(asset_manager, data_id, name, subname, statistics).convert("RGB")
            else:
                continue
            print(f'Saving "{data["name"]}" cardfront to {outpath}...')
            gen.save(outpath)
        outpath_back = f'{basepath}/{data["id"]}b.jpg'
        if (not Path(outpath_back).exists() or not AMEND) and "cardback" in CARDSIDE_FILTER:
            if key == "units":
                gen_back = generate_unit_back(asset_manager, data_id, name, subname, statistics, fluff).convert("RGB")
            elif key == "attachments":
                gen_back = generate_attachment_back(asset_manager, data_id, name, subname, statistics, fluff).convert("RGB")
            elif key == "ncus":
                gen_back = generate_ncu_back(asset_manager, data_id, name, subname, statistics, fluff).convert("RGB")
            else:
                continue
            print(f'Saving "{data["name"]}" cardback to {outpath_back}...')
            gen_back.save(outpath_back)


def main():
    asset_manager = AssetManager()
    with open(f"{DATA_PATH}/en/abilities.json", "r", encoding="utf-8") as file:
        en_abilities_data = json.load(file)
    for lang in LANGUAGES:
        if lang == "en":
            abilities_data = en_abilities_data
        else:
            with open(f"{DATA_PATH}/{lang}/abilities.json", "r", encoding="utf-8") as file:
                translated_abilities_data = json.load(file)
                abilities_data = en_abilities_data
                for k, v in translated_abilities_data.items():
                    abilities_data[k] = v
        if len(LANG_FILTER) and lang not in LANG_FILTER:
            continue
        for faction in FACTIONS:
            with open(f"{DATA_PATH}/{lang}/{faction}.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            tactics_path = f"./generated/{lang}/{faction}/tactics"
            Path(tactics_path).mkdir(parents=True, exist_ok=True)
            gen_all(data, "tactics", tactics_path, asset_manager, None)

            cards_path = f"./generated/{lang}/{faction}/cards"
            Path(cards_path).mkdir(parents=True, exist_ok=True)
            gen_all(data, "units", cards_path, asset_manager, abilities_data)
            gen_all(data, "attachments", cards_path, asset_manager, abilities_data)
            gen_all(data, "ncus", cards_path, asset_manager, None)


AMEND = False

ID_FILTER = [
]

TYPES_FILTER = [
]

LANG_FILTER = [
    "en",
    "fr",
    "de"
]

CARDSIDE_FILTER = [
    "cardface",
    "cardback",
]


if __name__ == "__main__":
    main()
