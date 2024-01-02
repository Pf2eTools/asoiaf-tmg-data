import json
from pathlib import Path
from asset_manager import AssetManager
from generate_tactics import generate_tactics
from generate_units import generate_unit
from generate_ncus import generate_ncu
from generate_attachments import generate_attachment
from const import *


def gen_generic(all_data, key, gen_func, basepath):
    if len(TYPES_FILTER) and key not in TYPES_FILTER:
        return
    for data in all_data.get(key, []):
        data_id = data["id"]
        if len(ID_FILTER) and data_id not in ID_FILTER:
            continue
        outpath = f'{basepath}/{data["id"]}.jpg'
        if Path(outpath).exists() and AMEND:
            continue
        gen = gen_func(data).convert("RGB")
        print(f'Saving "{data["name"]}" to {outpath}...')
        gen.save(outpath)


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
        if lang in LANG_FILTER:
            continue
        for faction in FACTIONS:
            with open(f"{DATA_PATH}/{lang}/{faction}.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            tactics_path = f"./generated/{lang}/{faction}/tactics"
            Path(tactics_path).mkdir(parents=True, exist_ok=True)
            gen_generic(data, "tactics", lambda t: generate_tactics(asset_manager, t.get("name"), t.get("statistics")), tactics_path)

            cards_path = f"./generated/{lang}/{faction}/cards"
            Path(cards_path).mkdir(parents=True, exist_ok=True)
            gen_generic(data, "units", lambda u: generate_unit(asset_manager, u.get("id"), u.get("name"), u.get("subname"), u.get("statistics"), abilities_data), cards_path)
            gen_generic(data, "attachments", lambda a: generate_attachment(asset_manager, a.get("id"), a.get("name"), a.get("subname"), a.get("statistics"), abilities_data), cards_path)
            gen_generic(data, "ncus", lambda n: generate_ncu(asset_manager, n.get("id"), n.get("name"), n.get("subname"), n.get("statistics")), cards_path)


AMEND = True

ID_FILTER = [
]

TYPES_FILTER = [
]

LANG_FILTER = [
]


if __name__ == "__main__":
    main()
