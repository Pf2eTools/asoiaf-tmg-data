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
    attack_type = Image.open(f"{ASSETS_DIR}/Units/AttackType.{'Melee' if atk_type == 'melee' else 'ranged'}{border_color}.webp").convert('RGBA')
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
                                   thickness_factor=1.8)
    attack_bar.alpha_composite(rd_atk_name, (224 - rd_atk_name.size[0] // 2, 56 - rd_atk_name.size[1] // 2))

    if atk_type != "melee":
        range_graphic = Image.open(f"{ASSETS_DIR}/graphics/Range{atk_type.capitalize()}{border_color}.png").convert('RGBA')
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
        rd_num_dice = render_text_line(str(atk_ranks[i]), "#cdcecb", 37, "Garamond-Bold", thickness_factor=0)

        # This was an interesting programming journey, but having a transparent font makes it pretty hard to read the text
        # rd_num_dice = render_text_line(str(atk_ranks[i]), "black", 35, "Garamond-Bold", thickness_factor=0)
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
        "martell": "#9e4c00",
        "neutral": "#3e2a19",
        "nightswatch": "#302a28",
        "stark": "#3b6680",
        "targaryen": "#530818",
        "baratheon": "#904523",
        "bolton": "#7a312b",
        "freefolk": "#4b4138",
        "greyjoy": "#10363b",
        "lannister": "#9d1323",
    }
    faction = re.sub(r"[^a-z]", "", faction.lower())
    return faction_colors.get(faction) or "#7FDBFF"


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


def text_to_image(text, font_path, font_size, font_color, thickness_factor=3):
    # The stroke_width property (see below) would be really nice if it worked with smaller font sizes
    # As a workaround, we use a bigger fontsize, then downscale the image later
    stroke_width = 0 if thickness_factor == 0 else 1
    thickness_factor = thickness_factor or 1
    font = ImageFont.truetype(font_path, int(font_size * thickness_factor))
    bbox = font.getbbox(text)
    # Offset of 1, otherwise tall letters are clipped
    offset_x, offset_y = 0, 1
    # For vertical center alignment, ensure the height is consistent. "yjg" are the tallest letters.
    # Usually, this means h == font_size
    w, h = bbox[2], font.getbbox("yjg")[3] + 1
    # Avoid clipping of letters such as "j"
    if bbox[0] < 0:
        w -= bbox[0]
        offset_x += bbox[0]
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text((offset_x, offset_y), text, font_color, font=font, stroke_width=stroke_width)

    return canvas.resize((int(canvas.size[0] / thickness_factor), int(canvas.size[1] / thickness_factor)))


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
        icon = icon.crop(icon.getbbox())
        icon_h = int(font_size * 1.15)
        icon = icon.resize((int(icon_h * icon.size[0] / icon.size[1]), icon_h))
        rendered = Image.new("RGBA", (icon.size[0] + 2, icon.size[1]))
        if icons[token] == "simple":
            rendered.paste(font_color, (1, 0), mask=icon)
        elif icons[token] == "image":
            rendered.alpha_composite(icon, (1, 0))

    return rendered


def render_text_line(line, font_color, font_size, font_family=None, thickness_factor=3):
    is_bold = False
    is_italic = False
    rendered_tokens = []
    for token in re.split(r"(\*+|\[[A-Z]+])", line):
        if token == "":
            continue
        elif token.startswith("["):
            rendered = render_text_icon(token, font_color, font_size)
            rendered_tokens.append({"im": rendered, "type": "icon"})
        elif token == "*":
            is_italic = not is_italic
        elif token == "**":
            is_bold = not is_bold
        else:
            font_style = f"{'Bold' if is_bold else ''}{'Italic' if is_italic else ''}{'Normal' if not is_italic and not is_bold else ''}"
            font_path = f"./fonts/Tuff-{font_style}.ttf" if font_family is None else f"./fonts/{font_family}.ttf"
            rendered = text_to_image(token, font_path, font_size, font_color, thickness_factor)
            rendered_tokens.append({"im": rendered, "type": "text"})

    total_width = sum([tkn["im"].size[0] for tkn in rendered_tokens])
    max_height = max([tkn["im"].size[1] for tkn in rendered_tokens])
    rendered_line = Image.new("RGBA", (total_width, max_height + 7))
    x = 0
    for token in rendered_tokens:
        image = token["im"]
        # It's disgusting, but icons need to be rendered higher than the font. So we pad each text line by 7px.
        if token["type"] == "icon":
            rendered_line.paste(image, (x, 0), image)
        else:
            rendered_line.paste(image, (x, 7), image)
        x += image.size[0]

    out = Image.new("RGBA", rendered_line.size, "red")
    out.alpha_composite(rendered_line)
    return rendered_line


def render_paragraph(paragraph, font_color, font_size, padding_lines, font_family=None, thickness_factor=3):
    rendered_lines = []
    for line in paragraph:
        rendered_line = render_text_line(line, font_color, font_size, font_family=font_family,
                                         thickness_factor=thickness_factor)
        rendered_lines.append(rendered_line)

    return combine_images_horizontal_center(rendered_lines, padding_lines, int(font_size * 0.7))


def render_paragraphs(paragraphs, font_color="#5d4d40", font_size=41, line_padding=18, padding_paragraph=16):
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
            offset = (-38, -82)
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
            rendered_paragraph = render_paragraph(content, color, size, padding)
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

    tactics_bg = Image.open(f"{ASSETS_DIR}/Tactics/Bg_{faction}.jpg").convert('RGBA')
    tactics_bg2 = Image.open(f"{ASSETS_DIR}/Tactics/Bg2.jpg").convert('RGBA')
    tactics_card = Image.new('RGBA', tactics_bg.size)
    tactics_card.paste(tactics_bg.rotate(180))
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

    bars.alpha_composite(ImageOps.flip(weird_bar.rotate(270, expand=1)), (-460, 25))
    bars.alpha_composite(weird_bar.rotate(270, expand=1), (-460, -95))
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
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1])), (692, 336))
    else:
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (46, 246))
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (692, 246))
    bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                         ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, 985))
    bars.alpha_composite(small_bar, (0, 246))
    bars.alpha_composite(small_bar, (0, 328))

    decor = Image.open(f"{ASSETS_DIR}/Tactics/Decor{faction}.webp").convert('RGBA')
    bars.alpha_composite(decor, (33, 316))
    bars.alpha_composite(decor, (678, 316))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (678, 971))
    if commander_id is not None:
        bars.alpha_composite(decor, (33, 232))
        bars.alpha_composite(decor, (678, 232))

    all_text = Image.new('RGBA', tactics_bg.size)

    rendered_name = render_paragraph([f"**{l.upper()}**" for l in name], font_color="white", font_size=51, padding_lines=12)
    if commander_name is not None:
        rendered_cmdr_name = render_text_line(commander_name.upper(), font_color="white", font_size=32)
        all_text.alpha_composite(rendered_cmdr_name, ((tactics_bg.size[0] - rendered_cmdr_name.size[0]) // 2, 275))
        all_text.alpha_composite(rendered_name, (
        (tactics_bg.size[0] - rendered_name.size[0]) // 2 + 162, 136 - rendered_name.size[1] // 2))
    else:
        all_text.alpha_composite(rendered_name, (
        (tactics_bg.size[0] - rendered_name.size[0]) // 2 + 128, 140 - rendered_name.size[1] // 2))

    card_text_y = 360
    for ix, trigger_effect in enumerate(card_text):
        trigger = trigger_effect.get("trigger")
        effect = trigger_effect.get("effect")
        is_remove_text = ix > 0 and card_info.get("remove") is not None
        if ix > 0:
            card_text_y += 30
            bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                                 ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, card_text_y))
            bars.alpha_composite(decor, (33, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            bars.alpha_composite(decor, (678, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            card_text_y += small_bar.size[1] + 30

        font_color = get_faction_color(faction) if not is_remove_text  else "#5d4d40"
        rd_trigger = render_paragraph(trigger, font_color=font_color, font_size=41, padding_lines=18)
        trigger_x, trigger_y = (tactics_bg.size[0] - rd_trigger.size[0]) // 2, card_text_y
        all_text.alpha_composite(rd_trigger, (trigger_x, trigger_y))
        card_text_y += rd_trigger.size[1]

        if not is_remove_text:
            rd_effect_text = render_paragraphs(effect)
            effect_text_x, effect_text_y = (tactics_bg.size[0] - rd_effect_text.size[0]) // 2, card_text_y + 12
            all_text.alpha_composite(rd_effect_text, (effect_text_x, effect_text_y))
            card_text_y += rd_effect_text.size[1]
    
    rendered_version = render_text_line(version, font_color="white", font_size=20)
    version_x, version_y = 21, tactics_bg.size[1] - rendered_version.size[0] - 70
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    tactics_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))

    crest = Image.open(f"{ASSETS_DIR}/Tactics/Crest{faction}.webp").convert('RGBA')
    if commander_id is None:
        tactics_card.alpha_composite(
            apply_drop_shadow(crest.rotate(16, expand=1, resample=Image.BILINEAR), shadow_size=2), (54, 48))
    else:
        tactics_card.alpha_composite(
            apply_drop_shadow(crest.resize((int(crest.size[0] * 0.68), int(crest.size[1] * 0.68)))), (200, 100))


    tactics_card.alpha_composite(all_text)

    return tactics_card


def main():
    hurl = {
        "faction": "FreeFolk",
        "commander_id": "10313",
        "commander_name": "**Mag the Mighty** - Mag Mar Tun Doh Weg",
        "version": "*2021*",
        "name": ["**HURL BOULDER**"],
        "trigger": [
            "**When a friendly Giant Unit**",
            "**performs an Action, before**",
            "**resolving that Action:**",
        ],
        "text": [
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
        "name": ["**INTRIGUE AND**", "**SUBTERFUGE**"],
        "trigger": ["**When an enemy NCU Activates:**"],
        "text": [
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

    tactics_card = build_tactics_card(exploit)
    tactics_card.save("int.png")
    tactics_card_original = Image.open("exploit.jpg")
    app = ImageEditor(tactics_card, tactics_card_original)


ASSETS_DIR = "./assets"

if __name__ == "__main__":
    main()
