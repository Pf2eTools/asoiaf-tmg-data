import csv
import json
from pathlib import Path
import re
from copy import deepcopy
from const import *


def split_name(string):
    if string.startswith("Baelor Schwarzfluth"):
        pass
    string = re.sub(r"\s", " ", string)
    string = re.sub(r"\s[-–]\s", ", ", string)
    return [s.strip() for s in string.split(", ", 1)]


def normalize(string):
    return re.sub(r"[^A-Za-z]", "", string).lower()


def keymap(key):
    key_map = {
        "Name2": "Translated Name",
    }
    return key_map.get(key, key)


def csv_to_dict(path):
    with open(path, "r", encoding="utf-8") as csv_file:
        line = csv_file.readline()
        headers = [keymap(h) if h else str(ix) for ix, h in enumerate(line.strip().split(","))]
        csv_reader = csv.DictReader(csv_file, fieldnames=headers)
        data = [dict(row) for row in csv_reader if len([v for v in dict(row).values() if v]) > 0]
    return data


def parse_tactics_text(text_trigger_effect):
    single_split = [re.sub(r"\s", " ", s.strip()) for s in text_trigger_effect.split("\n") if s.strip()]
    double_split = [re.sub(r"\s", " ", s.strip()) for s in text_trigger_effect.split("\n\n")]
    out = {
        "trigger": "",
        "effect": []
    }
    if len([ln for ln in single_split if len(ln) > 50]) < 2:
        if double_split[0].endswith("**"):
            out["trigger"] = double_split[0].strip("*")
            out["effect"] = double_split[1:]
        elif single_split[0].endswith("**"):
            out["trigger"] = single_split[0].strip("*")
            out["effect"] = single_split[1:]
        else:
            raise Exception("Problem?")
    else:
        if single_split[0].endswith("**"):
            out["trigger"] = single_split[0].strip("*")
            out["effect"] = single_split[1:]
        else:
            ix_end_bold = [i for i, v in enumerate(single_split) if v.endswith("**")][0]
            out["trigger"] = " ".join(single_split[:ix_end_bold + 1]).strip("*")
            out["effect"] = single_split[ix_end_bold + 1:]

    if len(out["effect"]) == 0:
        del out["effect"]
        out["remove"] = out["trigger"]
        del out["trigger"]

    return out


def parse_tactics():
    data = csv_to_dict(f"{CSV_PATH}/tactics.csv")
    parsed_cards = {
        "en": {}
    }
    for card_data in data:
        id = card_data.get("Id")
        parsed = {
            "id": id,
            "name": card_data.get("Name").replace("\n", " ").strip(),
            "statistics": {
                "version": card_data.get("Version"),
                "faction": normalize(card_data.get("Faction")),
                "text": [parse_tactics_text(p) for p in card_data.get("Text").replace("./", ". /").split(" /")],
            },
        }
        if card_data.get("Remove") != "":
            parsed["statistics"]["remove"] = card_data.get("Remove")
        if card_data.get("Unit") != "":
            parsed["statistics"]["commander_id"] = card_data.get("Unit")
            parsed["statistics"]["commander_name"] = split_name(card_data.get("Deck"))[0]
            parsed["statistics"]["commander_subname"] = split_name(card_data.get("Deck"))[1]
        parsed_cards["en"][id] = parsed
    for lang in LANGUAGES:
        if lang == "en":
            continue
        translated_data = csv_to_dict(f"{CSV_PATH}/tactics.{lang}.csv")
        parsed_cards[lang] = {}
        for card_data in translated_data:
            id = card_data.get("Id")
            parsing = deepcopy(parsed_cards["en"][id])
            parsing["name"] = card_data.get("Name").replace("\n", " ").strip()
            parsing["statistics"]["text"] = [parse_tactics_text(p) for p in card_data.get("Text").replace("./", ". /").split(" /")]
            if parsed_cards["en"][id]["statistics"].get("commander_id") is not None:
                cmdr_name_split = split_name(card_data.get("Deck"))
                parsing["statistics"]["commander_name"] = cmdr_name_split[0]
                if len(cmdr_name_split) == 2:
                    parsing["statistics"]["commander_subname"] = cmdr_name_split[1]
                else:
                    del parsing["statistics"]["commander_subname"]
            parsed_cards[lang][id] = parsing
    return parsed_cards


# TODO: Don't do this .upper() bullshit
def parse_abilities():
    data = csv_to_dict(f"{CSV_PATH}/newskills.csv")
    parsed_abilities = {
        "en": {}
    }
    icons_to_long = {
        "M": "melee",
        "Melee": "melee",
        "R": "ranged",
        "W": "wounds",
        "F": "faith",
        "Fire": "fire",
        "P": "pillage",
        "V": "venom",
    }
    for ability_data in data:
        name = ability_data.get("Name")
        description = ability_data.get("Description")
        if name.startswith("Order:"):
            parts = [p for p in re.split(r"(\*\*.*?\*\*)", description) if p]
            parsed = {
                "trigger": parts[0].strip("*"),
                "effect": ["".join(parts[1:]).strip()],
            }
        else:
            parsed = {
                "effect": [description]
            }
        if name.startswith("Order:"):
            parsed["icons"] = ["order"]
        if ability_data.get("Icons") != "":
            parsed["icons"] = parsed.get("icons") or []
            for icon in ability_data.get("Icons").split(","):
                parsed_icon = icons_to_long.get(icon)
                if parsed_icon is None:
                    print(f'Uknown icon: "{icon}" in ability "{name}"')
                    parsed_icon = icon.lower()
                elif parsed_icon == "wounds":
                    match = re.search(r"this unit has (\d+) wounds", description, re.IGNORECASE)
                    if match:
                        parsed_icon += match.group(1)
                parsed["icons"].append(parsed_icon)
        parsed_abilities["en"][name.upper()] = parsed

    for lang in LANGUAGES:
        if lang == "en":
            continue
        translated_abilities = csv_to_dict(f"{CSV_PATH}/newskills.{lang}.csv")
        parsed_abilities[lang] = {}
        for translated_data in translated_abilities:
            orig_name = translated_data.get("Original Name").upper()
            orig = parsed_abilities["en"].get(orig_name)
            if orig is None:
                parsing = {}
            else:
                parsing = deepcopy(orig)
            description = translated_data.get("Translated Description")
            if parsing.get("trigger") is not None:
                parts = [p for p in re.split(r"(\*\*.*?\*\*)", description) if p]
                parsing["trigger"] = parts[0].strip("*")
                parsing["effect"] = ["".join(parts[1:]).strip()]
            else:
                parsing["effect"] = [ln.strip() for ln in description.split("\n") if ln.strip()]
            name = translated_data.get("Translated Name").upper()
            parsed_abilities[lang][name] = parsing

    return parsed_abilities


def parse_units():
    data = csv_to_dict(f"{CSV_PATH}/units.csv")
    parsed_cards = {
        "en": {}
    }

    def parse_attack(name_type, hit, dice):
        t, name = name_type.split("]")
        return {
            "name": name,
            "type": "melee" if t == "[M" else "short" if t == "[RS" else "long",
            "hit": int(hit.strip("+")),
            "dice": [int(d) for d in dice.split(".")],
        }

    for card_data in data:
        card_id = card_data.get("Id")
        name_parts = split_name(card_data.get("Name"))
        parsed = {
            "id": card_id,
            "name": name_parts[0],
            "subname": None,
            "statistics": {
                "version": card_data.get("Version"),
                "faction": normalize(card_data.get("Faction")),
                "type": normalize(card_data.get("Type")),
                "cost": "C" if card_data.get("Cost") == "C" else int(card_data.get("Cost")),
                "speed": int(card_data.get("Spd")),
                "defense": int(card_data.get("Def").strip("+")),
                "morale": int(card_data.get("Moral").strip("+")),
                "attacks": [],
                "abilities": [a.strip() for a in re.split(r"\s/|/\s", card_data.get("Abilities"))],
            },
        }
        if len(name_parts) == 2:
            parsed["subname"] = name_parts[1]
        else:
            del parsed["subname"]
        parsed["statistics"]["attacks"].append(parse_attack(card_data.get("Attack 1"), card_data.get("7"), card_data.get("8")))
        if card_data.get("Attack 2") != "":
            parsed["statistics"]["attacks"].append(parse_attack(card_data.get("Attack 2"), card_data.get("10"), card_data.get("11")))

        parsed_cards["en"][card_id] = parsed

    for lang in LANGUAGES:
        if lang == "en":
            continue
        translated_data = csv_to_dict(f"{CSV_PATH}/units.{lang}.csv")
        translated_skills = csv_to_dict(f"{CSV_PATH}/newskills.{lang}.csv")
        parsed_cards[lang] = {}
        for card_data in translated_data:
            id = card_data.get("Id")
            original = parsed_cards["en"][id]
            parsing = deepcopy(original)
            name_parts = split_name(card_data.get("Translated Name"))
            parsing["name"] = name_parts[0]
            if len(name_parts) == 2:
                parsing["subname"] = name_parts[1]
            elif parsing.get("subname") is not None:
                del parsing["subname"]
            for ix, attack in enumerate(original["statistics"]["attacks"]):
                parsing["statistics"]["attacks"][ix]["name"] = card_data.get(f"Attack {ix + 1}")
            parsing["statistics"]["abilities"] = []
            for ability in original["statistics"]["abilities"]:
                translated = next((a for a in translated_skills if a["Original Name"].lower() == ability.lower()), None)
                if translated is None:
                    print(f'Did not find tranlation ({lang}) for "{ability}" in unit "{parsing["name"]}".')
                    parsing["statistics"]["abilities"].append(ability)
                else:
                    parsing["statistics"]["abilities"].append(translated.get("Translated Name"))
            parsed_cards[lang][id] = parsing

    return parsed_cards


def parse_ncus():
    data = csv_to_dict(f"{CSV_PATH}/ncus.csv")
    parsed_cards = {
        "en": {}
    }

    for card_data in data:
        card_id = card_data.get("Id")
        name_parts = split_name(card_data.get("Name"))
        parsed = {
            "id": card_id,
            "name": name_parts[0],
            "subname": None,
            "statistics": {
                "version": card_data.get("Version"),
                "faction": normalize(card_data.get("Faction")),
                "abilities": [],
            },
        }
        if len(name_parts) > 1:
            parsed["subname"] = name_parts[1]
        else:
            del parsed["subname"]
        ability_names = [n.strip() for n in re.split(r"\s/|/\s", card_data.get("Names"))]
        ability_text = [n.strip() for n in re.split(r"\s/|/\s", card_data.get("Descriptions"))]
        for name, text in zip(ability_names, ability_text):
            ability = {
                "name": name,
                "effect": [t.strip() for t in text.split("\n\n") if t.strip()]
            }
            parsed["statistics"]["abilities"].append(ability)
        parsed_cards["en"][card_id] = parsed

    for lang in LANGUAGES:
        if lang == "en":
            continue
        translated_data = csv_to_dict(f"{CSV_PATH}/ncus.{lang}.csv")
        translated_abilities = csv_to_dict(f"{CSV_PATH}/newskills.{lang}.csv")
        parsed_cards[lang] = {}
        for card_data in translated_data:
            id = card_data.get("Id")
            parsing = deepcopy(parsed_cards["en"][id])
            name_parts = split_name(card_data.get("Translated Name"))
            parsing["name"] = name_parts[0]
            if len(name_parts) == 2:
                parsing["subname"] = name_parts[1]
            elif parsing.get("subname") is not None:
                del parsing["subname"]
            for ability in parsing["statistics"]["abilities"]:
                translated = next((a for a in translated_abilities if a["Original Name"] == ability["name"]), None)
                if translated is None:
                    print(f'Did not find tranlation ({lang}) for "{ability["name"]}" in NCU "{parsing["name"]}".')
                    continue
                ability["name"] = translated["Translated Name"].strip()
                ability["effect"] = [x.strip() for x in translated["Translated Description"].split("\n")]
            parsed_cards[lang][id] = parsing

    return parsed_cards


def parse_attachments():
    data = csv_to_dict(f"{CSV_PATH}/attachments.csv")
    data_specials = csv_to_dict(f"{CSV_PATH}/special.csv")
    parsed_cards = {
        "en": {}
    }

    # Add enemy attachments
    all_data = data + data_specials
    for card_data in all_data:
        card_id = card_data.get("Id")
        name_parts = split_name(card_data.get("Name"))

        parsed = {
            "id": card_id,
            "name": name_parts[0],
            "subname": None,
            "statistics": {
                "version": card_data.get("Version"),
                "faction": normalize(card_data.get("Faction")),
                "type": normalize(card_data.get("Type")),
                "cost": "C" if card_data.get("Cost") == "C" else int(card_data.get("Cost")),
                "abilities": [re.sub(r"\[(\w|Fire)]", "", a.strip()) for a in re.split(r"\s/|/\s", card_data.get("Abilities"))],
            },
        }
        if len(name_parts) > 1:
            parsed["subname"] = name_parts[1]
        else:
            del parsed["subname"]
        if parsed["statistics"]["cost"] == "C":
            parsed["statistics"]["commander"] = True

        parsed_cards["en"][card_id] = parsed

    for lang in LANGUAGES:
        if lang == "en":
            continue
        translated_data = csv_to_dict(f"{CSV_PATH}/attachments.{lang}.csv")
        translated_skills = csv_to_dict(f"{CSV_PATH}/newskills.{lang}.csv")
        parsed_cards[lang] = {}
        for card_data in translated_data:
            id = card_data.get("Id")
            original = parsed_cards["en"][id]
            parsing = deepcopy(original)
            name_parts = split_name(card_data.get("Translated Name"))
            parsing["name"] = name_parts[0]
            if len(name_parts) == 2:
                parsing["subname"] = name_parts[1]
            elif parsing.get("subname") is not None:
                del parsing["subname"]
            parsing["statistics"]["abilities"] = []
            for ability in original["statistics"]["abilities"]:
                translated = next((a for a in translated_skills if a["Original Name"].lower() == ability.lower()), None)
                if translated is None:
                    print(f'Did not find tranlation ({lang}) for "{ability}" in attachment "{parsing["name"]}".')
                    parsing["statistics"]["abilities"].append(ability)
                else:
                    parsing["statistics"]["abilities"].append(translated.get("Translated Name"))
            parsed_cards[lang][id] = parsing

    return parsed_cards


def dump(data, path):
    print(f'Writing to "{path}"...')
    with open(path, "wb") as f:
        as_string = json.dumps(data, indent=4, ensure_ascii=False)
        as_string = as_string.replace(" ", " ")
        as_string = as_string.replace(" ", " ")
        as_string = as_string.replace(" ", " ")
        as_string = as_string.replace("­", "")
        as_string = as_string.replace("", "")
        as_string = as_string.replace("[LONG RANGE]", "[LONGRANGE]")
        f.write(as_string.encode("utf-8"))


def main():
    abilities = parse_abilities()
    units = parse_units()
    ncus = parse_ncus()
    attachments = parse_attachments()
    tactics = parse_tactics()

    for lang in LANGUAGES:
        ab = abilities.get(lang)
        if ab is None:
            pass
            # raise Exception("")
        else:
            dump(ab, f"{DATA_PATH}/{lang}/abilities.json")

        for faction in FACTIONS:
            path = f"{DATA_PATH}/{lang}"
            Path(path).mkdir(parents=True, exist_ok=True)
            data = {
                "units": [u for u in units.get(lang, {}).values() if normalize(u["statistics"]["faction"]) == faction],
                "ncus": [n for n in ncus.get(lang, {}).values() if normalize(n["statistics"]["faction"]) == faction],
                "attachments": [a for a in attachments.get(lang, {}).values() if normalize(a["statistics"]["faction"]) == faction],
                "tactics": [t for t in tactics.get(lang, {}).values() if normalize(t["statistics"]["faction"]) == faction],
            }
            dump(data, f"{path}/{faction}.json")


if __name__ == "__main__":
    main()
