import json
from PIL import Image
import os

from py.song_data import FACTIONS

DIST = {
    "commander": 21,
    "unit": 77,
    "ncu": 48,
    "attachment": 36,
    "basedeck": 18,
}

PROP_TO_MAGIC_TYPE = {
    "units": "Unit",
    "ncus": "NCU",
    "attachments": "Attachment",
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
        with open(f"./data/en/{faction}.json", "r", encoding="utf-8") as f:
            fdata = json.load(f)
        for key, items in fdata.items():
            for item in items:
                if item.get("id") in BANNED_IDS:
                    continue
                item["prop"] = key
                if item.get("statistics").get("commander"):
                    data["commander"].append(item)
                elif key == "units":
                    data["unit"].append(item)
                elif key == "attachments":
                    data["attachment"].append(item)
                elif key == "ncus":
                    data["ncu"].append(item)

    return data


def get_basedeck(faction):
    return {
        "name": f"{faction}Basedeck",
        "mana_cost": "{0}",
        "image": f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/generated/en/{faction}/{faction}.png",
        "type": PROP_TO_MAGIC_TYPE["basedeck"],
    }


def get_full_name(unt):
    full_name = unt.get("name")
    if unt.get("subname"):
        full_name = f"{full_name} - {unt.get('subname')}"
    return full_name


def get_unit(unt):
    cost = unt.get("statistics").get("cost", 0)
    cost = 0 if cost == "C" else cost
    unit_type = "commander" if unt.get("statistics").get("commander") else unt.get("prop")
    unit_type = PROP_TO_MAGIC_TYPE.get(unit_type, PROP_TO_MAGIC_TYPE["default"])
    unit_type_front = f"{unit_type} - Battle" if unt.get("prop") == "units" else unit_type
    img_url = f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/generated/en/{unt.get('statistics').get('faction')}/{unt.get('id')}.jpg"
    if unt.get("prop") == "units":
        img_url = f"https://raw.githubusercontent.com/Pf2eTools/asoiaf-tmg-data/refs/heads/master/draft/img/{unt.get('id')}.jpg"
    full_name = get_full_name(unt)
    layout = "split" if unt.get("prop") == "units" else ""

    return {
        "name": f"{full_name} ({unt.get('id')})",
        "mana_cost": f"{{{cost}}}",
        "image": img_url,
        "type": unit_type_front,
        "layout": layout,
        "printed_names": {
            "en": unt.get("id"),
        },
        "back": {
            "name": f"{full_name} ({unt.get('id')})",
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
            cmdr = item.get("statistics").get("commander", False)
            char = item.get("statistics").get("character", False)
            max_picks = 1 if cmdr else 5
            cube_text += f"{max_picks} {get_full_name(item)} ({item.get('id')})\n"

    return cube_text


def rotate_images(overwrite=False):
    for faction in FACTIONS:
        with open(f"./data/en/{faction}.json", "r", encoding="utf-8") as f:
            fdata = json.load(f)
        for unit in fdata["units"]:
            uid = unit.get("id")
            faction = unit.get("statistics").get("faction")
            outpath = f"./draft/img/{uid}.jpg"
            if overwrite or not os.path.exists(outpath):
                im = Image.open(f"./generated/en/{faction}/{uid}.jpg").rotate(90, expand=1)
                im.save(outpath)
                print(f"Saving '{outpath}'...")
            outpath_b = f"./draft/img/{uid}b.jpg"
            if overwrite or not os.path.exists(outpath_b):
                im = Image.open(f"./generated/en/{faction}/{uid}b.jpg").rotate(90, expand=1)
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
