from generate_utils import *
from image_editor import ImageEditor


def generate_unit(asset_manager, unit_id, name, subname, unit_data, abilities_data):
    faction = unit_data.get("faction")
    version = unit_data.get("version")
    attacks = unit_data.get("attacks")
    abilities = unit_data.get("abilities") or []

    unit_bg = asset_manager.get_unit_bg(faction)
    w, h = unit_bg.size
    unit_card = Image.new("RGBA", (w, h))
    unit_card.paste(unit_bg)

    if len(abilities) > 0:
        skills_bg = asset_manager.get_unit_skills_bg()
        unit_card.paste(skills_bg, (w - skills_bg.size[0], 0))

    unit_image = asset_manager.get_unit_image(unit_id)
    unit_card.paste(unit_image, (497 - unit_image.size[0] // 2, min(0, 642 - unit_image.size[1])))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = asset_manager.get_bars(faction)
    decor = asset_manager.get_decor(faction)

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
    crest = asset_manager.get_crest_shadow(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.rotate(-12, expand=1, resample=Image.BICUBIC)
    offset_crop = crest.crop((0, 0, crest.width, crests.height // 4))
    offset = (offset_crop.width - offset_crop.getbbox()[2]) // 2
    crest_w, crest_h = int(188 * crest.size[0] / crest.size[1]), 188
    crest = crest.resize((crest_w, crest_h), resample=Image.LANCZOS)
    crests.alpha_composite(apply_drop_shadow(crest), (704 - crest_w + offset, 456))
    unit_type = asset_manager.get_unit_type(unit_data.get("type"), faction)
    crests.alpha_composite(unit_type, (228 - unit_type.size[0] // 2, h - unit_type.size[1]))

    statistics = Image.new("RGBA", (w, h))
    icon_speed = asset_manager.get_stat_icon("speed")
    rd_speed = render_stat_value(asset_manager, unit_data.get("speed"))
    statistics.alpha_composite(rd_speed, (bar_vl_x - 3 - rd_speed.size[0] // 2, 104 - rd_speed.size[1] // 2))
    statistics.alpha_composite(icon_speed, (bar_vl_x - 140, 104 - icon_speed.size[1] // 2))
    icon_defense = asset_manager.get_stat_icon("defense")
    rd_defense = render_stat_value(asset_manager, f'{unit_data.get("defense")}+')
    statistics.alpha_composite(rd_defense, (bar_vl_x - rd_defense.size[0] // 2, 638 - rd_defense.size[1] // 2))
    statistics.alpha_composite(icon_defense, (bar_vl_x - 140, 638 - icon_defense.size[1] // 2))
    icon_morale = asset_manager.get_stat_icon("morale")
    rd_morale = render_stat_value(asset_manager, f'{unit_data.get("morale")}+')
    statistics.alpha_composite(rd_morale, (bar_vl_x + 192 - rd_morale.size[0] // 2, 638 - rd_morale.size[1] // 2))
    statistics.alpha_composite(icon_morale, (bar_vl_x + 52, 638 - icon_morale.size[1] // 2))

    for ix, attack_data in enumerate(attacks):
        # TODO: ???
        if ix > 1:
            continue
        rd_attack = render_attack(asset_manager, attack_data, get_faction_highlight_color(faction))
        statistics.alpha_composite(rd_attack, (30, 198 + ix * 188))

    all_text = Image.new("RGBA", (w, h))
    renderer_name = TextRenderer(name.upper(), "Tuff", (340, 120), asset_manager, font_size=45, bold=True, font_color="white", leading=1,
                                 tracking=-15, stroke_width=0, supersample=4, align_y=TextRenderer.ALIGN_CENTER)
    rd_name = renderer_name.render()
    name_x, name_y = 499, 740
    if subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (300, 80), asset_manager, font_size=30, font_color="white", leading=1,
                                        stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        name_sect = renderer_subname.rendered_section_coords[0]
        rd_subname = rd_subname.crop((0, int(name_sect[0]), rd_subname.size[0], int(name_sect[1])))
        rd_name = rd_name.crop(rd_name.getbbox())
        rd_names = Image.new("RGBA", (max(rd_name.size[0], rd_subname.size[0]), rd_name.size[1] + rd_subname.size[1] + 4))
        rd_names.alpha_composite(rd_name, ((rd_names.size[0] - rd_name.size[0]) // 2, 0))
        rd_names.alpha_composite(rd_subname, ((rd_names.size[0] - rd_subname.size[0]) // 2, rd_name.size[1] + 4))
        all_text.alpha_composite(rd_names, (name_x - rd_names.size[0] // 2, name_y - rd_names.size[1] // 2))
    else:
        all_text.alpha_composite(rd_name, (name_x - rd_name.size[0] // 2, name_y - rd_name.size[1] // 2))

    renderer_version = TextRenderer(version, "Tuff", (100, 25), asset_manager, font_size=20, italic=True, font_color="white",
                                    stroke_width=0, leading=1, tracking=-10, align_y=TextRenderer.ALIGN_BOTTOM,
                                    align_x=TextRenderer.ALIGN_LEFT, padding=(5, 0, 5, 0))
    rd_version = renderer_version.render()
    version_x, version_y = 25, h - rd_version.size[0] - 25
    all_text.alpha_composite(rd_version.rotate(90, expand=1), (version_x, version_y))

    rd_abilities = Image.new("RGBA", (w, h))
    filtered_abilities_data = get_filtered_ability_data(abilities, abilities_data)
    abilities_to_render = get_ability_data_for_renderer(filtered_abilities_data, get_faction_text_color(faction))

    skill_top = ImageOps.flip(asset_manager.get_skill_bottom(faction))
    skill_divider = asset_manager.get_skill_divider(faction)
    skill_bottom = asset_manager.get_skill_bottom(faction)
    section_padding = skill_divider.size[1]
    renderer_abilities = TextRenderer(abilities_to_render, "Tuff", (560, h - 100), asset_manager, font_size=36,
                                      align_x=TextRenderer.ALIGN_LEFT, section_padding=section_padding, font_color="#5d4d40",
                                      padding=(10, 20, 10, 20))
    rendered = renderer_abilities.render()
    rd_abilities.alpha_composite(rendered, (830, 50))

    section_coords = renderer_abilities.rendered_section_coords
    # 30 = 50 (offset from rendered) - 20 (offset from dropshadow)
    rd_abilities.alpha_composite(apply_drop_shadow(skill_top), (783, int(section_coords[0][0]) + 30 - skill_top.size[1]))
    rd_abilities.alpha_composite(apply_drop_shadow(skill_bottom), (783, int(section_coords[-1][1]) + 30))
    for ix in range(len(section_coords) - 1):
        top, bot = section_coords[ix][1], section_coords[ix + 1][0]
        center = int(top + (bot - top) / 2) + 30
        rd_abilities.alpha_composite(apply_drop_shadow(skill_divider), (740, center - skill_divider.size[1] // 2))

    for data, coords in zip(filtered_abilities_data, section_coords):
        icons = data.get("icons")
        if icons is None:
            continue
        highlight_color = get_faction_highlight_color(faction)
        rd_icons = render_skill_icons(asset_manager, icons, highlight_color)
        x, y = 694, 50 + coords[0] + (coords[1] - coords[0] - rd_icons.size[1]) // 2
        rd_abilities.alpha_composite(rd_icons, (x, int(y)))

    unit_card.alpha_composite(apply_drop_shadow(bars, color="#00000033", shadow_size=7), (-20, -20))
    unit_card.alpha_composite(crests)
    unit_card.alpha_composite(apply_drop_shadow(statistics), (-20, -20))
    unit_card.alpha_composite(all_text)
    unit_card.alpha_composite(rd_abilities)

    return unit_card


def generate_unit_back(asset_manager, unit_id, name, subname, unit_data, unit_fluff):
    faction = unit_data.get("faction")

    unit_bg = asset_manager.get_unit_bg(faction)
    w, h = unit_bg.size
    unit_card = Image.new("RGBA", (w, h))
    unit_card.paste(unit_bg)
    img = asset_manager.get_unit_image(unit_id + "b")
    unit_card.paste(img)
    skills_bg = asset_manager.get_unit_skills_bg()
    # TODO: Units with subname/quotes
    unit_card.paste(skills_bg, (893, 166))

    layer_bars = Image.new("RGBA", (w, h))
    layer_bars_lower = Image.new("RGBA", (w, h))
    large_bar, small_bar, corner_bar = asset_manager.get_bars(faction)
    sb_w, sb_h = small_bar.size
    lb_w, lb_h = large_bar.size
    # TODO: Corner bar
    layer_bars_lower.alpha_composite(large_bar.rotate(270, expand=1).crop((0, lb_w - h, lb_h, lb_w)), (846 - lb_h // 2, 0))
    layer_bars.alpha_composite(small_bar.rotate(90, expand=1), (846 - (lb_h + sb_h) // 2, 0))
    layer_bars.alpha_composite(small_bar.rotate(90, expand=1), (846 + (lb_h - sb_h) // 2, 0))
    layer_bars.alpha_composite(small_bar, (846 + (lb_h - sb_h) // 2, 164))

    layer_crests = Image.new("RGBA", (w, h))
    unit_type = asset_manager.get_unit_type(unit_data.get("type"), faction)
    layer_crests.alpha_composite(unit_type, (846 - unit_type.size[0] // 2, h - unit_type.size[1]))
    # TODO: Varamyr Commander
    rd_cost = render_cost(asset_manager, unit_data.get("cost", 0), get_faction_highlight_color(faction), unit_data.get("commander"))
    layer_crests.alpha_composite(rd_cost, (846 - rd_cost.size[0] // 2, 555))
    crest = asset_manager.get_crest(faction)
    crest = crest.crop(crest.getbbox())
    crest_size = min(184, int(crest.size[0] * 213 / crest.size[1])), min(213, int(crest.size[1] * 184 / crest.size[0]))
    crest = crest.resize(crest_size)
    crest_x, crest_y = 826 - crest.size[0] // 2, 25
    layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_x, crest_y))

    layer_text = Image.new("RGBA", (w, h))
    renderer_name = TextRenderer(name.upper(), "Tuff", (440, 80), asset_manager, font_size=46, bold=True, font_color="white", leading=1,
                                 stroke_width=0.2, align_y=TextRenderer.ALIGN_CENTER)
    rd_name = renderer_name.render()
    layer_text.alpha_composite(rd_name, (947, 50))
    renderer_lore = TextRenderer(unit_fluff.get("lore"), "Tuff", (460, 620), asset_manager, font_size=38, italic=True, font_color="#5d4d40",
                                 stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER, align_x=TextRenderer.ALIGN_LEFT,
                                 padding=(20, 20, 20, 20))
    rd_lore = renderer_lore.render()
    layer_text.alpha_composite(rd_lore, (915, 190))

    # TODO: Restrictions/Loyalty

    unit_card.alpha_composite(apply_drop_shadow(layer_bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
    unit_card.alpha_composite(apply_drop_shadow(layer_bars), (-20, -20))
    unit_card.alpha_composite(apply_drop_shadow(layer_crests), (-20, -20))
    unit_card.alpha_composite(layer_text)

    return unit_card


def main():
    from asset_manager import AssetManager
    data = {
        "faction": "greyjoy",
        "cost": 7,
        "type": "infantry"
    }
    fluff = {
        "lore": "Of the different warriors that House Greyjoy sends to assault shoreline settlements, the Blacktyde Chosen are the most feared. When these elite warriors hit the beach, they rapidly form their ranks and sweep a path clear through any defences or defenders that stand in their way. Clad in scale mail, armed with master-crafted axes, and wielding large round shields, the Chosen are among the heaviest troops under the Kraken banner."
    }
    back = generate_unit_back(AssetManager(), "10806", "Blacktyde Chosen", None, data, fluff)
    org = Image.open(r"").convert("RGBA")
    org = org.resize((1417, 827))
    editor = ImageEditor(back, org)


if __name__ == "__main__":
    main()
