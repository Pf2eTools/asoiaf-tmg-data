from PIL import Image
import os
import re
from pathlib import Path
from song_data import FACTIONS
import tkinter as tk
from tkinter.filedialog import askopenfilename
from image_cropper import ImageLoader, ImageSaver, ImageCropper, Rectangle


# TODO: Get all the sizes in
class AssetManager:
    ASSETS_DIR = "./assets/warcouncil"
    DEFAULT_ASSET_SIZE = (100, 100)
    DEFAULT_SIZE_TOLERANCE = (10, 10)

    def get_missing(self, path, size, tolerance):
        return Image.new("RGBA", size)

    def get(self, path, size=DEFAULT_ASSET_SIZE, tolerance=DEFAULT_SIZE_TOLERANCE):
        if not os.path.exists(path):
            return self.get_missing(path, size, tolerance)
        return self._get(path)

    @staticmethod
    def _get(path):
        return Image.open(path).convert("RGBA")

    def get_bg(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/bg-small.png", (750, 1050), (0, 0))

    def get_text_bg(self):
        return self.get(f"{self.ASSETS_DIR}/common/bg-text.png", (656, 659), (0, 0))

    def get_bars(self, faction):
        large_bar = self.get(f"{self.ASSETS_DIR}/{faction}/bar-large.png", (1010, 85), (60, 2))
        small_bar = self.get(f"{self.ASSETS_DIR}/{faction}/bar-small.png", (1064, 16), (1, 0))
        corner_bar = self.get(f"{self.ASSETS_DIR}/{faction}/bar-corner.png", (229, 680), (3, 40))

        return large_bar, small_bar, corner_bar

    def get_decor(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/bar-decor.png", (42, 42), (0, 0))

    def get_crest_shadow(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/crest-shadow.png", (282, 300), (40, 0))

    def get_crest(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/crest.png", (200, 230), (60, 40))

    def get_unit_bg(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/bg-large.png", (1417, 827), (0, 0))

    def get_unit_skills_bg(self):
        return self.get(f"{self.ASSETS_DIR}/common/bg-skills.png", (611, 827), (0, 0))

    def get_unit_image(self, unit_id):
        return self.get(f"{self.ASSETS_DIR}/units/{unit_id}.png", (460, 640), (10, 40))

    def get_unit_back_image(self, unit_id):
        return self.get(f"{self.ASSETS_DIR}/units/{unit_id}b.png", (797, 827), (40, 40))

    def get_attachment_image(self, attachment_id, commander=False):
        size = (240, 250) if commander else (185, 235)
        return self.get(f"{self.ASSETS_DIR}/attachments/{attachment_id}.png", size, (60, 60))

    def get_attachment_back_image(self, attachment_id, commander=False, character=False):
        if commander:
            size = (610, 760)
        elif character:
            size = (560, 715)
        else:
            size = (560, 800)
        return self.get(f"{self.ASSETS_DIR}/attachments/{attachment_id}b.png", size, (200, 200))

    def get_special_image(self, attachment_id, img_size=None):
        return self.get(f"{self.ASSETS_DIR}/specials/{attachment_id}.png", img_size)

    def get_special_back_image(self, attachment_id, img_size=None):
        return self.get(f"{self.ASSETS_DIR}/specials/{attachment_id}b.png", img_size)

    def get_unit_type(self, unit_type, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/unit-{unit_type.lower()}.png", (103, 175), (1, 20))

    def get_attachment_type(self, unit_type, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/attach-{unit_type.lower()}.png", (102, 160), (0, 20))

    def get_stat_background(self):
        return self.get(f"{self.ASSETS_DIR}/common/bg-stat.png", (78, 78), (0, 0))

    def get_stat_icon(self, name):
        return self.get(f"{self.ASSETS_DIR}/common/{name}.png", (116, 116), (2, 2))

    def get_attack_bg(self, color):
        return self.get(f"{self.ASSETS_DIR}/common/bg-attack-{color}.png", (293, 107), (0, 0))

    def get_attack_dice_bg(self):
        return self.get(f"{self.ASSETS_DIR}/common/bg-dice.png", (214, 54), (0, 0))

    def get_attack_type_bg(self, color):
        return self.get(f"{self.ASSETS_DIR}/common/bg-attacktype-{color}.png", (106, 106), (0, 0))

    def get_attack_type(self, attack_type, color):
        atk_type = "melee" if attack_type == "melee" else "ranged"
        return self.get(f"{self.ASSETS_DIR}/common/attacktype-{atk_type}-{color}.png", (119, 119), (0, 0))

    def get_attack_range_icon(self, attack_range, color):
        return self.get(f"{self.ASSETS_DIR}/common/{attack_range}-{color}.png", (44, 44), (0, 0))

    def get_skill_icon(self, skill_name, color):
        path = f"{self.ASSETS_DIR}/common/skill-{skill_name}-{color}.png"
        return self.get(path, (106, 106), (0, 0))

    def get_skill_divider(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/skill-divider.png", (690, 50), (40, 0))

    def get_skill_bottom(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/skill-bottom.png", (614, 640), (0, 100))

    def get_tactics_commmander_img(self, commander_id):
        return self.get(f"{self.ASSETS_DIR}/tactics/{commander_id}.png", (243, 252), (10, 10))

    def get_ncu_img(self, ncu_id):
        return self.get(f"{self.ASSETS_DIR}/ncus/{ncu_id}.png", (269, 309), (5, 5))

    def get_ncu_back_img(self, ncu_id):
        return self.get(f"{self.ASSETS_DIR}/ncus/{ncu_id}b.png", (560, 660), (10, 200))

    def get_text_icon(self, icon):
        return self.get(f"{self.ASSETS_DIR}/common/icon-{icon.lower()}.png", (140, 140), (100, 100))

    def get_character_box(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/box-character.png", (345, 61), (20, 1))

    def get_text_box(self, faction):
        return self.get(f"{self.ASSETS_DIR}/{faction}/box-text.png", (503, 340), (0, 100))

    def get_cost_bg(self, border_color, commander):
        return self.get(f"{self.ASSETS_DIR}/common/bg-cost-{border_color}-{commander}.png", (78, 78), (0, 0))

    def get_blank_objective(self):
        return self.get(f"./assets/objectives/blank.png", (488, 750), (0, 0))

    def get_blank_mission(self):
        return self.get(f"./assets/missions/blank.png", (488, 750), (0, 0))

    def get_blank_siege_attacker(self):
        return self.get(f"./assets/siege/blank-attacker.png", (546, 750), (0, 0))

    def get_blank_siege_defender(self):
        return self.get(f"./assets/siege/blank-defender.png", (546, 750), (0, 0))

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
        path_specials = f"{self.ASSETS_DIR}/specials"
        Path(path_attachments).mkdir(parents=True, exist_ok=True)
        Path(path_specials).mkdir(parents=True, exist_ok=True)
        for file in os.listdir(f"{source}/Attachments"):
            if not re.match(r"\d+b?\.jpg", file):
                continue
            convert(f"{source}/Attachments/{file}", f"{path_attachments}/{file.replace('.jpg', '.png')}")
        for file in os.listdir(f"{source}/Specials"):
            match = re.match(r"(\d+)b?\.jpg", file)
            if match is None:
                continue
            elif match.group(1).startswith("5"):
                convert(f"{source}/Specials/{file}", f"{path_specials}/{file.replace('.jpg', '.png')}")
            elif match.group(1).startswith("2"):
                convert(f"{source}/Specials/{file}", f"{path_attachments}/{file.replace('.jpg', '.png')}")
            else:
                print(f"WARN: Strange ID: {file}")

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


# TODO: Might only look for .png image, even though .jpg exists
# TODO: For custom factions, the assetmanager expects ALL files in the same directory
# All in all, it's pretty disgusting
class CustomAssetManager(AssetManager):
    CUSTOM_ASSET_BASE_DIR = "./custom/assets"

    def __init__(self, asset_path):
        super().__init__()
        self._asset_path = asset_path

    @staticmethod
    def swap_filetype(string):
        return string.replace(".jpg", ".$$$").replace(".png", ".jpg").replace(".$$$", ".png")

    @staticmethod
    def get_cropped_path(path):
        return path.replace(".jpg", "-cropped.jpg").replace(".png", "-cropped.png")

    @property
    def asset_path(self):
        return f"{self.CUSTOM_ASSET_BASE_DIR}/{self._asset_path}"

    def get(self, path, size=AssetManager.DEFAULT_ASSET_SIZE, tolerance=AssetManager.DEFAULT_SIZE_TOLERANCE):

        custom_path = re.sub(r".+/", f"{self.asset_path}/", path)
        custom_path2 = re.sub(AssetManager.ASSETS_DIR, f"{self.asset_path}/", path)
        custom_paths = [custom_path, self.swap_filetype(custom_path), custom_path2, self.swap_filetype(custom_path2), path]
        for p in [self.get_cropped_path(cp) for cp in custom_paths]:
            if os.path.exists(p):
                return self.get_resized(p, size, tolerance)

        for p in custom_paths:
            if os.path.exists(p):
                return self.get_cropped(p, size, tolerance, self.get_cropped_path(custom_path))

        return self.get_missing(custom_path, size, tolerance)

    @staticmethod
    def is_image_right_size(image, size, tolerance):
        w, h = size
        img_w, img_h = image.size
        tol_w, tol_h = tolerance

        if w - tol_w <= img_w <= w + tol_w and h - tol_h <= img_h <= h + tol_h:
            return True
        return False

    # FIXME: cropped image overwrites
    def get_cropped(self, path, size, tolerance, cropped_path):
        original = self._get(path)
        if size is None or self.is_image_right_size(original, size, tolerance):
            return original

        root = tk.Tk()
        root.title("Warning")
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        w, h = size
        img_w, img_h = original.size
        tk.Label(frame, text=f"The image at {path} has bad dimensions.\n(expected {w}x{h}, got {img_w}x{img_h})"
                             f"\nDo you wish to crop and resize?").pack()

        out_path = path
        is_ignore = False

        def click_yes():
            loader = ImageLoader(path)
            saver = ImageSaver(cropped_path)
            shape = Rectangle({"w": size[0], "h": size[1]})
            cropper = ImageCropper(loader, saver, shape)
            cropper.create_ui()
            if cropper.did_write:
                nonlocal out_path
                out_path = cropped_path
            root.destroy()

        def click_ignore():
            nonlocal is_ignore
            is_ignore = True
            root.destroy()

        tk.Button(frame, text="Crop & Resize", command=click_yes).pack(side=tk.LEFT, expand=True)
        tk.Button(frame, text="Ignore", command=click_ignore).pack(side=tk.RIGHT, expand=True)
        tk.Button(frame, text="Resize", command=lambda: root.destroy()).pack(side=tk.RIGHT, expand=True)
        root.wait_window()

        if is_ignore:
            return self._get(out_path)

        return self.get_resized(out_path, size, tolerance)

    def get_resized(self, path, size, tolerance):
        image = self._get(path)

        if self.is_image_right_size(image, size, tolerance):
            return image
        return image.resize(size)

    def get_missing(self, path, size, tolerance):
        file_path = get_path_or_dialogue(path, initial_search_dir=self.asset_path)
        if file_path is None:
            return Image.new("RGBA", size)

        return self.get_cropped(file_path, size, tolerance, self.get_cropped_path(path))


def get_path_or_dialogue(path, initial_search_dir="./"):
    if os.path.exists(path):
        return path
    root = tk.Tk()
    root.title("Error")
    frame = tk.Frame(root, padx=10, pady=10)
    frame.pack(fill=tk.BOTH, expand=True)
    tk.Label(frame, text=f"Encountered missing image at '{path}'.\nDo you wish to locate the missing file?").pack()

    filename = None

    def click_yes():
        nonlocal filename
        filename = askopenfilename(initialdir=os.path.abspath(initial_search_dir), title=f"Choose a file", filetypes=(("image files", "*.png;*.jpg"),))
        if filename:
            root.destroy()

    tk.Button(frame, text="Yes", command=click_yes).pack(side=tk.LEFT, expand=True)
    tk.Button(frame, text="Ignore", command=lambda: root.destroy()).pack(side=tk.RIGHT, expand=True)
    root.wait_window()

    return filename


def main():
    am = AssetManager()
    am.prepare("./warcouncil", False)


if __name__ == "__main__":
    main()
