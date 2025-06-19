import json
from PIL import Image
import os
from song_data import FACTIONS, DataLoader

DIST = {
    "commander": 21,
    "unit": 77,
    "ncu": 48,
    "attachment": 36,
    "basedeck": 18,
}

PROP_TO_MAGIC_TYPE = {
    "unit": "Unit",
    "ncu": "NCU",
    "attachment": "Attachment",
    "basedeck": "Base Deck",
    "commander": "Commander",
    "default": "Unknown"
}

BANNED_IDS = [
    "20330",  # varamyrs eagle
    "10310",  # bear
    "20308",  # eagle
    "20309",  # wolf
    "10316",  # borroq's boar
    "30712",  # alicent
    "30713",  # rhaenyra
    "30404",  # seneschal
]


def get_data():
    data = {
        "commander": [],
        "unit": [],
        "ncu": [],
        "attachment": [],
    }
    for faction in FACTIONS:
        structured = DataLoader.load_structured(f"./data/en/{faction}.json")
        for item in structured.all_entities:
            if item.id in BANNED_IDS:
                continue
            if item.role in ["tactics", "special"]:
                continue
            if item.commander:
                data["commander"].append(item)
            elif item.role == "unit":
                data["unit"].append(item)
            elif item.role == "attachment":
                data["attachment"].append(item)
            elif item.role == "ncu":
                data["ncu"].append(item)

    return data


def get_basedeck(faction):
    return {
        "name": f"{faction}Basedeck",
        "mana_cost": "{0}",
        "image": f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/generated/en/{faction}/{faction}.png",
        "type": PROP_TO_MAGIC_TYPE["basedeck"],
    }


def get_full_name(ent):
    full_name = ent.name
    if ent.title:
        full_name = f"{full_name} - {ent.title}"
    return full_name


def get_unit(ent):
    cost = ent.cost
    unit_type = "commander" if ent.commander else ent.role
    unit_type = PROP_TO_MAGIC_TYPE.get(unit_type, PROP_TO_MAGIC_TYPE["default"])
    unit_type_front = f"{unit_type} - Battle" if ent.role == "unit" else unit_type
    img_url = f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/generated/en/{ent.faction}/{ent.id}.jpg"
    if ent.role == "unit":
        img_url = f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/draft/img/{ent.id}.jpg"
    full_name = get_full_name(ent)
    layout = "split" if ent.role == "unit" else ""

    return {
        "name": f"{full_name} ({ent.id})",
        "mana_cost": f"{{{cost}}}",
        "image": img_url,
        "type": unit_type_front,
        "layout": layout,
        "printed_names": {
            "en": ent.id,
        },
        "back": {
            "name": f"{full_name} ({ent.id})",
            "type": unit_type,
            "image": img_url.replace(".jpg", "b.jpg"),
            "layout": layout
        }
    }


def get_settings():
    return {
        "name": "ASOIAF: TMG",
        "withReplacement": False,
        "colorBalance": False,
        "cardBack": "https://steamusercontent-a.akamaihd.net/ugc/786378723752096342/8B70BD5C3F78C9C5C124F529E4447CC8C1621686/",
        "layouts": {
            "Default": {
                "weight": 1,
                "slots": [
                    {
                        "name": f"Item{i}",
                        "count": 1,
                        "sheets": [
                            {"name": k, "weight": v} for k, v in DIST.items()
                        ]
                    } for i in range(PACKSIZE)
                ]
            }
        },
    }


def get_cube_text():
    data = get_data()
    cube_text = "[Settings]\n"
    cube_text += json.dumps(get_settings(), indent=4)

    cube_text += "\n[CustomCards]\n[\n"
    custom_cards = [json.dumps(get_basedeck(f)) for f in FACTIONS]
    for items in data.values():
        custom_cards += [json.dumps(get_unit(u)) for u in items]
    cube_text += ",\n".join(custom_cards)
    cube_text += "\n]\n"

    cube_text += "[basedeck]\n"
    for faction in FACTIONS:
        cube_text += f"999 {faction}Basedeck\n"
    for key, items in data.items():
        cube_text += f"[{key}]\n"
        for item in items:
            cmdr = item.commander or False
            char = item.character or False
            max_picks = 1 if cmdr else 5
            cube_text += f"{max_picks} {get_full_name(item)} ({item.id})\n"

    return cube_text


def rotate_images(overwrite=False):
    for faction in FACTIONS:
        structured = DataLoader.load_structured(f"./data/en/{faction}.json")
        for unit in structured.unit:
            outpath = f"./draft/img/{unit.id}.jpg"
            if overwrite or not os.path.exists(outpath):
                im = Image.open(f"./generated/en/{faction}/{unit.id}.jpg").rotate(90, expand=1)
                im.save(outpath)
                print(f"Saving '{outpath}'...")
            outpath_b = f"./draft/img/{unit.id}b.jpg"
            if overwrite or not os.path.exists(outpath_b):
                im = Image.open(f"./generated/en/{faction}/{unit.id}b.jpg").rotate(90, expand=1)
                im.save(outpath_b)
                print(f"Saving '{outpath_b}'...")


def main(prepare_cube=True, prepare_img=True):
    if prepare_cube:
        txt = get_cube_text()
        with open("./draft/cube.txt", "w", encoding="utf-8") as f:
            print("Writing to './draft/cube.txt'...")
            f.write(txt)
    if prepare_img:
        rotate_images()


PACKSIZE = 12

if __name__ == "__main__":
    main()
