from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
import re
from asset_manager import AssetManager


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
    alpha.paste(circle.crop((rad, rad, 2 * rad, 2* rad)), (w - rad, h - rad))

    im = im.convert("RGBA")
    old_alpha = im.getchannel("A")
    im.putalpha(ImageChops.darker(alpha, old_alpha))

    return im


def split_on_center_space(text, maxlen=14):
    # If the length of the text is less than the maximum length or there's no space, return the text in a single-item list
    if len(text) < maxlen or ' ' not in text:
        return [text]

    # Find the middle index of the string
    middle = len(text) // 2
    left_index = text.rfind(' ', 0, middle)  # Search for space going left from the middle
    right_index = text.find(' ', middle)  # Search for space going right from the middle

    # Determine the closest space to the middle to use as the split point
    # If no space to the left, use the right one; if both exist, choose the closest
    if left_index == -1 or (right_index != -1 and (middle - left_index) > (right_index - middle)):
        split_index = right_index
    else:
        split_index = left_index

    # Split the string into two parts
    part1 = text[:split_index]
    part2 = text[split_index + 1:]  # +1 to exclude the space itself

    # Return the parts in a list
    return [part1, part2]


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
        "neutral":"Silver",
        "nightswatch":"Gold",
        "stark":"Gold",
        "targaryen":"Gold",
        "baratheon":"Silver",
        "bolton":"Gold",
        "freefolk":"Gold",
        "greyjoy":"Gold",
        "martell":"Gold",
        "lannister":"Silver",
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
    shadow = Image.new('RGBA', (image.size[0] + border * 2, image.size[1] + border * 2))
    image_alpha_channel = image.split()[-1]
    pixels = image_alpha_channel.load()
    for x in range(0, image_alpha_channel.size[0]):
        for y in range(0, image_alpha_channel.size[1]):
            if pixels[x, y] < 255:
                pixels[x, y] = 0

    mask = Image.new("RGBA", image.size)
    for xy in [(0,0), (shadow_size, 0), (-shadow_size, 0), (0, shadow_size), (0, -shadow_size)]:
        mask.paste(image_alpha_channel, xy, mask=image_alpha_channel)

    shadow.paste(color, (border, border), mask=mask)
    for i in range(passes):
        shadow = shadow.filter(ImageFilter.BLUR)
    shadow.alpha_composite(image, (border, border))
    return shadow


# TODO: Breaks down for specials
def calc_height_paragraph(paragraph, font_size, line_padding):
    return (len(paragraph) - 1) * int(font_size * FACTOR_FIXED_LINE_HEIGHT + line_padding) + font_size + 7


def calc_height_paragraphs(paragraphs, font_size, line_padding, paragraph_padding):
    h = [calc_height_paragraph(p, font_size, line_padding) for p in paragraphs]
    return sum(h) + (len(h) - 1) * paragraph_padding


def text_to_image(text, font_path, font_size, font_color, stroke_width=0.35, letter_spacing=0, max_width=0, **kwargs):
    # The stroke_width property (see below) would be really nice if it worked with smaller font sizes (or floats)
    # As a workaround, we use a bigger fontsize, then downscale the image later
    scale = 1 if int(stroke_width) == stroke_width else 1 / (stroke_width % 1)
    stroke_width = 0 if stroke_width == 0 else int(stroke_width / (stroke_width % 1))

    font = ImageFont.truetype(font_path, int(font_size * scale))
    bbox = font.getbbox(text)
    # Dynamically adjust the letter-spacing if the text is too wide
    if max_width != 0 and bbox[2] > max_width * scale:
        letter_spacing -= min(1.1, ((bbox[2] - max_width * scale) * 1.05) / len(text))

    # Offset, otherwise tall letters are clipped, Umlaute (ÖÄÜ) in particular
    offset_x, offset_y = 0, 1 + int(7 * scale)
    # For vertical center alignment, ensure the height is consistent. "yjg" are the tallest letters.
    # Usually, this means h == font_size + 7 after scaling the image back to size
    w, h = bbox[2] + int((len(text) - 1) * letter_spacing), font.getbbox("yjg")[3] + 1 + int(7 * scale)
    # Avoid clipping of letters such as "j" at the start of the text
    if bbox[0] < 0:
        w -= bbox[0]
        offset_x -= bbox[0]
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    for i in range(len(text)):
        char = text[i]
        draw.text((offset_x, offset_y), char, font_color, font=font, stroke_width=stroke_width)

        char_next = text[i + 1] if i + 1 < len(text) else " "
        offset_next = font.getlength(char + char_next) - font.getlength(char_next)
        # Fix the disgusting Kerning of uppercase T and small letters
        if "Tuff" in font_path and char == "T" and font.getbbox(char_next)[1] >= font.getbbox("a")[1]:
            offset_next -= 4
        offset_x += offset_next + letter_spacing

    canvas = canvas.resize((int(canvas.size[0] / scale), int(canvas.size[1] / scale)))
    return canvas


def render_text_icon(token, font_color, font_size):
    token = token.strip('[]')
    icons = {
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

    if token.startswith("ATTACK"):
        # [ATTACK:LongRanged:Hurl Boulder:3+1]
        # _, atk_range, atk_name, atk_stats = token.split(":")
        # rendered = make_attack_bar("Ranged", "Long", "Hurl Boulder", [1], "3+")
        raise NotImplementedError(
            "Tried to render [ATTACK] inline. You should parse it first and leave it to paragraph rendering.")
    else:
        icon = AssetManager.get_text_icon(token)
        icon_h = int(font_size * 1.15)
        icon = icon.resize((int(icon_h * icon.size[0] / icon.size[1]), icon_h))
        bbox = icon.getbbox()
        icon = icon.crop((bbox[0], 0, bbox[2], bbox[3]))
        rendered = Image.new("RGBA", (icon.size[0] + 2, icon.size[1]))
        if icons[token] == "simple":
            rendered.paste(font_color, (1, 0), mask=icon)
        elif icons[token] == "image":
            rendered.alpha_composite(icon, (1, 0))

    return rendered


def render_text_line(line, font_color, font_size, font_family=None, font_style=None, **kwargs):
    font_style = font_style or {"is_bold": False, "is_italic": False}
    rendered_tokens = []
    for token in re.split(r"(\*+|\[[A-Z]+])", line):
        if token == "":
            continue
        elif token.startswith("["):
            rendered = render_text_icon(token, font_color, font_size)
            rendered_tokens.append(rendered)
        elif token == "*":
            font_style["is_italic"] = not font_style["is_italic"]
        elif token == "**":
            font_style["is_bold"] = not font_style["is_bold"]
        else:
            font_style_str = f"{'Bold' if font_style['is_bold'] else ''}"
            font_style_str += f"{'Italic' if font_style['is_italic'] else ''}"
            font_style_str = font_style_str or "Normal"
            font_path = f"./fonts/Tuff-{font_style_str}.ttf" if font_family is None else f"./fonts/{font_family}.ttf"
            rendered = text_to_image(token, font_path, font_size, font_color, **kwargs)
            rendered_tokens.append(rendered)

    total_width = sum([image.size[0] for image in rendered_tokens])
    max_height = max([image.size[1] for image in rendered_tokens])
    rendered_line = Image.new("RGBA", (total_width, max_height))
    x = 0
    for image in rendered_tokens:
        rendered_line.paste(image, (x, 0), image)
        x += image.size[0]

    return rendered_line


def combine_text_images(images, vertical_padding, **kwargs):
    align = kwargs.get("align") or "center"
    offsets = kwargs.get("offsets")
    fixed_height = kwargs.get("fixed_height") or 0

    if offsets is None:
        offsets = [(0, 0) for _ in images]
    max_width = max([im.size[0] for im in images])
    if fixed_height != 0:
        # The last line should be full height, because we only care about line spacing.
        # Letters such as "g" or "y" might be clipped otherwise.
        total_height = images[-1].size[1] + (len(images) - 1) * (vertical_padding + fixed_height)
    else:
        total_height = sum([im.size[1] for im in images]) + vertical_padding * (len(images) - 1)

    out = Image.new("RGBA", (max_width, total_height))
    x, y = 0, 0
    for offset, image in zip(offsets, images):
        if align == "left":
            x = 0
        elif align == "right":
            x = max_width - image.size[0]
        else: # align == "center"
            x = (max_width - image.size[0]) // 2
        out.alpha_composite(image, (x, y + offset[0]))
        y += (fixed_height or image.size[1]) + vertical_padding + offset[1]
    return out


def render_paragraph(paragraph, **kwargs):
    font_style = {
        "is_bold": False,
        "is_italic": False
    }
    rendered_lines = []
    for line in paragraph:
        rendered_line = render_text_line(line, font_style=font_style, **kwargs)
        rendered_lines.append(rendered_line)

    fixed_height = int(kwargs.get("font_size") * FACTOR_FIXED_LINE_HEIGHT)
    line_padding = kwargs.get("line_padding")
    return combine_text_images(rendered_lines, vertical_padding=line_padding, fixed_height=fixed_height, **kwargs)


def render_paragraphs(paragraphs, **kwargs):
    rendered_paragraphs = []
    offsets = []
    paragraph_padding = kwargs.get("paragraph_padding")

    for paragraph in paragraphs:
        offset = (0, 0)
        if isinstance(paragraph, dict) and paragraph.get("content") is None:
            rd_attack = render_attack(paragraph)
            rendered_paragraph = apply_drop_shadow(rd_attack, color="#00000077")
            offset = (-22 - paragraph_padding, -66 - paragraph_padding)
        else:
            if isinstance(paragraph, dict):
                content = paragraph.get("content")
                kwargs["font_color"] = paragraph.get("font_color") or kwargs.get("font_color")
                kwargs["font_size"] = paragraph.get("font_size") or kwargs.get("font_size")
                kwargs["line_padding"] = paragraph.get("line_padding") or kwargs.get("line_padding")
            else:
                content = paragraph
            rendered_paragraph = render_paragraph(content,  **kwargs)
        rendered_paragraphs.append(rendered_paragraph)
        offsets.append(offset)

    return combine_text_images(rendered_paragraphs, paragraph_padding, offsets=offsets)


def render_stat_value(stat):
    bg = AssetManager.get_stat_background()
    stat = str(stat)
    rd_stat = render_text_line(stat, font_color="white", font_size=46, font_family="Garamond-Bold", stroke_width=0)
    offset = 2 if stat.endswith("+") else 0
    bg.alpha_composite(rd_stat, (offset + (bg.size[0] - rd_stat.size[0]) // 2, (bg.size[1] - rd_stat.size[1]) // 2))
    return bg


def render_attack(attack_data, border_color="Gold"):
    atk_type = attack_data.get("type")
    atk_name = attack_data.get("name")
    tohit = attack_data.get("hit")
    atk_ranks = attack_data.get("dice")

    attack_bg = AssetManager.get_attack_bg(border_color)
    attack_dice_bg = AssetManager.get_attack_dice_bg()

    attack_bar = Image.new("RGBA", (367, 166))
    skill_icon = render_skill_icons(atk_type, border_color)
    attack_bar.alpha_composite(attack_bg, (skill_icon.size[0] // 2, 14 + (attack_bg.size[1] - 106) // 2))
    attack_bar.alpha_composite(skill_icon)

    atk_name_color = "#0e2e45" if atk_type == "melee" else "#87282a"
    text_lines_list = split_on_center_space(atk_name.upper())
    rd_atk_name = render_paragraph(text_lines_list, font_color=atk_name_color, font_size=29, line_padding=6, font_family="Tuff-Italic",
                                   stroke_width=0.7)
    attack_bar.alpha_composite(rd_atk_name, (221 - rd_atk_name.size[0] // 2, 56 - rd_atk_name.size[1] // 2))

    if atk_type != "melee":
        range_icon = AssetManager.get_attack_range_icon(atk_type, border_color)
        attack_bar.alpha_composite(apply_drop_shadow(range_icon), (60, -14))

    rd_statistics = Image.new("RGBA", attack_bar.size)
    rd_statistics.alpha_composite(attack_dice_bg, (104, 88))
    rd_to_hit = render_stat_value(f"{tohit}+")
    rd_statistics.alpha_composite(apply_drop_shadow(rd_to_hit), (58, 56))
    rank_colors = ["#648f4a", "#dd8e29", "#bd1a2b"]
    for i in range(len(atk_ranks)):
        rank_bg = Image.new("RGBA", (35, 35), rank_colors[i])
        rd_num_dice = render_text_line(str(atk_ranks[i]), font_color="#cdcecb", font_size=37, font_family="Garamond-Bold", stroke_width=0.1)

        # This was an interesting programming journey, but having a transparent font makes it pretty hard to read the text
        # rd_num_dice = render_text_line(str(atk_ranks[i]), "black", 35, "Garamond-Bold", stroke_width=0)
        rd_num_dice = rd_num_dice.crop(rd_num_dice.getbbox())
        rank_bg.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 5))
        # mask = Image.new("RGBA", (35, 35))
        # mask.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 5))
        # r,g,b,_ = rank_bg.split()
        # rank_bg = Image.merge("RGBA", (r,g,b,ImageChops.invert(mask.getchannel("A"))))
        rd_statistics.alpha_composite(add_rounded_corners(rank_bg, 10), (164 + i * 43, 98))
    attack_bar.alpha_composite(apply_drop_shadow(rd_statistics, color="#00000077"), (-20 ,-20))

    return attack_bar


def render_skill_icons(name, highlight_color="Gold"):
    rendered = Image.new("RGBA", (134,134))
    if name in ["ranged", "melee", "long", "short"]:
        attack_type_bg = AssetManager.get_attack_type_bg(highlight_color)
        x, y = (134 - attack_type_bg.size[0]) // 2, (134 - attack_type_bg.size[1]) // 2
        rendered.alpha_composite(attack_type_bg, (x, y))
        attack_type = apply_drop_shadow(AssetManager.get_attack_type(name, highlight_color))
        x, y = (136 - attack_type.size[0]) // 2, (136 - attack_type.size[1]) // 2
        rendered.alpha_composite(attack_type, (x, y))
    else:
        icon = AssetManager.get_skill_icon(name, highlight_color)
        x, y = (134 - icon.size[0]) // 2, (134 - icon.size[1]) // 2
        rendered.alpha_composite(icon, (x, y))
    return rendered

FACTOR_FIXED_LINE_HEIGHT = 0.7
ASSETS_DIR = "./assets"
