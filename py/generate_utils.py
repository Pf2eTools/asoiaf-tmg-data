from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import re
from copy import deepcopy


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


def render_stat_value(asset_manager, stat):
    background = asset_manager.get_stat_background()
    stat = str(stat)
    renderer = TextRenderer(stat, "Garamond", background.size, asset_manager, font_size=46, font_color="white", stroke_width=0,
                            supersample=4, bold=True, align_y=TextRenderer.ALIGN_CENTER)
    rd_stat = renderer.render()
    offset = (2, 0) if stat.endswith("+") else (0, 0)
    background.alpha_composite(rd_stat, offset)
    return background


def render_cost(asset_manager, cost, border="gold", is_commander=False):
    commander = "commander" if is_commander else "regular"
    background = asset_manager.get_cost_bg(border, commander)
    cost = str(cost)
    renderer = TextRenderer(cost, "Garamond", background.size, asset_manager, font_size=46, font_color="white", stroke_width=0,
                            supersample=4, bold=True, align_y=TextRenderer.ALIGN_CENTER)
    rd_stat = renderer.render()
    offset = (-1, -2) if is_commander else (0, 0)
    background.alpha_composite(rd_stat, offset)
    return background


def render_attack(asset_manager, attack_data, border_color="Gold"):
    atk_type = attack_data.get("type")
    atk_name = attack_data.get("name")
    tohit = attack_data.get("hit")
    atk_ranks = attack_data.get("dice")

    attack_bg = asset_manager.get_attack_bg(border_color)
    attack_dice_bg = asset_manager.get_attack_dice_bg()

    attack_bar = Image.new("RGBA", (367, 166))
    skill_icon = render_skill_icon(asset_manager, atk_type, border_color)
    attack_bar.alpha_composite(attack_bg, (skill_icon.size[0] // 2, 14 + (attack_bg.size[1] - 106) // 2))
    attack_bar.alpha_composite(skill_icon)

    atk_name_color = "#0e2e45" if atk_type == "melee" else "#87282a"
    name_renderer = TextRenderer(atk_name.upper(), "Tuff", (180, 60), asset_manager, font_size=29, font_color=atk_name_color,
                                 stroke_width=0.7, leading=0.9, italic=True, padding=(5, 5, 5, 5), align_y=TextRenderer.ALIGN_CENTER)
    rd_atk_name = name_renderer.render()
    attack_bar.alpha_composite(rd_atk_name, (221 - rd_atk_name.size[0] // 2, 56 - rd_atk_name.size[1] // 2))

    if atk_type != "melee":
        range_icon = asset_manager.get_attack_range_icon(atk_type, border_color)
        attack_bar.alpha_composite(apply_drop_shadow(range_icon), (60, -14))

    rd_statistics = Image.new("RGBA", attack_bar.size)
    rd_statistics.alpha_composite(attack_dice_bg, (104, 88))
    rd_to_hit = render_stat_value(asset_manager, f"{tohit}+")
    rd_statistics.alpha_composite(apply_drop_shadow(rd_to_hit), (58, 56))
    rank_colors = ["#648f4a", "#dd8e29", "#bd1a2b"]
    for i in range(len(atk_ranks)):
        rank_bg = Image.new("RGBA", (35, 35), rank_colors[i])
        renderer_num_dice = TextRenderer(str(atk_ranks[i]), "Garamond", (44, 44), asset_manager, font_size=37, font_color="#cdcecb",
                                         stroke_width=0.1, bold=True, padding=(0, 0, 0, 0))
        rd_num_dice = renderer_num_dice.render()

        # This was an interesting programming journey, but having a transparent font makes it pretty hard to read the
        # text rd_num_dice = render_text_line(str(atk_ranks[i]), "black", 35, "Garamond-Bold", stroke_width=0)
        rank_bg.alpha_composite(rd_num_dice, (-5, 1))
        # mask = Image.new("RGBA", (35, 35))
        # mask.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 5))
        # r,g,b,_ = rank_bg.split()
        # rank_bg = Image.merge("RGBA", (r,g,b,ImageChops.invert(mask.getchannel("A"))))
        rd_statistics.alpha_composite(add_rounded_corners(rank_bg, 10), (164 + i * 43, 98))
    attack_bar.alpha_composite(apply_drop_shadow(rd_statistics, color="#00000077"), (-20, -20))

    return attack_bar


def render_skill_icon(asset_manager, name, highlight_color="Gold"):
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
        rd_morale = render_stat_value(asset_manager, f'{number or 5}+')
        x, y = (134 - rd_morale.size[0]) // 2, 196 - 9 - rd_morale.size[1]
        rendered.alpha_composite(rd_morale, (x, y))
        x, y = (134 - icon_morale.size[0]) // 2, 9
        rendered.alpha_composite(icon_morale, (x, y))
    else:
        icon = asset_manager.get_skill_icon(name, highlight_color)
        x, y = (134 - icon.size[0]) // 2, (134 - icon.size[1]) // 2
        rendered.alpha_composite(icon, (x, y))
        if number is not None:
            renderer_number = TextRenderer(number, "Garamond", (134, 134), asset_manager, bold=True, font_color="white", font_size=36,
                                           align_y=TextRenderer.ALIGN_CENTER)
            rendered.alpha_composite(renderer_number.render())
    return rendered


def render_skill_icons(asset_manager, icons, highlight_color="Gold"):
    rd_icons = [render_skill_icon(asset_manager, icon, highlight_color) for icon in icons]
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


def get_ability_data_for_renderer(abilities_data, color):
    abilities_to_render = []
    for ability in abilities_data:
        data = {
            "type": "section",
            "content": [
                {
                    "type": "paragraph",
                    "content": [c for c in [
                        {
                            "type": "text",
                            "style": {
                                "color": color,
                                "tracking": 24,
                            },
                            "content": f"**{ability.get('name').upper()}**"
                        },
                        {"type": "text", "content": f"**{ability.get('trigger')}**"} if ability.get("trigger") is not None else None,
                        {"type": "text", "content": "\n".join(ability.get("effect"))}
                    ] if c is not None]
                }
            ]
        }
        abilities_to_render.append(data)
    return abilities_to_render


def get_requirement_data_for_renderer(requirements):
    to_render = []
    for req in requirements:
        data = {
            "type": "section",
            "content": [
                {
                    "type": "paragraph",
                    "content": [c for c in [
                        {
                            "type": "text",
                            "style": {
                                "tracking": 40,
                            },
                            "content": f"**{req.get('heading')}**"
                        } if req.get("heading") is not None else None,
                        {"type": "text", "content": req.get("text")},
                    ] if c is not None]
                }
            ]
        }
        to_render.append(data)
    return to_render


def render_character_box(asset_manager, faction):
    return render_small_box(asset_manager, faction, "CHARACTER")


def render_commander_box(asset_manager, faction):
    return render_small_box(asset_manager, faction, "COMMANDER", font_color=get_faction_text_color(faction), tracking=0, font_size=36)


def render_small_box(asset_manager, faction, text, font_color="#5d4d40", tracking=50, font_size=38):
    # TODO (MAYBE): Shrink (or crop out the center of) the box when the text is short?
    box = asset_manager.get_character_box(faction)
    renderer_character = TextRenderer(text, "Tuff", (200, 35), asset_manager, bold=True, stroke_width=0.1, font_size=font_size,
                                      font_color=font_color, tracking=tracking, padding=(5, 5, 5, 5), align_y=TextRenderer.ALIGN_CENTER,
                                      overflow_policy_x=TextRenderer.OVERFLOW_CLIP)
    rendered_character_text = renderer_character.render()
    box.alpha_composite(rendered_character_text, (box.width // 2 - 100, 13))
    return box


CHAR_BULLET = "•"


class Cursor:
    x = 0
    y = 0


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

    def __init__(self, data, font_family, bounding_box, asset_manager, **kwargs):
        """
        Documentation text
        
        :param data: The text to render. Either as str, or an array of dictionaries.
        :param str font_family: Font name
        :param tuple bounding_box:
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
        self.max_w, self.max_h = bounding_box
        self.overflow_policy_y = kwargs.get("overflow_policy_y", self.OVERFLOW_AUTO)
        self.overflow_policy_x = kwargs.get("overflow_policy_x", self.OVERFLOW_AUTO)
        self.linebreak_algorithm = kwargs.get("linebreak_algorithm", self.LINEBREAK_GREEDY)
        self.scale_padding_x = kwargs.get("scale_padding_x", 0)
        self.font_family = font_family
        self._fonts = {}
        self.font_size = kwargs.get("font_size", 20)
        self.font_color = kwargs.get("font_color", "black")
        self.background_color = kwargs.get("background_color", (0, 0, 0, 0))
        self.stroke_width = kwargs.get("stroke_width", 0.3)
        self.bold = self._bold = kwargs.get("bold", False)
        self.italic = self._italic = kwargs.get("italic", False)
        self.align_x = kwargs.get("align_x", self.ALIGN_CENTER)
        self.align_y = kwargs.get("align_y", self.ALIGN_TOP)
        self._supersample = kwargs.get("supersample", 1)
        self.fix_kerning = kwargs.get("fix_kerning", True)
        self.tracking = kwargs.get("tracking", 0)
        self._tracking = self.tracking * self._font_size / 1000
        self._word_spacing = kwargs.get("word_spacing", 200)
        self.leading = kwargs.get("leading", 1.15)
        self.padding = kwargs.get("padding", (10, 10, 10, 10))
        self.paragraph_padding = kwargs.get("paragraph_padding", 0.7)
        self.section_padding = kwargs.get("section_padding", 0)
        self.base_bias_extra_height = kwargs.get("base_bias_extra_height", 0.7)

        self.asset_manager = asset_manager
        self.input = self.fix_input(data)
        self.cursor = Cursor()
        self.image = Image.new("RGBA", (self._max_w, self._max_h), self.background_color)
        self.draw = ImageDraw.Draw(self.image)
        self.rendered_section_coords = []

    @property
    def supersample(self):
        if int(self.stroke_width) == self.stroke_width:
            return self._supersample
        else:
            # TODO: Make sure this is at least as big as self._supersample. Care with the stroke_width math
            return 1 / (self.stroke_width % 1)

    @property
    def _stroke_width(self):
        """
        The stroke_width property (see self.render below) would be really nice if it worked with smaller font sizes (or floats)
        As a workaround, we use a bigger fontsize, then downscale the image later
        """
        if self.stroke_width == 0:
            return 0
        elif int(self.stroke_width) == self.stroke_width:
            return self.stroke_width
        else:
            return int(self.stroke_width / (self.stroke_width % 1))

    @property
    def _max_w(self):
        return int(self.max_w * self.supersample)

    @property
    def _max_h(self):
        return int(self.max_h * self.supersample)

    @property
    def _font_size(self):
        return self.font_size * self.supersample

    @property
    def _leading(self):
        return self._font_size * self.leading

    def set_styles(self, styles):
        self._tracking = styles.get("tracking", self.tracking) * self._font_size / 1000
        self.bold = styles.get("bold", self.bold)
        self.italic = styles.get("italic", self.italic)

    @property
    def word_spacing(self):
        return self._font_size * self._word_spacing / 1000

    @property
    def _padding(self):
        return tuple(self.supersample * x for x in self.padding)

    @property
    def _paragraph_padding(self):
        return self._font_size * self.paragraph_padding

    @property
    def _section_padding(self):
        return int(self.supersample * self.section_padding)

    def get_font(self, bold=None, italic=None):
        bold = bold if bold is not None else self.bold
        italic = italic if italic is not None else self.italic
        font_style_str = "Bold" if bold else ""
        font_style_str += "Italic" if italic else ""
        font_style_str = font_style_str or "Normal"
        key = f"{self.font_family}-{font_style_str}-{self._font_size}"
        font = self._fonts.get(key)
        if font is None:
            font_path = self.FONTS.get(f"{self.font_family}-{font_style_str}")
            font = ImageFont.truetype(font_path, self._font_size)
            self._fonts[key] = font
            return font
        else:
            return font

    @staticmethod
    def fix_input(input_data):
        if type(input_data) == str:
            return [
                {
                    "type": "section",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "content": input_data
                                }
                            ]
                        }
                    ]
                }
            ]
        return input_data

    @staticmethod
    def iterate_chars(token):
        for ix, char in enumerate(token):
            char_next = token[ix + 1] if ix + 1 < len(token) else " "
            yield char, char_next

    def calculate_line_width(self, line, token_widths=None):
        width = self._padding[0] + self._padding[2]
        if token_widths is None:
            token_widths = self.get_token_widths(line)
        for ix, width_token in enumerate(token_widths):
            width += width_token
            # FIXME: we need to check if the token is the last token with width 0
            if width_token != 0 and ix != len(line) - 1:
                width += self.word_spacing

        return width

    def get_token_widths(self, tokens):
        bold = self.bold
        italic = self.italic
        widths = []
        for token in tokens:
            if token == self.TOKEN_BOLD:
                bold = not bold
                widths.append(0)
                continue
            elif token == self.TOKEN_ITALIC:
                italic = not italic
                widths.append(0)
                continue
            font = self.get_font(bold=bold, italic=italic)
            token_width = self.calculate_token_width(font, token)
            widths.append(token_width)
        return widths

    def calculate_token_width(self, font, token):
        if token == self.TOKEN_ITALIC or token == self.TOKEN_BOLD:
            return 0
        elif token == self.TOKEN_NEWLINE:
            return self._max_w
        elif token.startswith("[") and token.endswith("]"):
            token = token.strip("[]")
            # FIXME: Uh Oh! Stinky! This crashes the renderer if we encounter an inline symbol that doesn't exist
            if self.ICONS.get(token) is None:
                return self._max_w
            icon = self.get_icon(token)
            return self.get_icon_width(icon)
        w = 0
        for char, char_next in self.iterate_chars(token):
            w += self.calculate_char_width(font, char, char_next)
        return w

    def calculate_char_width(self, font, char, char_next):
        offset_chars = font.getlength(char + char_next) - font.getlength(char_next)
        return offset_chars + self._tracking + self.fix_kern(font, char, char_next)

    def get_icon_width(self, icon):
        return icon.size[0] + 0.1 * self._font_size + self._tracking

    @staticmethod
    def tokenize(string):
        tokens = [t for t in re.split(r"(\[.*?]|(?<!\\)\*{1,2}| |\n)", string.strip()) if t.strip(" ")]
        return tokens

    def split_text(self, input_string):
        if self.linebreak_algorithm == self.LINEBREAK_GREEDY:
            return self.split_text_greedy(input_string)
        elif self.linebreak_algorithm == self.LINEBREAK_OPTIMAL:
            return self.split_text_optimal(input_string)
        raise Exception(f"Invalid linebreak algorithm: {self.linebreak_algorithm}")

    def split_text_greedy(self, input_string):
        tokens = self.tokenize(input_string)
        lines = [[]]
        cur_len = 0
        skipped = []
        font = self.get_font()
        for token in tokens:
            token_len = self.calculate_token_width(font, token)
            if token_len == 0:
                skipped.append(token)
                continue

            break_line = False
            if token.startswith(CHAR_BULLET):
                break_line = True
            # don't put single commas and periods in a new line. I guess numbers as well.
            elif cur_len + token_len + self.word_spacing > self._max_w - self._padding[0] - self._padding[2] and len(token) > 1:
                break_line = True
            else:
                pass

            if token == self.TOKEN_NEWLINE:
                cur_len = 0
                lines.append([])
            elif break_line:
                cur_len = token_len
                lines.append(skipped + [token])
                skipped = []
            else:
                cur_len += token_len + self.word_spacing
                lines[-1] += skipped
                skipped = []
                lines[-1].append(token)
        lines[-1] += skipped

        return [ln for ln in lines if len(ln) > 0]

    def split_text_optimal(self, input_string):
        tokens = self.tokenize(input_string)
        for ix, token in reversed(list(enumerate(tokens))):
            if ix == 0 or not token.startswith(CHAR_BULLET):
                continue
            for i in range(ix - 1, 0, -1):
                if tokens[i] in [self.TOKEN_BOLD, self.TOKEN_ITALIC]:
                    continue
                elif tokens[i] == self.TOKEN_NEWLINE:
                    break
                else:
                    tokens.insert(i + 1, self.TOKEN_NEWLINE)
                    break
        tokens.insert(0, "")
        token_widths = self.get_token_widths(tokens)

        # Dijkstra might throw errors, because no shortest path exists. In this case we should relax the threshold
        try:
            threshold = 9 ** 2
            breakpoints = self.find_optimal_breaks(tokens, token_widths, threshold)
        except ValueError:
            threshold = 18 ** 2
            breakpoints = self.find_optimal_breaks(tokens, token_widths, threshold)

        optimal_breaks = [[t for t in tokens[i + 1:j + 1] if t != self.TOKEN_NEWLINE] for i, j in zip([0] + breakpoints, breakpoints)]
        return [ln for ln in optimal_breaks if ln]

    def find_optimal_breaks(self, tokens, token_widths, threshold):
        graph = Graph(len(tokens))
        active_breaks = [0]
        while active_breaks:
            if active_breaks[0] == len(tokens) - 1:
                break
            for ix_token_end in range(active_breaks[0] + 1, len(tokens)):
                potential_line = tokens[active_breaks[0] + 1:ix_token_end + 1]
                widths = token_widths[active_breaks[0] + 1:ix_token_end + 1]
                is_final_line = ix_token_end == len(tokens) - 1
                penalty = self.calculate_line_penalty(potential_line, widths, is_final_line)
                if penalty == float("inf"):
                    break
                if penalty > threshold and not is_final_line and tokens[ix_token_end] != self.TOKEN_NEWLINE:
                    continue
                graph.add_edge(active_breaks[0], ix_token_end, penalty)
                if ix_token_end not in active_breaks:
                    active_breaks.append(ix_token_end)
            active_breaks.pop(0)

        return graph.dijkstra()

    def calculate_line_penalty(self, line, token_widths, is_final_line):
        # Starting with a little penalty helps to minimize lines
        penalty = 2
        line_no_newline = [tk for ix, tk in enumerate(line) if ix < len(line) - 1 or tk != self.TOKEN_NEWLINE]
        token_widths_no_newline = [token_widths[ix] for ix, tk in enumerate(line) if ix < len(line) - 1 or tk != self.TOKEN_NEWLINE]
        tokens_nonzero_len = [tk for ix, tk in enumerate(line_no_newline) if token_widths_no_newline[ix]]
        line_width = self.calculate_line_width(line_no_newline, token_widths_no_newline)
        if len(line) == 1 and line_width > self._max_w:
            pass
        elif line_width > self._max_w:
            return float("inf")
        factor_line_length = 30 if is_final_line else 100
        penalty += factor_line_length * ((self._max_w - line_width) / (self._max_w - self._padding[0] - self._padding[2])) ** 3
        if tokens_nonzero_len:
            # reward lines ending in punctuation
            if re.search(r"[,.;:!?]$", tokens_nonzero_len[-1]):
                penalty -= 3
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

    def split_data(self, data):
        self.bold = self._bold
        self.italic = self._italic
        new_data = deepcopy(data)
        for section in new_data:
            for paragraph in section["content"]:
                for lines in paragraph["content"]:
                    styles = lines.get("style", paragraph.get("style", section.get("style", {})))
                    self.set_styles(styles)
                    lines["content"] = self.split_text(lines["content"])
        return new_data

    @staticmethod
    def count_data(data):
        section_counts = []
        for section in data:
            sc = {
                "section": 1,
                "paragraph": 0,
                "line": 0,
            }
            for paragraph in section["content"]:
                sc["paragraph"] += 1
                for lines in paragraph["content"]:
                    for line in lines["content"]:
                        sc["line"] += 1
            section_counts.append(sc)

        count = {
            "section": len(section_counts),
            "paragraph": sum([sc["paragraph"] for sc in section_counts]),
            "line": sum([sc["line"] for sc in section_counts]),
        }

        return count, section_counts

    def calculate_height(self, data):
        height = 0
        # I have cancer
        for ix_section, section in enumerate(data):
            height += self._padding[1]
            for ix_paragraph, paragraph in enumerate(section["content"]):
                for lines in paragraph["content"]:
                    for line in lines["content"]:
                        if len(line) == 1 and line[0].startswith("[") and line[0].endswith("["):
                            if line[0].startswith("[ATTACK"):
                                height += 165 * self.supersample
                            else:
                                height += self.get_icon(line[0].strip("[]")).size[1] * self.supersample
                        else:
                            height += self._leading
                height -= self._leading - 0.82 * self._font_size
                if ix_paragraph < len(section["content"]) - 1:
                    height += self._paragraph_padding
            height += self._padding[3]
            if ix_section < len(data) - 1:
                height += self._section_padding

        return height

    def fix_kern(self, font, char1, char2):
        if not self.fix_kerning:
            return 0
        mem = self._font_size / 1000
        if self.font_family == "Tuff":
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
                case ("A", "T"):
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
        return 0

    def adjust_vertical_spacing(self, data):
        initial_leading = self.leading
        for i in range(19):
            height = self.calculate_height(data)
            if height < self._max_h:
                break
            if i in [0, 2, 10, 13, 15] and self.leading >= 0.75:
                self.leading -= 0.05
            elif i in [1, 7, 16] and self.paragraph_padding > 0.3:
                self.paragraph_padding -= 0.15
            elif i in [3, 4, 5, 6, 9, 12, 14, 17, 18]:
                self.font_size -= 1
                data = self.split_data(self.input)
            elif i == 8:
                self.padding = (self.padding[0], self.padding[1] // 2, self.padding[2], self.padding[3] // 2)
            elif i == 11:
                self.tracking = max(-20, self.tracking - 20)
                self._word_spacing = max(150, self._word_spacing * 0.75)
                data = self.split_data(self.input)

        height = self.calculate_height(data)
        if height < self._max_h:
            count, _ = self.count_data(data)
            if count["line"] - count["paragraph"] > 0:
                self.leading += (self._max_h - height) / (self._font_size * (count["line"] - count["paragraph"]))
                self.leading = min(initial_leading, self.leading)
        elif height > self._max_h + self._padding[1] + self._padding[3]:
            print(f"Text exceeded maximum height, after adjusting spacing!")

        return data

    def adjust_horizontal_spacing(self, data):
        max_width = 0
        max_textlen = 0
        for section in data:
            for paragraph in section["content"]:
                for lines in paragraph["content"]:
                    for line in lines["content"]:
                        w = self.calculate_line_width(line)
                        if w > max_width:
                            max_width = w
                            max_textlen = len(" ".join([tk for tk in line if tk.strip("*") and not tk.startswith("[")]))
                            max_textlen += 2 * len([tk for tk in line if tk.startswith("[")])
        if max_width < self._max_w:
            return data

        # TODO: Do we need to calculate the linebreaks again?
        self.font_size -= self.font_size * (self._font_size * max_textlen + 50 * (self._max_w - max_width)) / (
                self._font_size * max_textlen - 50 * max_width)
        self.tracking = -20

        return data

    def set_cursor_x(self, line):
        if self.align_x == self.ALIGN_LEFT:
            self.cursor.x = self._padding[0]
        elif self.align_x == self.ALIGN_RIGHT:
            w = self.calculate_line_width(line)
            self.cursor.x = self._max_w - w + self._padding[0]
        elif self.align_x == self.ALIGN_CENTER:
            w = self.calculate_line_width(line)
            self.cursor.x = (self._max_w - w) // 2 + self._padding[0]
        else:
            raise Exception(f"Invalid horizontal align: {self.align_x}")

    def set_cursor_y(self, height, num_sections):
        extra_padding = [0 for _ in range(num_sections)]
        if self.align_y == self.ALIGN_TOP:
            self.cursor.y = 0
        elif self.align_y == self.ALIGN_BOTTOM:
            self.cursor.y = self._max_h - height
        elif self.align_y == self.ALIGN_CENTER:
            # This isn't exactly the visual center some of the time. More noticeable if the text is only 1-2 lines. We'll fix it in post
            self.cursor.y = (self._max_h - height) // 2
        elif self.align_y == self.CENTER_SECTION:
            self.cursor.y = 0
            extra_height = self._max_h - height
            bias = self.base_bias_extra_height ** (num_sections - 1)
            weights_extra_height = [bias if i == 0 else (1 - bias) / (num_sections - 1) for i in range(num_sections)]
            return [w * extra_height * 0.5 for w in weights_extra_height]
        else:
            raise Exception(f"Invalid vertical align: {self.align_y}")
        return extra_padding

    def render(self):
        data = self.split_data(self.input)

        if self.scale_padding_x:
            height = self.calculate_height(data)
            scale = max(self.scale_padding_x, min(1, 2 - self.scale_padding_x - (1 - self.scale_padding_x) * 2 * height / self._max_h))
            self.padding = (int(scale * self.padding[0]), self.padding[1], int(scale * self.padding[2]), self.padding[3])
        if self.overflow_policy_x == self.OVERFLOW_AUTO:
            self.adjust_horizontal_spacing(data)
        if self.overflow_policy_y == self.OVERFLOW_AUTO:
            data = self.adjust_vertical_spacing(data)

        height = self.calculate_height(data)
        extra_padding = self.set_cursor_y(height, len(data))
        # TODO: Mr. President, a sixth layer of indentation has hit the render function. The codebase is under attack.
        for ix_section, section in enumerate(data):
            y_start_section = self.cursor.y / self.supersample
            self.cursor.y += self._padding[1] + extra_padding[ix_section]
            for ix_paragraph, paragraph in enumerate(section["content"]):
                for lines in paragraph["content"]:
                    self.bold = self._bold
                    self.italic = self._italic
                    styles = lines.get("style", paragraph.get("style", section.get("style", {})))
                    for line in lines["content"]:
                        self._render_line(line, styles)
                # The last line in each paragraph should only be calculated as cap-height instead of full leading. 0.82 is a good estimate
                self.cursor.y -= self._leading - 0.82 * self._font_size
                if ix_paragraph < len(section["content"]) - 1:
                    self.cursor.y += self._paragraph_padding
            coords = (y_start_section, (self.cursor.y + self._padding[3] + extra_padding[ix_section]) / self.supersample)
            self.rendered_section_coords.append(coords)
            self.cursor.y += self._padding[3] + extra_padding[ix_section] + self._section_padding

        self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
        return self.image

    def _render_line(self, line, styles):
        self.set_styles(styles)
        color = styles.get("color", self.font_color)
        self.set_cursor_x(line)

        for ix, token in enumerate(line):
            if token == self.TOKEN_BOLD:
                self.bold = not self.bold
                continue
            elif token == self.TOKEN_ITALIC:
                self.italic = not self.italic
                continue
            elif token.startswith("[") and token.endswith("]"):
                self.render_icon(token, color)
                if ix < len(line) - 1 and line[ix + 1].startswith(","):
                    self.cursor.x -= self._tracking + 0.75 * self.word_spacing
                continue
            # TODO: Whats going on here?
            if re.match(r"^[,.:?!]", token) is not None:
                if ix != 0 and line[ix - 1] in [self.TOKEN_BOLD, self.TOKEN_ITALIC]:
                    self.cursor.x -= self._tracking + self.word_spacing
            font = self.get_font()
            for char, char_next in self.iterate_chars(token):
                self.draw.text((self.cursor.x, self.cursor.y), char, color, font=font, stroke_width=self._stroke_width)
                self.cursor.x += self.calculate_char_width(font, char, char_next)
            self.cursor.x += self._tracking + self.word_spacing
        self.cursor.y += self._leading

    def render_icon(self, token, color=None):
        color = color or self.font_color
        token = token.strip("[]")
        if token.startswith("ATTACK"):
            _, atk_type, atk_name, atk_stats = token.split(":")
            hit, dice = atk_stats.split("+")
            atk_data = {
                "name": atk_name,
                "type": "long" if "Long" in atk_type else "short" if "Short" in atk_type else "melee",
                "hit": int(hit),
                "dice": [int(d) for d in dice.split(",")]
            }
            rendered = render_attack(self.asset_manager, atk_data)
            self._do_render_full_width_icon(rendered)
        elif token.startswith("SKILL"):
            rendered = apply_drop_shadow(render_skill_icon(self.asset_manager, token.replace("SKILL:", "")), color="black")
            self._do_render_full_width_icon(rendered)
        else:
            icon = self.get_icon(token)
            if self.ICONS[token] == "simple":
                self.image.paste(color, (int(self.cursor.x) - 5, int(self.cursor.y - 0.15 * self._font_size)), mask=icon)
            elif self.ICONS[token] == "image":
                self.image.alpha_composite(icon, (int(self.cursor.x) - 5, int(self.cursor.y - 0.15 * self._font_size)))
            self.cursor.x += self.get_icon_width(icon)

    def _do_render_full_width_icon(self, rendered):
        rendered = rendered.crop(rendered.getbbox())
        rendered = rendered.resize((int(self.supersample * rendered.size[0]), int(self.supersample * rendered.size[1])))
        # Icons should always be centered?
        self.cursor.x = (self._max_w - self._padding[0] - self._padding[2] - rendered.size[0]) // 2 + self._padding[0]
        self.image.alpha_composite(rendered, (int(self.cursor.x), int(self.cursor.y - 0.2 * self._leading)))
        # subtract the leading which gets added in self._render_line
        self.cursor.y += rendered.size[1] - self._leading

    def get_icon(self, token):
        icon = self.asset_manager.get_text_icon(token)
        icon = icon.resize((int(self._font_size * 1.15 * icon.size[0] / icon.size[1]), int(self._font_size * 1.15)), resample=Image.LANCZOS)
        icon_bbox = icon.getbbox()
        icon = icon.crop((icon_bbox[0], 0, icon_bbox[2], icon_bbox[3]))
        return icon

    def render_cmdr_name(self, name, subname):
        name_string = f"**{name}** - {subname}".upper() if subname is not None else f"**{name}**".upper()
        tokenized = self.tokenize(name_string)
        width_line = self.calculate_line_width(tokenized)
        height = 0.82 * self._font_size + self._padding[1] + self._padding[3]
        text_len = len(name_string) - 4
        tracking = (self._max_w - width_line) * 1000 / (self._font_size * text_len)
        if width_line < self._max_w:
            tracking = 0
        elif tracking >= -20:
            # actually do nothing
            pass
        # Welcome to 3 am
        elif tracking > -20 - width_line * (1 - (self.font_size - 3) / self.font_size) * 1000 / (self._font_size * text_len):
            self.font_size -= 3
            width_line = self.calculate_line_width(tokenized)
            tracking = (self._max_w - width_line) * 1000 / (self._font_size * text_len)
            tracking = min(0, tracking)
        else:
            self.font_size -= 3
            height += self._leading
            self.set_cursor_y(height, 1)
            self.cursor.y += self._padding[1]
            self._render_line(self.tokenize(f"**{name}**".upper()), {})
            self._render_line(self.tokenize(subname.upper()), {})
            self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
            return self.image

        self.set_cursor_y(height, 1)
        self.cursor.y += self._padding[1]
        self._render_line(tokenized, {"tracking": tracking})
        self.image = self.image.resize((self.max_w, self.max_h), resample=Image.LANCZOS)
        return self.image


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


if __name__ == "__main__":
    pass
