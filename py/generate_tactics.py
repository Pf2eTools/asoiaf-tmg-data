from image_editor import ImageEditor
from generate_utils import *


def generate_tactics(asset_manager, name,  tactics_data):
    faction = tactics_data.get("faction")
    card_text = tactics_data.get("text")
    version = tactics_data.get("version")
    commander_id = tactics_data.get("commander_id")
    commander_name = tactics_data.get("commander_name")
    commander_subname = tactics_data.get("commander_subname")

    tactics_bg = asset_manager.get_bg(faction)
    w, h = tactics_bg.size
    tactics_bg2 = asset_manager.get_text_bg()
    tactics_card = Image.new("RGBA", (w, h))
    tactics_card.alpha_composite(tactics_bg.rotate(get_faction_bg_rotation(faction)))
    tactics_card.alpha_composite(tactics_bg2, (47, 336))

    if commander_id is not None:
        cmdr_image = asset_manager.get_tactics_commmander_img(commander_id)
        tactics_card.alpha_composite(cmdr_image, (-1, -2))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = asset_manager.get_bars(faction)

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
    bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)), ((w - tactics_bg2.size[0]) // 2, 985))
    bars.alpha_composite(small_bar, (0, 246))
    bars.alpha_composite(small_bar, (0, 328))

    decor = asset_manager.get_decor(faction)
    bars.alpha_composite(decor, (33, 316))
    bars.alpha_composite(decor, (673, 316))
    bars.alpha_composite(decor, (33, 971))
    bars.alpha_composite(decor, (673, 971))
    if commander_id is not None:
        bars.alpha_composite(decor, (33, 232))
        bars.alpha_composite(decor, (673, 232))

    all_text = Image.new("RGBA", (w, h))

    name_max_w = 440 if commander_name is None else 392
    renderer_name = TextRenderer(name.upper(), "Tuff", (name_max_w, 200), asset_manager, font_size=50, bold=True, font_color="white",
                                 leading=0.94, align_y=TextRenderer.ALIGN_CENTER)
    rendered_name = renderer_name.render()
    if commander_name is not None:
        name_x, name_y = (tactics_bg.size[0] - rendered_name.size[0]) // 2 + 170, 136 - rendered_name.size[1] // 2
        all_text.alpha_composite(rendered_name, (name_x, name_y))
    else:
        name_x, name_y = (w - rendered_name.size[0]) // 2 + 138, 140 - rendered_name.size[1] // 2
        all_text.alpha_composite(rendered_name, (name_x, name_y))

    if commander_name is not None:
        renderer_cmdr_name = TextRenderer("", "Tuff", (622, 65), asset_manager, font_size=32, font_color="white",
                                          leading=0.94, align_y=TextRenderer.ALIGN_CENTER)
        rendered_cmdr_name = renderer_cmdr_name.render_cmdr_name(commander_name, commander_subname)
        cmdr_x, cmdr_y = (tactics_bg.size[0] - rendered_cmdr_name.size[0]) // 2, 294 - rendered_cmdr_name.size[1] // 2
        all_text.alpha_composite(rendered_cmdr_name, (cmdr_x, cmdr_y))

    card_text_to_render = []
    for trigger_effect in card_text:
        data = {
            "type": "section",
            "content": [
            ]
        }
        if trigger_effect.get("trigger") is not None:
            data["content"].append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "style": {"color": get_faction_text_color(faction)},
                        "content": f"**{trigger_effect.get('trigger')}**"
                    }
                ]
            })
        for paragraph in trigger_effect.get("effect", []):
            data["content"].append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "content": paragraph
                    },
                ]
            })
        if trigger_effect.get("remove") is not None:
            data["content"].append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "style": {"color": "#5d4d40"},
                        "content": f"**{trigger_effect.get('remove')}**"
                    }
                ]
            })
        card_text_to_render.append(data)
    section_padding = small_bar.size[1]
    align_y = TextRenderer.CENTER_SECTION if len(card_text_to_render) > 1 else TextRenderer.ALIGN_TOP
    renderer_card_text = TextRenderer(card_text_to_render, "Tuff", (620, 635), asset_manager, font_size=36, align_y=align_y,
                                      section_padding=section_padding, font_color="#5d4d40", padding=(30, 15, 30, 15),
                                      scale_padding_x=15 / 50, linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)
    rendered_card_text = renderer_card_text.render()
    all_text.alpha_composite(rendered_card_text, ((w - 620) // 2, 347))

    section_coords = renderer_card_text.rendered_section_coords
    for ix in range(len(section_coords) - 1):
        top, bot = section_coords[ix][1], section_coords[ix + 1][0]
        center = int(top + (bot - top) / 2) + 347
        bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                             ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, center - small_bar.size[1] // 2))
        bars.alpha_composite(decor, (33, center - decor.size[1] // 2))
        bars.alpha_composite(decor, (673, center - decor.size[1] // 2))

    renderer_version = TextRenderer(version, "Tuff", (100, 25), asset_manager, font_size=20, italic=True, font_color="white",
                                    stroke_width=0, leading=1, tracking=-10, align_y=TextRenderer.ALIGN_BOTTOM,
                                    align_x=TextRenderer.ALIGN_LEFT, padding=(5, 0, 5, 0))
    rendered_version = renderer_version.render()
    version_x, version_y = 21, h - rendered_version.size[0] - 70
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    tactics_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))

    crest = asset_manager.get_crest(faction)
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
    pass


if __name__ == "__main__":
    main()
