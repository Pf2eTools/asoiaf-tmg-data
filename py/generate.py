import json
from pathlib import Path
from generate_tactics import generate_tactics
from generate_units import generate_unit
from generate_ncus import generate_ncu
from generate_attachments import generate_attachment


def gen_generic(all_data, key, gen_func, basepath):
    if len(TYPES_FILTER) and key not in TYPES_FILTER:
        return
    for data in all_data.get(key, []):
        data_id = data["id"]
        if len(ID_FILTER) and data_id not in ID_FILTER:
            continue
        gen = gen_func(data).convert("RGB")
        outpath = f'{basepath}/{data["id"]}.jpg'
        print(f'Saving "{data["name"]}" to {outpath}...')
        gen.save(outpath)


def main():
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
        for faction in FACTIONS:
            with open(f"{DATA_PATH}/{lang}/{faction}.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            tactics_path = f"./generated/{lang}/{faction}/tactics"
            Path(tactics_path).mkdir(parents=True, exist_ok=True)
            gen_generic(data, "tactics", generate_tactics, tactics_path)

            cards_path = f"./generated/{lang}/{faction}/cards"
            Path(cards_path).mkdir(parents=True, exist_ok=True)
            gen_generic(data, "units", lambda x: generate_unit(x, abilities_data), cards_path)
            gen_generic(data, "attachments", lambda x: generate_attachment(x, abilities_data), cards_path)
            gen_generic(data, "ncus", generate_ncu, cards_path)


DATA_PATH = "./data"
LANGUAGES = [
    "en",
    "de",
    "fr",
]

FACTIONS = [
    "lannister",
    "stark",
    "baratheon",
    "targaryen",
    "freefolk",
    "nightswatch",
    "greyjoy",
    "martell",
    "bolton",
    "neutral",
]

ID_FILTER = [
]

TYPES_FILTER = [
]

if __name__ == "__main__":
    main()
