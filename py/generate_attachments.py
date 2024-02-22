from generate_utils import *
from image_editor import ImageEditor


def generate_attachment(asset_manager, attachment_id, name, subname, attachment_data, abilities_data):
    faction = attachment_data.get("faction")
    version = attachment_data.get("version")
    abilities = attachment_data.get("abilities")
    is_commander = attachment_data.get("commander", False)

    background = asset_manager.get_bg(faction)
    w, h = background.size
    attachment_card = Image.new("RGBA", (w, h))
    attachment_card.paste(background.rotate(get_faction_bg_rotation(faction)))
    if is_commander:
        text_bg = asset_manager.get_unit_skills_bg()
        attachment_card.paste(text_bg, (141, 338))
    else:
        text_bg = asset_manager.get_unit_skills_bg()
        text_bg = text_bg.crop((0, 0, 555, text_bg.size[1]))
        attachment_card.paste(text_bg, (141, 338))
    portrait = asset_manager.get_attachment_image(attachment_id)
    # FIXME: HACK
    if attachment_id == "20521" or attachment_id == "20517":
        portrait = portrait.resize((portrait.width // 2, portrait.height // 2)).crop((0, 0, 197, 248))
    if is_commander:
        attachment_card.paste(portrait)
    else:
        attachment_card.paste(portrait, (50, 50))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = asset_manager.get_bars(faction)
    small_bar_ds = apply_drop_shadow(small_bar)
    decor = asset_manager.get_decor(faction)
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
        bars.alpha_composite(weird_bar.rotate(90, expand=1).crop((0, 0, 370, weird_bar.size[0])), (327, 290 - weird_bar.size[0]))
        weird_bar_cropped = ImageOps.mirror(weird_bar.rotate(90, expand=1)).crop((weird_bar.size[1] - portrait.size[0], 0, weird_bar.size[1], weird_bar.size[0]))
        bars.alpha_composite(weird_bar_cropped, (245 - weird_bar_cropped.size[0], 290 - weird_bar_cropped.size[1]))

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

    attach_type = attachment_data.get("type")
    if attach_type is not None and attach_type != "None":
        unit_type = asset_manager.get_attachment_type(attach_type, faction)
        if is_commander:
            bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, -23))
        else:
            unit_type = unit_type.crop((0, unit_type.size[1] - 142, unit_type.size[0], unit_type.size[1]))
            bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, 30))

    crest = asset_manager.get_crest(faction)
    crest = crest.crop(crest.getbbox())
    crest_size = min(158, int(crest.size[0] * 182 / crest.size[1])), min(182, int(crest.size[1] * 158 / crest.size[0]))
    crest = crest.resize(crest_size)
    crest_resize_x, crest_resize_y = 265 - crest.size[0] // 2, 244 - crest.size[1] // 2
    bars.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

    layer_abilities = Image.new("RGBA", (w, h))
    skill_divider = asset_manager.get_skill_divider(faction)
    skill_bottom = asset_manager.get_skill_bottom(faction)
    if not is_commander:
        skill_divider = skill_divider.crop((0, 0, 600, skill_divider.size[1]))
        skill_bottom = skill_bottom.crop((0, 0, 560, skill_bottom.size[1]))
    filtered_abilities_data = get_filtered_ability_data(abilities, abilities_data)
    abilities_to_render = get_ability_data_for_renderer(filtered_abilities_data, get_faction_text_color(faction))

    section_padding = skill_divider.size[1]
    w_abilities = w - 150 if is_commander else 536
    renderer_abilities = TextRenderer(abilities_to_render, "Tuff", (w_abilities, h - 396), asset_manager, font_size=36,
                                      align_x=TextRenderer.ALIGN_LEFT, align_y=TextRenderer.ALIGN_TOP, section_padding=section_padding,
                                      font_color="#5d4d40", padding=(15, 16, 25, 16), leading=1.08)
    rd_abilities = renderer_abilities.render()
    layer_abilities.alpha_composite(rd_abilities, (150, 346))
    section_coords = renderer_abilities.rendered_section_coords
    bars.alpha_composite(apply_drop_shadow(skill_bottom, shadow_size=7), (117, min(int(section_coords[-1][1]), h - 396) + 326))
    for ix in range(len(section_coords) - 1):
        top, bot = section_coords[ix][1], section_coords[ix + 1][0]
        center = int(top + (bot - top) / 2) + 326
        bars.alpha_composite(apply_drop_shadow(skill_divider), (73, center - skill_divider.size[1] // 2))

    for data, coords in zip(filtered_abilities_data, section_coords):
        icons = data.get("icons")
        if icons is None:
            continue
        highlight_color = get_faction_highlight_color(faction)
        rd_icons = render_skill_icons(asset_manager, icons, highlight_color)
        x, y = 28, 346 + coords[0] + (coords[1] - coords[0] - rd_icons.size[1]) // 2
        layer_abilities.alpha_composite(rd_icons, (x, int(y)))

    all_text = Image.new("RGBA", (w, h))
    # FIXME: HACK
    name_font_size = 50 if attachment_id != "20517" else 35
    renderer_name = TextRenderer(name.upper(), "Tuff", (340, 100), asset_manager, font_size=name_font_size, bold=True, font_color="white",
                                 leading=0.9, stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
    rd_name = renderer_name.render()
    rd_name = rd_name.crop((0, 0, rd_name.size[0], int(renderer_name.rendered_section_coords[0][1])))

    if is_commander:
        name_x, name_y = 536, 130
        subname_w = 340
    else:
        name_x, name_y = 511, 170
        subname_w = 280
    if subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (subname_w, 80), asset_manager, font_size=30, font_color="white",
                                        leading=1, stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        rd_subname = rd_subname.crop((0, 0, rd_subname.size[0], int(renderer_subname.rendered_section_coords[0][1])))
        rd_names = Image.new("RGBA", (max(rd_name.size[0], rd_subname.size[0]), rd_name.size[1] + rd_subname.size[1] - 8))
        rd_names.alpha_composite(rd_name, ((rd_names.size[0] - rd_name.size[0]) // 2, 0))
        rd_names.alpha_composite(rd_subname, ((rd_names.size[0] - rd_subname.size[0]) // 2, rd_name.size[1] - 8))
        all_text.alpha_composite(rd_names, (name_x - rd_names.size[0] // 2, name_y - rd_names.size[1] // 2))
    else:
        all_text.alpha_composite(rd_name, (name_x - rd_name.size[0] // 2, name_y - rd_name.size[1] // 2))

    renderer_version = TextRenderer(version, "Tuff", (100, 25), asset_manager, font_size=20, italic=True, font_color="white",
                                    stroke_width=0, leading=1, tracking=-10, align_y=TextRenderer.ALIGN_BOTTOM,
                                    align_x=TextRenderer.ALIGN_LEFT, padding=(5, 0, 5, 0))
    rendered_version = renderer_version.render()
    version_x, version_y = 19, h - rendered_version.size[0] - 30
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    if not is_commander:
        bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (667, 30))
        bars.alpha_composite(small_horizontal_crop, (35, 26))
        bars.alpha_composite(decor, (674, 271))
        bars.alpha_composite(decor, (674, 314))
        bars.alpha_composite(decor, (33, 33))
        bars.alpha_composite(decor, (674, 33))

    attachment_card.alpha_composite(apply_drop_shadow(bars, shadow_size=7, color="#00000033"), (-20, -20))
    attachment_card.alpha_composite(layer_abilities)
    attachment_card.alpha_composite(all_text)

    return attachment_card


def generate_attachment_back(asset_manager, attachment_id, name, subname, attachment_data, attachment_fluff):
    faction = attachment_data.get("faction")
    background = asset_manager.get_bg(faction)
    w, h = background.size
    attachment_card = Image.new("RGBA", (w, h))
    attachment_card.paste(background.rotate(get_faction_bg_rotation(faction)))

    portrait = asset_manager.get_attachment_image(attachment_id + "b")
    if attachment_data.get("commander"):
        attachment_card.paste(portrait, (148, 292))
    elif attachment_data.get("character"):
        attachment_card.paste(portrait, (135, 345))
    else:
        attachment_card.paste(portrait, (135, 242))

    bars = Image.new("RGBA", (w, h))
    bars_lower = Image.new("RGBA", (w, h))
    large_bar, small_bar, corner_bar = asset_manager.get_bars(faction)
    decor = asset_manager.get_decor(faction)
    lb_w, lb_h = large_bar.size
    sb_w, sb_h = small_bar.size
    if attachment_data.get("commander"):
        bars_lower.alpha_composite(large_bar.crop((220, lb_h // 4, lb_w, 3 * lb_h // 4)), (140, 238))
        bars_lower.alpha_composite(large_bar.rotate(90, expand=1), (98 - lb_h // 2, 0))
        bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 233))
        bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 280))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 - (lb_h + sb_h) // 2, 0))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 + (lb_h - sb_h) // 2, 0))
    elif attachment_data.get("character"):
        bars_lower.alpha_composite(large_bar.crop((220, lb_h // 4, 780, 3 * lb_h // 4)), (140, 292))
        bars_lower.alpha_composite(large_bar.rotate(90, expand=1), (98 - lb_h // 2, 55))
        bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, 287))
        bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, 330))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 - (lb_h + sb_h) // 2, 55))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 + (lb_h - sb_h) // 2, 55))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (687, 55))
        bars.alpha_composite(apply_drop_shadow(small_bar.crop((0, 0, 650, 100))), (30, 26))
        bars.alpha_composite(decor, (98 - (lb_h + decor.width) // 2, 33))
        bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, 33))
        bars.alpha_composite(decor, (98 - (lb_h + decor.width) // 2, 273))
        bars.alpha_composite(decor, (98 - (lb_h + decor.width) // 2, 316))
        bars.alpha_composite(decor, (674, 273))
        bars.alpha_composite(decor, (674, 316))
        bars.alpha_composite(decor, (674, 33))
    else:
        bars_lower.alpha_composite(large_bar.rotate(90, expand=1), (98 - lb_h // 2, 55))
        bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, 240))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 - (lb_h + sb_h) // 2, 55))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 + (lb_h - sb_h) // 2, 55))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (687, 55))
        bars.alpha_composite(small_bar.crop((0, 0, 650, 100)), (50, 46))
        bars.alpha_composite(decor, (98 - (lb_h + decor.width) // 2, 33))
        bars.alpha_composite(decor, (98 - (lb_h + decor.width) // 2, 226))
        bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, 33))
        bars.alpha_composite(decor, (674, 226))
        bars.alpha_composite(decor, (674, 33))

    layer_text = Image.new("RGBA", (w, h))
    layer_crests = Image.new("RGBA", (w, h))

    requirements = attachment_data.get("requirements")
    if attachment_data.get("commander") and requirements is not None:
        pass
    elif requirements is not None:
        requirement_y = 985 - len(requirements) * 112
        # FIXME: Hack alert
        # jaqen, reaver captain
        if attachment_id in ["20221", "20805"]:
            requirement_y -= 70
        # scorpion mods
        elif attachment_id in ["20521", "20517"]:
            requirement_y -= 160
        text_bg = asset_manager.get_text_bg().crop((0, 0, portrait.width, 1000))
        attachment_card.paste(text_bg, (135, requirement_y))
        bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, requirement_y - sb_h // 2))
        bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, requirement_y - decor.height // 2))
        bars.alpha_composite(decor, (674, requirement_y - decor.height // 2))
        requirements_to_render = get_requirement_data_for_renderer(requirements)
        h_requirements = h - requirement_y - sb_h // 2
        renderer_requirements = TextRenderer(requirements_to_render, "Tuff", (520, h_requirements), asset_manager, font_size=30,
                                             font_color="#5d4d40", stroke_width=0.2, align_y=TextRenderer.CENTER_SECTION,
                                             padding=(10, 10, 10, 10))
        rd_requirements = renderer_requirements.render()
        layer_text.alpha_composite(rd_requirements, (155, requirement_y + sb_h // 2))
        section_coords = renderer_requirements.rendered_section_coords
        for ix in range(len(section_coords) - 1):
            top, bot = section_coords[ix][1], section_coords[ix + 1][0]
            center = int(top + (bot - top) / 2) + requirement_y
            bars.alpha_composite(small_bar.crop((0, 0, 560, 100)), (140, center - sb_h // 2))
            bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, center - decor.height // 2))
            bars.alpha_composite(decor, (674, center - decor.height // 2))

        if requirements[0].get("name") is not None:
            box_name = render_small_box(asset_manager, faction, requirements[0].get("name").upper(), get_faction_text_color(faction))
            box_name = apply_drop_shadow(box_name)
            layer_crests.alpha_composite(box_name, (415 - box_name.width // 2, requirement_y - box_name.height // 2))

    if attachment_data.get("commander"):
        box_character = render_character_box(asset_manager, faction)
        layer_crests.alpha_composite(apply_drop_shadow(box_character), (270, 212))
    elif attachment_data.get("character"):
        box_character = render_character_box(asset_manager, faction)
        layer_crests.alpha_composite(apply_drop_shadow(box_character), (395 - box_character.width // 2, 266))
    rendered_cost = render_cost(asset_manager, attachment_data.get("cost", 0), get_faction_highlight_color(faction), attachment_data.get("commander"))
    layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (78 - rendered_cost.width // 2, 764))
    crest = asset_manager.get_crest(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.rotate(14, expand=1, resample=Image.BICUBIC)
    crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
    crest = crest.resize(crest_size)
    if attachment_data.get("commander"):
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2
    elif attachment_data.get("character"):
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 340 - crest.size[1] // 2
    else:
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2
    layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))
    # FIXME: HACK ALERT:
    if attachment_data.get("type") != "none":
        unit_type = asset_manager.get_unit_type(attachment_data.get("type"), faction)
        layer_crests.alpha_composite(apply_drop_shadow(unit_type), (78 - unit_type.width // 2, h - unit_type.size[1] - 20))

    if attachment_data.get("commander"):
        renderer_name = TextRenderer(name.upper(), "Tuff", (572, 60), asset_manager, font_size=54, bold=True, font_color="white", leading=1,
                                     stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
        rd_name = renderer_name.render()
        layer_text.alpha_composite(rd_name, (164, 48))
    elif attachment_data.get("character"):
        renderer_name = TextRenderer(name.upper(), "Tuff", (520, 60), asset_manager, font_size=54, bold=True, font_color="white", leading=1,
                                     stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
        rd_name = renderer_name.render()
        layer_text.alpha_composite(rd_name, (158, 92))
    else:
        name_fs = 44 if attachment_id in ["20521", "20517"] else 54
        renderer_name = TextRenderer(name.upper(), "Tuff", (520, 60), asset_manager, font_size=name_fs, bold=True, font_color="white",
                                     leading=1, stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
        rd_name = renderer_name.render()
        layer_text.alpha_composite(rd_name, (158, 122))

    if attachment_data.get("commander") and subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (572, 40), asset_manager, font_size=30, font_color="white", leading=1,
                                        stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        layer_text.alpha_composite(rd_subname, (164, 98))
    elif attachment_data.get("character") and subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (520, 40), asset_manager, font_size=30, font_color="white", leading=1,
                                        stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        layer_text.alpha_composite(rd_subname, (158, 142))

    if attachment_data.get("commander"):
        renderer_quote = TextRenderer(attachment_fluff.get("quote", ""), "Tuff", (532, 80), asset_manager, font_size=32, font_color="white",
                                      italic=True, stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_quote = renderer_quote.render()
        layer_text.alpha_composite(rd_quote, (184, 143))
    elif attachment_data.get("character"):
        renderer_quote = TextRenderer(attachment_fluff.get("quote", ""), "Tuff", (480, 90), asset_manager, font_size=32, font_color="white",
                                      italic=True, stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_quote = renderer_quote.render()
        layer_text.alpha_composite(rd_quote, (178, 182))

    # TODO: Commander tactics cards

    attachment_card.alpha_composite(apply_drop_shadow(bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
    attachment_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))
    attachment_card.alpha_composite(layer_crests)
    attachment_card.alpha_composite(layer_text)

    return attachment_card


def main():
    from asset_manager import AssetManager
    devan = {
        "id": "20606",
        "name": "Devan Seaworth",
        "subname": "King's Squire",
        "statistics": {
            "version": "2021",
            "faction": "baratheon",
            "type": "infantry",
            "cost": 1,
            "abilities": [
                "Order: Reckless Heroism",
                "True Conviction (Baratheon)"
            ],
            "requirements": [
                {
                    "name": "Loyalty",
                    "heading": "STANNIS BARATHEON",
                    "text": "*Your army may never contain Units or Attachments with different Loyalties.*"
                }
            ],
            "character": True
        },
        "fluff": {
            "quote": "\"You have a passing clever father, Devan\" -Stannis Baratheon"
        }
    }
    bryce = {
        "id": "20632",
        "name": "Bryce Caron",
        "subname": "Bryce the Orange",
        "statistics": {
            "version": "2021-S03",
            "faction": "baratheon",
            "type": "infantry",
            "cost": 1,
            "abilities": [
                "Order: Taunt"
            ],
            "requirements": [
                {
                    "name": "Loyalty",
                    "heading": "RENLY BARATHEON",
                    "text": "*Your army may never contain Units or Attachments with different Loyalties.*"
                },
                {
                    "text": "*May not be fielded in an army containing the Rainbow Guard unit.*"
                }
            ],
            "character": True
        },
        "fluff": {
            "quote": "\"Why are they not here in your company,\nthey who loved Renly best?\"\n-Cortnay Penrose"
        }
    }
    data = devan
    back = generate_attachment_back(AssetManager(), data["id"], data["name"], data["subname"], data["statistics"], data["fluff"])
    editor = ImageEditor(back, back)


if __name__ == "__main__":
    main()
