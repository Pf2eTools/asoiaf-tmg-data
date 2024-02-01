from generate_utils import *
from image_editor import ImageEditor


def generate_ncu(asset_manager, ncu_id, name, subname, ncu_data):
    faction = ncu_data.get("faction")
    version = ncu_data.get("version")
    abilities = ncu_data.get("abilities")

    background = asset_manager.get_bg(faction)
    w, h = background.size
    ncu_card = Image.new("RGBA", (w, h))
    ncu_card.paste(background.rotate(get_faction_bg_rotation(faction)))
    text_bg = asset_manager.get_text_bg()
    text_bg = text_bg.crop((10, 20, text_bg.size[0] - 10, text_bg.size[1] - 5))
    ncu_card.paste(text_bg, (57, 356))
    portrait = asset_manager.get_ncu_img(ncu_id)
    ncu_card.paste(portrait, (52, 54))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = asset_manager.get_bars(faction)
    unit_type = asset_manager.get_unit_type("NCU", faction)
    decor = asset_manager.get_decor(faction)

    wb_w, wb_h = weird_bar.size
    bars.alpha_composite(weird_bar.crop((0, 0, 130, 150)), (52, 52))
    bars.alpha_composite(ImageOps.flip(weird_bar).crop((0, wb_h - 150, 130, wb_h)), (52, 210))
    bars.alpha_composite(ImageOps.mirror(weird_bar).crop((wb_w - 130, 0, wb_w, 150)), (191, 52))
    bars.alpha_composite(weird_bar.crop((0, 0, 130, 150)).rotate(180), (191, 210))
    bars.alpha_composite(large_bar.crop((0, 0, 370, 200)), (320, 222))
    bars.alpha_composite(large_bar.crop((0, large_bar.size[1] // 2, 370, 200)), (320, 315))
    bars.alpha_composite(small_bar.crop((0, 0, text_bg.size[0] + 10, 100)), (50, 46))
    bars.alpha_composite(small_bar.crop((0, 0, text_bg.size[0] + 10, 100)), (50, 350))
    bars.alpha_composite(small_bar.crop((0, 0, text_bg.size[0] + 10, 100)), (50, 984))
    bars.alpha_composite(small_bar.crop((0, 0, 370, 100)), (320, 265))
    bars.alpha_composite(small_bar.crop((0, 0, 370, 100)), (320, 307))
    bars.alpha_composite(unit_type.crop((0, 20, unit_type.size[0], unit_type.size[1])), (323, 228))
    bars.alpha_composite(small_bar.crop((0, 0, 370, 100)), (320, 222))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 300)), (310, 55))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (46, 55))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (687, 55))
    bars.alpha_composite(decor, (33, 33))
    bars.alpha_composite(decor, (33, 185))
    bars.alpha_composite(decor, (33, 337))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (165, 33))
    bars.alpha_composite(decor, (165, 337))
    bars.alpha_composite(decor, (298, 33))
    bars.alpha_composite(decor, (298, 185))
    bars.alpha_composite(decor, (298, 337))
    bars.alpha_composite(decor, (674, 33))
    bars.alpha_composite(decor, (674, 337))
    bars.alpha_composite(decor, (674, 971))

    all_text = Image.new("RGBA", (w, h))
    card_text_to_render = []
    for ability in abilities:
        data = {
            "type": "section",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "style": {
                                "color": get_faction_text_color(faction)
                            },
                            "content": f"**{ability.get('name').upper()}**"
                        },
                    ]
                }
            ]
        }
        for paragraph in ability.get("effect", []):
            data["content"].append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "content": paragraph
                    },
                ]
            })
        card_text_to_render.append(data)
    section_padding = small_bar.size[1]
    align_y = TextRenderer.CENTER_SECTION if len(card_text_to_render) > 1 else TextRenderer.ALIGN_TOP
    renderer_card_text = TextRenderer(card_text_to_render, "Tuff", (620, 605), asset_manager, font_size=36, align_y=align_y,
                                      section_padding=section_padding, font_color="#5d4d40", padding=(15, 15, 15, 15))
    rendered_card_text = renderer_card_text.render()
    all_text.alpha_composite(rendered_card_text, ((w - 620) // 2, 372))
    section_coords = renderer_card_text.rendered_section_coords
    for ix in range(len(section_coords) - 1):
        top, bot = section_coords[ix][1], section_coords[ix + 1][0]
        center = int(top + (bot - top) / 2) + 372
        bars.alpha_composite(small_bar.crop((0, 0, text_bg.size[0], 100)),
                             ((w - text_bg.size[0]) // 2, center - small_bar.size[1] // 2))
        bars.alpha_composite(decor, (33, center - decor.size[1] // 2))
        bars.alpha_composite(decor, (673, center - decor.size[1] // 2))

    renderer_name = TextRenderer(name.upper(), "Tuff", (345, 100), asset_manager, font_size=50, bold=True, font_color="white", leading=0.9,
                                 stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
    rd_name = renderer_name.render()
    rd_name = rd_name.crop((0, 0, rd_name.size[0], int(renderer_name.rendered_section_coords[0][1])))
    name_x, name_y = 506, 135
    if subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (280, 80), asset_manager, font_size=30, font_color="white", leading=1,
                                        stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        rd_subname = rd_subname.crop((0, 0, rd_subname.size[0], int(renderer_subname.rendered_section_coords[0][1])))
        rd_names = Image.new("RGBA", (345, rd_name.size[1] + rd_subname.size[1] - 8))
        rd_names.alpha_composite(rd_name, ((rd_names.size[0] - 345) // 2, 0))
        rd_names.alpha_composite(rd_subname, ((rd_names.size[0] - rd_subname.size[0]) // 2, rd_name.size[1] - 8))
        all_text.alpha_composite(rd_names, (name_x - rd_names.size[0] // 2, name_y - rd_names.size[1] // 2))
    else:
        all_text.alpha_composite(rd_name, (name_x - 172, name_y - 50))

    renderer_version = TextRenderer(version, "Tuff", (100, 25), asset_manager, font_size=20, italic=True, font_color="white",
                                    stroke_width=0, leading=1, tracking=-10, align_y=TextRenderer.ALIGN_BOTTOM,
                                    align_x=TextRenderer.ALIGN_LEFT, padding=(5, 0, 5, 0))
    rendered_version = renderer_version.render()
    version_x, version_y = 19, h - rendered_version.size[0] - 70
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    ncu_card.alpha_composite(apply_drop_shadow(bars, color="#00000055", shadow_size=5), (-20, -20))
    crest = asset_manager.get_crest(faction)
    crest = crest.rotate(-12, expand=1, resample=Image.BICUBIC)
    crest = crest.resize((int(crest.size[0] * 172 / crest.size[1]), 172), resample=Image.LANCZOS)
    ncu_card.alpha_composite(apply_drop_shadow(crest, color="#00000055", shadow_size=5), (523, 182))
    ncu_card.alpha_composite(all_text)

    return ncu_card


def generate_ncu_back(asset_manager, ncu_id, name, subname, ncu_data, fluff):
    faction = ncu_data.get("faction")
    background = asset_manager.get_bg(faction)
    w, h = background.size
    ncu_card = Image.new("RGBA", (w, h))
    ncu_card.paste(background.rotate(get_faction_bg_rotation(faction)))

    portrait = asset_manager.get_ncu_img(ncu_id + "b")
    ncu_card.paste(portrait, (135, 332))

    bars = Image.new("RGBA", (w, h))
    bars_lower = Image.new("RGBA", (w, h))
    large_bar, small_bar, corner_bar = asset_manager.get_bars(faction)
    unit_type = asset_manager.get_unit_type("NCU", faction)
    decor = asset_manager.get_decor(faction)
    wb_w, wb_h = corner_bar.size
    lb_w, lb_h = large_bar.size
    bars_lower.alpha_composite(large_bar.crop((220, lb_h // 4, 780, 3 * lb_h // 4)), (140, 292))
    bars_lower.alpha_composite(large_bar.rotate(270, expand=1).crop((0, lb_w - 960, lb_h, lb_w - 20)), (56, 55))
    # TODO: Ughh...
    # bars_lower.alpha_composite(corner_bar.crop((0, 0, 130, 150)), (52, 52))
    # bars_lower.alpha_composite(ImageOps.flip(corner_bar).crop((0, wb_h - 150, 130, wb_h)), (52, 210))
    # bars_lower.alpha_composite(ImageOps.mirror(corner_bar).crop((wb_w - 130, 0, wb_w, 150)), (191, 52))
    # bars_lower.alpha_composite(corner_bar.crop((0, 0, 278, 330)).rotate(180), (418, 664))
    bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, 287))
    bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, 330))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (46, 55))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (131, 55))
    bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (687, 55))
    bars.alpha_composite(apply_drop_shadow(unit_type), (26, 31))
    bars.alpha_composite(small_bar.crop((0, 0, 650, 100)), (50, 984))
    bars.alpha_composite(apply_drop_shadow(small_bar.crop((0, 0, 650, 100))), (30, 26))
    bars.alpha_composite(decor, (33, 33))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (33, 273))
    bars.alpha_composite(decor, (118, 273))
    bars.alpha_composite(decor, (674, 273))
    bars.alpha_composite(decor, (674, 316))
    bars.alpha_composite(decor, (118, 971))
    bars.alpha_composite(decor, (674, 33))
    bars.alpha_composite(decor, (674, 971))

    layer_crests = Image.new("RGBA", (w, h))
    box_character = render_character_box(asset_manager, faction)
    layer_crests.alpha_composite(apply_drop_shadow(box_character), (234, 266))
    rendered_cost = render_cost(asset_manager, ncu_data.get("cost", 0), get_faction_highlight_color(faction), ncu_data.get("commander"))
    layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (38, 194))
    crest = asset_manager.get_crest(faction)
    crest = crest.crop(crest.getbbox())
    crest = crest.rotate(14, expand=1, resample=Image.BICUBIC)
    crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
    crest = crest.resize(crest_size)
    crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 390 - crest.size[1] // 2
    layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

    layer_text = Image.new("RGBA", (w, h))
    renderer_name = TextRenderer(name.upper(), "Tuff", (520, 60), asset_manager, font_size=54, bold=True, font_color="white", leading=1,
                                 stroke_width=0.1, align_y=TextRenderer.ALIGN_CENTER)
    rd_name = renderer_name.render()
    layer_text.alpha_composite(rd_name, (158, 92))
    if subname is not None:
        renderer_subname = TextRenderer(subname.upper(), "Tuff", (520, 40), asset_manager, font_size=30, font_color="white", leading=1,
                                        stroke_width=0.1, padding=(5, 5, 5, 5))
        rd_subname = renderer_subname.render()
        layer_text.alpha_composite(rd_subname, (158, 142))
    renderer_quote = TextRenderer(fluff["quote"], "Tuff", (480, 90), asset_manager, font_size=32, font_color="white", italic=True,
                                  stroke_width=0.1, padding=(5, 5, 5, 5))
    rd_quote = renderer_quote.render()
    layer_text.alpha_composite(rd_quote, (178, 182))

    # TODO: Restrictions/Loyalty

    ncu_card.alpha_composite(apply_drop_shadow(bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
    ncu_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))
    ncu_card.alpha_composite(layer_crests)
    ncu_card.alpha_composite(layer_text)
    return ncu_card


def main():
    from asset_manager import AssetManager
    data = {
        "faction": "greyjoy",
        "cost": 4
    }
    fluff = {
        "quote": "\"What is dead may never die, but rises again, harder and stronger.\""
    }
    back = generate_ncu_back(AssetManager(), "30802", "Aeron Greyjoy", "The Damphair", data, fluff)
    org = Image.open(r"").convert("RGBA")
    editor = ImageEditor(back, org)


if __name__ == "__main__":
    main()
