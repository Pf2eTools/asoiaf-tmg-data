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


def main():
    pass


if __name__ == "__main__":
    main()
