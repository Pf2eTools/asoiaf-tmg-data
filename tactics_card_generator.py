import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
from image_editor import ImageEditor


def add_rounded_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, "white")
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(90), (0, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(180), (w - rad, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(270), (w - rad, 0))
    alpha.paste(255, (rad, 0, w - rad, h - rad))
    alpha.paste(255, (0, rad, rad, h - rad))
    alpha.paste(255, (w - rad, rad, w, h - rad))
    alpha.paste(255, (rad, rad, w - rad, h - rad))

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


def make_attack_bar(atk_type, atk_name, atk_ranks, tohit, border_color="Gold"):
    units_folder = f"{ASSETS_DIR}/Units/"
    attack_type_bg = Image.open(f"{ASSETS_DIR}/Units/AttackTypeBg{border_color}.webp").convert('RGBA')
    attack_type = Image.open(
        f"{ASSETS_DIR}/Units/AttackType.{'Melee' if atk_type == 'melee' else 'ranged'}{border_color}.webp").convert(
        'RGBA')
    attack_type = attack_type.resize((124, 124))
    attack_bg = Image.open(f"{ASSETS_DIR}/Units/AttackBg{border_color}.webp").convert('RGBA')
    attack_dice_bg = Image.open(f"{units_folder}DiceBg.webp").convert('RGBA')
    attack_stat_bg = Image.open(f"{units_folder}StatBg.webp").convert('RGBA')

    attack_bar = Image.new("RGBA", (367, 166))
    attack_bar.alpha_composite(attack_bg, (
        14 + attack_type_bg.size[0] // 2, 14 + (attack_bg.size[1] - attack_type_bg.size[1]) // 2))
    attack_bar.alpha_composite(attack_type_bg, (14, 14))
    attack_bar.alpha_composite(apply_drop_shadow(attack_type), (-15, -14))

    atk_name_color = "#0e2e45" if atk_type == "melee" else "#87282a"
    text_lines_list = split_on_center_space(atk_name.upper())
    rd_atk_name = render_paragraph(text_lines_list, atk_name_color, 30, 6, font_family="Tuff-Italic",
                                   stroke_width=0.55)
    attack_bar.alpha_composite(rd_atk_name, (224 - rd_atk_name.size[0] // 2, 56 - rd_atk_name.size[1] // 2))

    if atk_type != "melee":
        range_graphic = Image.open(f"{ASSETS_DIR}/graphics/Range{atk_type.capitalize()}{border_color}.png").convert(
            'RGBA')
        attack_bar.alpha_composite(apply_drop_shadow(range_graphic), (60, -14))

    rd_statistics = Image.new("RGBA", attack_bar.size)
    rd_statistics.alpha_composite(attack_dice_bg, (84, 68))
    rd_statistics.alpha_composite(attack_stat_bg, (58, 56))
    rd_tohit = render_text_line(f"{tohit}+", "white", 44, font_family="Garamond-Bold")
    rd_statistics.alpha_composite(rd_tohit, (
        58 + (attack_stat_bg.size[0] - rd_tohit.size[0]) // 2, 56 + (attack_stat_bg.size[1] - rd_tohit.size[1]) // 2))
    rank_colors = ["#648f4a", "#dd8e29", "#bd1a2b"]
    for i in range(len(atk_ranks)):
        rank_bg = Image.new("RGBA", (35, 35), rank_colors[i])
        rd_num_dice = render_text_line(str(atk_ranks[i]), "#cdcecb", 37, "Garamond-Bold", stroke_width=0)

        # This was an interesting programming journey, but having a transparent font makes it pretty hard to read the text
        # rd_num_dice = render_text_line(str(atk_ranks[i]), "black", 35, "Garamond-Bold", stroke_width=0)
        rd_num_dice = rd_num_dice.crop(rd_num_dice.getbbox())
        rank_bg.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 6))
        # mask = Image.new("RGBA", (35, 35))
        # mask.alpha_composite(rd_num_dice, (16 - rd_num_dice.size[0] // 2, 5))
        # r,g,b,_ = rank_bg.split()
        # rank_bg = Image.merge("RGBA", (r,g,b,ImageChops.invert(mask.getchannel("A"))))
        rd_statistics.alpha_composite(add_rounded_corners(rank_bg, 10), (144 + i * 42, 78))
    attack_bar.alpha_composite(apply_drop_shadow(rd_statistics))

    return attack_bar


def get_faction_color(faction):
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


def apply_drop_shadow(image, shadow_size=3, color="black", passes=5):
    border = 20
    shadow = Image.new('RGBA',
                       (image.size[0] + shadow_size * 2 + border * 2, image.size[1] + shadow_size * 2 + border * 2))
    mask = image.copy()
    # mask = mask.resize((image.size[0] + shadow_size * 2, image.size[1] + shadow_size * 2))
    # shadow.paste(color, (border - shadow_size, border - shadow_size), mask=mask)
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


def text_to_image(text, font_path, font_size, font_color, stroke_width=0.35, letter_spacing=0, max_width=0):
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
        icon = Image.open(f"{ASSETS_DIR}/graphics/{token}.png").convert("RGBA")
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


def combine_images_horizontal_center(images, vertical_padding, fixed_height=0, offsets=None):
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
        x = (max_width - image.size[0]) // 2
        out.alpha_composite(image, (x, y + offset[0]))
        y += (fixed_height or image.size[1]) + vertical_padding + offset[1]
    return out

FACTOR_FIXED_LINE_HEIGHT = 0.7
def render_paragraph(paragraph, font_color, font_size, padding_lines, **kwargs):
    font_style = {
        "is_bold": False,
        "is_italic": False
    }
    rendered_lines = []
    for line in paragraph:
        rendered_line = render_text_line(line, font_color, font_size, font_style=font_style, **kwargs)
        rendered_lines.append(rendered_line)

    return combine_images_horizontal_center(rendered_lines, padding_lines, int(font_size * FACTOR_FIXED_LINE_HEIGHT))


def render_paragraphs(paragraphs, font_color, font_size, line_padding, padding_paragraph, **kwargs):
    rendered_paragraphs = []
    offsets = []
    for paragraph in paragraphs:
        offset = (0, 0)
        if isinstance(paragraph, dict) and paragraph.get("content") is None:
            atk_name = paragraph.get("name")
            atk_type = paragraph.get("type")
            tohit = paragraph.get("hit")
            atk_ranks = paragraph.get("dice")
            bar = make_attack_bar(atk_type, atk_name, atk_ranks, tohit)
            rendered_paragraph = apply_drop_shadow(bar, color="#00000099")
            offset = (-22 - padding_paragraph, -66 - padding_paragraph)
        else:
            if isinstance(paragraph, dict):
                content = paragraph.get("content")
                color = paragraph.get("font_color") or font_color
                size = paragraph.get("font_size") or font_size
                padding = paragraph.get("line_padding") or line_padding
            else:
                content = paragraph
                color = font_color
                size = font_size
                padding = line_padding
            rendered_paragraph = render_paragraph(content, color, size, padding, **kwargs)
        rendered_paragraphs.append(rendered_paragraph)
        offsets.append(offset)

    return combine_images_horizontal_center(rendered_paragraphs, padding_paragraph, offsets=offsets)


def build_tactics_card(card_info):
    faction = re.sub(r"[^A-Za-z]", "", card_info.get("faction"))
    name = card_info.get("name")
    card_text = card_info.get("text")
    version = card_info.get("version")
    commander_id = card_info.get("commander_id")
    commander_name = card_info.get("commander_name")
    commander_subname = card_info.get("commander_subname")

    tactics_bg = Image.open(f"{ASSETS_DIR}/Tactics/Bg_{faction}.jpg").convert('RGBA')
    tactics_bg2 = Image.open(f"{ASSETS_DIR}/Tactics/Bg2.jpg").convert('RGBA')
    tactics_card = Image.new('RGBA', tactics_bg.size)
    tactics_card.paste(tactics_bg.rotate(get_faction_bg_rotation(faction)))
    tactics_card.paste(tactics_bg2, (47, 336))

    if commander_id is not None:
        cmdr_image = Image.open(f"{ASSETS_DIR}/Tactics/{commander_id}.jpg").convert('RGBA')
        tactics_card.paste(cmdr_image, (-1, -2))

    bars = Image.new('RGBA', tactics_bg.size)
    large_bar = Image.open(f"{ASSETS_DIR}/Units/LargeBar{faction}.webp").convert('RGBA')
    small_bar = Image.open(f"{ASSETS_DIR}/Attachments/Bar{faction}.webp").convert('RGBA')
    weird_bar = Image.open(f"{ASSETS_DIR}/Units/Corner{faction}.webp").convert('RGBA')

    bars.alpha_composite(large_bar.rotate(180), (-96, 252))
    if commander_id is not None:
        bars.paste(Image.new("RGBA", (646, 82), (0, 0, 0, 0)), (55, 246))

    bars.alpha_composite(ImageOps.flip(weird_bar.rotate(270, expand=1)), (242 - weird_bar.size[1], 25))
    bars.alpha_composite(weird_bar.rotate(270, expand=1), (242 - weird_bar.size[1], -95))
    if commander_id is not None:
        bars.alpha_composite(large_bar.rotate(90, expand=1), (240, 235 - large_bar.size[0]))
        bars.alpha_composite(weird_bar.rotate(90, expand=1), (323, 25))
        bars.alpha_composite(ImageOps.flip(weird_bar.rotate(90, expand=1)), (323, -95))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (234, 255 - small_bar.size[0]))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (314, 255 - small_bar.size[0]))
    else:
        bars.alpha_composite(weird_bar.rotate(90, expand=1), (243, 25))
        bars.alpha_composite(ImageOps.flip(weird_bar.rotate(90, expand=1)), (243, -95))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (234, 255 - small_bar.size[0]))

    if commander_id is None:
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1])), (46, 336))
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1])), (687, 336))
    else:
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (46, 246))
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (687, 246))
    bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                         ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, 985))
    bars.alpha_composite(small_bar, (0, 246))
    bars.alpha_composite(small_bar, (0, 328))

    decor = Image.open(f"{ASSETS_DIR}/Tactics/Decor{faction}.webp").convert('RGBA')
    bars.alpha_composite(decor, (33, 316))
    bars.alpha_composite(decor, (673, 316))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (673, 971))
    if commander_id is not None:
        bars.alpha_composite(decor, (33, 232))
        bars.alpha_composite(decor, (673, 232))

    all_text = Image.new('RGBA', tactics_bg.size)

    rendered_name = render_paragraph([f"**{l.upper()}**" for l in name], font_color="white", font_size=51,
                                     padding_lines=12)
    name_max_w = 440 if commander_name is None else 392
    if rendered_name.getbbox()[2] > name_max_w:
        rendered_name = rendered_name.resize((name_max_w, int(rendered_name.size[1] * name_max_w / rendered_name.size[0])))
    if commander_name is not None:
        full_commander_name = f"**{commander_name}**".upper()
        full_commander_name += f" - {commander_subname}".upper() if commander_subname is not None else ""
        letter_spacing = 0 if len(full_commander_name) < 36 else -1.5
        font_size = 32 if len(full_commander_name) < 43 else 29
        if len(full_commander_name) < 46 or commander_subname is None:
            rendered_cmdr_name = render_text_line(full_commander_name, "white", font_size, letter_spacing=letter_spacing)
        else:
            # yeah, that's not happening if commander_subname == None
            rendered_cmdr_name = render_paragraph([f"**{commander_name.upper()}**", commander_subname.upper()], "white", 29, 4)
        cmdr_x, cmdr_y = (tactics_bg.size[0] - rendered_cmdr_name.size[0]) // 2, 294 - rendered_cmdr_name.size[1] // 2
        all_text.alpha_composite(rendered_cmdr_name, (cmdr_x, cmdr_y))
        name_x, name_y = (tactics_bg.size[0] - rendered_name.size[0]) // 2 + 170, 136 - rendered_name.size[1] // 2
        all_text.alpha_composite(rendered_name, (name_x, name_y))
    else:
        name_x, name_y = (tactics_bg.size[0] - rendered_name.size[0]) // 2 + 138, 140 - rendered_name.size[1] // 2
        all_text.alpha_composite(rendered_name, (name_x, name_y))

    card_text_y = 360
    font_size = 41
    line_padding = 18
    paragraph_padding = 16
    total_text_height = sum([calc_height_paragraph(te.get("trigger"), 41, 18) for te in card_text])
    total_text_height += sum([calc_height_paragraphs(te.get("effect"), 41, 18, 16) for te in card_text])
    # height of the bars
    total_text_height += (len(card_text) - 1) * (18 + paragraph_padding + small_bar.size[1])
    # height of the space between trigger and effect
    total_text_height += len(card_text) * (paragraph_padding - 4)

    # text taller than this will clip
    max_text_height = 600
    text_overflow_px = total_text_height - max_text_height
    if text_overflow_px > 0:
        num_lines = 0
        num_paragraphs = 0
        for te in card_text:
            if te.get("trigger") is not None:
                num_paragraphs += 1
                for l in te.get("trigger"):
                    num_lines += 1
            for p in te.get("effect") or []:
                num_paragraphs += 1
                for l in p:
                    num_lines += 1

        if text_overflow_px >= 100:
            # allow getting closer to the edge
            card_text_y -= 12
            text_overflow_px -= 12
        if text_overflow_px >= 60:
            font_size -= 3
            text_overflow_px -= int(num_lines * FACTOR_FIXED_LINE_HEIGHT * 3)
        for i in range(18):
            if text_overflow_px <= 0:
                break
            if i == 15:
                font_size -= 3
                text_overflow_px -= int(num_lines * FACTOR_FIXED_LINE_HEIGHT * 3)
            elif i % 2 == 0:
                line_padding -= 1
                text_overflow_px -= num_lines
            else:
                paragraph_padding -= 2
                text_overflow_px -= 2 * num_paragraphs

        if text_overflow_px > 0:
            print(f'[WARNING] "{" ".join(name)}" might render with clipping text!')

    for ix, trigger_effect in enumerate(card_text):
        trigger = trigger_effect.get("trigger")
        effect = trigger_effect.get("effect")
        is_remove_text = ix > 0 and card_info.get("remove") is not None

        should_render_low = is_remove_text or (ix == len(card_text) - 1 and ix > 0)
        font_color = get_faction_color(faction) if not is_remove_text else "#5d4d40"
        rd_trigger = render_paragraph(trigger, font_color, font_size, line_padding, max_width=590)
        if not is_remove_text:
            rd_effect_text = render_paragraphs(effect, "#5d4d40", font_size, line_padding, paragraph_padding, max_width=590)
        else:
            rd_effect_text = Image.new("RGBA", (0,0))
        if should_render_low:
            height_remaining = rd_trigger.size[1] + rd_effect_text.size[1] + paragraph_padding - 4
            height_remaining += small_bar.size[1] + 2 * paragraph_padding + 18
            card_text_y = max(card_text_y, 961 - height_remaining)

        # paste the divider
        if ix > 0:
            card_text_y += paragraph_padding + 14
            bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                                 ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, card_text_y))
            bars.alpha_composite(decor, (33, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            bars.alpha_composite(decor, (673, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            card_text_y += small_bar.size[1] + paragraph_padding + 4

        # finally paste the text
        trigger_x, trigger_y = (tactics_bg.size[0] - rd_trigger.size[0]) // 2, card_text_y
        all_text.alpha_composite(rd_trigger, (trigger_x, trigger_y))
        card_text_y += rd_trigger.size[1]

        effect_text_x = (tactics_bg.size[0] - rd_effect_text.size[0]) // 2
        effect_text_y = card_text_y + paragraph_padding - 4
        all_text.alpha_composite(rd_effect_text, (effect_text_x, effect_text_y))
        card_text_y += rd_effect_text.size[1]

    rendered_version = render_text_line(f"*{version.strip('*')}*", font_color="white", font_size=20)
    version_x, version_y = 21, tactics_bg.size[1] - rendered_version.size[0] - 70
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    tactics_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))

    crest = Image.open(f"{ASSETS_DIR}/Tactics/Crest{faction}.webp").convert('RGBA')
    crest = crest.crop(crest.getbbox())
    crest = crest.resize(((189 + crest.size[0]) // 2, int(crest.size[1] * ((189 + crest.size[0]) / 2) / crest.size[0])))
    if commander_id is None:
        crest_rot = crest.rotate(16, expand=1, resample=Image.BILINEAR)
        crest_rot_x, crest_rot_y = 175 - crest_rot.size[0] // 2, 181 - crest_rot.size[1] // 2
        tactics_card.alpha_composite(apply_drop_shadow(crest_rot, shadow_size=2), (crest_rot_x, crest_rot_y))
    else:
        crest_resize = crest.resize((int(crest.size[0] * 0.68), int(crest.size[1] * 0.68)))
        crest_resize_x, crest_resize_y = 264 - crest_resize.size[0] // 2, 175 - crest_resize.size[1] // 2
        tactics_card.alpha_composite(apply_drop_shadow(crest_resize), (crest_resize_x, crest_resize_y))

    tactics_card.alpha_composite(all_text)

    return tactics_card


def main():
    hurl = {
        "faction": "FreeFolk",
        "commander_id": "10313",
        "commander_name": "**Mag the Mighty** - Mag Mar Tun Doh Weg",
        "version": "*2021*",
        "name": ["**HURL BOULDER**"],
        "text": [
            {
                "trigger": [
                    "**When a friendly Giant Unit**",
                    "**performs an Action, before**",
                    "**resolving that Action:**",
                ],
                "effect": [
                    [
                        "That unit replaces that",
                        "Action with performing",
                        "the following Ranged Attack:",
                    ],
                    {
                        "name": "Hurl Boulder",
                        "type": "long",
                        "to_hit": 3,
                        "atk_ranks": [1]
                    },
                    {
                        "font_size": 36,
                        "line_padding": 12,
                        "content": [
                            "If this Attack generates any Hits, instead",
                            "of rolling Defense Dice, the Defender",
                            "suffers D3 Wounds, +1 Wound",
                            "for each remaining rank in that unit.",
                        ],
                    }
                ]
            }
        ]
    }
    exploit = {
        "faction": "Lannister",
        "commander_id": "20104",
        "commander_name": "**TYWIN LANNISTER** - LORD OF CASTERLY ROCK",
        "version": "*2021-S03*",
        "name": ["**EXPLOIT**", "**WEAKNESS**"],
        "trigger": ["**When a friendly unit is performing**", "**an Attack, before rolling Attack Dice:**"],
        "text": [
            [
                "The Defender becomes **Vulnerable**."
            ],
            [
                "If the Defender is **Weakened**,",
                "the Attacker may re-roll",
                "any Attack Dice.",
            ],
        ]
    }
    intrigue = {
        "faction": "Lannister",
        "version": "*2021*",
        "name": ["INTRIGUE AND", "SUBTERFUGE"],
        "text": [
            {
                "trigger": ["**When an enemy NCU Activates:**"],
                "effect": [
                    [
                        "That NCU loses all Abilities",
                        "until the end of the Round."
                    ],
                    [
                        "If you Control [MONEY], target",
                        "1 enemy Combat Unit. That",
                        "enemy becomes **Weakened**."
                    ]
                ]
            },
        ]
    }
    traps = {
        "faction": "Stark",
        "commander_id": "20225",
        "commander_name": "**Howland Reed** - Lord of the Crannogs",
        "version": "*2021-S03*",
        "name": ["**CRANNOG**", "**TRAPS**"],
        "trigger": ["**When an enemy unit Activates:**"],
        "text": [
            [
                "If that enemy is in Long Range of",
                "a friendly Crannogman unit, it",
                "suffers -1[MOVEMENT] this Turn.",
            ],
            [
                "If that enemy declares a Maneuver,",
                "March, or Retreat Action, it is treated",
                "as moving through Dangerous terrain.",
            ],
        ]
    }

    tactics_card = build_tactics_card(intrigue)
    tactics_card_original = Image.open("tactics/en/40101.jpg")
    app = ImageEditor(tactics_card, tactics_card_original)


ASSETS_DIR = "./assets"

if __name__ == "__main__":
    main()
