import csv
import json
import re
from tactics_card_generator import build_tactics_card


def csv_to_dict(path):
    with open(path, "r", encoding="utf-8") as csv_file:
        line = csv_file.readline()
        headers = [h if h else str(ix) for ix, h in enumerate(line.strip().split(","))]
        csv_reader = csv.DictReader(csv_file, fieldnames=headers)
        data = [dict(row) for row in csv_reader]
    return data


def parse_tactics():
    data = csv_to_dict(f"{CSV_PATH}/tactics.csv")
    parsed_cards = []
    for card_data in data:
        parsed = {
            "id": card_data.get("Id"),
            "name": card_data.get("Name").split("\n"),
            "version": card_data.get("Version"),
            "faction": card_data.get("Faction"),
            "text": [parse_ability_trigger(parse_ability_text(p.strip())) for p in card_data.get("Text").split(" /")],
        }
        if card_data.get("Remove") != "":
            parsed["remove"] = card_data.get("Remove")
        if card_data.get("Unit") != "":
            parsed["commander_id"] = card_data.get("Unit")
            parsed["commander_name"] = card_data.get("Deck").split(", ")[0].strip()
            parsed["commander_subname"] = card_data.get("Deck").split(", ")[1].strip()
        parsed_cards.append(parsed)
    return parsed_cards


def parse_ability_trigger(paragraphs):
    if len(paragraphs) > 1:
        return {
            "trigger": paragraphs[0],
            "effect": paragraphs[1:],
        }
    else:
        ix_end_bold = [i for i, v in enumerate(paragraphs[0]) if v.endswith("**")][0]
        return {
            "trigger": paragraphs[0][:ix_end_bold + 1],
            "effect": paragraphs[0][ix_end_bold + 1:],
        }


def parse_ability_text(text):
    def parse_para(para):
        match = re.match(r"^\[ATTACK:(.*)]$", para)
        if match:
            atk_type, atk_name, atk_stats = match.group(1).split(":")
            hit, dice = atk_stats.split("+")
            return {
                "name": atk_name,
                "type": "long" if "Long" in atk_type else "short" if "Short" in atk_type else "melee",
                "hit": int(hit),
                "dice": [int(d) for d in dice.split(",")]
            }
        else:
            return [line.strip() for line in para.split("\n")]

    paragraphs = [parse_para(p.strip()) for p in text.split("\n\n")]

    return paragraphs


def main():
    # In the future, dump this info as JSON (It's useful for TTS).
    tactics = parse_tactics()
    for ix, t in enumerate(tactics):
        gen = build_tactics_card(t).convert("RGB")
        outpath = f"./tactics/{t['id']}.jpg"
        print(f"Saving \"{' '.join(t['name'])}\" (ix: {ix}) to {outpath}...")
        gen.save(outpath)


CSV_PATH = "./assets/data"

if __name__ == "__main__":
    main()
