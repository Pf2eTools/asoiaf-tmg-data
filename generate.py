import json
from pathlib import Path
from generate_tactics import generate_tactics
from generate_units import generate_unit
from generate_ncus import generate_ncu
from generate_attachments import generate_attachment


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
                for tactics in data.get("tactics", []):
                    id = tactics['id']
                    if len(ID_FILTER) and id not in ID_FILTER:
                        continue
                    gen = generate_tactics(tactics).convert("RGB")
                    outpath = f"{tactics_path}/{id}.jpg"
                    print(f"Saving \"{tactics['name']}\" to {outpath}...")
                    gen.save(outpath)

                cards_path = f"./generated/{lang}/{faction}/cards"
                Path(cards_path).mkdir(parents=True, exist_ok=True)
                for unit in data.get("units", []):
                    id = unit['id']
                    if len(ID_FILTER) and id not in ID_FILTER:
                        continue
                    gen = generate_unit(unit, abilities_data).convert("RGB")
                    outpath = f"{cards_path}/{id}.jpg"
                    print(f"Saving \"{unit['name']}\" to {outpath}...")
                    gen.save(outpath)
                for attachment in data.get("attachments", []):
                    id = attachment['id']
                    if len(ID_FILTER) and id not in ID_FILTER:
                        continue
                    gen = generate_attachment(attachment, abilities_data).convert("RGB")
                    outpath = f"{cards_path}/{id}.jpg"
                    print(f"Saving \"{attachment['name']}\" to {outpath}...")
                    gen.save(outpath)
                for ncu in data.get("ncus", []):
                    id = ncu['id']
                    if len(ID_FILTER) and id not in ID_FILTER:
                        continue
                    gen = generate_ncu(ncu).convert("RGB")
                    outpath = f"{cards_path}/{id}.jpg"
                    print(f"Saving \"{ncu['name']}\" to {outpath}...")
                    gen.save(outpath)


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

if __name__ == "__main__":
    main()
