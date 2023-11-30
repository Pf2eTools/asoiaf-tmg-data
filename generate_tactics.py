from image_editor import ImageEditor
from generate_utils import *

# FIXME: recalculate the offsets with shadow stuffs
def generate_tactics(tactics_data):
    faction = re.sub(r"[^A-Za-z]", "", tactics_data.get("faction"))
    name = tactics_data.get("name")
    card_text = tactics_data.get("text")
    version = tactics_data.get("version")
    commander_id = tactics_data.get("commander_id")
    commander_name = tactics_data.get("commander_name")
    commander_subname = tactics_data.get("commander_subname")

    tactics_bg = AssetManager.get_bg(faction)
    tactics_bg2 = AssetManager.get_text_bg()
    tactics_card = Image.new('RGBA', tactics_bg.size)
    tactics_card.paste(tactics_bg.rotate(get_faction_bg_rotation(faction)))
    tactics_card.paste(tactics_bg2, (47, 336))

    if commander_id is not None:
        cmdr_image = AssetManager.get_tactics_commmander_img(commander_id)
        tactics_card.paste(cmdr_image, (-1, -2))

    bars = Image.new('RGBA', tactics_bg.size)
    large_bar, small_bar, weird_bar = AssetManager.get_bars(faction)

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

    decor = AssetManager.get_decor(faction)
    bars.alpha_composite(decor, (33, 316))
    bars.alpha_composite(decor, (673, 316))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (673, 971))
    if commander_id is not None:
        bars.alpha_composite(decor, (33, 232))
        bars.alpha_composite(decor, (673, 232))

    all_text = Image.new('RGBA', tactics_bg.size)

    rendered_name = render_paragraph([f"**{l.upper()}**" for l in name], font_color="white", font_size=51,
                                     line_padding=12)
    name_max_w = 440 if commander_name is None else 392
    if rendered_name.getbbox()[2] > name_max_w:
        rendered_name = rendered_name.resize((name_max_w, int(rendered_name.size[1] * name_max_w / rendered_name.size[0])))
    if commander_name is not None:
        full_commander_name = f"**{commander_name}**".upper()
        full_commander_name += f" - {commander_subname}".upper() if commander_subname is not None else ""
        letter_spacing = 0 if len(full_commander_name) < 36 else -1.5
        font_size = 32 if len(full_commander_name) < 43 else 29
        if len(full_commander_name) < 46 or commander_subname is None:
            rendered_cmdr_name = render_text_line(full_commander_name, font_color="white", font_size=font_size, letter_spacing=letter_spacing)
        else:
            # yeah, that's not happening if commander_subname == None
            rendered_cmdr_name = render_paragraph([f"**{commander_name.upper()}**", commander_subname.upper()], font_color="white", font_size=29, line_padding=4)
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
        is_remove_text = ix > 0 and tactics_data.get("remove") is not None

        should_render_low = is_remove_text or (ix == len(card_text) - 1 and ix > 0)
        font_color = get_faction_text_color(faction) if not is_remove_text else "#5d4d40"
        rd_trigger = render_paragraph(trigger, font_color=font_color, font_size=font_size, line_padding=line_padding, max_width=590)
        if not is_remove_text:
            rd_effect_text = render_paragraphs(effect, font_color="#5d4d40", font_size=font_size, line_padding=line_padding, paragraph_padding=paragraph_padding,
                                               max_width=590)
        else:
            rd_effect_text = Image.new("RGBA", (0, 0))
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

    crest = AssetManager.get_crest_tactics(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.resize(((189 + crest.size[0]) // 2, int(crest.size[1] * ((189 + crest.size[0]) / 2) / crest.size[0])))
    if commander_id is None:
        crest_rot = crest.rotate(16, expand=1, resample=Image.BILINEAR)
        crest_rot_x, crest_rot_y = 175 - crest_rot.size[0] // 2, 181 - crest_rot.size[1] // 2
        tactics_card.alpha_composite(apply_drop_shadow(crest_rot), (crest_rot_x, crest_rot_y))
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
                "trigger": [
                    "**When an enemy NCU Activates:**"
                ],
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

    tactics_card = generate_tactics(intrigue)
    tactics_card_original = Image.open("generated/en/tactics/40101.jpg")
    app = ImageEditor(tactics_card, tactics_card_original)


if __name__ == "__main__":
    main()
