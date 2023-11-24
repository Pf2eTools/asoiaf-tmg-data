from generate_utils import *
from image_editor import ImageEditor
from asset_manager import AssetManager


def generate_unit(unit_data, abilities_data):
    faction = re.sub(r"[^A-Za-z]", "", unit_data.get("faction"))
    unit_id = unit_data.get("id")
    name = unit_data.get("name")
    version = unit_data.get("version")
    attacks = unit_data.get("attacks")
    abilities = unit_data.get("abilities") or []

    unit_bg = AssetManager.get_unit_bg(faction)
    w, h = unit_bg.size
    unit_card = Image.new("RGBA", (w, h))
    unit_card.paste(unit_bg)

    if len(abilities) > 0 :
        skills_bg = AssetManager.get_unit_skills_bg()
        unit_card.paste(skills_bg, (w - skills_bg.size[0], 0))

    unit_image = AssetManager.get_unit_image(unit_id)
    unit_card.paste(unit_image, (497 - unit_image.size[0] // 2, min(0, 642 - unit_image.size[1])))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = AssetManager.get_bars(faction)
    decor = AssetManager.get_decor(faction)

    large_bar_shortened = ImageOps.flip(large_bar.copy().rotate(180)).crop((164, 0, 346, large_bar.size[1]))
    small_bar_shortened = apply_drop_shadow(small_bar.copy().crop((514, 0, 696, small_bar.size[1])))
    small_bar_ds = apply_drop_shadow(small_bar, passes=10)
    # top left
    bars.alpha_composite(large_bar_shortened, (0, 104 - large_bar.size[1] // 2))
    bars.alpha_composite(small_bar_shortened, (-20, 46 - small_bar.size[1] // 2))
    bars.alpha_composite(small_bar_shortened, (-20, 126 - small_bar.size[1] // 2))

    # bottom left
    bars.alpha_composite(large_bar_shortened, (0, 638 - large_bar.size[1] // 2))
    bars.alpha_composite(small_bar_shortened, (-20, 580 - small_bar.size[1] // 2))
    bars.alpha_composite(small_bar_shortened, (-20, 660 - small_bar.size[1] // 2))

    # vertical left
    bar_vl_x, bar_vl_y = 230 - large_bar.size[1] // 2, 316 - large_bar.size[0] // 2
    # vertical right
    bar_vr_x, bar_vr_y = 764 - large_bar.size[1] // 2, 316 - large_bar.size[0] // 2
    crop_crossbar = small_bar_ds.crop((23, 0, 23 + bar_vr_x - bar_vl_x - large_bar.size[1], small_bar_ds.size[1]))
    bars.alpha_composite(ImageOps.flip(weird_bar), (bar_vl_x + large_bar.size[1], 639 - weird_bar.size[1]))
    bars.alpha_composite(weird_bar, (bar_vl_x + large_bar.size[1], 639))
    bars.alpha_composite(weird_bar.rotate(180, expand=1), (bar_vr_x - weird_bar.size[0], 639 - weird_bar.size[1]))
    bars.alpha_composite(ImageOps.flip(weird_bar.rotate(180, expand=1)), (bar_vr_x - weird_bar.size[0], 639))
    bars.alpha_composite(crop_crossbar, (bar_vl_x + large_bar.size[1], 638 - small_bar_ds.size[1] // 2))
    bars.alpha_composite(apply_drop_shadow(decor), (479 - decor.size[0] // 2, 618 - decor.size[1] // 2))

    bars.alpha_composite(large_bar.rotate(270, expand=1), (bar_vl_x, max(bar_vl_y, h - large_bar.size[0])))
    bars.alpha_composite(small_bar_ds.rotate(270, expand=1), (bar_vl_x - small_bar_ds.size[1] // 2, bar_vl_y))
    bars.alpha_composite(small_bar_ds.rotate(270, expand=1), (bar_vl_x + 86 - small_bar_ds.size[1] // 2, bar_vl_y))

    bars.alpha_composite(large_bar.rotate(270, expand=1), (bar_vr_x, max(bar_vr_y, h - large_bar.size[0])))
    bars.alpha_composite(small_bar_ds.rotate(270, expand=1), (bar_vr_x + 83 - small_bar_ds.size[1] // 2, bar_vr_y))
    bars.alpha_composite(small_bar_ds.rotate(270, expand=1), (bar_vr_x - small_bar_ds.size[1] // 2, bar_vr_y))

    crests = Image.new("RGBA", (w, h))
    crest = AssetManager.get_crest(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.rotate(-12, expand=1, resample=Image.BICUBIC)
    crest_w, crest_h = int(188 * crest.size[0] / crest.size[1]), 188
    crest = crest.resize((crest_w, crest_h), resample=Image.LANCZOS)
    crests.alpha_composite(apply_drop_shadow(crest), (704 - crest_w, 456))
    unit_type = AssetManager.get_unit_type(unit_data.get("type"), faction)
    crests.alpha_composite(unit_type, (228 - unit_type.size[0] // 2, h - unit_type.size[1]))

    statistics = Image.new("RGBA", (w, h))
    icon_speed = AssetManager.get_stat_icon("speed")
    rd_speed = render_stat_value(unit_data.get("speed"))
    statistics.alpha_composite(rd_speed, (bar_vl_x - 3 - rd_speed.size[0] // 2, 104 - rd_speed.size[1] // 2))
    statistics.alpha_composite(icon_speed, (bar_vl_x - 140, 104 - icon_speed.size[1] // 2))
    icon_defense = AssetManager.get_stat_icon("defense")
    rd_defense = render_stat_value(f'{unit_data.get("defense")}+')
    statistics.alpha_composite(rd_defense, (bar_vl_x - rd_defense.size[0] // 2, 638 - rd_defense.size[1] // 2))
    statistics.alpha_composite(icon_defense, (bar_vl_x - 140, 638 - icon_defense.size[1] // 2))
    icon_morale = AssetManager.get_stat_icon("morale")
    rd_morale = render_stat_value(f'{unit_data.get("morale")}+')
    statistics.alpha_composite(rd_morale, (bar_vl_x + 192 - rd_morale.size[0] // 2, 638 - rd_morale.size[1] // 2))
    statistics.alpha_composite(icon_morale, (bar_vl_x + 52, 638 - icon_morale.size[1] // 2))

    for ix, attack_data in enumerate(attacks):
        # TODO: ???
        if ix > 1:
            continue
        rd_attack = render_attack(attack_data)
        statistics.alpha_composite(rd_attack, (30, 198 + ix * 188))

    all_text = Image.new("RGBA", (w, h))
    name_split = [f"**{l.upper()}**" for l in split_on_center_space(name, maxlen=14)]
    rd_name = render_paragraph(name_split, font_color="white", font_size=45, line_padding=14, stroke_width=0, letter_spacing=-0.7)
    name_x, name_y = 499 - rd_name.size[0] // 2, 734 - rd_name.size[1] // 2
    all_text.alpha_composite(rd_name, (name_x, name_y))
    rd_version = render_text_line(f"*{version.strip('*')}*", font_color="white", font_size=20, stroke_width=0.15, letter_spacing=-0.2)
    version_x, version_y = 21, h - rd_version.size[0] - 30
    all_text.alpha_composite(rd_version.rotate(90, expand=1), (version_x, version_y))

    rd_abilities = Image.new("RGBA", (w,h))
    abilities_part_y = 64
    filtered_abilities_data = []
    for ability_name in abilities:
        ability_data = abilities_data.get(ability_name.upper())
        if ability_data is None:
            print(f'WARNING: Couldn\'t find ability "{ability_name}" in unit "{name}"')
            continue
        ability_data["name"] = ability_name
        filtered_abilities_data.append(ability_data)

    skill_top = ImageOps.flip(AssetManager.get_skill_bottom(faction))
    skill_divider = AssetManager.get_skill_divider(faction)
    skill_bottom = AssetManager.get_skill_bottom(faction)

    font_size = 36
    line_padding = 16
    divider_padding = 15
    get_all_text = lambda a: [a.get("name")] + (a.get("trigger") or []) + a.get("effect")
    h_abilities = sum([calc_height_paragraph(get_all_text(a), 36, 16) for a in filtered_abilities_data])
    h_abilities += 150 + (len(filtered_abilities_data) - 1) * (skill_divider.size[1] + 30)
    overflow_px = h_abilities - h

    num_lines = sum([len(get_all_text(a)) for a in filtered_abilities_data])
    if overflow_px > 0:
        for i in range(18):
            if overflow_px <= 0:
                break
            if i == 0:
                abilities_part_y -= 5
                overflow_px -= 5
            elif i == 15:
                font_size -= 3
                overflow_px -= int(num_lines * FACTOR_FIXED_LINE_HEIGHT * 3)
            elif i % 3 == 0:
                divider_padding -= 2
                overflow_px -= 4 * (len(filtered_abilities_data) - 0.5)
            else:
                line_padding -= 1
                overflow_px -= num_lines

    for ix, ability_data in enumerate(filtered_abilities_data):
        if ix == 0:
            rd_abilities.alpha_composite(apply_drop_shadow(skill_top), (783, abilities_part_y - skill_top.size[1] - 35))

        rd_ability, h_text = render_ability(ability_data, faction, font_size=font_size, line_padding=line_padding)
        ability_y = abilities_part_y + (h_text - rd_ability.size[1]) // 2
        abilities_part_y += h_text + divider_padding

        if ix + 1 == len(filtered_abilities_data):
            rd_abilities.alpha_composite(apply_drop_shadow(skill_bottom), (783, abilities_part_y - 25))
        else:
            rd_abilities.alpha_composite(apply_drop_shadow(skill_divider), (740, abilities_part_y - 20))
            abilities_part_y += skill_divider.size[1] + divider_padding
        rd_abilities.alpha_composite(rd_ability, (694, ability_y))

    unit_card.alpha_composite(apply_drop_shadow(bars, passes=10, shadow_size=5), (-20, -20))
    unit_card.alpha_composite(crests)
    unit_card.alpha_composite(apply_drop_shadow(statistics), (-20, -20))
    unit_card.alpha_composite(all_text)
    unit_card.alpha_composite(rd_abilities)

    return unit_card


def render_ability(ability_data, faction, **kwargs):
    font_size = kwargs.get("font_size")

    name = ability_data.get("name")
    icons = ability_data.get("icons") or []
    name_font_color = get_faction_text_color(faction)
    rd_name = render_text_line(f"**{name.upper()}**", font_color=name_font_color, font_size=font_size, letter_spacing=2.3)
    trigger_effect = (ability_data.get("trigger") or []) + (ability_data.get("effect") or [])
    rd_trigger_effect = render_paragraph(trigger_effect, font_color="#5d4d40", align="left", **kwargs)
    highlight_color = get_faction_highlight_color(faction)
    rd_icons = [render_skill_icons(icon, highlight_color) for icon in icons]
    h_icons = sum([114 for _ in rd_icons]) + 20
    w_icons = 134
    h_text = rd_name.size[1] + rd_trigger_effect.size[1]
    w_text = max(rd_name.size[0], rd_trigger_effect.size[0])

    all_icons = Image.new("RGBA", (w_icons, h_icons))
    for ix, icon in enumerate(rd_icons):
        all_icons.alpha_composite(apply_drop_shadow(icon), (-20, ix * 114 -20))
    w, h = w_icons + w_text + 100, max(h_text, h_icons)
    rendered = Image.new("RGBA", (w, h))
    rendered.alpha_composite(rd_name, (144, (h - h_text) // 2))
    rendered.alpha_composite(rd_trigger_effect, (144, (h - h_text) // 2 + rd_name.size[1]))
    rendered.alpha_composite(all_icons, (0, (rendered.size[1] - h_icons) // 2))

    return rendered, h_text



def main():
    archers = {
        "name": "Ironborn Bowmen",
        "id": "10802",
        "faction": "Greyjoy",
        "type": "infantry",
        "cost": 4,
        "speed": 5,
        "defense": 6,
        "morale": 8,
        "attacks": [
            {
                "name": "Ironborn Arrows",
                "type": "long",
                "hit": 4,
                "dice": [
                    6,
                    5,
                    4
                ]
            },
            {
                "name": "Shortsword",
                "type": "melee",
                "hit": 4,
                "dice": [
                    5,
                    4,
                    3
                ]
            }
        ],
        "abilities": [
            "Order: Divide the Spoils",
            "Ironborn Arrows"
        ],
        "version": "2021-S03"
    }
    abilities = {
        "ORDER: DIVIDE THE SPOILS": {
            "trigger": [
                "**Start of any Turn:**"
            ],
            "effect": [
                "Target 1 friendly House Greyjoy unit in",
                "Short Range. You may remove 1 Pillage",
                "token from that unit and then place 1",
                "Pillage token on 1 other friendly House",
                "Greyjoy unit in Short Range of them.",
            ],
            "icons": [
                "order",
            ]
        },
        "IRONBORN ARROWS": {
            "effect": [
                "May re-roll Attack Dice when",
                "Attacking enemies in the **Flank** or **Rear.**",
            ],
            "icons": [
                "ranged",
            ]
        },
    }
    unit_card = generate_unit(archers, abilities)
    unit_card.save("gen.png")
    unit_card_original = Image.open("archers.jpg")
    ImageEditor(unit_card, unit_card_original)


if __name__ == "__main__":
    main()
