from generate_utils import *
from image_editor import ImageEditor
from asset_manager import AssetManager


def generate_ncu(ncu_data):
    faction = re.sub(r"[^A-Za-z]", "", ncu_data.get("faction"))
    name = ncu_data.get("name")
    ncu_id = ncu_data.get("id")
    subname = ncu_data.get("subname")
    version = ncu_data.get("version")

    background = AssetManager.get_bg(faction)
    w, h = background.size
    ncu_card = Image.new("RGBA", (w, h))
    ncu_card.paste(background.rotate(get_faction_bg_rotation(faction)))
    text_bg = AssetManager.get_text_bg()
    text_bg = text_bg.crop((10, 20, text_bg.size[0] - 10, text_bg.size[1] - 5))
    ncu_card.paste(text_bg, (57, 356))
    portrait = AssetManager.get_ncu_img(ncu_id)
    ncu_card.paste(portrait, (52, 54))

    bars = Image.new("RGBA", (w, h))
    large_bar, small_bar, weird_bar = AssetManager.get_bars(faction)
    unit_type = AssetManager.get_unit_type("NCU", faction)
    decor = AssetManager.get_decor(faction)

    wb_w, wb_h = weird_bar.size
    bars.alpha_composite(weird_bar.crop((0,0,130, 150)), (54, 54))
    bars.alpha_composite(ImageOps.flip(weird_bar).crop((0, wb_h - 150, 130, wb_h)), (54, 208))
    bars.alpha_composite(ImageOps.mirror(weird_bar).crop((wb_w - 130, 0, wb_w, 150)), (190, 54))
    bars.alpha_composite(weird_bar.crop((0,0,130, 150)).rotate(180), (190, 208))
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
    card_text_y = 380
    font_size = 38
    line_padding = 14
    paragraph_padding = 8
    total_text_height = sum([calc_height_paragraphs(a.get("text"), 41, 18, 16) for a in ncu_data.get("abilities")])
    for ix, ability_data in enumerate(ncu_data.get("abilities")):
        font_color = get_faction_text_color(faction)
        ability_name_split = [f"**{s}**" for s in split_on_center_space(ability_data.get("name").upper(), maxlen=30)]
        rd_name = render_paragraph(ability_name_split, font_color=font_color, font_size=font_size, line_padding=line_padding)
        rd_ability_text = render_paragraphs(ability_data.get("text"), font_color="#5d4d40", font_size=font_size,
                                           line_padding=line_padding, paragraph_padding=paragraph_padding)

        if ix > 0:
            card_text_y += paragraph_padding + 10
            bars.alpha_composite(small_bar.crop((0, 0, text_bg.size[0], 100)), ((w - text_bg.size[0]) // 2, card_text_y))
            bars.alpha_composite(decor, (33, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            bars.alpha_composite(decor, (674, card_text_y + (small_bar.size[1] - decor.size[1]) // 2))
            card_text_y += small_bar.size[1] + paragraph_padding

        name_x, name_y = (w - rd_name.size[0]) // 2, card_text_y
        all_text.alpha_composite(rd_name, (name_x, name_y))
        card_text_y += rd_name.size[1]

        ability_text_x = (w - rd_ability_text.size[0]) // 2
        ability_text_y = card_text_y + paragraph_padding - 4
        all_text.alpha_composite(rd_ability_text, (ability_text_x, ability_text_y))
        card_text_y += rd_ability_text.size[1]

    rd_name = render_text_line(f"**{name.upper()}**", font_color="white", font_size=50)
    name_x, name_y = 506 - rd_name.size[0] // 2, 130 - rd_name.size[1] // 2
    all_text.alpha_composite(rd_name, (name_x, name_y))
    if subname is not None:
        rd_subname = render_text_line(f"{subname.upper()}", font_color="white", font_size=30, stroke_width=0.1)
        subname_x, subname_y = 506 - rd_subname.size[0] // 2, 36 + name_y + rd_name.size[1] // 2 - rd_subname.size[1] // 2
        all_text.alpha_composite(rd_subname, (subname_x, subname_y))

    rendered_version = render_text_line(f"*{version.strip('*')}*", font_color="white", font_size=20)
    version_x, version_y = 21, h - rendered_version.size[0] - 70
    all_text.alpha_composite(rendered_version.rotate(90, expand=1), (version_x, version_y))

    ncu_card.alpha_composite(apply_drop_shadow(bars, color="#00000055", shadow_size=5), (-20, -20))
    crest = AssetManager.get_crest_tactics(faction)
    crest = crest.rotate(-12, expand=1, resample=Image.BICUBIC)
    crest = crest.resize((int(crest.size[0] * 172 / crest.size[1]), 172), resample=Image.LANCZOS)
    ncu_card.alpha_composite(apply_drop_shadow(crest, color="#00000055", shadow_size=5), (523, 182))
    ncu_card.alpha_composite(all_text)

    return ncu_card


def main():
    jon = {
        "name": "Jon Snow",
        "subname": "Turncloak Crow",
        "id": "30308",
        "faction": "Free Folk",
        "cost": 4,
        "abilities": [
            {
                "name": "Northern Resilience",
                "text": [
                    [
                        "**Influence** *(When this unit Claims",
                        "a zone, attach this card to a Combat",
                        "Unit until the end of athe Round):*",
                    ],
                    [
                        "While Influencing a unit,",
                        "it gains +1 to Morale Test rolls.",
                    ],
                ]
            },
            {
                "name": "Southern Discipline",
                "text": [
                    [
                        "Once per game, at the start of",
                        "any Round, you may search your",
                        "Tactics deck or discard pile for one",
                        "**Coordination Tactics** or **Regroup and",
                        "Reform** Tactics cad and add it to your",
                        "hand. Shuffle your Tactics deck.",
                    ],
                ]
            }
        ],
        "version": "2021-S03"
    }
    tyene = {
        "name": "Tyene Sand",
        "subname": "Tochter einer Septa",
        "id": "30905",
        "faction": "Martell",
        "cost": 5,
        "abilities": [
            {
                "name": "Heilende Hände",
                "text": [
                    [
                        "Immer wenn Tyene eine Zone auf der",
                        "Taktiktafel beansprucht, darfst du 1",
                        "freundliche Einheit zum Ziel bestimmen.",
                        "Jene Einheit heilt 1 **Wunde.**"
                    ],
                    [
                        "Zu Beginn der zweiten Runde wähle",
                        "1 Taktikzone. Sobald eine feindliche",
                        "zivile Einheit jene Zone beansprucht, lege",
                        "die Giftarte **Der Würger** an jene",
                        "zivile Einheit an.",
                        "[SKILL:Venom]"
                    ],
                ]
            }
        ],
        "version": "2021-S03"
    }
    ncu_card = generate_ncu(tyene)
    ncu_card.save("tyene.png")
    ncu_original = Image.open("jon.jpg")
    ImageEditor(ncu_card, ncu_original)


if __name__ == "__main__":
    main()
