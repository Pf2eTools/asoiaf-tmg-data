import re
import multiprocessing
from asset_manager import AssetManager
from generate_utils import TextRenderer
from generate_tactics import ImageGeneratorTactics
from generate_units import ImageGeneratorUnits
from generate_ncus import ImageGeneratorNCUs
from generate_attachments import ImageGeneratorAttachments
from generate_specials import ImageGeneratorSpecials
from song_data import *


def get_filter(languages=None, ids=None, roles=None, factions=None, versions=None):
    def filter_func(context):
        entity: SongEntity = context["data"]
        language = context.get("language")
        sides = [
            "front",
            "back"
        ]

        if languages and language not in languages:
            return []
        if ids and entity.id not in ids:
            return []
        if roles and entity.role not in roles:
            return []
        if factions and entity.faction not in factions:
            return []
        if versions and entity.version not in versions:
            return []

        if isinstance(entity, SongDataTactics):
            return ["front"]

        if isinstance(entity, SongDataSpecials):
            if entity.category == "mission":
                return ["front"]
            elif entity.category == "objective":
                return ["front"]

        return sides

    return filter_func

def worker(instance, context, side, save_meta):
    image = instance.do_generate(context, side)
    for sm in save_meta:
        instance.do_save(image, sm)
    return 0


def get_generate_context(data: SongEntity, all_data: SongDataCollection):
    context = {
        "data": data,
        "abilities": [],
        "tactics": [],
        "commander": None,
        "meta": all_data.meta,
    }
    if isinstance(data, SongDataAttachment) or isinstance(data, SongDataUnit) or isinstance(data, SongDataNCU):
        if data.tactics:
            context["tactics"] = [t for t in all_data.tactics if t.id in data.tactics]

    if isinstance(data, SongDataAttachment) or isinstance(data, SongDataUnit):
        for ab in data.abilities:
            find = next((a for a in all_data.abilities if a.name.upper() == ab.upper()), None)
            if find is None:
                continue
            context["abilities"].append(find)

    if isinstance(data, SongDataTactics) and data.commander:
        context["commander"] = next((e for e in all_data.all_entities if e.id == data.commander.id), None)

    return context


class Generator:
    @staticmethod
    def generator_factory(entity: SongEntity):
        am = AssetManager()
        tr = TextRenderer(am)
        if isinstance(entity, SongDataTactics):
            return ImageGeneratorTactics(am, tr)
        elif isinstance(entity, SongDataSpecials):
            return ImageGeneratorSpecials(am, tr)
        elif isinstance(entity, SongDataNCU):
            return ImageGeneratorNCUs(am, tr)
        elif isinstance(entity, SongDataUnit):
            return ImageGeneratorUnits(am, tr)
        elif isinstance(entity, SongDataAttachment):
            return ImageGeneratorAttachments(am, tr)

        return None

    def do_generate(self, context, side):
        entity = context["data"]
        generator = self.generator_factory(entity)
        if side == "back":
            gen = generator.generate_back(context)
        else:
            gen = generator.generate(context)
        return gen

    @staticmethod
    def do_save(img, save_meta):
        path = save_meta.get("fp")
        print(f"Saving to '{path}'...")
        folder = re.sub(r"/.*$", "", path)
        Path(folder).mkdir(parents=True, exist_ok=True)

        preprocess = save_meta.get("preprocess")
        if preprocess is None:
            to_save = img
        else:
            to_save = preprocess(img)
            del save_meta["preprocess"]

        if path.endswith("png"):
            to_save = to_save.convert("RGBA")
        elif path.endswith("webp"):
            to_save = to_save.convert("RGBA")
        elif path.endswith("jpg"):
            to_save = to_save.convert("RGB")

        to_save.save(**save_meta)

    def get_items_to_generate(self, data, data_filter=None, get_save_metas=None, overwrite=False):
        if data_filter is None:
            data_filter = self._default_filter
        if get_save_metas is None:
            get_save_metas = self._default_saves

        all_entities = data.all_entities
        entities_context = [get_generate_context(e, data) for e in all_entities]

        to_generate = []
        for context in entities_context:
            render_sides = data_filter(context)
            save_metas = get_save_metas(context, render_sides)
            if not overwrite:
                save_metas = {
                    "front": [sm for sm in save_metas["front"] if not Path(sm.get("fp")).exists()],
                    "back": [sm for sm in save_metas["back"] if not Path(sm.get("fp")).exists()]
                }
            if save_metas["front"]:
                to_generate.append([self, context, "front", save_metas["front"]])
            if save_metas["back"]:
                to_generate.append([self, context, "back", save_metas["back"]])

        return to_generate

    def generate(self, data, data_filter=None, get_save_metas=None, overwrite=False, multiproc=True):
        items = self.get_items_to_generate(data, data_filter, get_save_metas, overwrite)
        if multiproc:
            with multiprocessing.Pool() as pool:
                pool.starmap(worker, items)
        else:
            for args in items:
                _, context, side, save_meta = args
                image = self.do_generate(context, side)
                for sm in save_meta:
                    self.do_save(image, sm)

    @staticmethod
    def _default_saves(context, sides):
        entity: SongEntity = context["data"]
        lang = context.get("meta").language
        out = {"front": [], "back": []}
        for side in sides:
            back_str = "b" if side == "back" else ""
            out[side].append({
                "fp": f"./generated/{lang}/{entity.faction}/{entity.id}{back_str}.jpg"
            })
            # out[side].append({
            #     "fp": f"../ASOIAF-Nexus-UI/public/img/{entity.id}{back_str}x2.webp",
            #     "quality": 75,
            #     "method": 6
            # })
            # out[side].append({
            #     "fp": f"../ASOIAF-Nexus-UI/public/img/{entity.id}{back_str}x1.webp",
            #     "quality": 75,
            #     "method": 6,
            #     "preprocess": lambda img: img.resize((img.width // 2, img.height // 2))
            # })

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


def main():
    for lang in LANGUAGES:
        for faction in FACTIONS:
            data = DataLoader.load_structured(f"./data/{lang}/{faction}.json")
            generator = Generator()
            generator.generate(data, overwrite=True)


if __name__ == "__main__":
    main()
