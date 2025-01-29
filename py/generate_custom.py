import os.path
from generate import Generator, load_json
from generate_utils import TextRenderer, LanguageStore, FactionStore
from generate_tactics import ImageGeneratorTactics
from generate_units import ImageGeneratorUnits
from generate_ncus import ImageGeneratorNCUs
from generate_attachments import ImageGeneratorAttachments
from generate_specials import ImageGeneratorSpecials
from asset_manager import CustomAssetManager, get_path_or_dialogue
from image_cropper import *
from pathlib import Path


class CustomGenerator(Generator):
    def __init__(self, ig_tactics, ig_units, ig_ncus, ig_attachments, ig_specials, custom_data, overwrite=False, get_path=None, filter_data=None):
        super().__init__(ig_tactics, ig_units, ig_ncus, ig_attachments, ig_specials, overwrite, get_path, filter_data)
        self.custom_data = custom_data
        self._meta = custom_data.get("_meta")

    def _get_path(self, data_object, back=False):
        custom_data_id = self._meta.get("id")
        data_id = data_object.get("id")
        back_str = "b" if back else ""
        return f"./custom/generated/{custom_data_id}/", f"{data_id}{back_str}.jpg"

    def get_abilitiy_data(self, language):
        with open(f"{DATA_PATH}/en/abilities.json", "r", encoding="utf-8") as file:
            abilities_data = json.load(file)

        if language == "en":
            pass
        else:
            if language in LanguageStore.BASE_LANGUAGES.keys():
                lang_path = f"{DATA_PATH}/{language}/abilities.json"
            else:
                lang_path = f"./custom/data/{language}-abilities.json"
            if os.path.exists(lang_path):
                with open(lang_path, "r", encoding="utf-8") as file:
                    translated_abilities_data = json.load(file)
                abilities_data.update(translated_abilities_data)

        abilities_data.update(self.custom_data.get("abilities", {}))

        return abilities_data

    def generate_all(self):
        data = self.mutate_data(self.custom_data)
        language = self._meta.get("language", "en")
        self.generate(data, language)


def filter_data_custom(data_obj):
    data_id = data_obj.get("id")
    data_type = data_obj.get("type")
    statistics = data_obj.get("statistics")
    faction = statistics.get("faction")
    sides = [
        "face",
        "back"
    ]

    ids = [
    ]
    types = [
    ]
    factions = [
    ]

    if ids and data_id not in ids:
        return []
    if types and data_type not in types:
        return []
    if factions and faction not in factions:
        return []

    return sides


def main(path, skip_portrait=True, overwrite=True):
    json_data = load_json(path)

    meta = json_data.get("_meta")
    if meta is None or meta.get("id") is None:
        raise Exception("Invalid custom data!")
    custom_data_id = meta.get("id")

    language_store = LanguageStore()
    custom_languages = json_data.get("languages")
    if custom_languages is not None:
        for lang_key, lang_data in custom_languages.items():
            language_store.inject_language(lang_key, lang_data)
    faction_store = FactionStore()
    custom_factions = json_data.get("factions")
    if custom_factions is not None:
        for faction_name, faction_data in custom_factions.items():
            faction_store.inject_faction(faction_name, faction_data)

    asset_manager = CustomAssetManager(custom_data_id)
    text_renderer = TextRenderer(asset_manager)
    custom_icons = json_data.get("icons")
    if custom_icons is not None:
        text_renderer.inject_icons(custom_icons)

    ig_tactics = ImageGeneratorTactics(asset_manager, text_renderer, language_store=language_store, faction_store=faction_store)
    ig_units = ImageGeneratorUnits(asset_manager, text_renderer, language_store=language_store, faction_store=faction_store)
    ig_ncus = ImageGeneratorNCUs(asset_manager, text_renderer, language_store=language_store, faction_store=faction_store)
    ig_attachments = ImageGeneratorAttachments(asset_manager, text_renderer, language_store=language_store, faction_store=faction_store)
    ig_specials = ImageGeneratorSpecials(asset_manager, text_renderer, language_store=language_store, faction_store=faction_store)

    generator = CustomGenerator(
        ig_tactics,
        ig_units,
        ig_ncus,
        ig_attachments,
        ig_specials,
        json_data,
        overwrite=overwrite,
        get_path=None,
        filter_data=filter_data_custom,
    )
    generator.generate_all()

    if skip_portrait:
        return

    for lang_key in ["units", "attachments", "ncus"]:
        for data_object in json_data[lang_key]:
            object_id = data_object.get("id")
            path = None

            Path(f"./custom/portraits/{custom_data_id}/round").mkdir(parents=True, exist_ok=True)
            path_round = f"./custom/portraits/{custom_data_id}/round/{object_id}.png"
            if not os.path.exists(path_round):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_round = ImageSaver(path_round)
                circle = Circle({})
                cropper_circle = ImageCropper(loader, saver_round, circle)
                cropper_circle.create_ui()

            Path(f"./custom/portraits/{custom_data_id}/square").mkdir(parents=True, exist_ok=True)
            path_square = f"./custom/portraits/{custom_data_id}/square/{object_id}.jpg"
            if not os.path.exists(path_square):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_square = ImageSaver(path_square)
                square = Square({})
                cropper_square = ImageCropper(loader, saver_square, square)
                cropper_square.create_ui()

            Path(f"./custom/portraits/{custom_data_id}/standees").mkdir(parents=True, exist_ok=True)
            path_standee = f"./custom/portraits/{custom_data_id}/standees/{object_id}.jpg"
            if not os.path.exists(path_standee):
                path = path or get_path_or_dialogue(f"{asset_manager.asset_path}/{object_id}b.png", asset_manager.asset_path)
                loader = ImageLoader(path)
                saver_standee = ImageSaver(path_standee)
                rectangle = Rectangle({"aspect": 0.7})
                cropper_standee = ImageCropper(loader, saver_standee, rectangle)
                cropper_standee.create_ui()


if __name__ == "__main__":
    # main("./custom/data/cmon-prerelease.json", skip_portrait=False)
    main("./custom/data/example.json", overwrite=False)
