from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import math
import re
from copy import copy


def add_rounded_corners(im, rad, supersample=4):
    circle = Image.new('L', (rad * 2 * supersample, rad * 2 * supersample), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 * supersample, rad * 2 * supersample), fill=255)
    circle = circle.resize((rad * 2, rad * 2), resample=Image.LANCZOS)
    alpha = Image.new('L', im.size, "white")
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((rad, 0, 2 * rad, rad)), (w - rad, 0))
    alpha.paste(circle.crop((0, rad, rad, 2 * rad)), (0, h - rad))
    alpha.paste(circle.crop((rad, rad, 2 * rad, 2 * rad)), (w - rad, h - rad))

    im = im.convert("RGBA")
    old_alpha = im.getchannel("A")
    im.putalpha(ImageChops.darker(alpha, old_alpha))

    return im


def get_faction_text_color(faction):
    faction_colors = {
        "martell": "#a85b25",
        "neutral": "#8a300e",
        "nightswatch": "#302a28",
        "stark": "#3b6680",
        "targaryen": "#ac4c5d",
        "baratheon": "#904523",
        "bolton": "#7a312b",
        "freefolk": "#4b4138",
        "greyjoy": "#577b79",
        "lannister": "#9d1323",
    }
    faction = re.sub(r"[^a-z]", "", faction.lower())
    return faction_colors.get(faction) or "#7FDBFF"


def get_faction_highlight_color(faction):
    faction_colors = {
        "neutral": "Silver",
        "nightswatch": "Gold",
        "stark": "Gold",
        "targaryen": "Gold",
        "baratheon": "Silver",
        "bolton": "Gold",
        "freefolk": "Gold",
        "greyjoy": "Gold",
        "martell": "Gold",
        "lannister": "Silver",
    }
    faction = re.sub(r"[^a-z]", "", faction.lower())
    return faction_colors.get(faction) or "Gold"


def get_faction_bg_rotation(faction):
    faction_bg_rotation = {
        "martell": 180,
        "neutral": 0,
        "nightswatch": 0,
        "stark": 180,
        "targaryen": 0,
        "baratheon": 0,
        "bolton": 0,
        "freefolk": 0,
        "greyjoy": 180,
        "lannister": 0,
    }
    faction = re.sub(r"[^a-z]", "", faction.lower())
    return faction_bg_rotation.get(faction) or 0


def apply_drop_shadow(image, color="#00000088", passes=5, shadow_size=3):
    border = 20
    shadow = Image.new("RGBA", (image.size[0] + border * 2, image.size[1] + border * 2))
    image_alpha_channel = image.split()[-1]
    pixels = image_alpha_channel.load()
    for x in range(0, image_alpha_channel.size[0]):
        for y in range(0, image_alpha_channel.size[1]):
            if pixels[x, y] < 255:
                pixels[x, y] = 0

    mask = Image.new("RGBA", image.size)
    for xy in [(0, 0), (shadow_size, 0), (-shadow_size, 0), (0, shadow_size), (0, -shadow_size)]:
        mask.paste(image_alpha_channel, xy, mask=image_alpha_channel)

    shadow.paste(color, (border, border), mask=mask)
    for i in range(passes):
        shadow = shadow.filter(ImageFilter.BLUR)
    shadow.alpha_composite(image, (border, border))
    return shadow


def render_stat_value(asset_manager, text_renderer, stat):
    background = asset_manager.get_stat_background()
    stat = str(stat)
    entry = TextEntry.from_string(stat, styles=RootStyle(font_family="Garamond", font_size=46, font_color="white", stroke_width=0,
                                                         bold=True))

    rd_stat = text_renderer.render(entry, bbox=background.size, supersample=4, align_y=TextRenderer.ALIGN_CENTER)
    offset = (2, -2) if stat.endswith("+") else (0, -1)
    background.alpha_composite(rd_stat, offset)
    return background


def render_cost(asset_manager, text_renderer, cost, border="gold", is_commander=False):
    commander = "commander" if is_commander else "regular"
    background = asset_manager.get_cost_bg(border, commander)
    entry = TextEntry.from_string(str(cost), styles=RootStyle(font_family="Garamond", font_size=46, font_color="white", bold=True,
                                                              stroke_width=0))
    rd_stat = text_renderer.render(entry, bbox=background.size, supersample=4.0, align_y=TextRenderer.ALIGN_CENTER)
    offset = (-1, -2) if type(cost) == str else (0, 0)
    background.alpha_composite(rd_stat, offset)
    return background


def render_attack(asset_manager, text_renderer, attack_data, border_color="Gold"):
    atk_type = attack_data.get("type")
    atk_name = attack_data.get("name")
    tohit = attack_data.get("hit")
    atk_ranks = attack_data.get("dice")

    attack_bg = asset_manager.get_attack_bg(border_color)
    attack_dice_bg = asset_manager.get_attack_dice_bg()

    attack_bar = Image.new("RGBA", (367, 166))
    skill_icon = render_skill_icon(asset_manager, text_renderer, atk_type, border_color)
    attack_bar.alpha_composite(attack_bg, (skill_icon.size[0] // 2, 14 + (attack_bg.size[1] - 106) // 2))
    attack_bar.alpha_composite(skill_icon)

    atk_name_color = "#0e2e45" if atk_type == "melee" else "#87282a"
    entry_name = TextEntry.from_string(atk_name.upper(), styles=RootStyle(font_size=29, font_color=atk_name_color, stroke_width=0.7,
                                                                          leading=900, italic=True))
    rd_atk_name = text_renderer.render(entry_name, bbox=(180, 60), margin=Spacing(5), align_y=TextRenderer.ALIGN_CENTER)
    attack_bar.alpha_composite(rd_atk_name, (221 - rd_atk_name.size[0] // 2, 56 - rd_atk_name.size[1] // 2))

    if atk_type in ["short", "long"]:
        range_icon = asset_manager.get_attack_range_icon(atk_type, border_color)
        attack_bar.alpha_composite(apply_drop_shadow(range_icon), (60, -14))

    rd_statistics = Image.new("RGBA", attack_bar.size)
    rd_statistics.alpha_composite(attack_dice_bg, (104, 88))
    rd_to_hit = render_stat_value(asset_manager, text_renderer, f"{tohit}+")
    rd_statistics.alpha_composite(apply_drop_shadow(rd_to_hit), (58, 56))
    rank_colors = ["#648f4a", "#dd8e29", "#bd1a2b"]
    for i in range(len(atk_ranks)):
        rank_bg = Image.new("RGBA", (35, 35), rank_colors[i])
        entry_num_dice = TextEntry.from_string(str(atk_ranks[i]), styles=RootStyle(font_size=37, font_color="#cdcecb", stroke_width=0.1,
                                                                                   bold=True, font_family="Garamond"))
        rd_num_dice = text_renderer.render(entry_num_dice, bbox=(44, 44))
        # This was an interesting programming journey, but having a transparent font makes it pretty hard to read the text
        # rd_num_dice = render_text_line(str(atk_ranks[i]), "black", 35, "Garamond-Bold", stroke_width=0)
        rank_bg.alpha_composite(rd_num_dice, (-5, 1))
        # mask = Image.new("RGBA", (35, 35))
        # mask.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 5))
        # r,g,b,_ = rank_bg.split()
        # rank_bg = Image.merge("RGBA", (r,g,b,ImageChops.invert(mask.getchannel("A"))))
        rd_statistics.alpha_composite(add_rounded_corners(rank_bg, 10), (164 + i * 43, 98))
    attack_bar.alpha_composite(apply_drop_shadow(rd_statistics, color="#00000077"), (-20, -20))

    return attack_bar


def render_skill_icon(asset_manager, text_renderer, name, highlight_color="Gold"):
    rendered = Image.new("RGBA", (134, 134))
    name, number, _ = re.split(r"(\d+)|$", name, maxsplit=1)
    if name in ["ranged", "melee", "long", "short"]:
        attack_type_bg = asset_manager.get_attack_type_bg(highlight_color)
        x, y = (134 - attack_type_bg.size[0]) // 2, (134 - attack_type_bg.size[1]) // 2
        rendered.alpha_composite(attack_type_bg, (x, y))
        attack_type = apply_drop_shadow(asset_manager.get_attack_type(name, highlight_color))
        x, y = (136 - attack_type.size[0]) // 2, (136 - attack_type.size[1]) // 2
        rendered.alpha_composite(attack_type, (x, y))
    # Buff asha
    elif name == "morale":
        rendered = Image.new("RGBA", (134, 196))
        icon_morale = asset_manager.get_stat_icon("morale")
        rd_morale = render_stat_value(asset_manager, text_renderer, f"{number or 5}+")
        x, y = (134 - rd_morale.size[0]) // 2, 196 - 9 - rd_morale.size[1]
        rendered.alpha_composite(rd_morale, (x, y))
        x, y = (134 - icon_morale.size[0]) // 2, 9
        rendered.alpha_composite(icon_morale, (x, y))
    else:
        icon = asset_manager.get_skill_icon(name, highlight_color)
        x, y = (134 - icon.size[0]) // 2, (134 - icon.size[1]) // 2
        rendered.alpha_composite(icon, (x, y))
        if number is not None:
            entry = TextEntry.from_string(number, styles=RootStyle(font_family="Garamond", bold=True, font_color="white", font_size=36))
            rd_number = text_renderer.render(entry, bbox=(134, 134), align_y=TextRenderer.ALIGN_CENTER)
            rendered.alpha_composite(rd_number)
    return rendered


def render_skill_icons(asset_manager, text_renderer, icons, highlight_color="Gold"):
    rd_icons = [render_skill_icon(asset_manager, text_renderer, icon, highlight_color) for icon in icons]
    h = sum([i.size[1] - 20 for i in rd_icons]) + 20
    w = 134

    all_icons = Image.new("RGBA", (w, h))
    y = 0
    for ix, icon in enumerate(rd_icons):
        all_icons.alpha_composite(apply_drop_shadow(icon, color="#00000055"), (-20, y - 20))
        y += icon.size[1] - 20

    return all_icons


def get_filtered_ability_data(abilities, abilities_data):
    filtered_abilities_data = []
    for ability in abilities:
        if type(ability) == dict:
            filtered_abilities_data.append(ability)
            continue
        elif type(ability) != str:
            raise Exception(f"Bad Data! Explected ability name (str) or ability (dict), but got {type(ability)}.")
        name_upper = ability.upper()
        ability_data = abilities_data.get(name_upper)
        if ability_data is None:
            print(f"Couldn't find ability: {ability}")
            continue
        ability_data["name"] = re.sub(r"\(.+", "", ability)
        filtered_abilities_data.append(ability_data)

    return filtered_abilities_data


def get_ability_sections(abilities_data, color):
    sections = []
    for ability in abilities_data:
        content = [
            TextEntry(ability.get("name").upper(), styles=TextStyle(bold=True, tracking=24, font_color=color))
        ]
        trigger = ability.get("trigger")
        if trigger:
            content.append(TextEntry(trigger, styles=TextStyle(bold=True)))
        content.append(TextEntry("\n".join(ability.get("effect"))))
        sections.append(TextEntry(TextEntry(content)))
    return sections


def get_requirement_data_for_renderer(requirements):
    sections = []
    for req in requirements:
        content = []
        if req.get("heading") is not None:
            content.append(TextEntry(req.get("heading"), styles=TextStyle(bold=True, tracking=40)))
        content.append(TextEntry(req.get("text")))
        sect = TextEntry(TextEntry(content))
        sections.append(sect)
    return TextEntry.from_array(sections, styles=RootStyle(font_size=32, font_color="#5d4d40", stroke_width=0.2))


def render_character_box(asset_manager, text_renderer, faction):
    return render_small_box(asset_manager, text_renderer, faction, "CHARACTER")


def render_commander_box(asset_manager, text_renderer, faction):
    return render_small_box(asset_manager, text_renderer, faction, "COMMANDER", font_color=get_faction_text_color(faction), tracking=0,
                            font_size=36)


def render_small_box(asset_manager, text_renderer, faction, text, font_color="#5d4d40", tracking=50, font_size=38):
    # TODO (MAYBE): Shrink (or crop out the center of) the box when the text is short?
    box = asset_manager.get_character_box(faction)
    entry = TextEntry.from_string(text, styles=RootStyle(font_size=font_size, font_color=font_color, tracking=tracking, bold=True,
                                                         stroke_width=0.1))
    rd_text = text_renderer.render(entry, bbox=(200, 35), margin=Spacing(5), align_y=TextRenderer.ALIGN_CENTER,
                                   overflow_policy_x=TextRenderer.OVERFLOW_CLIP)
    box.alpha_composite(rd_text, (box.width // 2 - 100, 13))
    return box


class ImageGenerator:
    def __init__(self, asset_manager, text_renderer):
        self.asset_manager = asset_manager
        self.text_renderer: TextRenderer = text_renderer


class Cursor:
    x = 0
    y = 0


class Spacing:
    def __init__(self, *args):
        """
        @param args: top=right=bottom=left; top=bottom,right=left; top,right=left,bottom; top,right,bottom,left
        """
        self._data = [0, 0, 0, 0]

        if len(args) == 1:
            self._data = [args[0], args[0], args[0], args[0]]
        elif len(args) == 2:
            self._data = [args[0], args[1], args[0], args[1]]
        elif len(args) == 3:
            self._data = [args[0], args[1], args[2], args[1]]
        elif len(args) == 4:
            self._data = [args[0], args[1], args[2], args[3]]
        else:
            raise

    def __getitem__(self, item):
        return self._data[item]

    # FIXME: remove this garbage: Keep top & bottom padding of left element
    def __add__(self, other):
        return Spacing(self[0], self[1] + other[1], self[2], self[3] + other[3])

    def __mul__(self, other):
        return Spacing(self[0] * other, self[1] * other, self[2] * other, self[3] * other)

    @property
    def top(self):
        return self._data[0]

    @property
    def right(self):
        return self._data[1]

    @property
    def bottom(self):
        return self._data[2]

    @property
    def left(self):
        return self._data[3]

    @property
    def x(self):
        return self.left + self.right

    @property
    def y(self):
        return self.top + self.bottom


class TextStyle:
    UNSET = "unset"

    UNIT_MILI_EM = "mili_em"
    UNIT_RES = "res"
    UNIT_BOOL = "bool"
    PROPERTY_TO_UNIT = {
        "tracking": UNIT_MILI_EM,
        "word_spacing": UNIT_MILI_EM,
        "leading": UNIT_MILI_EM,
        "paragraph_padding": UNIT_MILI_EM,
        "section_padding": UNIT_RES,
        "font_size": UNIT_RES,
        "padding": UNIT_RES,
        "bold": UNIT_BOOL,
        "italic": UNIT_BOOL,
    }

    def __init__(self, **kwargs):
        self.font_family = kwargs.get("font_family", None)
        self.font_color = kwargs.get("font_color", None)
        self.font_size = kwargs.get("font_size", 1.0)
        if kwargs.get("stroke_width") is None:
            self.stroke_width = None
        else:
            self.stroke_width = (100 * kwargs.get("stroke_width") // 1) / 100
        self.bold = kwargs.get("bold", None)
        self.italic = kwargs.get("italic", None)

        self.tracking = kwargs.get("tracking", 1.0)
        self.word_spacing = kwargs.get("word_spacing", 1.0)
        self.leading = kwargs.get("leading", 1.0)
        self.padding = kwargs.get("padding", Spacing(0))

        self.icon_scale = kwargs.get("icon_scale", 1.0)
        # These should only be used by root elements
        self.paragraph_padding = kwargs.get("paragraph_padding", 0)
        self.section_padding = kwargs.get("section_padding", 0)

        self.adjustments = {}
        self.supersample = kwargs.get("supersample", 1.0)

    def __getattribute__(self, item):
        if item.startswith("raw"):
            return object.__getattribute__(self, item.replace("raw_", "", 1))
        adjustment = object.__getattribute__(self, "adjustments").get(item)
        if type(adjustment) == int:
            return object.__getattribute__(self, item) + adjustment
        elif type(adjustment) == float:
            return object.__getattribute__(self, item) * adjustment
        elif isinstance(adjustment, Spacing):
            val = object.__getattribute__(self, item)
            return Spacing(val[0] + adjustment[0], val[1] + adjustment[1], val[2] + adjustment[2], val[3] + adjustment[3])
        return object.__getattribute__(self, item)

    def get(self, item):
        val = self.__getattribute__(item)
        unit = TextStyle.PROPERTY_TO_UNIT.get(item)
        if unit == TextStyle.UNIT_MILI_EM:
            return val * self.supersample * self.font_size / 1000
        elif unit == TextStyle.UNIT_RES:
            return val * self.supersample
        elif unit == TextStyle.UNIT_BOOL:
            return val is True

        return val

    @staticmethod
    def combine(parent, child):
        return TextStyle(
            font_family=parent.font_family if child.font_family is None else child.font_family,
            font_color=child.font_color or parent.font_color or "black",
            font_size=TextStyle.abs_or_rel(parent.font_size, child.font_size),
            stroke_width=parent.stroke_width if child.stroke_width is None else child.stroke_width,
            bold=None if child.bold == TextStyle.UNSET else parent.bold if child.bold is None else child.bold,
            italic=None if child.italic == TextStyle.UNSET else parent.italic if child.italic is None else child.italic,
            tracking=TextStyle.abs_or_rel(parent.tracking, child.tracking),
            word_spacing=TextStyle.abs_or_rel(parent.word_spacing, child.word_spacing),
            leading=TextStyle.abs_or_rel(parent.leading, child.leading),
            padding=child.padding + parent.padding,
            supersample=parent.supersample,
            icon_scale=child.icon_scale,
        )

    @staticmethod
    def abs_or_rel(prop_parent, prop_child):
        if type(prop_child) == int:
            return prop_child
        else:
            return prop_parent * prop_child


class RootStyle(TextStyle):
    def __init__(self, **kwargs):
        defaults = {
            "font_family": "Tuff",
            "font_size": 30,
            "leading": 1150,
            "word_spacing": 200,
            "paragraph_padding": 700,
            "section_padding": 0,
            "stroke_width": 0.3,
            "icon_scale": 1.0,
        }
        defaults.update(kwargs)
        super().__init__(**defaults)


class TextEntry:
    ROOT = 0
    SECT = 1
    PARA = 2
    TEXT = 3

    def __init__(self, children, etype=None, parent=None, styles=None):
        self.parent = parent

        if etype is not None:
            self.type = etype
        elif type(children) == str:
            self.type = TextEntry.TEXT
        elif type(children) == list:
            self.type = children[0].type - 1
        elif isinstance(children, TextEntry):
            self.type = children.type - 1
            children = [children]
        else:
            raise TypeError
        if self.type < 0:
            raise TypeError

        if self.type == TextEntry.TEXT:
            self.children = []
            self.text = children
            self.tokens = self.tokenize(self.text)
            self.split = []
        else:
            self.children = children or []
            self.text = None
            self.tokens = None
            self.split = None
            for child in self.children:
                if child.parent is None:
                    child.parent = self

        if styles is None and self.type == TextEntry.ROOT:
            self._styles = RootStyle()
        elif styles is None:
            self._styles = TextStyle()
        elif isinstance(styles, dict):
            self._styles = TextStyle(**styles)
        elif isinstance(styles, TextStyle):
            self._styles = styles
        self.__styles = None

        self.computed = [None, None]

    def __iter__(self):
        yield self
        for child in self.children:
            yield from child.__iter__()

    def iter_types(self, types):
        if self.type == types:
            yield self
        else:
            for child in self.children:
                yield from child.iter_types(types)

    # Yes, this makes debugging a nightmare, but have you considered that it saves writing a few characters?
    def __getattr__(self, item):
        return self.styles.get(item)

    def adjust_style(self, **kwargs):
        for key, val in kwargs.items():
            null = Spacing(0) if isinstance(val, Spacing) else 0
            self._styles.adjustments[key] = val + self._styles.adjustments.get(key, null)
        for entry in self:
            entry.build_styles()

    def build_styles(self):
        root_to_leaf = self.get_path_to_root()[::-1]
        styles = root_to_leaf[0]._styles
        for entry in root_to_leaf[1:]:
            styles = TextStyle.combine(styles, entry._styles)
        self.__styles = styles

    @property
    def styles(self) -> TextStyle:
        if self.__styles is None:
            self.build_styles()
        return self.__styles

    def set_style(self, prop, value):
        setattr(self._styles, prop, value)
        for it in self:
            it.build_styles()

    @property
    def root(self):
        root = self
        while root.parent is not None:
            root = root.parent
        return root

    def get_path_to_root(self):
        step = self
        out = [self]
        while step.parent is not None:
            step = step.parent
            out.append(step)
        return out

    @property
    def sections(self):
        yield from self.iter_types(TextEntry.SECT)

    @property
    def paragraphs(self):
        yield from self.iter_types(TextEntry.PARA)

    @property
    def entries(self):
        yield from self.iter_types(TextEntry.TEXT)

    @property
    def lines(self):
        for e in self.entries:
            yield from e.split

    @staticmethod
    def tokenize(string):
        tokens = [t for t in re.split(r"(\[.*?]|(?<!\\)\*{1,2}| |\n)", string.strip()) if t.strip(" ")]
        return tokens

    @staticmethod
    def from_string(string, styles=None):
        if type(string) != str:
            raise TypeError
        return TextEntry(TextEntry(TextEntry(TextEntry(string))), styles=styles)

    @staticmethod
    def from_array(array, styles=None):
        if type(array) != list:
            raise TypeError
        if not all([isinstance(a, TextEntry) for a in array]):
            raise TypeError("You must provide an array of TextEntries")
        if len(set([a.type for a in array])) != 1:
            raise TypeError("All TextEntries must be of the same type")

        types = array[0].type
        if types == TextEntry.SECT:
            sections = array
        elif types == TextEntry.PARA:
            sections = TextEntry(array)
        elif types == TextEntry.TEXT:
            sections = TextEntry(TextEntry(array))
        else:
            raise TypeError

        return TextEntry(sections, styles=styles)


CHAR_BULLET = "•"


class TextRenderer:
    FONTS_BASEPATH = "./fonts"
    FONTS = {
        "Tuff-Normal": f"{FONTS_BASEPATH}/Tuff-Normal.ttf",
        "Tuff-Bold": f"{FONTS_BASEPATH}/Tuff-Bold.ttf",
        "Tuff-Italic": f"{FONTS_BASEPATH}/Tuff-Italic.ttf",
        "Tuff-BoldItalic": f"{FONTS_BASEPATH}/Tuff-BoldItalic.ttf",

        "Garamond-Normal": f"{FONTS_BASEPATH}/Garamond-Bold.ttf",
        "Garamond-Bold": f"{FONTS_BASEPATH}/Garamond-Bold.ttf",
    }

    TOKEN_ITALIC = "*"
    TOKEN_BOLD = "**"
    TOKEN_NEWLINE = "\n"

    ALIGN_TOP = "top"
    ALIGN_BOTTOM = "bottom"
    ALIGN_LEFT = "left"
    ALIGN_RIGHT = "right"
    ALIGN_CENTER = "center"
    CENTER_SECTION = "center_section"

    OVERFLOW_AUTO = "auto"
    OVERFLOW_CLIP = "clip"

    LINEBREAK_GREEDY = "greedy"
    LINEBREAK_OPTIMAL = "optimal"
    LINEBREAK_NAME = "name"

    # FIXME/TODO: Custom data might require custom icons!
    ICONS = {
        "CROWN": "simple",
        "MONEY": "simple",
        "LETTER": "simple",
        "SWORDS": "simple",
        "HORSE": "simple",
        "UNDYING": "simple",
        "OASIS": "simple",

        "MOVEMENT": "image",
        "WOUND": "image",
        "LONGRANGE": "image",
    }

    FACTOR_CAP_HEIGHT = 0.82

    def __init__(self, asset_manager):
        """
        :key str overflow_policy_x:
        :key str overflow_policy_y:
        :key str linebreak_algorithm: Default: greedy
        :key str align_x:
        :key str align_y:
        :key int font_size: Target font size
        :key str font_color: Font color
        :key float stroke_width: Determines the thickness of text. Sensible values between 0-1. Default: 0.3.
        :key int supersample: Determines the scale to render text at a higher resolution. The final image is then downscaled. Creates a
            smoother image.
        :key bool fix_kerning: For fonts that don't provide a kerning table. Default: True
        :key float tracking: Determines the spacing between letters. Unit: 1/1000 em. Default: 0.
        :key float word_spacing: Determines the spacing between words. Unit: 1/1000 em. Default: 200.
        :key float leading: Determines the spacing between lines. Unit: em. Default 1.15.
        :key bool bold: If the text should be rendered bold by default. Default: False.
        :key bool italic: If the text should be rendered italic by default. Default: False.
        :key tuple padding: (left, top, right, bottom)
        :key float paragraph_padding:
        :key int section_padding:
        :key float base_bias_extra_height: 0.7
        :return: None
        """
        self.asset_manager = asset_manager
        self._fonts = {}

        self.overflow_policy_x = None
        self.overflow_policy_y = None
        self.max_w = None
        self.max_h = None
        self.linebreak_algorithm = None
        self.scale_margin = None
        self.background_color = None
        self.align_x = None
        self.align_y = None
        self._supersample = None
        self.fix_kerning = None
        self.margin = None
        self.base_bias_extra_height = None
        self.input: TextEntry = None
        self.cursor = None
        self.bold = None
        self.italic = None
        self.image = None
        self.draw = None
        self.max_font_reduction = None

    def set(self, *, bbox, **kwargs):
        self.max_w, self.max_h = bbox
        self.overflow_policy_x = kwargs.get("overflow_policy_x", self.OVERFLOW_AUTO)
        self.overflow_policy_y = kwargs.get("overflow_policy_y", self.OVERFLOW_AUTO)
        self.linebreak_algorithm = kwargs.get("linebreak_algorithm", self.LINEBREAK_GREEDY)
        self.scale_margin = kwargs.get("scale_margin", 0)
        self.background_color = kwargs.get("background_color", (0, 0, 0, 0))

        self.align_x = kwargs.get("align_x", self.ALIGN_CENTER)
        self.align_y = kwargs.get("align_y", self.ALIGN_TOP)
        self._supersample = kwargs.get("supersample", 0)
        self.fix_kerning = kwargs.get("fix_kerning", True)

        self.margin = kwargs.get("margin", Spacing(0, 0))
        self.base_bias_extra_height = kwargs.get("base_bias_extra_height", 0.7)
        self.max_font_reduction = kwargs.get("max_font_reduction", 10)

        self.bold = False
        self.italic = False
        self.cursor = Cursor()
        self.image = Image.new("RGBA", (int(self.max_w * self.supersample), int(self.max_h * self.supersample)), self.background_color)
        self.draw = ImageDraw.Draw(self.image)

    @property
    def supersample(self):
        if self._supersample != 0:
            return self._supersample
        # FIXME: If some strokewidth is set to 0, supersample is required
        return (100 / math.gcd(*[int(100 * e.stroke_width) for e in self.input.entries]) * 100 // 1) / 100

    @property
    def _max_w(self):
        return int((self.max_w - self.margin.x) * self.supersample)

    @property
    def _max_h(self):
        return int((self.max_h - self.margin.y) * self.supersample)

    def get_font(self, entry, bold=None, italic=None):
        bold = bold if bold is not None else self.bold
        italic = italic if italic is not None else self.italic
        font_style_str = "Bold" if bold else ""
        font_style_str += "Italic" if italic else ""
        font_style_str = font_style_str or "Normal"
        key = f"{entry.font_family}-{font_style_str}-{entry.font_size}"
        font = self._fonts.get(key)
        if font is None:
            font_path = self.FONTS.get(f"{entry.font_family}-{font_style_str}")
            font = ImageFont.truetype(font_path, entry.font_size)
            self._fonts[key] = font
            return font
        else:
            return font

    @staticmethod
    def fix_input(input_data):
        if type(input_data) == str:
            return TextEntry.from_string(input_data)
        elif isinstance(input_data, TextEntry):
            return input_data
        else:
            raise Exception("Invalid input passed to TextRenderer. Must be of type string or TextEntry.")

    @staticmethod
    def iterate_chars(token):
        for ix, char in enumerate(token):
            char_next = token[ix + 1] if ix + 1 < len(token) else " "
            yield char, char_next

    def calculate_line_width(self, entry, line, token_widths=None):
        width = entry.padding.x
        if token_widths is None:
            token_widths = self.get_token_widths(entry, tokens=line)
        for ix, width_token in enumerate(token_widths):
            width += width_token
            if re.match(r"^[,.:?!]", line[ix]) is not None:
                if ix != 0 and line[ix - 1] in [self.TOKEN_BOLD, self.TOKEN_ITALIC]:
                    width -= entry.tracking + entry.word_spacing
            if width_token != 0 and sum(token_widths[ix + 1:]) != 0:
                width += entry.word_spacing

        return width

    def get_token_widths(self, entry, tokens=None):
        bold = self.bold
        italic = self.italic
        widths = []
        tokens = tokens or entry.tokens
        for token in tokens:
            if token == self.TOKEN_BOLD:
                bold = not bold
                widths.append(0)
                continue
            elif token == self.TOKEN_ITALIC:
                italic = not italic
                widths.append(0)
                continue
            font = self.get_font(entry, bold=bold, italic=italic)
            token_width = self.calculate_token_width(entry, font, token)
            widths.append(token_width)
        return widths

    def calculate_token_width(self, entry, font, token):
        if token == self.TOKEN_ITALIC or token == self.TOKEN_BOLD:
            return 0
        elif token == self.TOKEN_NEWLINE:
            return self._max_w
        elif token.startswith("[") and token.endswith("]"):
            token = token.strip("[]")
            # FIXME: Uh Oh! Stinky! This crashes the renderer if we encounter an inline symbol that doesn't exist
            if self.ICONS.get(token) is None:
                return self._max_w
            icon = self.get_icon(entry, token)
            return self.get_icon_width(entry, icon)
        w = 0
        for char, char_next in self.iterate_chars(token):
            w += self.calculate_char_width(entry, font, char, char_next)
        return w

    def calculate_char_width(self, entry, font, char, char_next):
        offset_chars = font.getlength(char + char_next) - font.getlength(char_next)
        return offset_chars + entry.tracking + self.fix_kern(entry, font, char, char_next)

    @staticmethod
    def get_icon_width(entry, icon):
        return icon.size[0] + 0.1 * entry.font_size + entry.tracking

    def split_text_greedy(self, entry):
        token_widths = self.get_token_widths(entry)
        lines = [[]]
        ix_start_line = 0
        for ix, token in enumerate(entry.tokens):
            if token == self.TOKEN_NEWLINE:
                lines.append([])
                ix_start_line = ix + 1
                continue
            if entry.tokens[ix].startswith(CHAR_BULLET):
                width_prev = self.calculate_line_width(entry, lines[-1], token_widths=token_widths[ix_start_line:ix])
                if width_prev > 0:
                    lines.append([])
                    ix_start_line = ix
            line_width = self.calculate_line_width(entry, lines[-1] + [token], token_widths=token_widths[ix_start_line:ix + 1])
            if line_width > self._max_w and len(token) > 1:
                lines.append([])
                ix_start_line = ix
            lines[-1].append(token)
        return [ln for ln in lines if ln]

    def split_text_optimal(self, entry):
        tokens = copy(entry.tokens)
        # This represents an imaginary previous line and makes the indices for breaking cleaner
        tokens.insert(0, "")
        token_widths = [0] + self.get_token_widths(entry)

        if len(tokens) == 3:
            threshold = float("inf")
        elif len(tokens) < 6:
            threshold = 18 ** 2
        else:
            threshold = 9 ** 2
        # Dijkstra might throw errors, because no shortest path exists. In this case we should relax the threshold
        try:
            breakpoints = self.find_optimal_breaks(entry, tokens, token_widths, threshold)
        except ValueError:
            threshold *= 4
            breakpoints = self.find_optimal_breaks(entry, tokens, token_widths, threshold)

        optimal_breaks = [[t for t in tokens[i + 1:j + 1] if t != self.TOKEN_NEWLINE] for i, j in zip([0] + breakpoints, breakpoints)]
        return [ln for ln in optimal_breaks if ln]

    def find_optimal_breaks(self, entry, tokens, token_widths, threshold):
        graph = Graph(len(tokens))
        active_breaks = [0]
        while active_breaks:
            if active_breaks[0] == len(tokens) - 1:
                break
            for ix_token_end in range(active_breaks[0] + 1, len(tokens)):
                potential_line = tokens[active_breaks[0] + 1:ix_token_end + 1]
                widths = token_widths[active_breaks[0] + 1:ix_token_end + 1]
                is_final_line = ix_token_end == len(tokens) - 1
                # We don't need multiple breaks for zero-width characters, the dijkstra implementation doesn't want it either
                if not is_final_line and token_widths[ix_token_end] == 0:
                    continue
                penalty = self.calculate_line_penalty(entry, potential_line, widths, is_final_line)
                # TODO: If it's the final line and there are no edges in the graph, we should probably do something
                if penalty == float("inf"):
                    break
                if penalty > threshold and not is_final_line and tokens[ix_token_end] != self.TOKEN_NEWLINE:
                    continue
                graph.add_edge(active_breaks[0], ix_token_end, penalty)
                if ix_token_end not in active_breaks:
                    active_breaks.append(ix_token_end)
            active_breaks.pop(0)

        return graph.dijkstra()

    def calculate_line_penalty(self, entry, line, token_widths, is_final_line):
        # Starting with a little penalty helps to minimize lines
        penalty = 2
        line_no_newline = [tk for ix, tk in enumerate(line) if ix < len(line) - 1 or tk != self.TOKEN_NEWLINE]
        token_widths_no_newline = [token_widths[ix] for ix, tk in enumerate(line) if ix < len(line) - 1 or tk != self.TOKEN_NEWLINE]
        tokens_nonzero_len = [tk for ix, tk in enumerate(line_no_newline) if token_widths_no_newline[ix]]
        line_width = self.calculate_line_width(entry, line_no_newline, token_widths_no_newline)
        if len(line) == 1 and line_width > self._max_w:
            pass
        elif line_width > self._max_w:
            return float("inf")
        factor_line_length = 30 if is_final_line else 100
        penalty += factor_line_length * ((self._max_w - line_width) / (self._max_w - entry.padding.x)) ** 3
        if tokens_nonzero_len:
            # reward lines ending in punctuation
            if re.search(r"[,.;:!?]$", tokens_nonzero_len[-1]):
                penalty -= 3
            # heavily reward lines ending in quotation marks
            if re.search(r"\"$", tokens_nonzero_len[-1]):
                penalty -= 5
            # punish line that have punctuation after the first word
            if re.search(r"[,.;:!?]$", tokens_nonzero_len[0]):
                penalty += 1.5
            elif len(tokens_nonzero_len) > 3 and re.search(r"[,.;:!?]$", tokens_nonzero_len[-2]):
                penalty += 3
            # punish lines starting icons
            if tokens_nonzero_len[0].startswith("["):
                penalty += 3
            # punish lines ending with numbers
            if re.search(r"\d$", tokens_nonzero_len[-1]):
                penalty += 2
        if line[-1] == self.TOKEN_NEWLINE:
            penalty *= 0.2
        # python doesn't have a sign function lol
        return (penalty ** 2) * ((penalty > 0) - (penalty < 0))

    def split_data(self):
        if self.linebreak_algorithm == self.LINEBREAK_GREEDY:
            self.split_data_greedy()
        elif self.linebreak_algorithm == self.LINEBREAK_OPTIMAL:
            self.split_data_optimal()
        elif self.linebreak_algorithm == self.LINEBREAK_NAME:
            self.split_data_name()
        else:
            raise Exception(f"Invalid linebreak algorithm: {self.linebreak_algorithm}")

    def split_data_greedy(self):
        for entry in self.input.entries:
            self.bold = entry.bold
            self.italic = entry.italic
            entry.split = self.split_text_greedy(entry)

    def split_data_optimal(self):
        for entry in self.input.entries:
            self.bold = entry.bold
            self.italic = entry.italic
            entry.split = self.split_text_optimal(entry)

    def split_data_name(self):
        entries = [e for e in self.input.entries]
        names, others = entries[:2], entries[2:]
        for entry in names:
            self.bold = entry.bold
            self.italic = entry.italic
            # If there is a very bad line (0.4 * MAX), we should check if reducing the font size and tracking allows for a better line
            split = self.split_text_greedy(entry)
            lengths = [self.calculate_line_width(entry, ln) for ln in split]
            ratio = min(lengths) / max(lengths)
            if ratio < 0.4:
                self.input.adjust_style(font_size=-3, tracking=-5)
                split2 = self.split_text_greedy(entry)
                lengths2 = [self.calculate_line_width(entry, ln) for ln in split2]
                ratio2 = min(lengths2) / max(lengths2)
                if ratio2 > 0.6:
                    split = split2
                else:
                    self.input.adjust_style(font_size=3, tracking=5)
            entry.split = split
        for entry in others:
            self.bold = entry.bold
            self.italic = entry.italic
            entry.split = self.split_text_optimal(entry)

    def calculate_height(self):
        height = 0
        for section, is_last_section in iter_is_last(self.input.sections):
            height += section.padding.top
            for paragraph, is_last_paragraph in iter_is_last(section.paragraphs):
                height += paragraph.padding.top
                for entry, is_last_entry in iter_is_last(paragraph.entries):
                    height += entry.padding.top
                    for line in entry.split:
                        # TODO: yikes...
                        if len(line) == 1 and line[0].startswith("[") and line[0].endswith("]"):
                            if line[0].startswith("[ATTACK"):
                                height += 165 * self.supersample * entry.icon_scale
                            elif line[0].startswith("[SKILL"):
                                height += 134 * self.supersample * entry.icon_scale
                            else:
                                height += self.get_icon(entry, line[0].strip("[]")).size[1] * self.supersample
                        else:
                            height += entry.leading
                    height += entry.padding.bottom
                    if is_last_entry:
                        height -= entry.leading - self.FACTOR_CAP_HEIGHT * entry.font_size
                height += paragraph.padding.bottom
                if not is_last_paragraph:
                    as_list = list(paragraph.lines)
                    # there is one line, that one line has one token, and that token is an icon
                    if len(as_list) == 1 and len(as_list[0]) == 1 and as_list[0][0].startswith("[") and as_list[0][0].endswith("]"):
                        height -= (self.input.paragraph_padding * 0.4) // 1
                    height += self.input.paragraph_padding
            height += section.padding.bottom
            if not is_last_section:
                height += self.input.section_padding
                height += self.margin.top * self.supersample
                height += self.margin.bottom * self.supersample

        return height

    def fix_kern(self, entry, font, char1, char2):
        if not self.fix_kerning:
            return 0
        if char2 == " ":
            return 0
        mem = entry.font_size / 1000
        if entry.font_family == "Tuff":
            match (char1, char2):
                # uppercase T and small letters
                case ("T", c) if font.getbbox(c)[1] >= font.getbbox("a")[1]:
                    return -100 * mem
                case ("g", "y"):
                    return 30 * mem
                case ("V", "A") | ("A", "V"):
                    return -110 * mem
                case ("W", "A") | ("A", "W"):
                    return -60 * mem
                case ("P", "A"):
                    return -30 * mem
                case ("A", "T") | ("T", "A"):
                    return -50 * mem
                case ("A", "C"):
                    return -10 * mem
                case ("R", "O"):
                    return -20 * mem
                case ("Y", "J"):
                    return -30 * mem
                case ("L", "Y"):
                    return -30 * mem
                case ("L", "T"):
                    return -40 * mem
                case ("E", "A"):
                    return 30 * mem
        return 0

    def adjust_vertical_spacing(self):
        for i in range(10 + self.max_font_reduction):
            height = self.calculate_height()
            if height < self._max_h:
                break
            # TODO: How do we handle absolutely set leading of child elements? Small relative values might even produce clipping
            if i in [0, 2, 10, 13, 15] and self.input.styles.leading >= 750:
                self.input.adjust_style(leading=-50)
            elif i in [1, 7, 16] and self.input.paragraph_padding > 300:
                self.input.adjust_style(paragraph_padding=-150)
            elif i == 8:
                self.margin = self.margin * 0.5
            elif i == 11:
                adjust_tracking = clamp(-20 - self.input.styles.tracking, -20, 0)
                adjust_word_spacing = clamp(int(-self.input.styles.word_spacing * 0.25), 150 - self.input.styles.word_spacing, 0)
                self.input.adjust_style(tracking=adjust_tracking, word_spacing=adjust_word_spacing)
                self.split_data()
            elif i not in [0, 1, 7, 8, 10, 11, 13, 15, 16]:
                self.input.adjust_style(font_size=-1)
                self.split_data()

        height = self.calculate_height()
        if height < self._max_h:
            line_count = sum([len(entry.split) for entry in self.input.entries])
            paragraph_count = len([p for p in self.input.paragraphs])
            if line_count - paragraph_count > 0:
                adjust_leading = 1000 * (self._max_h - height) / (self.input.font_size * (line_count - paragraph_count))
                adjust_leading = int(clamp(adjust_leading, 0, -self.input.styles.adjustments.get("leading", 0)))
                self.input.adjust_style(leading=adjust_leading)
        elif height > self._max_h:
            print(f"Text exceeded maximum height, after adjusting spacing!")

    def adjust_horizontal_spacing(self):
        def get_max_width():
            max_width = 0
            for entry in self.input.entries:
                self.bold = entry.bold
                self.italic = entry.italic
                for line in entry.split:
                    w = self.calculate_line_width(entry, line)
                    if w == self._max_w:
                        continue
                    if w > max_width:
                        max_width = w
            return max_width

        for ix in range(20):
            width = get_max_width()
            if width < self._max_w:
                break
            if ix in [0, 1, 2, 4, 5, 7, 8, 11, 12, 15] and self.input.styles.tracking >= -20:
                self.input.adjust_style(tracking=-2)
            else:
                self.input.adjust_style(font_size=-2)

    def set_cursor_x(self, entry, line):
        if self.align_x == self.ALIGN_LEFT:
            self.cursor.x = self.margin.left * self.supersample + entry.padding.left
        elif self.align_x == self.ALIGN_RIGHT:
            w = self.calculate_line_width(entry, line)
            self.cursor.x = self._max_w - w + self.margin.left * self.supersample + entry.padding.left
        elif self.align_x == self.ALIGN_CENTER:
            w = self.calculate_line_width(entry, line)
            self.cursor.x = (self._max_w - w) // 2 + self.margin.left * self.supersample + entry.padding.left
        else:
            raise Exception(f"Invalid horizontal align: {self.align_x}")

    def set_cursor_y(self):
        height = self.calculate_height()
        if self.align_y == self.ALIGN_TOP:
            self.cursor.y = 0
        elif self.align_y == self.ALIGN_BOTTOM:
            self.cursor.y = self._max_h - height
        elif self.align_y == self.ALIGN_CENTER:
            # This isn't exactly the visual center some of the time. More noticeable if the text is only 1-2 lines. We'll fix it in post
            self.cursor.y = (self._max_h - height) // 2
        elif self.align_y == self.CENTER_SECTION:
            self.cursor.y = 0
            num_sections = len(list(self.input.sections))
            extra_height = self._max_h - height
            bias = self.base_bias_extra_height ** (num_sections - 1)
            weights_extra_height = [bias if i == 0 else (1 - bias) / (num_sections - 1) for i in range(num_sections)]
            for section, w in zip(self.input.sections, weights_extra_height):
                section.adjust_style(padding=Spacing(w * extra_height * 0.5 / self.supersample, 0))
        else:
            raise Exception(f"Invalid vertical align: {self.align_y}")

    def render(self, input_data, *, bbox, **kwargs):
        """
        :param input_data: The text to render. Either as str, or TextEntry
        :param tuple bbox:
        :key str overflow_policy_x:
        :key str overflow_policy_y:
        :key str linebreak_algorithm: Default: greedy
        :key str align_x:
        :key str align_y:
        :key Spacing margin:
        :key float scale_margin:
        :key str background_color:
        :key float supersample:
        :key bool fix_kerning: For fonts that don't provide a kerning table. Default: True
        :key float base_bias_extra_height:
        :return: PIL.Image
        """
        self.input = self.fix_input(input_data)
        self.set(bbox=bbox, **kwargs)
        self.input.set_style("supersample", self.supersample)
        self.split_data()

        if self.scale_margin:
            height = self.calculate_height()
            # TODO: reconsider this behaviour
            scale = clamp(2 - self.scale_margin - (1 - self.scale_margin) * 2 * height / self._max_h, self.scale_margin, 1)
            self.margin = Spacing(self.margin.top, self.margin.right * scale, self.margin.bottom, self.margin.left * scale)
        if self.overflow_policy_x == self.OVERFLOW_AUTO:
            self.adjust_horizontal_spacing()
        if self.overflow_policy_y == self.OVERFLOW_AUTO:
            self.adjust_vertical_spacing()

        w = int(self._max_w + self.supersample * self.margin.x)
        self.set_cursor_y()
        for section in self.input.sections:
            # TODO: Should we apply the margin on each section?
            section.computed[0] = self.cursor.y / self.supersample
            # bar_mt = Image.new("RGBA", (w, int(self.margin.top * self.supersample)), "#ffff00aa")
            # self.image.alpha_composite(bar_mt, (0, int(self.cursor.y)))
            self.cursor.y += self.margin.top * self.supersample
            # bar_pt = Image.new("RGBA", (w, int(section.padding.top)), "#ff00ffaa")
            # self.image.alpha_composite(bar_pt, (0, int(self.cursor.y)))
            self.cursor.y += section.padding.top
            for paragraph, is_last_paragraph in iter_is_last(section.paragraphs):
                self.cursor.y += paragraph.padding.top
                for entry, is_last_entry in iter_is_last(paragraph.entries):
                    self.cursor.y += entry.padding.top
                    self.bold = entry.bold
                    self.italic = entry.italic
                    for line in entry.split:
                        # This also increments cursor.y as required
                        self._render_line(entry, line)
                    if is_last_entry:
                        # The last line in each paragraph should only be calculated as cap-height instead of full leading
                        self.cursor.y -= entry.leading - self.FACTOR_CAP_HEIGHT * entry.font_size
                    self.cursor.y += entry.padding.bottom
                self.cursor.y += paragraph.padding.bottom
                if not is_last_paragraph:
                    as_list = list(paragraph.lines)
                    # there is one line, that one line has one token, and that token is an icon
                    if len(as_list) == 1 and len(as_list[0]) == 1 and as_list[0][0].startswith("[") and as_list[0][0].endswith("]"):
                        self.cursor.y -= (self.input.paragraph_padding * 0.4) // 1
                    self.cursor.y += self.input.paragraph_padding
            # bar_pt = Image.new("RGBA", (w, int(section.padding.bottom)), "#ff00ffaa")
            # self.image.alpha_composite(bar_pt, (0, int(self.cursor.y)))
            self.cursor.y += section.padding.bottom
            # bar_mb = Image.new("RGBA", (w, int(self.margin.top * self.supersample)), "#00ffffaa")
            # self.image.alpha_composite(bar_mb, (0, int(self.cursor.y)))
            self.cursor.y += self.margin.bottom * self.supersample
            section.computed[1] = self.cursor.y / self.supersample
            self.cursor.y += self.input.section_padding

        # TODO: Instead of rendering icons/images immediately, hold off to avoid scaling them twice
        self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
        return self.image

    def _render_line(self, entry, line):
        self.set_cursor_x(entry, line)

        for ix, token in enumerate(line):
            if token == self.TOKEN_BOLD:
                self.bold = not self.bold
                continue
            elif token == self.TOKEN_ITALIC:
                self.italic = not self.italic
                continue
            elif token.startswith("[") and token.endswith("]"):
                self.render_icon(entry, token)
                if ix < len(line) - 1 and line[ix + 1].startswith(","):
                    self.cursor.x -= entry.tracking + 0.75 * entry.word_spacing
                continue
            # Don't render space before punctuation
            if re.match(r"^[,.:?!]", token) is not None:
                if ix != 0 and line[ix - 1] in [self.TOKEN_BOLD, self.TOKEN_ITALIC]:
                    self.cursor.x -= entry.tracking + entry.word_spacing
            font = self.get_font(entry)
            for char, char_next in self.iterate_chars(token):
                stroke_width = round(entry.stroke_width * self.supersample)
                self.draw.text((self.cursor.x, self.cursor.y), char, entry.font_color, font=font, stroke_width=stroke_width)
                # self.image.alpha_composite(Image.new("RGBA", (2, int(entry.leading)), "black"), (int(self.cursor.x), int(self.cursor.y)))
                self.cursor.x += self.calculate_char_width(entry, font, char, char_next)
                # self.image.alpha_composite(Image.new("RGBA", (2, int(entry.leading)), "black"), (int(self.cursor.x), int(self.cursor.y)))
            self.cursor.x += entry.tracking + entry.word_spacing
        self.cursor.y += entry.leading

    def render_icon(self, entry, token):
        token = token.strip("[]")
        if token.startswith("ATTACK"):
            _, atk_type, atk_name, atk_stats = token.split(":")
            hit, dice = atk_stats.split("+")
            atk_data = {
                "name": atk_name,
                "type": "long" if "Long" in atk_type else "short" if "Short" in atk_type else "ranged" if "Ranged" in atk_type else "melee",
                "hit": int(hit),
                "dice": [int(d) for d in dice.split(",")]
            }
            # This is dogshit. But if we pass self to render_attack, the settings will be wiped
            text_renderer = self.__class__(self.asset_manager)
            rendered = render_attack(self.asset_manager, text_renderer, atk_data)
            self._do_render_full_width_icon(entry, rendered)
        elif token.startswith("SKILL"):
            text_renderer = self.__class__(self.asset_manager)
            icon = token.replace("SKILL:", "")
            rendered = apply_drop_shadow(render_skill_icon(self.asset_manager, text_renderer, icon), color="black")
            self._do_render_full_width_icon(entry, rendered)
        else:
            icon = self.get_icon(entry, token)
            if self.ICONS[token] == "simple":
                self.image.paste(entry.font_color, (int(self.cursor.x) - 5, int(self.cursor.y - 0.15 * entry.font_size)), mask=icon)
            elif self.ICONS[token] == "image":
                self.image.alpha_composite(icon, (int(self.cursor.x) - 5, int(self.cursor.y - 0.15 * entry.font_size)))
            self.cursor.x += self.get_icon_width(entry, icon)

    def _do_render_full_width_icon(self, entry, rendered):
        rendered = rendered.crop(rendered.getbbox())
        rendered = rendered.resize((int(self.supersample * rendered.width * entry.icon_scale),
                                    int(self.supersample * rendered.height * entry.icon_scale)))
        # Icons should always be centered?
        self.cursor.x = (self._max_w - entry.padding.x - rendered.width) // 2 + entry.padding.left + self.margin.left * self.supersample
        self.image.alpha_composite(rendered, (int(self.cursor.x), int(self.cursor.y - 0.2 * entry.leading)))
        # subtract the leading which gets added in self._render_line
        self.cursor.y += rendered.height - entry.leading - self.input.paragraph_padding // 2

    def get_icon(self, entry, token):
        icon = self.asset_manager.get_text_icon(token)
        icon = icon.resize((int(entry.font_size * 1.15 * icon.size[0] / icon.size[1]), int(entry.font_size * 1.15)), resample=Image.LANCZOS)
        icon_bbox = icon.getbbox()
        icon = icon.crop((icon_bbox[0], 0, icon_bbox[2], icon_bbox[3]))
        return icon

    def render_cmdr_name(self, name, subname, *, bbox, **kwargs):
        name_string = f"**{name}** - {subname}".upper() if subname is not None else f"**{name}**".upper()
        self.input = TextEntry.from_string(name_string, styles=kwargs.get("styles"))
        self.set(bbox=bbox, **kwargs)
        self.input.set_style("supersample", self.supersample)
        entry = next(self.input.entries)
        entry.split = [entry.tokens]
        width_line = self.calculate_line_width(entry, entry.tokens)
        num_cha = len(name_string) - 4
        tracking = (self._max_w - width_line) * 1000 / (entry.font_size * num_cha)
        if width_line < self._max_w:
            tracking = 0
        elif tracking >= -20:
            # actually do nothing
            pass
        # Welcome to 3 am
        elif tracking > -20 - width_line * (1 - (entry.styles.font_size - 3) / entry.styles.font_size) * 1000 / (entry.font_size * num_cha):
            self.input.adjust_style(font_size=-3)
            width_line = self.calculate_line_width(entry, entry.tokens)
            tracking = (self._max_w - width_line) * 1000 / (entry.font_size * num_cha)
            tracking = min(0, tracking)
        else:
            self.input = TextEntry.from_array([
                TextEntry(f"**{name}**".upper()),
                TextEntry(subname.upper()),
            ], styles=kwargs.get("styles"))
            self.input.adjust_style(font_size=-3)
            self.input.set_style("supersample", self.supersample)
            for e in self.input.entries:
                e.split = [e.tokens]
            self.set_cursor_y()
            self.cursor.y += self.margin.top * self.supersample
            for e in self.input.entries:
                self._render_line(e, e.tokens)

            self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
            return self.image

        self.input.adjust_style(tracking=int(tracking))
        self.set_cursor_y()
        self.cursor.y += self.margin.top * self.supersample
        self._render_line(entry, entry.tokens)
        self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
        return self.image

    def get_computed(self):
        return [section.computed for section in self.input.sections]

    def get_computed_between(self):
        it = iter([y for sect in self.input.sections for y in sect.computed][1:-1])
        for y in it:
            yield y, next(it)


class Graph:
    def __init__(self, size):
        self.size = size
        self.adjacency = [[0] * size for _ in range(size)]

    def add_edge(self, ix_node1, ix_node2, weight):
        self.adjacency[ix_node1][ix_node2] = weight

    # always searches from source ix 0 to target ix -1
    def dijkstra(self):
        dist = [float("inf")] * self.size
        dist[0] = 0
        prev = [None] * self.size
        queue = [i for i in range(self.size)]

        while queue:
            # FIXME: this might be wrong if 2 vertices randomly have the same distance from the source
            ix_current_vertex = dist.index(min([dist[ix] for ix in queue]))
            if ix_current_vertex == self.size - 1:
                break
            queue.remove(ix_current_vertex)
            for ix_neighbor, weight in enumerate(self.adjacency[ix_current_vertex]):
                if weight == 0 or ix_neighbor not in queue:
                    continue
                new_path_dist = dist[ix_current_vertex] + weight
                if new_path_dist < dist[ix_neighbor]:
                    dist[ix_neighbor] = new_path_dist
                    prev[ix_neighbor] = ix_current_vertex

        out = []
        step = prev[-1]
        while step:
            out.insert(0, step)
            step = prev[step]
        out.append(self.size)
        return out

    def display(self, tokens):
        import matplotlib.pyplot as plt
        import networkx as nx
        import numpy as np

        plt.figure(2, figsize=(12, 12))
        G = nx.from_numpy_array(np.array(self.adjacency), create_using=nx.DiGraph)
        lens = nx.shortest_path_length(G, source=0)
        layers = {v: [] for v in lens.values()}
        layers[max(lens.values()) + 1] = []
        for k, v in lens.items():
            layers[v].append(k)
        for ix in range(self.size):
            if ix not in lens.keys():
                layers[max(lens.values()) + 1].append(ix)
        pos = nx.multipartite_layout(G, subset_key=layers)
        nx.draw_networkx(G,
                         with_labels=True,
                         pos=pos,
                         labels={i: f"{i}\n{tokens[i]}" for i in range(self.size) if i in pos},
                         node_size=200,
                         )
        nx.draw_networkx_edge_labels(G, pos, edge_labels={(v, w): round(self.adjacency[v][w], 2) for (v, w) in G.edges})
        plt.tight_layout()
        plt.show()


def iter_is_last(iterable):
    try:
        *init, last = iterable
    except ValueError:
        return

    for ele in init:
        yield ele, False
    yield last, True


def clamp(x, minimum, maximum):
    return max(minimum, min(x, maximum))


if __name__ == "__main__":
    pass
