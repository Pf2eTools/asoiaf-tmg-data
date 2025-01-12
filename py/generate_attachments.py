from generate_utils import *
from image_editor import ImageEditor


class ImageGeneratorAttachments(ImageGenerator):
    def generate(self, data, abilities_data):
        attachment_id = data.get("id")
        name = data.get("name")
        subname = data.get("subname")
        statistics = data.get("statistics")
        faction = statistics.get("faction")
        version = statistics.get("version")
        abilities = statistics.get("abilities")
        is_commander = statistics.get("commander", False)

        background = self.asset_manager.get_bg(faction)
        w, h = background.size
        attachment_card = Image.new("RGBA", (w, h))
        attachment_card.alpha_composite(background.rotate(get_faction_bg_rotation(faction)))
        if is_commander:
            text_bg = self.asset_manager.get_unit_skills_bg()
            attachment_card.alpha_composite(text_bg, (141, 338))
        else:
            text_bg = self.asset_manager.get_unit_skills_bg()
            text_bg = text_bg.crop((0, 0, 555, text_bg.size[1]))
            attachment_card.alpha_composite(text_bg, (141, 338))
        portrait = self.asset_manager.get_attachment_image(attachment_id)
        # FIXME: HACK
        if attachment_id == "20521" or attachment_id == "20517":
            portrait = portrait.resize((portrait.width // 2, portrait.height // 2)).crop((0, 0, 197, 248))
        if is_commander:
            attachment_card.alpha_composite(portrait.crop((0, 0, 243, 252)))
        else:
            attachment_card.alpha_composite(portrait.crop((0, 0, 197, 248)), (50, 50))

        bars = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar = self.asset_manager.get_bars(faction)
        small_bar_ds = apply_drop_shadow(small_bar)
        decor = self.asset_manager.get_decor(faction)
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
            bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, large_bar.size[0] - 192, large_bar.size[1], large_bar.size[0])),
                                 (243, 50))
            bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (215, 222 - small_bar.size[0]))
            bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (298, 222 - small_bar.size[0]))
        else:
            bars.alpha_composite(weird_bar.rotate(90, expand=1).crop((0, 0, 370, weird_bar.size[0])), (327, 290 - weird_bar.size[0]))
            weird_bar_cropped = ImageOps.mirror(weird_bar.rotate(90, expand=1)).crop(
                (weird_bar.size[1] - portrait.size[0], 0, weird_bar.size[1], weird_bar.size[0]))
            bars.alpha_composite(weird_bar_cropped, (245 - weird_bar_cropped.size[0], 290 - weird_bar_cropped.size[1]))

            bars.alpha_composite(large_horizontal_crop.rotate(180), (55, 292))
            bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, 106, large_bar.size[1], large_bar.size[0])), (54, 338))
            bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (26, 30))
            bars.alpha_composite(small_bar_ds.rotate(90, expand=1), (111, 318))
            bars.alpha_composite(large_bar.rotate(90, expand=1).crop((0, large_bar.size[0] - 192, large_bar.size[1], large_bar.size[0])),
                                 (243, 50))
            bars.alpha_composite(short_vertical, (215, 50))
            bars.alpha_composite(short_vertical, (298, 50))
            bars.alpha_composite(small_horizontal_crop, (35, 265))
            bars.alpha_composite(small_horizontal_crop, (35, 307))
            bars.alpha_composite(decor, (33, 271))

        bars.alpha_composite(decor, (33, 314))
        bars.alpha_composite(decor, (118, 314))

        attach_type = statistics.get("type")
        if attach_type is not None and attach_type != "None":
            unit_type = self.asset_manager.get_attachment_type(attach_type, faction)
            if is_commander:
                bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, -23))
            else:
                unit_type = unit_type.crop((0, unit_type.size[1] - 142, unit_type.size[0], unit_type.size[1]))
                bars.alpha_composite(apply_drop_shadow(unit_type), (265 - unit_type.size[0] // 2, 30))

        crest = self.asset_manager.get_crest(faction)
        crest = crest.crop(crest.getbbox())
        crest_size = min(158, int(crest.size[0] * 182 / crest.size[1])), min(182, int(crest.size[1] * 158 / crest.size[0]))
        crest = crest.resize(crest_size)
        crest_resize_x, crest_resize_y = 265 - crest.size[0] // 2, 244 - crest.size[1] // 2
        bars.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

        layer_abilities = Image.new("RGBA", (w, h))
        skill_divider = self.asset_manager.get_skill_divider(faction)
        skill_bottom = self.asset_manager.get_skill_bottom(faction)
        if not is_commander:
            skill_divider = skill_divider.crop((0, 0, 600, skill_divider.size[1]))
            skill_bottom = skill_bottom.crop((0, 0, 560, skill_bottom.size[1]))
        filtered_abilities_data = get_filtered_ability_data(abilities, abilities_data)

        section_padding = skill_divider.size[1]
        w_abilities = w - 150 if is_commander else 540
        ability_sections = get_ability_sections(filtered_abilities_data, get_faction_text_color(faction))
        entries_abilities = TextEntry(ability_sections, styles=RootStyle(font_size=36, font_color="#5d4d40", leading=1080,
                                                                         section_padding=section_padding))
        rd_abilities = self.text_renderer.render(entries_abilities, bbox=(w_abilities, h - 396), align_x=TextRenderer.ALIGN_LEFT,
                                                 align_y=TextRenderer.ALIGN_TOP, margin=Spacing(16, 25, 16, 15))
        layer_abilities.alpha_composite(rd_abilities, (148, 346))

        for top, bot in self.text_renderer.get_computed_between():
            center = int(top + (bot - top) / 2) + 326
            bars.alpha_composite(apply_drop_shadow(skill_divider), (73, center - skill_divider.size[1] // 2))
        last_coords = None
        for data, coords in zip(filtered_abilities_data, self.text_renderer.get_computed()):
            last_coords = coords
            icons = data.get("icons")
            if icons is None:
                continue
            highlight_color = get_faction_highlight_color(faction)
            rd_icons = render_skill_icons(self.asset_manager, self.text_renderer, icons, highlight_color)
            x, y = 28, 346 + coords[0] + (coords[1] - coords[0] - rd_icons.size[1]) // 2
            layer_abilities.alpha_composite(rd_icons, (x, int(y)))
        bars.alpha_composite(apply_drop_shadow(skill_bottom, shadow_size=7), (117, min(int(last_coords[1]), h - 396) + 326))

        all_text = Image.new("RGBA", (w, h))

        if is_commander:
            name_x, name_y = 366, 40
            padding_x = 20
            bbox = (340, 180)
        else:
            bbox = (320, 180)
            name_x, name_y = 354, 80
            padding_x = 30

        names = [
            TextEntry(TextEntry(name.upper(), styles=TextStyle(leading=850, bold=True)))
        ]
        if subname is not None:
            names.append(TextEntry(TextEntry(subname.upper(), styles=TextStyle(font_size=0.6, leading=950, padding=Spacing(0, padding_x)))))
        # FIXME: HACK
        name_font_size = 50 if attachment_id != "20517" else 35
        name_entries = TextEntry.from_array(names, styles=RootStyle(font_color="white", font_size=name_font_size, stroke_width=0.1,
                                                                    paragraph_padding=80))
        rd_names = self.text_renderer.render(name_entries, bbox=bbox, margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        all_text.alpha_composite(rd_names, (name_x, name_y))

        entry_version = TextEntry.from_string(version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                        tracking=-10, stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        all_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 130))

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

    def generate_back(self, data):
        attachment_id = data.get("id")
        language = data.get("language")
        name = data.get("name")
        subname = data.get("subname")
        statistics = data.get("statistics")
        faction = statistics.get("faction")
        requirements = statistics.get("requirements")
        attachment_fluff = data.get("fluff", {})
        attachment_tactics = data.get("tactics")
        is_commander = statistics.get("commander")
        is_character = statistics.get("character")

        background = self.asset_manager.get_bg(faction)
        w, h = background.size
        attachment_card = Image.new("RGBA", (w, h))
        attachment_card.alpha_composite(background.rotate(get_faction_bg_rotation(faction)))

        portrait = self.asset_manager.get_attachment_back_image(attachment_id)
        if is_commander:
            attachment_card.alpha_composite(portrait, (148, 292))
        elif is_character:
            attachment_card.alpha_composite(portrait, (135, 345))
        else:
            attachment_card.alpha_composite(portrait, (135, 242))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, corner_bar = self.asset_manager.get_bars(faction)
        decor = self.asset_manager.get_decor(faction)
        lb_w, lb_h = large_bar.size
        sb_w, sb_h = small_bar.size
        if is_commander:
            bars_lower.alpha_composite(large_bar.crop((220, lb_h // 4, lb_w, 3 * lb_h // 4)), (140, 238))
            bars_lower.alpha_composite(large_bar.rotate(90, expand=1), (98 - lb_h // 2, 0))
            bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 233))
            bars.alpha_composite(small_bar.crop((0, 0, sb_w, sb_h)), (140, 280))
            bars.alpha_composite(small_bar.rotate(90, expand=1), (98 - (lb_h + sb_h) // 2, 0))
            bars.alpha_composite(small_bar.rotate(90, expand=1), (98 + (lb_h - sb_h) // 2, 0))
        elif is_character:
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

        if requirements is not None or is_commander:
            requirement_y = 985 - len(requirements or []) * 112     # 873
            # FIXME: Hack alert
            # jaqen, reaver captain
            if attachment_id in ["20221", "20805"]:
                requirement_y -= 70
            # scorpion mods
            elif attachment_id in ["20521", "20517"]:
                requirement_y -= 160

            if is_commander:
                requirement_y -= 127
                box_text_org = self.asset_manager.get_text_box(faction)
                box_text = Image.new("RGBA", (box_text_org.width, box_text_org.height * 2))
                box_text.alpha_composite(box_text_org)
                box_text.alpha_composite(ImageOps.flip(box_text_org), (0, box_text_org.height))
                bars_lower.alpha_composite(box_text, (449 - box_text.width // 2, requirement_y - 8))

                req_text_width = box_text.width - 50
                requirement_x = 449 - req_text_width // 2
                divider_w = box_text.width
                divider_x = 449 - box_text.width // 2 + sb_h // 2
                sect_tactics = [TextEntry(
                    [TextEntry(TextEntry(t, styles=TextStyle(italic=True, leading=800))) for t in attachment_tactics["cards"].values()])]
            else:
                text_bg = self.asset_manager.get_text_bg().crop((0, 0, portrait.width, 1000))
                attachment_card.alpha_composite(text_bg, (135, requirement_y))
                bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, requirement_y - sb_h // 2))
                bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, requirement_y - decor.height // 2))
                bars.alpha_composite(decor, (674, requirement_y - decor.height // 2))

                req_text_width = 540
                requirement_x = 148
                divider_w = 560
                divider_x = 98 + lb_h // 2
                sect_tactics = None

            if is_commander:
                box_commander = render_commander_box(self.asset_manager, self.text_renderer, faction, language)
                box_commander = apply_drop_shadow(box_commander)
                layer_crests.alpha_composite(box_commander, (449 - box_commander.width // 2, requirement_y - box_commander.height // 2))
                requirement_y += box_commander.height // 2 - 20
            elif requirements[0].get("name") is not None:
                box_name = render_small_box(self.asset_manager, self.text_renderer, faction, requirements[0].get("name").upper(),
                                            get_faction_text_color(faction))
                box_name = apply_drop_shadow(box_name)
                layer_crests.alpha_composite(box_name, (415 - box_name.width // 2, requirement_y - box_name.height // 2))
                requirement_y += box_name.height // 2 - 20

            req_entries = get_requirement_data_for_renderer(requirements, sect_tactics, section_padding=sb_h)
            h_requirements = h - requirement_y - sb_h // 2
            rd_requirements = self.text_renderer.render(req_entries, bbox=(req_text_width, h_requirements),
                                                        align_y=TextRenderer.CENTER_SECTION, margin=Spacing(20))
            layer_text.alpha_composite(rd_requirements, (requirement_x, requirement_y))
            for top, bot in self.text_renderer.get_computed_between():
                center = int(top + (bot - top) / 2) + requirement_y
                bars.alpha_composite(small_bar.crop((0, 0, divider_w, 100)), (divider_x, center - sb_h // 2))
                bars.alpha_composite(decor, (divider_x - decor.width // 2, center - decor.height // 2))
                bars.alpha_composite(decor, (674, center - decor.height // 2))

        if is_commander:
            box_character = render_character_box(self.asset_manager, self.text_renderer, faction, language)
            layer_crests.alpha_composite(apply_drop_shadow(box_character), (429 - box_character.width // 2, 212))
        elif is_character:
            box_character = render_character_box(self.asset_manager, self.text_renderer, faction, language)
            layer_crests.alpha_composite(apply_drop_shadow(box_character), (395 - box_character.width // 2, 266))
        rendered_cost = render_cost(self.asset_manager, self.text_renderer, statistics.get("cost", 0),
                                    get_faction_highlight_color(faction), is_commander)
        layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (78 - rendered_cost.width // 2, 764))
        crest = self.asset_manager.get_crest(faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.rotate(14, expand=1, resample=Image.BICUBIC)
        crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
        crest = crest.resize(crest_size)
        if is_commander:
            crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2
        elif is_character:
            crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 340 - crest.size[1] // 2
        else:
            crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2
        layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))
        # FIXME: HACK ALERT:
        if statistics.get("type") != "none":
            unit_type = self.asset_manager.get_unit_type(statistics.get("type"), faction)
            layer_crests.alpha_composite(apply_drop_shadow(unit_type), (78 - unit_type.width // 2, h - unit_type.size[1] - 20))

        name_fs = 44 if attachment_id in ["20521", "20517"] else 54
        if is_commander:
            bbox = (572, 180)
            names_x, names_y = 168, 28
        elif is_character:
            bbox = (520, 180)
            names_x, names_y = 158, 92
        else:
            # FIXME/TODO: Clipping into the crest is possible if the name breaks into two very long lines. Seems Unlikely
            bbox = (520, 178)
            names_x, names_y = 158, 62

        names = [TextEntry(name.upper(), styles=TextStyle(bold=True, word_spacing=250))]
        if subname is not None:
            names.append(TextEntry(subname.upper(), styles=TextStyle(font_size=0.55)))
        paras = [TextEntry(names)]
        quote = attachment_fluff.get("quote")
        if quote:
            paras.append(TextEntry(TextEntry(quote, styles=TextStyle(italic=True, font_size=0.6))))
        entries = TextEntry.from_array(paras, styles=RootStyle(font_color="white", font_size=name_fs, stroke_width=0.1, leading=1000,
                                                               paragraph_padding=300))
        rd_names = self.text_renderer.render(entries, bbox=bbox, margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, (names_x, names_y))

        attachment_card.alpha_composite(apply_drop_shadow(bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
        attachment_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))
        attachment_card.alpha_composite(layer_crests)
        attachment_card.alpha_composite(layer_text)

        return attachment_card


def main():
    from asset_manager import AssetManager
    import json
    with open("./data/en/abilities.json", "r", encoding="utf-8") as f:
        abilities = json.load(f)

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
    king = {
        "id": "20602",
        "name": "Stannis Baratheon",
        "subname": "The Rightful Heir",
        "statistics": {
            "version": "2021",
            "faction": "baratheon",
            "type": "infantry",
            "cost": "C",
            "abilities": [
                "Order: Adaptive Planning",
                "Order: Mark Target",
                "Loyalty: Stannis Baratheon"
            ],
            "commander": True,
            "character": True
        },
        "tactics": {
            "cards": {
                "40623": "Will of the One True King",
                "40624": "Harsh Conditions",
                "40625": "Tactical Approach"
            }
        },
        "fluff": {
            "quote": "\"Kings have no friends, only subjects and enemies.\""
        }
    }
    knight = {
        "id": "20603",
        "name": "Stag Knight Noble",
        "statistics": {
            "version": "2021-S03",
            "faction": "baratheon",
            "type": "infantry",
            "cost": 1,
            "abilities": [
                "Go Down Fighting",
                "Iron Resolve"
            ]
        }
    }
    onion = {
        "id": "20607",
        "name": "Davos Seaworth",
        "subname": "Hero of Blackwater",
        "statistics": {
            "version": "S05",
            "faction": "baratheon",
            "type": "infantry",
            "cost": "C",
            "abilities": [
                "Loyalty: Stannis Baratheon",
                "Outflank",
                "Pathfinder"
            ],
            "requirements": [
                {
                    "text": "*Davos ignores the usual Attachment Limits*"
                }
            ],
            "commander": True,
            "character": True
        },
        "tactics": {
            "cards": {
                "40629": "Flea Bottom Tricks",
                "40630": "\"Everything\"",
                "40631": "Fealty To The Crown",
                "40632": "Parlay"
            },
            "remove": [
                "Final Strike"
            ]
        },
        "fluff": {
            "quote": "\"He makes me wish I had more smugglers in my service. And fewer lords.\" -Stannis Baratheon"
        }
    }
    data = devan
    am = AssetManager()
    gen = ImageGeneratorAttachments(am, TextRenderer(am))
    # card = gen.generate(data, abilities)
    card = gen.generate_back(data)
    org = Image.open(f"./generated/en/baratheon/{data['id']}b.jpg").convert("RGBA")
    editor = ImageEditor(card, org)


if __name__ == "__main__":
    main()
