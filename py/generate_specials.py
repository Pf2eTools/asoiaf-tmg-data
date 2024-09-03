from generate_utils import *
from image_editor import ImageEditor


class ImageGeneratorSpecials(ImageGenerator):
    def generate(self, data, is_back=False):
        special_id = data.get("id")
        name = data.get("name")
        statistics = data.get("statistics")
        faction = statistics.get("faction")
        version = statistics.get("version")
        side = (statistics.get("back") if is_back else None) or statistics.get("front")
        style = side.get("style", "default")

        if style == "commander":
            return self.generate_commander(data, is_back)
        if style == "zone":
            return self.generate_zone(data, is_back)
        if style == "sunspear":
            return self.generate_sunspear(data, is_back)

        background = self.asset_manager.get_bg(faction)
        w, h = background.size
        special_card = Image.new("RGBA", (w, h))
        special_card.alpha_composite(background.rotate(get_faction_bg_rotation(faction)))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar_original = self.asset_manager.get_bars(faction)
        weird_bar = Image.new("RGBA", (weird_bar_original.height, weird_bar_original.height))
        weird_bar.alpha_composite(weird_bar_original)
        weird_bar.alpha_composite(weird_bar_original.rotate(270, expand=1), (weird_bar_original.width, 0))
        decor = self.asset_manager.get_decor(faction)
        small_bar_crop = small_bar.crop((0, 0, 650, 100))

        if style == "banners":
            large_bar = large_bar.crop((0, 0, large_bar.width, large_bar.height // 2))

        h_divider = int((971 - 33) * side.get("ratio")) + 54
        bbox_top = (54, 54, 695, h_divider - large_bar.height // 2)
        bbox_bot = (54, h_divider + large_bar.height // 2, 695, 992)
        inner_w = bbox_top[2] - bbox_top[0]
        inner_h_top = bbox_top[3] - bbox_top[1]
        inner_h_bot = bbox_bot[3] - bbox_bot[1]
        text_bg_org = self.asset_manager.get_text_bg()
        text_bg_org = text_bg_org.crop((0, 0, text_bg_org.width, text_bg_org.height - 5))
        text_bg = Image.new("RGBA", (text_bg_org.width, text_bg_org.height * 2))
        text_bg.alpha_composite(text_bg_org)
        text_bg.alpha_composite(ImageOps.flip(text_bg_org), (0, text_bg_org.height))
        special_card.paste(text_bg.crop((0, 0, bbox_bot[2] - bbox_bot[0], bbox_bot[3] - bbox_bot[1])), (bbox_bot[0], bbox_bot[1]))

        if style in ["default", "small-margin", "small-padding"]:
            bars_lower.alpha_composite(weird_bar.copy().crop((0, 0, inner_w // 2, inner_h_top // 2)), (bbox_top[0], bbox_top[1]))
            bars_lower.alpha_composite(weird_bar.rotate(90).crop((0, weird_bar.height - inner_h_top // 2, inner_w // 2, weird_bar.height)),
                                       (bbox_top[0], bbox_top[3] - inner_h_top // 2))
            bars_lower.alpha_composite(weird_bar.rotate(180).crop(
                (weird_bar.width - inner_w // 2, weird_bar.height - inner_h_top // 2, weird_bar.width, weird_bar.height)),
                (bbox_top[2] - inner_w // 2, bbox_top[3] - inner_h_top // 2))
            bars_lower.alpha_composite(weird_bar.rotate(270).crop((weird_bar.width - inner_w // 2, 0, weird_bar.width, inner_h_top // 2)),
                                       (bbox_top[2] - inner_w // 2, bbox_top[1]))

            bars_lower.alpha_composite(weird_bar.copy().crop((0, 0, inner_w // 2, inner_h_bot // 2)), (bbox_bot[0], bbox_bot[1]))
            bars_lower.alpha_composite(weird_bar.rotate(90).crop((0, weird_bar.height - inner_h_bot // 2, inner_w // 2, weird_bar.height)),
                                       (bbox_bot[0], bbox_bot[3] - inner_h_bot // 2))
            bars_lower.alpha_composite(weird_bar.rotate(180).crop(
                (weird_bar.width - inner_w // 2, weird_bar.height - inner_h_bot // 2, weird_bar.width, weird_bar.height)),
                (bbox_bot[2] - inner_w // 2, bbox_bot[3] - inner_h_bot // 2))
            bars_lower.alpha_composite(weird_bar.rotate(270).crop((weird_bar.width - inner_w // 2, 0, weird_bar.width, inner_h_bot // 2)),
                                       (bbox_bot[2] - inner_w // 2, bbox_bot[1]))

        bars_lower.alpha_composite(large_bar.rotate(180).crop((100, 0, 741, large_bar.height)), (54, h_divider - large_bar.height // 2))
        bars.alpha_composite(small_bar_crop, (50, 46))
        bars.alpha_composite(small_bar_crop, (50, 984))
        bars.alpha_composite(small_bar_crop, (50, h_divider - large_bar.height // 2 - small_bar.height // 2))
        bars.alpha_composite(small_bar_crop, (50, h_divider + large_bar.height // 2 - small_bar.height // 2))
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (46, 55))
        bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, 940)), (687, 55))
        bars.alpha_composite(decor, (33, 33))
        bars.alpha_composite(decor, (33, bbox_top[1] + inner_h_top // 2 - decor.height // 2))
        bars.alpha_composite(decor, (33, bbox_bot[1] + inner_h_bot // 2 - decor.height // 2))
        bars.alpha_composite(decor, (bbox_top[0] + inner_w // 2 - decor.width // 2, 33))
        bars.alpha_composite(decor, (33, 971))
        bars.alpha_composite(decor, (bbox_top[0] + inner_w // 2 - decor.width // 2, 971))
        bars.alpha_composite(decor, (674, 33))
        bars.alpha_composite(decor, (674, bbox_top[1] + inner_h_top // 2 - decor.height // 2))
        bars.alpha_composite(decor, (674, bbox_bot[1] + inner_h_bot // 2 - decor.height // 2))
        bars.alpha_composite(decor, (674, 971))
        bars.alpha_composite(decor, (33, h_divider - large_bar.height // 2 - decor.height // 2))
        bars.alpha_composite(decor, (674, h_divider - large_bar.height // 2 - decor.height // 2))
        bars.alpha_composite(decor, (33, h_divider + large_bar.height // 2 - decor.height // 2))
        bars.alpha_composite(decor, (674, h_divider + large_bar.height // 2 - decor.height // 2))

        layer_crests = Image.new("RGBA", (w, h))
        crest = self.asset_manager.get_crest(faction)
        crest = crest.crop(crest.getbbox())
        crest_size = min(158, int(crest.width * 182 / crest.height)), min(182, int(crest.height * 158 / crest.width))
        crest = crest.resize(crest_size)
        if side.get("crests") == 1:
            crest_x, crest_y = (w - crest.width) // 2, h_divider - crest.height // 2
            layer_crests.alpha_composite(crest, (crest_x, crest_y))
        elif side.get("crests") == 2:
            crest_l = ImageOps.mirror(crest).rotate(16, expand=1, resample=Image.BICUBIC)
            crest_r = crest.rotate(-16, expand=1, resample=Image.BICUBIC)
            crest_l_x, crest_l_y = 135 - crest_l.width // 2, h_divider - crest_l.height // 2
            crest_r_x, crest_r_y = w - 135 - crest_r.width // 2, h_divider - crest_r.height // 2
            if style == "banners":
                crest_l_y -= 90
                crest_r_y -= 90
            layer_crests.alpha_composite(crest_l, (crest_l_x, crest_l_y))
            layer_crests.alpha_composite(crest_r, (crest_r_x, crest_r_y))

        layer_text = Image.new("RGBA", (w, h))
        if side.get("top"):
            names = [TextEntry(TextEntry(e, styles=TextStyle(icon_scale=1.2))) for e in side.get("top")]
        else:
            names = [TextEntry(TextEntry(name.upper(), styles=TextStyle(leading=1000, bold=True)))]
        quote = side.get("quote")
        if quote is not None:
            names.append(TextEntry(TextEntry(quote, styles=TextStyle(italic=True, font_size=0.64))))
        name_entries = TextEntry.from_array(names, styles=RootStyle(font_color="white", font_size=50, stroke_width=0.1))
        if style == "banners":
            name_bbox = (bbox_top[2] - bbox_top[0] - 200, bbox_top[3] - bbox_top[1] - 20)
        else:
            name_bbox = (bbox_top[2] - bbox_top[0] - 20, bbox_top[3] - bbox_top[1] - 20)
        rd_names = self.text_renderer.render(name_entries, bbox=name_bbox, margin=Spacing(20), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, ((w - rd_names.width) // 2, 64))

        if side.get("text") is not None:
            paragraph_padding = 500 if style in ["banners", "small-padding"] else 700
            text_entries = TextEntry.from_array([TextEntry(TextEntry(e)) for e in side.get("text")],
                                                styles=RootStyle(font_color="#5d4d40", font_size=48, paragraph_padding=paragraph_padding))

            margin = 40 if style in ["banners", "small-margin"] else 80
            text_bbox = (bbox_bot[2] - bbox_bot[0] - margin, bbox_bot[3] - bbox_bot[1] - margin)
            align_x = TextRenderer.ALIGN_LEFT if style == "banners" else TextRenderer.ALIGN_CENTER
            linebreak = TextRenderer.LINEBREAK_GREEDY if style == "banners" else TextRenderer.LINEBREAK_OPTIMAL
            rd_text = self.text_renderer.render(text_entries, bbox=text_bbox, margin=Spacing(10), align_x=align_x,
                                                align_y=TextRenderer.ALIGN_CENTER, linebreak_algorithm=linebreak, max_font_reduction=20)
            layer_text.alpha_composite(rd_text, (bbox_bot[0] + margin // 2, bbox_bot[1] + margin // 2))
        elif side.get("image"):
            if is_back:
                image = self.asset_manager.get_special_back_image(special_id)
            else:
                image = self.asset_manager.get_special_image(special_id)
            special_card.alpha_composite(image.crop((0, 0, inner_w, inner_h_bot)), (bbox_bot[0], bbox_bot[1]))

        entry_version = TextEntry.from_string(version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                        tracking=-10, stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        layer_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        special_card.alpha_composite(apply_drop_shadow(bars_lower), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(bars, color="#00000044"), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(layer_crests), (-20, -20))
        special_card.alpha_composite(layer_text)

        return special_card

    def generate_back(self, data):
        return self.generate(data, is_back=True)

    def generate_zone(self, data, is_back):
        special_id = data.get("id")
        name = data.get("name")
        statistics = data.get("statistics")
        version = statistics.get("version")
        side = (statistics.get("back") if is_back else None) or statistics.get("front")

        if is_back:
            background = self.asset_manager.get_special_back_image(special_id)
        else:
            background = self.asset_manager.get_special_image(special_id)
        special_card = Image.new("RGBA", background.size)
        w, h = special_card.size
        special_card.alpha_composite(background)

        layer_text = Image.new("RGBA", (w, h))
        if not is_back:
            name_entries = TextEntry.from_string(name.upper(), styles=RootStyle(font_color="#5b4a43", font_size=64, stroke_width=0.1,
                                                                                bold=True, leading=900))
            rd_names = self.text_renderer.render(name_entries, bbox=(380, 140), margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                                 linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
            layer_text.alpha_composite(rd_names, ((w - rd_names.width) // 2, 680))

            info_entries = [TextEntry(TextEntry(e, styles=TextStyle(font_color="#96232a"))) for e in side.get("note", [])]
            effect_entries = [TextEntry(TextEntry(e, styles=TextStyle(font_color="#5b4a43"))) for e in side.get("effect", [])]
            text_entries = TextEntry.from_array([*info_entries, *effect_entries], styles=RootStyle(font_size=48))
            rd_text = self.text_renderer.render(text_entries, bbox=(624, 420), margin=Spacing(20), align_x=TextRenderer.ALIGN_CENTER,
                                                align_y=TextRenderer.ALIGN_CENTER, linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL,
                                                max_font_reduction=20)
            layer_text.alpha_composite(rd_text, ((w - rd_text.width) // 2, 890))
        else:
            text_entries = TextEntry.from_array([TextEntry(e) for e in side.get("text")], styles=RootStyle(font_color="white", font_size=32))
            rd_text = self.text_renderer.render(text_entries, bbox=(624, 320), margin=Spacing(20), align_x=TextRenderer.ALIGN_CENTER,
                                                align_y=TextRenderer.ALIGN_CENTER, linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)
            layer_text.alpha_composite(rd_text, ((w - rd_text.width) // 2, 770))

        special_card.alpha_composite(layer_text)

        return special_card

    def generate_sunspear(self, data, is_back):
        special_id = data.get("id")
        name = data.get("name")
        statistics = data.get("statistics")
        version = statistics.get("version")
        side = (statistics.get("back") if is_back else None) or statistics.get("front")

        if is_back:
            background = self.asset_manager.get_special_back_image(special_id)
        else:
            background = self.asset_manager.get_special_image(special_id)
        special_card = Image.new("RGBA", background.size)
        w, h = special_card.size
        special_card.alpha_composite(background)

        layer_text = Image.new("RGBA", (w, h))
        if is_back:
            bbox_names = (312, 152)
        else:
            bbox_names = (624, 74)
        name_entries = TextEntry.from_string(name.upper(), styles=RootStyle(font_color="white", font_size=50, stroke_width=0.1, bold=True,
                                                                            leading=900))
        rd_names = self.text_renderer.render(name_entries, bbox=bbox_names, margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, ((w - rd_names.width) // 2, 64))

        if side.get("text") is not None:
            text_entries = TextEntry.from_array([TextEntry(TextEntry(e)) for e in side.get("text")],
                                                styles=RootStyle(font_color="#5d4d40", font_size=48))

            rd_text = self.text_renderer.render(text_entries, bbox=(564, 420), margin=Spacing(20), align_x=TextRenderer.ALIGN_CENTER,
                                                align_y=TextRenderer.ALIGN_CENTER, linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)
            layer_text.alpha_composite(rd_text, (94, 540))

        if not is_back:
            entry_version = TextEntry.from_string(version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                            tracking=-10, stroke_width=0))
            rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                                   align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
            layer_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        special_card.alpha_composite(layer_text)

        return special_card

    def generate_commander(self, data, is_back):
        special_id = data.get("id")
        name = data.get("name")
        statistics = data.get("statistics")
        faction = statistics.get("faction")
        side = (statistics.get("back") if is_back else None) or statistics.get("front")
        cmdr_data = side.get("data")
        subname = cmdr_data.get("subname")
        quote = cmdr_data.get("quote")
        tactics = cmdr_data.get("tactics")

        background = self.asset_manager.get_bg(faction)
        w, h = background.size
        special_card = Image.new("RGBA", (w, h))
        special_card.alpha_composite(background.rotate(get_faction_bg_rotation(faction)))

        if is_back:
            portrait = self.asset_manager.get_special_back_image(special_id)
        else:
            portrait = self.asset_manager.get_special_image(special_id)
        special_card.alpha_composite(portrait, (148, 292))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, corner_bar = self.asset_manager.get_bars(faction)
        decor = self.asset_manager.get_decor(faction)
        lb_w, lb_h = large_bar.size
        sb_w, sb_h = small_bar.size
        bars_lower.alpha_composite(large_bar.crop((220, lb_h // 4, lb_w, 3 * lb_h // 4)), (140, 238))
        bars_lower.alpha_composite(large_bar.rotate(90, expand=1), (98 - lb_h // 2, 0))
        bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 233))
        bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 280))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 - (lb_h + sb_h) // 2, 0))
        bars.alpha_composite(small_bar.rotate(90, expand=1), (98 + (lb_h - sb_h) // 2, 0))

        layer_text = Image.new("RGBA", (w, h))
        layer_crests = Image.new("RGBA", (w, h))

        box_character = render_character_box(self.asset_manager, self.text_renderer, faction)
        layer_crests.alpha_composite(apply_drop_shadow(box_character), (429 - box_character.width // 2, 212))

        rendered_cost = render_cost(self.asset_manager, self.text_renderer, cmdr_data.get("cost", 0),
                                    get_faction_highlight_color(faction), True)
        layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (78 - rendered_cost.width // 2, 764))
        crest = self.asset_manager.get_crest(faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.rotate(14, expand=1, resample=Image.BICUBIC)
        crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
        crest = crest.resize(crest_size)
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2

        layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

        unit_type = self.asset_manager.get_unit_type(cmdr_data.get("type"), faction)
        layer_crests.alpha_composite(apply_drop_shadow(unit_type), (78 - unit_type.width // 2, h - unit_type.size[1] - 20))

        names = [TextEntry(cmdr_data.get("name", name).upper(), styles=TextStyle(bold=True, word_spacing=250))]
        if subname is not None:
            names.append(TextEntry(subname.upper(), styles=TextStyle(font_size=0.55)))
        paras = [TextEntry(names)]
        if quote:
            paras.append(TextEntry(TextEntry(quote, styles=TextStyle(italic=True, font_size=0.6))))
        entries = TextEntry.from_array(paras, styles=RootStyle(font_color="white", font_size=54, stroke_width=0.1, leading=1000,
                                                               paragraph_padding=300))
        rd_names = self.text_renderer.render(entries, bbox=(572, 180), margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, (168, 28))

        box_text = self.asset_manager.get_text_box(faction)
        box_commander = render_commander_box(self.asset_manager, self.text_renderer, faction)
        layer_crests.alpha_composite(apply_drop_shadow(box_text), (429 - box_text.width // 2, 830))
        layer_crests.alpha_composite(apply_drop_shadow(box_commander),
                                     (429 - box_commander.width // 2, 838 - box_commander.height // 2))

        entries_tactics = TextEntry.from_array([TextEntry(t) for t in tactics],
                                               styles=RootStyle(font_size=36, font_color="#5d4d40", italic=True, leading=1000,
                                                                paragraph_padding=300))
        rd_tactics = self.text_renderer.render(entries_tactics, bbox=(box_text.width - 50, h - 895), align_y=TextRenderer.ALIGN_CENTER,
                                               align_x=TextRenderer.ALIGN_CENTER, margin=Spacing(15, 25))
        layer_text.alpha_composite(rd_tactics, (449 - rd_tactics.width // 2, 890))

        special_card.alpha_composite(apply_drop_shadow(bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))
        special_card.alpha_composite(layer_crests)
        special_card.alpha_composite(layer_text)

        return special_card


def main():
    from asset_manager import AssetManager
    pillage = {
        "name": "Raiders of the Iron Islands",
        "id": "50801",
        "statistics": {
            "faction": "greyjoy",
            "version": "2021-S03",
            "front": {
                "top": None,
                "quote": None,
                "ratio": 0.3,
                "crests": 2,
                "text": [
                    "[SKILL:Pillage]\nEach time a House Greyjoy unit destroys an enemy rank with a Melee Attack, it gains 1 Pillage token. A unit may have up to 2 Pillage tokens at any time.",
                    "That unit gains the following based on the number of Pillage tokens *(effects are cumulative)*:\n• **1+:** +1 to Morale Test rolls.\n• **2:** +1 Attack Die."
                ]
            }
        },
    }
    venom = {
        "name": "Manticore Venom",
        "id": "50902",
        "statistics": {
            "faction": "martell",
            "version": "2021",
            "front": {
                "ratio": 0.3,
                "crests": 1,
                "text": [
                    "[SKILL:Venom]",
                    "This unit cannot restore Wounds.",
                    "If this unit would become **Vulnerable** but is already **Vulnerable**, it instead suffers 1 Wound.",
                    "Each time this unit Activates, it becomes **Vulnerable**."
                ]
            },
            "back": {
                "top": [
                    "[SKILL:Venom]",
                    "**POISON**"
                ],
                "quote": "\"No true man killed with poison. Poison was for cravens, women, and Dornishmen.\"\n-Victarion Greyjoy",
                "ratio": 0.5,
                "crests": 1,
                "text": [
                    "**At the Start of the Game, place this card close to your Tactics Deck.**",
                    "An Ability or effect will state when this card will be played."
                ]
            }
        },
    }
    banners = {
        "name": "Baratheon Banners",
        "id": "50101",
        "statistics": {
            "faction": "lannister",
            "version": "2021",
            "front": {
                "ratio": 0.2,
                "crests": 2,
                "style": "banners",
                "text": [
                    "The Kingsguard come with 4 Baratheon Banners. At the start of its Activation, it may remove Baratheon Banners to gain the following. Each may be selected only once per Activation:",
                    "• This Turn, this unit's Attacks gain **Critical Blow** and **Sundering**.",
                    "• This Turn, this unit's Attacks gain **Vicious** and, if the Defender fails their Panic Test, they suffer +1 Wound.",
                    "• This Turn, when this unit is performing an Attack, before rolling Attack Dice, the Defender becomes **Panicked** and **Weakened**.",
                    "• This unit restores 2 Wounds and may re-roll Charge and Retreat Distance Dice this Turn."
                ]
            },
            "back": {
                "ratio": 0.25,
                "crests": 2,
                "image": True
            }
        }
    }
    doran = {
        "id": "50901",
        "name": "Lord of Sunspear",
        "statistics": {
            "faction": "martell",
            "version": "2021",
            "front": {
                "style": "sunspear",
                "text": [
                    "You may choose **Doran Martell, Lord of Sunspear** as your Commander *(you must still pay his points cost)*. If you do, your army **must** include **Areo Hotah, Captain of the Guard**. He counts as your Commander on the Battlefield for all gameplay purposes."
                ]
            },
            "back": {
                "style": "sunspear"
            }
        }
    }
    garden = {
        "id": "50900",
        "name": "Water Gardens",
        "statistics": {
            "faction": "martell",
            "version": "2021",
            "front": {
                "style": "zone",
                "note": [
                    "**There can only be 1 Water Gardens in the Game. While you Control this zone, opponents do not count as Controlling Tactics Zones for Abilities or Tactics cards.**"
                ],
                "effect": [
                    "On your opponent's next Turn, they must Activate a Combat Unit if possible."
                ]
            },
            "back": {
                "style": "zone",
                "text": [
                    "If your army includes Doran Martell, Prince of Dorne, before the game begins, place the Water Gardens Tactics zone card next to the Tactics Board. It acts as an additional Tactics Zone for all purposes."
                ]
            }
        }
    }
    data = venom
    am = AssetManager()
    gen = ImageGeneratorSpecials(am, TextRenderer(am))
    card = gen.generate(data)
    # card = gen.generate_back(data)
    # card = card.resize((card.width // 2, card.height // 2))
    faction = data.get("statistics").get("faction")
    org = Image.open(f"./generated/en/{faction}/cards/{data['id']}.jpg").convert("RGBA")
    editor = ImageEditor(card, org)


if __name__ == "__main__":
    main()
