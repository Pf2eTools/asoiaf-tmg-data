import os
from dataclasses import dataclass
import dataclasses
from typing import Optional, List, get_origin, get_args, Union
from enum import Enum, EnumType
import json
from pathlib import Path


class AttackType(Enum):
    melee = "melee"
    ranged_short = "short"
    ranged_long = "long"
    ranged_generic = "ranged"


class Tray(Enum):
    infantry = "infantry"
    cavalry = "cavalry"
    solo = "solo"
    warmachine = "warmachine"
    none = "none"


class ShieldIcon(Enum):
    infantry = "infantry"
    cavalry = "cavalry"
    monster = "monster"
    siegeengine = "siegeengine"
    none = "none"


class SongRole(Enum):
    unit = "unit"
    ncu = "ncu"
    attachment = "attachment"
    tactics = "tactics"
    special = "special"


def validate_type(value, expected_type):
    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if isinstance(expected_type, EnumType):
        return isinstance(value, expected_type) or value in expected_type

    if origin is None:
        return isinstance(value, expected_type)

    if origin is Union:
        return any(validate_type(value, arg) for arg in args)

    if origin is list:
        if not isinstance(value, list):
            return False
        if not value:
            return True
        return all(validate_type(item, args[0]) for item in value)

    return isinstance(value, origin)


@dataclass(frozen=True)
class MixinTypeCheck:
    def __post_init__(self):
        for field in dataclasses.fields(self.__class__):
            val = getattr(self, field.name)
            if not validate_type(val, field.type):
                raise TypeError(f"Field '{field.name}' expected type {field.type}, got {type(val)}: '{val}'")


@dataclass(frozen=True)
class TacticsCommander(MixinTypeCheck):
    id: str
    name: Optional[str] = None
    title: Optional[str] = None


@dataclass(frozen=True)
class BackText(MixinTypeCheck):
    text: str
    name: Optional[str] = None
    heading: Optional[str] = None


@dataclass(frozen=True)
class Fluff(MixinTypeCheck):
    lore: Optional[str] = None
    quote: Optional[str] = None


@dataclass(frozen=True)
class TacticsText(MixinTypeCheck):
    trigger: Optional[str] = None
    effect: Optional[List[str]] = None
    remove: Optional[str] = None


@dataclass(frozen=True)
class Attack(MixinTypeCheck):
    name: str
    type: AttackType
    hit: int
    dice: List[int]


@dataclass(frozen=True)
class UnitAbility(MixinTypeCheck):
    name: str
    trigger: Optional[str] = None
    effect: List[str] = dataclasses.field(default_factory=list)
    icons: Optional[List[str]] = None


@dataclass(frozen=True)
class NcuAbility(MixinTypeCheck):
    name: str
    effect: List[str]


@dataclass(frozen=True)
class Token(MixinTypeCheck):
    name: str
    number: int


@dataclass(frozen=True)
class SongData(MixinTypeCheck):
    id: str
    role: SongRole
    name: str
    title: Optional[str] = None
    faction: Optional[str] = None
    version: Optional[str] = None

    def to_json(self):
        def fix_dictionary(data):
            remove_vals = [None, False]

            if isinstance(data, dict):
                out = {}
                for key, val in data.items():
                    filtered_value = fix_dictionary(val)
                    if filtered_value not in remove_vals:
                        out[key] = filtered_value
                return out
            elif isinstance(data, list):
                out = []
                for item in data:
                    filtered_item = fix_dictionary(item)
                    if filtered_item not in remove_vals:
                        out.append(filtered_item)
                return out
            elif isinstance(data, Enum):
                return data.value
            else:
                return data

        return fix_dictionary(dataclasses.asdict(self))


@dataclass(frozen=True)
class SongDataNCU(SongData):
    role = SongRole.ncu
    icon: Optional[str] = None
    abilities: List[NcuAbility] = dataclasses.field(default_factory=list)
    cost: int = 0
    character: bool = True
    commander: bool = False
    tactics: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    back_text: Optional[List[BackText]] = None
    # These only affect rendering and TTS
    fluff: Optional[Fluff] = None
    tokens: Optional[Token] = None
    wounds: Optional[int] = None

    @staticmethod
    def from_json(data):
        back_text = [BackText(**bt) for bt in data.get("back_text")] if data.get("back_text") else None
        fluff = Fluff(**data.get("fluff")) if data.get("fluff") else None
        tokens = Token(**data.get("tokens")) if data.get("tokens") else None
        abilities = [NcuAbility(**ab) for ab in data.get("abilities", [])]
        kwargs = {
            **data,
            "abilities": abilities,
            "back_text": back_text,
            "fluff": fluff,
            "tokens": tokens,
        }

        return SongDataNCU(**kwargs)

    @staticmethod
    def from_legacy_json(data):
        kwargs = {
            **data,
            "role": SongRole.ncu,
            **data.get("statistics"),
            "title": data.get("subname"),
            "back_text": data.get("statistics").get("requirements"),
        }
        kwargs.pop("statistics", None)
        kwargs.pop("subname", None)
        kwargs.pop("requirements", None)
        kwargs.pop("portrait", None)
        kwargs.pop("portrait_square", None)
        kwargs.pop("standee", None)
        if kwargs.get("tactics") is not None:
            kwargs["tactics"] = [i for i in kwargs.get("tactics").get("cards").keys()]
        return SongDataNCU.from_json(kwargs)


@dataclass(frozen=True)
class SongDataUnit(SongData):
    role = SongRole.unit
    abilities: List[str] = dataclasses.field(default_factory=list)
    attacks: List[Attack] = dataclasses.field(default_factory=list)
    defense: int = 0
    morale: int = 0
    speed: int = 0
    cost: int = 0
    tray: Tray = Tray.infantry
    character: bool = False
    commander: bool = False
    tactics: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    back_text: Optional[List[BackText]] = None
    # These only affect rendering and TTS
    fluff: Optional[Fluff] = None
    icon: ShieldIcon = ShieldIcon.infantry
    tokens: Optional[Token] = None
    wounds: Optional[int] = None

    @staticmethod
    def from_json(data):
        back_text = [BackText(**bt) for bt in data.get("back_text")] if data.get("back_text") else None
        fluff = Fluff(**data.get("fluff")) if data.get("fluff") else None
        attacks = [Attack(**{**att, "type": AttackType(att.get("type"))}) for att in data.get("attacks", [])]
        tokens = Token(**data.get("tokens")) if data.get("tokens") else None
        kwargs = {
            **data,
            "attacks": attacks,
            "back_text": back_text,
            "fluff": fluff,
            "tokens": tokens,
        }

        return SongDataUnit(**kwargs)

    @staticmethod
    def from_legacy_json(data):
        kwargs = {
            **data,
            "role": SongRole.unit,
            **data.get("statistics"),
            "title": data.get("subname"),
            "icon": data.get("statistics").get("type"),
            "back_text": data.get("statistics").get("requirements"),
        }
        kwargs.pop("subname", None)
        kwargs.pop("requirements", None)
        kwargs.pop("statistics", None)
        kwargs.pop("type", None)
        kwargs.pop("portrait", None)
        kwargs.pop("portrait_square", None)
        kwargs.pop("standee", None)
        if kwargs.get("tactics") is not None:
            kwargs["tactics"] = [i for i in kwargs.get("tactics").get("cards").keys()]
        if kwargs.get("tray") == "siegeengine":
            kwargs["tray"] = Tray.warmachine
        if kwargs.get("tray") == "monster":
            kwargs["tray"] = Tray.solo
        return SongDataUnit.from_json(kwargs)


@dataclass(frozen=True)
class SongDataAttachment(SongData):
    role = SongRole.attachment
    abilities: List[str] = dataclasses.field(default_factory=list)
    cost: int = 0
    tray: Tray = Tray.infantry
    character: bool = False
    commander: bool = False
    enemy: bool = False
    tactics: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    back_text: Optional[List[BackText]] = None
    # These only affect rendering and TTS
    icon: ShieldIcon = ShieldIcon.infantry
    fluff: Optional[Fluff] = None
    tokens: Optional[Token] = None

    @staticmethod
    def from_json(data):
        fluff = Fluff(**data.get("fluff")) if data.get("fluff") else None
        tokens = Token(**data.get("tokens")) if data.get("tokens") else None
        back_text = [BackText(**bt) for bt in data.get("back_text")] if data.get("back_text") else None
        kwargs = {
            **data,
            "back_text": back_text,
            "fluff": fluff,
            "tokens": tokens,
        }
        return SongDataAttachment(**kwargs)

    @staticmethod
    def from_legacy_json(data):
        kwargs = {
            **data,
            "role": SongRole.attachment,
            **data.get("statistics"),
            "title": data.get("subname"),
            "icon": data.get("statistics").get("type"),
            "tray": data.get("statistics").get("type"),
            "back_text": data.get("statistics").get("requirements"),
        }
        kwargs.pop("subname", None)
        kwargs.pop("statistics", None)
        kwargs.pop("type", None)
        kwargs.pop("requirements", None)
        kwargs.pop("portrait", None)
        kwargs.pop("portrait_square", None)
        kwargs.pop("standee", None)
        if kwargs.get("cost") in ["C", "H", "G"]:
            kwargs["cost"] = 0
        if kwargs.get("tactics") is not None:
            kwargs["tactics"] = [i for i in kwargs.get("tactics").get("cards").keys()]
        if kwargs.get("tray") == "monster":
            kwargs["tray"] = Tray.solo
        if kwargs.get("tray") == "siegeengine":
            kwargs["tray"] = Tray.warmachine
        return SongDataAttachment.from_json(kwargs)


@dataclass(frozen=True)
class SongDataTactics(SongData):
    role = SongRole.tactics
    text: List[TacticsText] = dataclasses.field(default_factory=list)
    commander: Optional[TacticsCommander] = None
    remove: Optional[str] = None

    @staticmethod
    def from_json(data):
        kwargs = {
            **data,
            "text": [TacticsText(**t) for t in data.get("text")],
            "commander": TacticsCommander(**data.get("commander")) if data.get("commander") else None,
        }
        return SongDataTactics(**kwargs)

    @staticmethod
    def from_legacy_json(data):
        kwargs = {
            **data,
            "role": SongRole.tactics,
            **data.get("statistics"),
        }
        if kwargs.get("commander_id") is not None:
            kwargs["commander"] = {"id": kwargs.get("commander_id")}
        kwargs.pop("statistics", None)
        kwargs.pop("commander_id", None)
        kwargs.pop("commander_name", None)
        kwargs.pop("commander_subname", None)
        return SongDataTactics.from_json(kwargs)


@dataclass(frozen=True)
class SongDataSpecials(SongData):
    role = SongRole.special
    category: str = "unknown"
    front: dict = dataclasses.field(default_factory=dict)
    back: Optional[dict] = None
    size: Optional[dict] = None

    @staticmethod
    def from_json(data):
        return SongDataSpecials(**data)

    @staticmethod
    def from_legacy_json(data):
        kwargs = {
            **data,
            "role": SongRole.special,
            **data.get("statistics"),
            "category": data.get("type"),
        }
        if "subname" in json.dumps(data):
            print(f"WARNING: Song special {kwargs['name']} includes 'subname' key which was not converted. Change to 'title' manually.")
        kwargs.pop("statistics", None)
        kwargs.pop("type", None)
        return SongDataSpecials.from_json(kwargs)


type SongEntity = Union[SongDataAttachment, SongDataUnit, SongDataNCU, SongDataTactics, SongDataSpecials]


@dataclass(frozen=True)
class SongMeta(MixinTypeCheck):
    id: str
    author: Optional[str] = None
    language: Optional[str] = "en"
    pre: Optional[str] = None


@dataclass(frozen=True)
class SongDataCollection(MixinTypeCheck):
    meta: SongMeta
    unit: List[SongDataUnit] = dataclasses.field(default_factory=list)
    attachment: List[SongDataAttachment] = dataclasses.field(default_factory=list)
    ncu: List[SongDataNCU] = dataclasses.field(default_factory=list)
    tactics: List[SongDataTactics] = dataclasses.field(default_factory=list)
    special: List[SongDataSpecials] = dataclasses.field(default_factory=list)
    abilities: List[UnitAbility] = dataclasses.field(default_factory=list)
    languages: Optional[dict] = None
    factions: Optional[dict] = None
    icons: Optional[dict] = None

    @property
    def all_entities(self):
        return sum([self.unit, self.attachment, self.ncu, self.tactics, self.special], [])


class DataLoader:
    @staticmethod
    def load_json(path):
        with open(path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
        return json_data

    @staticmethod
    def load_meta(path):
        json_data = DataLoader.load_json(path)
        return SongMeta(**json_data.get("_meta"))

    @staticmethod
    def load_structured(path):
        json_data = DataLoader.load_json(path)
        meta = SongMeta(**json_data.get("_meta"))
        ability_paths = [f"{Path(__file__).parent.parent.resolve()}/data/{meta.language}/abilities.json", path]

        return SongDataCollection(
            meta=meta,
            unit=[SongDataUnit.from_json(jd) for jd in json_data.get("unit", [])],
            attachment=[SongDataAttachment.from_json(jd) for jd in json_data.get("attachment", [])],
            ncu=[SongDataNCU.from_json(jd) for jd in json_data.get("ncu", [])],
            tactics=[SongDataTactics.from_json(jd) for jd in json_data.get("tactics", [])],
            special=[SongDataSpecials.from_json(jd) for jd in json_data.get("special", [])],
            abilities=DataLoader.load_structured_abilities(*ability_paths),
            languages=json_data.get("languages"),
            factions=json_data.get("factions"),
            icons=json_data.get("icons"),
        )

    @staticmethod
    def load_structured_abilities(lang_path, primary_path):
        try:
            abilities_data = DataLoader.load_json(lang_path)
        except FileNotFoundError:
            abilities_data = {}

        json_data = DataLoader.load_json(primary_path)
        abilities_data.update(json_data.get("abilities", {}))

        return [UnitAbility(name=key, **data) for key, data in abilities_data.items()]


class FactionStore:
    BASE_FACTIONS = {
        "lannister": {
            "text_color": "#9d1323",
            "highlight_color": "silver",
            "bg_rotation": 0,
        },
        "stark": {
            "text_color": "#3b6680",
            "highlight_color": "gold",
            "bg_rotation": 180,
        },
        "freefolk": {
            "text_color": "#4b4138",
            "highlight_color": "gold",
            "bg_rotation": 0,
            "long": "Free Folk"
        },
        "neutral": {
            "text_color": "#8a300e",
            "highlight_color": "silver",
            "bg_rotation": 0,
        },
        "nightswatch": {
            "text_color": "#302a28",
            "highlight_color": "gold",
            "bg_rotation": 0,
            "long": "Night's Watch"
        },
        "baratheon": {
            "text_color": "#904523",
            "highlight_color": "silver",
            "bg_rotation": 0,
        },
        "targaryen": {
            "text_color": "#ac4c5d",
            "highlight_color": "gold",
            "bg_rotation": 0,
        },
        "greyjoy": {
            "text_color": "#577b79",
            "highlight_color": "gold",
            "bg_rotation": 180,
        },
        "martell": {
            "text_color": "#a85b25",
            "highlight_color": "gold",
            "bg_rotation": 180,
        },
        "bolton": {
            "text_color": "#7a312b",
            "highlight_color": "gold",
            "bg_rotation": 0,
        },
        "brotherhood": {
            "text_color": "#5c7d59",
            "highlight_color": "gold",
            "bg_rotation": 0,
            "long": "Brotherhood without Banners"
        },
    }

    def __init__(self):
        self._factions = {fac: {k: v for k, v in self.BASE_FACTIONS.get(fac).items()} for fac in self.BASE_FACTIONS.keys()}

    def inject_faction(self, key, faction):
        self._factions[key] = {k: v for k, v in faction.items()}

    def _get(self, faction_key, key, default):
        faction = self._factions.get(faction_key.lower())
        if faction is None:
            return default
        return faction.get(key, default)

    def name_color(self, faction):
        return self._get(faction, "name_text_color", "white")

    def text_color(self, faction):
        return self._get(faction, "text_color", "#7FDBFF")

    def highlight_color(self, faction):
        return self._get(faction, "highlight_color", "gold")

    def bg_rotation(self, faction):
        return self._get(faction, "bg_rotation", 0)

    def get_rendered(self, faction):
        return self._get(faction, "long", faction.capitalize())


class LanguageStore:
    BASE_LANGUAGES = {
        "en": {
            "character": "CHARACTER",
            "commander": "COMMANDER"
        },
        "de": {
            "character": "CHARAKTER",
            "commander": "HEERFÜHRER"
        },
        "fr": {
            "character": "PERSONNAGE",
            "commander": "GÉNÉRAL"
        },
    }

    def __init__(self):
        self._languages = {lang: {k: v for k, v in self.BASE_LANGUAGES.get(lang).items()} for lang in self.BASE_LANGUAGES.keys()}

    def inject_language(self, key, language):
        self._languages[key] = {k: v for k, v in language.items()}

    def translate(self, phrase, lang_key):
        language = self._languages.get(lang_key)
        if language is None:
            print(f"WARNING: Unknown language '{lang_key}'.")
            language = self._languages.get("en")
        translated = language.get(phrase, "")
        if translated == "":
            print(f"WARNING: Could not translate '{phrase}' to '{lang_key}'.")

        return translated


LANGUAGES = [l for l in LanguageStore.BASE_LANGUAGES.keys()]
FACTIONS = [f for f in FactionStore.BASE_FACTIONS.keys()]


def convert_legacy_data(path, outpath):
    print(f"Converting '{path}' to '{outpath}'...")
    with open(path, "r", encoding="utf-8") as f:
        legacy_data = json.load(f)

    meta = legacy_data.get("_meta", {
        "author": "CMON",
        "id": path.split("/")[-1].replace(".json", ""),
        "language": path.split("/")[-2],
    })

    out = {
        "_meta": meta,
        "languages": legacy_data.get("languages", None),
        "factions": legacy_data.get("factions", None),
        "icons": legacy_data.get("icons", None),
        "abilities": legacy_data.get("abilities", None),
        SongRole.unit.value: [SongDataUnit.from_legacy_json(unt).to_json() for unt in legacy_data["units"]],
        SongRole.ncu.value: [SongDataNCU.from_legacy_json(ncu).to_json() for ncu in legacy_data["ncus"]],
        SongRole.attachment.value: [SongDataAttachment.from_legacy_json(att).to_json() for att in legacy_data["attachments"]],
        SongRole.tactics.value: [SongDataTactics.from_legacy_json(tac).to_json() for tac in legacy_data["tactics"]],
        SongRole.special.value: [SongDataSpecials.from_legacy_json(sp).to_json() for sp in legacy_data.get("specials", [])],
    }
    if out["languages"] is None:
        del out["languages"]
    if out["factions"] is None:
        del out["factions"]
    if out["icons"] is None:
        del out["icons"]
    if out["abilities"] is None:
        del out["abilities"]

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=4, ensure_ascii=False)


def convert_all_legacy_data():
    for lang in ["en", "de", "fr"]:
        for faction in FACTIONS:
            inpath = f"legacy/{lang}/{faction}.json"
            outpath = f"data/{lang}/{faction}.json"
            Path(outpath).parent.mkdir(parents=True, exist_ok=True)
            convert_legacy_data(inpath, outpath)

    for file in os.listdir("./custom/data"):
        inpath = f"./custom/legacy/{file}"
        outpath = f"./custom/data/{file}"
        Path(outpath).parent.mkdir(parents=True, exist_ok=True)
        convert_legacy_data(inpath, outpath)

# TODO:
def test():
    for lang in ["en", "de", "fr"]:
        for faction in FACTIONS:
            data = DataLoader.load_structured(f"data/{lang}/{faction}.json")

    for file in os.listdir("./custom/data"):
        custom_data = DataLoader.load_structured(f"./custom/data/{file}")


if __name__ == "__main__":
    test()
