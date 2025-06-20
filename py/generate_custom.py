import os.path
from generate import *
from asset_manager import CustomAssetManager, get_path_or_dialogue
from image_cropper import *
from song_data import *
import argparse


class CustomGenerator(Generator):
    def __init__(self, custom_id, custom_languages, custom_factions, custom_icons):
        self.custom_id = custom_id
        self.custom_languages = custom_languages
        self.custom_factions = custom_factions
        self.custom_icons = custom_icons

    def generator_factory(self, entity: SongEntity):
        am = CustomAssetManager(self.custom_id)
        tr = TextRenderer(am)

        if self.custom_icons is not None:
            tr.inject_icons(self.custom_icons)

        ls = self.get_language_store()
        fs = self.get_faction_store()

        if isinstance(entity, SongDataTactics):
            return ImageGeneratorTactics(am, tr, language_store=ls, faction_store=fs)
        elif isinstance(entity, SongDataSpecials):
            return ImageGeneratorSpecials(am, tr, language_store=ls, faction_store=fs)
        elif isinstance(entity, SongDataNCU):
            return ImageGeneratorNCUs(am, tr, language_store=ls, faction_store=fs)
        elif isinstance(entity, SongDataUnit):
            return ImageGeneratorUnits(am, tr, language_store=ls, faction_store=fs)
        elif isinstance(entity, SongDataAttachment):
            return ImageGeneratorAttachments(am, tr, language_store=ls, faction_store=fs)

        return None

    def get_language_store(self):
        language_store = LanguageStore()
        if self.custom_languages is not None:
            for lang_key, lang_data in self.custom_languages.items():
                language_store.inject_language(lang_key, lang_data)
        return language_store

    def get_faction_store(self):
        faction_store = FactionStore()
        if self.custom_factions is not None:
            for faction_name, faction_data in self.custom_factions.items():
                faction_store.inject_faction(faction_name, faction_data)
        return faction_store

    @staticmethod
    def _default_saves(context, sides):
        entity: SongEntity = context["data"]
        meta = context["meta"]
        out = {"front": [], "back": []}
        for side in sides:
            back_str = "b" if side == "back" else ""
            out[side].append({
                "fp": f"./custom/generated/{meta.id}/{entity.id}{back_str}.jpg"
            })

        return out

    @staticmethod
    def _default_filter(context):
        filter_func = get_filter(
            languages=[
            ],
            ids=[
            ],
            roles=[
            ],
            factions=[
            ],
            versions=[
            ],
        )
        return filter_func(context)


def main(path, skip_portrait=True, overwrite=True):
    data = DataLoader.load_structured(path)
    meta = data.meta

    custom_gen = CustomGenerator(
        meta.id,
        data.languages,
        data.factions,
        data.icons,
    )
    custom_gen.generate(data, overwrite=overwrite, multiproc=False)

    if skip_portrait:
        return

    asset_manager = CustomAssetManager(meta.id)
    for key in ["unit", "attachment", "ncu"]:
        for entity in getattr(data, key):
            path = None

            Path(f"./custom/portraits/{meta.id}/round").mkdir(parents=True, exist_ok=True)
            path_round = f"./custom/portraits/{meta.id}/round/{entity.id}.png"
            if not os.path.exists(path_round):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{entity.id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_round = ImageSaver(path_round)
                circle = Circle({})
                cropper_circle = ImageCropper(loader, saver_round, circle)
                cropper_circle.create_ui()

            Path(f"./custom/portraits/{meta.id}/square").mkdir(parents=True, exist_ok=True)
            path_square = f"./custom/portraits/{meta.id}/square/{entity.id}.jpg"
            if not os.path.exists(path_square):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{entity.id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_square = ImageSaver(path_square)
                square = Square({})
                cropper_square = ImageCropper(loader, saver_square, square)
                cropper_square.create_ui()

            Path(f"./custom/portraits/{meta.id}/standees").mkdir(parents=True, exist_ok=True)
            path_standee = f"./custom/portraits/{meta.id}/standees/{entity.id}.jpg"
            if not os.path.exists(path_standee):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{entity.id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_standee = ImageSaver(path_standee)
                rectangle = Rectangle({"aspect": 0.7})
                cropper_standee = ImageCropper(loader, saver_standee, rectangle)
                cropper_standee.create_ui()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate custom data.")
    parser.add_argument("filenames", nargs="*", default=["brew.json"], help="List of filenames relative to ./custom/data/ path.")
    parser.add_argument("--portraits", default=False, action="store_true", help="Generate portrait images for TTS use.")
    parser.add_argument("--overwrite", default=False, action="store_true", help="Overwrite existing files.")

    args = parser.parse_args()
    for filename in args.filenames:
        filepath = filename
        if Path(filename).is_file():
            pass
        else:
            filepath = f"./custom/data/{filename}"
        main(filepath, skip_portrait=not args.portraits, overwrite=args.overwrite)
