from PIL import Image
import os
import re
from pathlib import Path
from const import FACTIONS


class AssetManager:
    ASSETS_DIR = "./assets/warcouncil"

    def get_bg(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/bg-small.png")

    def get_text_bg(self):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-text.png")

    def get_bars(self, faction):
        large_bar = Image.open(f"{self.ASSETS_DIR}/{faction}/bar-large.png")
        small_bar = Image.open(f"{self.ASSETS_DIR}/{faction}/bar-small.png")
        corner_bar = Image.open(f"{self.ASSETS_DIR}/{faction}/bar-corner.png")

        return large_bar, small_bar, corner_bar

    def get_decor(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/bar-decor.png")

    def get_crest_shadow(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/crest-shadow.png")

    def get_crest(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/crest.png")

    def get_unit_bg(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/bg-large.png")

    def get_unit_skills_bg(self):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-skills.png")

    def get_unit_image(self, unit_id):
        return Image.open(f"{self.ASSETS_DIR}/units/{unit_id}.png")

    def get_attachment_image(self, attachment_id):
        return Image.open(f"{self.ASSETS_DIR}/attachments/{attachment_id}.png")

    def get_unit_type(self, unit_type, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/unit-{unit_type.lower()}.png")

    def get_attachment_type(self, unit_type, faction):
        path = f"{self.ASSETS_DIR}/{faction}/attach-{unit_type.lower()}.png"
        if not os.path.exists(path):
            return Image.new("RGBA", (100, 100))
        return Image.open(path)

    def get_stat_background(self):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-stat.png")

    def get_stat_icon(self, name):
        return Image.open(f"{self.ASSETS_DIR}/common/{name}.png")

    def get_attack_bg(self, color):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-attack-{color}.png")

    def get_attack_dice_bg(self):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-dice.png")

    def get_attack_type_bg(self, color):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-attacktype-{color}.png")

    def get_attack_type(self, attack_type, color):
        atk_type = "melee" if attack_type == "melee" else "ranged"
        return Image.open(f"{self.ASSETS_DIR}/common/attacktype-{atk_type}-{color}.png")

    def get_attack_range_icon(self, attack_range, color):
        return Image.open(f"{self.ASSETS_DIR}/common/{attack_range}-{color}.png")

    # FIXME: ?
    def get_skill_icon(self, skill_name, color):
        path = f"{self.ASSETS_DIR}/common/skill-{skill_name}-{color}.png"
        if os.path.exists(path):
            return Image.open(path)
        else:
            return Image.new("RGBA", (134, 134))

    def get_skill_divider(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/skill-divider.png")

    def get_skill_bottom(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/skill-bottom.png")

    def get_tactics_commmander_img(self, commander_id):
        return Image.open(f"{self.ASSETS_DIR}/tactics/{commander_id}.png")

    def get_ncu_img(self, ncu_id):
        return Image.open(f"{self.ASSETS_DIR}/ncus/{ncu_id}.png")

    def get_text_icon(self, icon):
        return Image.open(f"{self.ASSETS_DIR}/common/icon-{icon.lower()}.png")

    def get_character_box(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/box-character.png")

    def get_text_box(self, faction):
        return Image.open(f"{self.ASSETS_DIR}/{faction}/box-text.png")

    def get_cost_bg(self, border_color, commander):
        return Image.open(f"{self.ASSETS_DIR}/common/bg-cost-{border_color}-{commander}.png")

    @staticmethod
    def get_warcouncil_faction(faction):
        if faction == "nightswatch":
            return "NightsWatch"
        if faction == "freefolk":
            return "FreeFolk"
        return faction.capitalize()

    def prepare(self, source, overwrite=True):
        def convert(inpath, outpath):
            if overwrite or not Path(outpath).exists():
                im = Image.open(inpath).convert("RGBA")
                print(f"Writing to {outpath}...")
                im.save(outpath)

        path = f"{self.ASSETS_DIR}/common"
        Path(path).mkdir(parents=True, exist_ok=True)
        convert(f"{source}/Tactics/Bg2.jpg", f"{path}/bg-text.png")
        convert(f"{source}/Units/SkillsBg.webp", f"{path}/bg-skills.png")
        convert(f"{source}/Units/StatBg.webp", f"{path}/bg-stat.png")
        convert(f"{source}/Units/DiceBg.webp", f"{path}/bg-dice.png")
        convert(f"{source}/Units/Movement.webp", f"{path}/speed.png")
        convert(f"{source}/Units/Defense.webp", f"{path}/defense.png")
        convert(f"{source}/Units/Morale.webp", f"{path}/morale.png")

        for icon in ["CROWN", "MONEY", "LETTER", "SWORDS", "HORSE", "UNDYING", "OASIS", "MOVEMENT", "WOUND", "LONGRANGE"]:
            convert(f"{source}/graphics/{icon}.png", f"{path}/icon-{icon.lower()}.png")

        for color in ["Gold", "Silver"]:
            color_lower = color.lower()
            convert(f"{source}/Units/AttackBg{color}.webp", f"{path}/bg-attack-{color_lower}.png")
            convert(f"{source}/Units/AttackTypeBg{color}.webp", f"{path}/bg-attacktype-{color_lower}.png")
            convert(f"{source}/Units/Cost{color}Commander.webp", f"{path}/bg-cost-{color_lower}-commander.png")
            convert(f"{source}/Units/Cost{color}Regular.webp", f"{path}/bg-cost-{color_lower}-regular.png")
            for atk_type in ["Melee", "Ranged"]:
                convert(f"{source}/Units/AttackType.{atk_type}{color}.webp", f"{path}/attacktype-{atk_type.lower()}-{color_lower}.png")
            for atk_range in ["Long", "Short"]:
                convert(f"{source}/graphics/Range{atk_range}{color}.png", f"{path}/{atk_range.lower()}-{color_lower}.png")
            for skill in ["Faith", "Fire", "Order", "Pillage", "Venom", "Wounds"]:
                inpath_skill = f"{source}/Units/Skill{skill}{color}.webp"
                if not Path(inpath_skill).exists():
                    continue
                convert(inpath_skill, f"{path}/skill-{skill.lower()}-{color_lower}.png")

        for faction in FACTIONS:
            warcouncil_faction = self.get_warcouncil_faction(faction)
            base_path = f"{self.ASSETS_DIR}/{faction}"
            Path(base_path).mkdir(parents=True, exist_ok=True)

            convert(f"{source}/Units/UnitBg{warcouncil_faction}.jpg", f"{base_path}/bg-large.png")
            convert(f"{source}/Tactics/Bg_{warcouncil_faction}.jpg", f"{base_path}/bg-small.png")
            convert(f"{source}/Units/LargeBar{warcouncil_faction}.webp", f"{base_path}/bar-large.png")
            convert(f"{source}/Attachments/Bar{warcouncil_faction}.webp", f"{base_path}/bar-small.png")
            convert(f"{source}/Units/Corner{warcouncil_faction}.webp", f"{base_path}/bar-corner.png")
            convert(f"{source}/Tactics/Decor{warcouncil_faction}.webp", f"{base_path}/bar-decor.png")
            convert(f"{source}/Units/Crest{warcouncil_faction}.webp", f"{base_path}/crest-shadow.png")
            convert(f"{source}/Tactics/Crest{warcouncil_faction}.webp", f"{base_path}/crest.png")
            convert(f"{source}/Units/SkillBottom{warcouncil_faction}.webp", f"{base_path}/skill-bottom.png")
            convert(f"{source}/Units/Divider{warcouncil_faction}.webp", f"{base_path}/skill-divider.png")
            convert(f"{source}/NCUs/UnitTypeNCU{warcouncil_faction}.webp", f"{base_path}/unit-ncu.png")
            convert(f"{source}/NCUs/Character{warcouncil_faction}.webp", f"{base_path}/box-character.png")
            convert(f"{source}/Attachments/TextBox{warcouncil_faction}.webp", f"{base_path}/box-text.png")

            types = ["Cavalry", "Infantry", "Monster", "SiegeEngine"]
            for unit_type in types:
                unit_inpath = f"{source}/Units/UnitType.{unit_type}{warcouncil_faction}.webp"
                unit_outpath = f"{base_path}/unit-{unit_type.lower()}.png"
                attach_inpath = f"{source}/Attachments/UnitType.{unit_type}{warcouncil_faction}.webp"
                attach_outpath = f"{base_path}/attach-{unit_type.lower()}.png"
                if Path(unit_inpath).exists():
                    convert(unit_inpath, unit_outpath)
                if Path(attach_inpath).exists():
                    convert(attach_inpath, attach_outpath)

        path_attachments = f"{self.ASSETS_DIR}/attachments"
        Path(path_attachments).mkdir(parents=True, exist_ok=True)
        for file in os.listdir(f"{source}/Attachments"):
            if not re.match(r"\d+b?\.jpg", file):
                continue
            convert(f"{source}/Attachments/{file}", f"{path_attachments}/{file.replace('.jpg', '.png')}")
        for file in os.listdir(f"{source}/Specials"):
            if not re.match(r"\d+b?\.jpg", file):
                continue
            convert(f"{source}/Specials/{file}", f"{path_attachments}/{file.replace('.jpg', '.png')}")

        path_ncus = f"{self.ASSETS_DIR}/ncus"
        Path(path_ncus).mkdir(parents=True, exist_ok=True)
        for file in os.listdir(f"{source}/NCUs"):
            if not re.match(r"\d+b?\.jpg", file):
                continue
            convert(f"{source}/NCUs/{file}", f"{path_ncus}/{file.replace('.jpg', '.png')}")

        path_tactics = f"{self.ASSETS_DIR}/tactics"
        Path(path_tactics).mkdir(parents=True, exist_ok=True)
        for file in os.listdir(f"{source}/Tactics"):
            if not re.match(r"\d+\.jpg", file):
                continue
            convert(f"{source}/Tactics/{file}", f"{path_tactics}/{file.replace('.jpg', '.png')}")

        path_units = f"{self.ASSETS_DIR}/units"
        Path(path_units).mkdir(parents=True, exist_ok=True)
        for file in os.listdir(f"{source}/Units"):
            if not re.match(r"\d+b?\.jpg", file):
                continue
            convert(f"{source}/Units/{file}", f"{path_units}/{file.replace('.jpg', '.png')}")


def main():
    am = AssetManager()
    am.prepare("./warcouncil", False)


if __name__ == "__main__":
    main()
