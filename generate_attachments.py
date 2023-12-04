from generate_utils import *
from image_editor import ImageEditor
from asset_manager import AssetManager


def generate_attachment(attachment_data, abilities_data):
    faction = re.sub(r"[^A-Za-z]", "", attachment_data.get("faction"))
    name = attachment_data.get("name")
    subname = attachment_data.get("subname")
    attachment_id = attachment_data.get("id")
    version = attachment_data.get("version")
    abilities = attachment_data.get("abilities")
    is_commander = attachment_data.get("commander", False)

    background = AssetManager.get_bg(faction)
    w, h = background.size
    attachment_card = Image.new("RGBA", (w, h))
    attachment_card.paste(background.rotate(get_faction_bg_rotation(faction)))
    if is_commander:
        text_bg = AssetManager.get_unit_skills_bg()
        attachment_card.paste(text_bg, (141, 338))
    else:
        text_bg = AssetManager.get_unit_skills_bg()
        text_bg = text_bg.crop((0, 0, 555, text_bg.size[1]))
        attachment_card.paste(text_bg, (141, 338))
    portrait = AssetManager.get_attachment_image(attachment_id)
    if is_commander:
        attachment_card.paste(portrait)
    else:
        attachment_card.paste(portrait, (50, 50))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = AssetManager.get_bars(faction)
    small_bar_ds = apply_drop_shadow(small_bar)
    decor = AssetManager.get_decor(faction)
    small_horizontal_crop = small_bar_ds.crop((0, 0, 662, small_bar_ds.size[1]))
    large_horizontal_crop = large_bar.crop((200, large_bar.size[1] // 2 - 21, 842, large_bar.size[1] // 2 + 21))
    short_vertical = small_bar_ds.rotate(90, expand=1).crop((0, 20, small_bar_ds.size[0], 212))

    if is_commander:
        bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, 106, large_bar.size[1], large_bar.size[0])), (54, 338))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (26, 318))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (111, 318))
        bars.alpha_composite(weird_bar.rotate(90, expand=1), (327, 250 - weird_bar.size[0]))
        bars.alpha_composite(ImageOps.flip(weird_bar.rotate(90, expand=1)), (327, 250 - 2 * weird_bar.size[0]))
        bars.alpha_composite(ImageOps.mirror(weird_bar.rotate(90, expand=1)), (245 - weird_bar.size[1], 250 - weird_bar.size[0]))
        bars.alpha_composite(weird_bar.rotate(270, expand=1), (245 - weird_bar.size[1], 250 - 2 * weird_bar.size[0]))
        bars.alpha_composite(ImageOps.mirror(large_bar), (-150, 249))
        bars.alpha_composite(small_bar_ds, (-20, 222))
        bars.alpha_composite(small_bar_ds, (-20, 307))
        bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, large_bar.size[0] - 192, large_bar.size[1], large_bar.size[0])), (243, 50))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (215, 222 - small_bar.size[0]))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (298, 222 - small_bar.size[0]))
    else:
        bars.alpha_composite(large_horizontal_crop.rotate(180), (55, 292))
        bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, 106, large_bar.size[1], large_bar.size[0])), (54, 338))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (26, 30))
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (111, 318))
        bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, large_bar.size[0] - 192, large_bar.size[1], large_bar.size[0])), (243, 50))
        bars.alpha_composite(short_vertical, (215, 50))
        bars.alpha_composite(short_vertical, (298, 50))
        bars.alpha_composite(small_horizontal_crop, (35, 265))
        bars.alpha_composite(small_horizontal_crop, (35, 307))
        bars.alpha_composite(decor, (33, 271))

    bars.alpha_composite(decor, (33, 314))
    bars.alpha_composite(decor, (118, 314))

    unit_type = AssetManager.get_attachment_type(attachment_data.get("type"), faction)
    if is_commander:
        bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, -23))
    else:
        unit_type = unit_type.crop((0, 34, unit_type.size[0], unit_type.size[1]))
        bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, 30))

    crest = AssetManager.get_crest_tactics(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.resize(((102 + crest.size[0]) // 2, int(crest.size[1] * ((102 + crest.size[0]) / 2) / crest.size[0])))
    crest_resize_x, crest_resize_y = 265 - crest.size[0] // 2, 244 - crest.size[1] // 2
    bars.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

    rd_abilities = Image.new("RGBA", (w,h))
    skill_divider = AssetManager.get_skill_divider(faction)
    skill_bottom = AssetManager.get_skill_bottom(faction)
    if not is_commander:
        skill_divider = skill_divider.crop((0, 0, 590, skill_divider.size[1]))
        skill_bottom = skill_bottom.crop((0, 0, 560, skill_bottom.size[1]))
    filtered_abilities_data = get_filtered_ability_data(abilities, abilities_data)

    abilities_part_y = 354
    font_size = 36
    line_padding = 16
    divider_padding = 15
    for ix, ability_data in enumerate(filtered_abilities_data):
        rd_ability, h_text = render_ability(ability_data, faction, font_size=font_size, line_padding=line_padding, x_spacing=12)
        ability_y = abilities_part_y + (h_text - rd_ability.size[1]) // 2
        abilities_part_y += h_text + divider_padding

        if ix + 1 == len(filtered_abilities_data):
            bars.alpha_composite(apply_drop_shadow(skill_bottom, shadow_size=7), (119, abilities_part_y - 25))
        else:
            bars.alpha_composite(apply_drop_shadow(skill_divider, shadow_size=7), (73, abilities_part_y - 20))
            abilities_part_y += skill_divider.size[1] + divider_padding
        rd_abilities.alpha_composite(rd_ability, (27, ability_y))

    all_text = Image.new("RGBA", (w, h))
    name_split = [f"**{np.upper()}**" for np in split_on_center_space(name, maxlen=10)]
    rd_name = render_paragraph(name_split, font_color="white", font_size=50, line_padding=8)
    if is_commander:
        name_x, name_y = 536, 130
    else:
        name_x, name_y = 511, 170
    if subname is not None:
        subname_split = [np.upper() for np in split_on_center_space(subname, maxlen=24)]
        rd_subname = render_paragraph(subname_split, font_color="white", font_size=30, stroke_width=0.1, line_padding=8)
        rd_names = Image.new("RGBA", (max(rd_name.size[0], rd_subname.size[0]), rd_name.size[1] + rd_subname.size[1] - 8))
        rd_names.alpha_composite(rd_name, ((rd_names.size[0] - rd_name.size[0]) // 2, 0))
        rd_names.alpha_composite(rd_subname, ((rd_names.size[0] - rd_subname.size[0]) // 2, rd_name.size[1] - 8))
        all_text.alpha_composite(rd_names, (name_x - rd_names.size[0] // 2, name_y - rd_names.size[1] // 2))
    else:
        all_text.alpha_composite(rd_name, (name_x - rd_name.size[0] // 2, name_y - rd_name.size[1] // 2))

    rendered_version = render_text_line(f"*{version.strip('*')}*", font_color="white", font_size=20)
    version_x, version_y = 21, h - rendered_version.size[0] - 40
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    if not is_commander:
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (667, 30))
        bars.alpha_composite(small_horizontal_crop, (35, 26))
        bars.alpha_composite(decor, (674, 271))
        bars.alpha_composite(decor, (674, 314))
        bars.alpha_composite(decor, (33, 33))
        bars.alpha_composite(decor, (674, 33))

    attachment_card.alpha_composite(apply_drop_shadow(bars, shadow_size=7, color="#00000055"), (-20, -20))
    attachment_card.alpha_composite(rd_abilities)
    attachment_card.alpha_composite(all_text)

    return attachment_card


def main():
    theon = {
        "id": "20808",
        "name": "Theon Greyjoy",
        "subname": "\"Prince\" of Winterfell",
        "faction": "Greyjoy",
        "type": "Infantry",
        "commander": True,
        "abilities": [
            "Order: Sentinel",
            "Ambush",
            "Enhanced Mobility"
        ],
        "version": "2021-S03"
    }
    asha = {
        "id": "20802",
        "name": "Asha Greyjoy",
        "subname": "Captain of the Black Wind",
        "faction": "Greyjoy",
        "type": "Infantry",
        "abilities": [
            "Order: War Cry",
            "Iron Resolve"
        ],
        "version": "2021-S03"
    }
    from parse_csv import parse_abilities
    abilities = parse_abilities()
    attachment_card = generate_attachment(asha, abilities["en"])
    attachment_original = Image.open("asha.jpg")
    ImageEditor(attachment_card, attachment_original)


if __name__ == "__main__":
    main()
