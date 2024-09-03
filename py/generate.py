import json
import traceback
import concurrent.futures
from pathlib import Path
from asset_manager import AssetManager
from generate_utils import TextRenderer
from generate_tactics import ImageGeneratorTactics
from generate_units import ImageGeneratorUnits
from generate_ncus import ImageGeneratorNCUs
from generate_attachments import ImageGeneratorAttachments
from generate_specials import ImageGeneratorSpecials
from const import *


class Generator:
    def __init__(self, ig_tactics, ig_units, ig_ncus, ig_attachments, ig_specials, overwrite=False, get_path=None, filter_data=None):
        self.ig_tacics = ig_tactics
        self.ig_units = ig_units
        self.ig_ncus = ig_ncus
        self.ig_attachments = ig_attachments
        self.ig_specials = ig_specials

        self.overwrite = overwrite
        if get_path is None:
            self.get_path = self._get_path
        else:
            self.get_path = get_path

        if filter_data is None:
            self.filter_data = self._filter_data
        else:
            self.filter_data = filter_data

        self.errors = {}

    @staticmethod
    def _filter_data(data_object):
        return ["face", "back"]

    @staticmethod
    def _get_path(data_object, back=False):
        lang = data_object.get("language")
        faction = data_object.get("statistics").get("faction")
        data_id = data_object.get("id")
        back_str = "b" if back else ""
        if data_object.get("type") == "tactics":
            return f"./generated/{lang}/{faction}/tactics/", f"{data_id}{back_str}.jpg"
        else:
            return f"./generated/{lang}/{faction}/cards/", f"{data_id}{back_str}.jpg"

    @staticmethod
    def get_abilitiy_data(language):
        with open(f"{DATA_PATH}/en/abilities.json", "r", encoding="utf-8") as file:
            abilities_data = json.load(file)
        if language == "en":
            return abilities_data

        with open(f"{DATA_PATH}/{language}/abilities.json", "r", encoding="utf-8") as file:
            translated_abilities_data = json.load(file)
        abilities_data.update(translated_abilities_data)

        return abilities_data

    @staticmethod
    def mutate_data(raw_data, **kwargs):
        meta = raw_data.get("_meta", kwargs)
        data = []
        for key, arr in raw_data.items():
            if key.startswith("_"):
                continue
            if type(arr) != list:
                continue
            for item in arr:
                item["language"] = meta.get("language")
                item["type"] = key
                data.append(item)
        return data

    def generate(self, data, language):
        ability_data = self.get_abilitiy_data(language)
        for data_object in data:
            data_id = data_object.get("id")
            data_type = data_object.get("type")

            sides = self.filter_data(data_object)

            if "face" in sides:
                out_dir, filename = self.get_path(data_object)
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                outpath = out_dir + filename
                if self.overwrite or not Path(outpath).exists():
                    try:
                        self._do_generate(data_object, outpath, ability_data=ability_data)
                    except Exception as e:
                        msg = f"{e.__class__.__name__}: {str(e)}"
                        print(msg)
                        traceback.print_exc()
                        self.errors[f"{data_id}_{language}"] = msg
            if "back" in sides and data_type != "tactics":
                out_dir_back, filename_back = self.get_path(data_object, back=True)
                Path(out_dir_back).mkdir(parents=True, exist_ok=True)
                outpath_back = out_dir_back + filename_back
                if self.overwrite or not Path(outpath_back).exists():
                    try:
                        self._do_generate(data_object, outpath_back, back=True)
                    except Exception as e:
                        msg = f"{e.__class__.__name__}: {str(e)}"
                        print(msg)
                        traceback.print_exc()
                        self.errors[f"{data_id}b_{language}"] = msg

    def _do_generate(self, data, path, ability_data=None, back=False):
        data_type = data.get("type")
        match data_type:
            case "tactics": gen = self.ig_tacics
            case "attachments": gen = self.ig_attachments
            case "units": gen = self.ig_units
            case "ncus": gen = self.ig_ncus
            case "specials": gen = self.ig_specials
            case _: raise TypeError

        if back:
            generated = gen.generate_back(data)
        else:
            match data_type:
                case "attachments" | "units":
                    generated = gen.generate(data, ability_data)
                case _:
                    generated = gen.generate(data)

        if path.endswith("png"):
            generated = generated.convert("RGBA")
        elif path.endswith("jpg"):
            generated = generated.convert("RGB")
        else:
            raise Exception(f"Invalid path: {path}")
        print(f'Saving to: "{path}"')
        generated.save(path)

    def generate_all(self):
        for lang in LANGUAGES:
            for faction in FACTIONS:
                json_data = load_json(f"./data/{lang}/{faction}.json")
                data = self.mutate_data(json_data, language=lang)
                self.generate(data, lang)


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
    return json_data


def main():
    am = AssetManager()
    renderer = TextRenderer(am)
    generator = Generator(
        ImageGeneratorTactics(am, renderer),
        ImageGeneratorUnits(am, renderer),
        ImageGeneratorNCUs(am, renderer),
        ImageGeneratorAttachments(am, renderer),
        ImageGeneratorSpecials(am, renderer),
        overwrite=True,
        filter_data=filter_data_generic
    )
    generator.generate_all()

    # with open("./py/generate_log.json", "w") as f:
    #     json.dump(generator.errors, f, indent=4)


def worker(args):
    lang, faction = args
    am = AssetManager()
    renderer = TextRenderer(am)
    generator = Generator(
        ImageGeneratorTactics(am, renderer),
        ImageGeneratorUnits(am, renderer),
        ImageGeneratorNCUs(am, renderer),
        ImageGeneratorAttachments(am, renderer),
        ImageGeneratorSpecials(am, renderer),
        filter_data=filter_data_generic,
        overwrite=True
    )
    path = f"./data/{lang}/{faction}.json"
    json_data = load_json(path)
    data = generator.mutate_data(json_data, language=lang)
    generator.generate(data, lang)
    return 0


def pooled():
    args = [[lang, faction] for lang in LANGUAGES for faction in FACTIONS]
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(worker, args)


def filter_data_errors(data_obj):
    with open("./py/generate_log.json") as f:
        errors = json.load(f)
    data_id = data_obj.get("id")
    language = data_obj.get("language")
    out = []
    if f"{data_id}_{language}" in errors.keys():
        out.append("face")
    if f"{data_id}b_{language}" in errors.keys():
        out.append("back")
    return out


def filter_data_generic(data_obj):
    language = data_obj.get("language")
    data_id = data_obj.get("id")
    data_type = data_obj.get("type")
    statistics = data_obj.get("statistics")
    faction = statistics.get("faction")
    sides = [
        "face",
        "back"
    ]

    languages = [
    ]
    ids = [
    ]
    types = [
    ]
    factions = [
    ]

    if languages and language not in languages:
        return []
    if ids and data_id not in ids:
        return []
    if types and data_type not in types:
        return []
    if factions and faction not in factions:
        return []

    return sides


if __name__ == "__main__":
    pooled()
    # main()
