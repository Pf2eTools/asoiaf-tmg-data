from PIL.Image import Resampling
from generate_utils import *
from song_data import *


class ImageGeneratorUnits(ImageGenerator):
    def generate(self, context):
        data: SongDataUnit = context["data"]
        abilities = context["abilities"]

        unit_bg = self.asset_manager.get_unit_bg(data.faction)
        w, h = unit_bg.size
        unit_card = Image.new("RGBA", (w, h))
        unit_card.alpha_composite(unit_bg)

        if len(abilities) > 0:
            skills_bg = self.asset_manager.get_unit_skills_bg()
            unit_card.alpha_composite(skills_bg, (w - skills_bg.size[0], 0))

        unit_image = self.asset_manager.get_unit_image(data.id)
        unit_card.alpha_composite(unit_image, (497 - unit_image.size[0] // 2, min(0, 642 - unit_image.size[1])))

        bars = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar = self.asset_manager.get_bars(data.faction)
        decor = self.asset_manager.get_decor(data.faction)

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
        crest = self.asset_manager.get_crest_shadow(data.faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.rotate(-12, expand=1, resample=Resampling.BICUBIC)
        offset_crop = crest.crop((0, 0, crest.width, crests.height // 4))
        offset = (offset_crop.width - offset_crop.getbbox()[2]) // 2
        crest_w, crest_h = int(188 * crest.size[0] / crest.size[1]), 188
        crest = crest.resize((crest_w, crest_h), resample=Resampling.LANCZOS)
        crests.alpha_composite(apply_drop_shadow(crest), (704 - crest_w + offset, 456))
        unit_type = self.asset_manager.get_unit_type(data.icon, data.faction)
        crests.alpha_composite(unit_type, (228 - unit_type.size[0] // 2, h - unit_type.size[1]))

        layer_statistics = Image.new("RGBA", (w, h))
        icon_speed = self.asset_manager.get_stat_icon("speed")
        rd_speed = self.render_stat_value(data.speed)
        layer_statistics.alpha_composite(rd_speed, (bar_vl_x - 3 - rd_speed.size[0] // 2, 104 - rd_speed.size[1] // 2))
        layer_statistics.alpha_composite(icon_speed, (bar_vl_x - 140, 104 - icon_speed.size[1] // 2))
        icon_defense = self.asset_manager.get_stat_icon("defense")
        rd_defense = self.render_stat_value(f'{data.defense}+')
        layer_statistics.alpha_composite(rd_defense, (bar_vl_x - rd_defense.size[0] // 2, 638 - rd_defense.size[1] // 2))
        layer_statistics.alpha_composite(icon_defense, (bar_vl_x - 140, 638 - icon_defense.size[1] // 2))
        icon_morale = self.asset_manager.get_stat_icon("morale")
        rd_morale = self.render_stat_value(f'{data.morale}+')
        layer_statistics.alpha_composite(rd_morale, (bar_vl_x + 192 - rd_morale.size[0] // 2, 638 - rd_morale.size[1] // 2))
        layer_statistics.alpha_composite(icon_morale, (bar_vl_x + 52, 638 - icon_morale.size[1] // 2))

        for ix, attack_data in enumerate(data.attacks):
            # TODO: ???
            if ix > 1:
                continue
            rd_attack = self.render_attack(attack_data, self.faction_store.highlight_color(data.faction))
            layer_statistics.alpha_composite(rd_attack, (30, 198 + ix * 188))

        all_text = Image.new("RGBA", (w, h))
        names = [
            TextEntry(data.name.upper(), styles=TextStyle(bold=True))
        ]
        if data.title:
            names.append(TextEntry(data.title.upper(), styles=TextStyle(font_size=0.55, padding=Spacing(0, 40))))
        entries = TextEntry.from_array(names, styles=RootStyle(font_color="white", font_size=45, stroke_width=0.1, leading=1000,
                                                               paragraph_padding=300))
        rd_names = self.text_renderer.render(entries, bbox=(428, 139), margin=Spacing(20), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        all_text.alpha_composite(rd_names, (284, 668))

        entry_version = TextEntry.from_string(data.version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                        tracking=-10, stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        all_text.alpha_composite(rd_version.rotate(90, expand=1), (25, h - 125))

        layer_abilities = Image.new("RGBA", (w, h))

        skill_top = ImageOps.flip(self.asset_manager.get_skill_bottom(data.faction))
        skill_divider = self.asset_manager.get_skill_divider(data.faction)
        skill_bottom = self.asset_manager.get_skill_bottom(data.faction)
        section_padding = skill_divider.height
        ability_sections = get_ability_sections(abilities, self.faction_store.text_color(data.faction))
        entries_abilities = TextEntry.from_array(ability_sections, styles=RootStyle(font_size=36, font_color="#5d4d40",
                                                                                    section_padding=section_padding))
        rd_abilities = self.text_renderer.render(entries_abilities, bbox=(560, h - 100), align_x=TextRenderer.ALIGN_LEFT,
                                                 margin=Spacing(20, 10))
        layer_abilities.alpha_composite(rd_abilities, (830, 50))

        for top, bot in self.text_renderer.get_computed_between():
            center = int(top + (bot - top) / 2) + 30
            layer_abilities.alpha_composite(apply_drop_shadow(skill_divider), (740, center - skill_divider.size[1] // 2))

        computed = self.text_renderer.get_computed()
        layer_abilities.alpha_composite(apply_drop_shadow(skill_top), (783, int(computed[0][0]) + 30 - skill_top.size[1]))
        layer_abilities.alpha_composite(apply_drop_shadow(skill_bottom), (783, int(computed[-1][1]) + 30))
        for ability, coords in zip(abilities, computed):
            if ability.icons is None:
                continue
            highlight_color = self.faction_store.highlight_color(data.faction)
            rd_icons = self.render_skill_icons(ability.icons, highlight_color)
            x, y = 694, 50 + coords[0] + (coords[1] - coords[0] - rd_icons.size[1]) // 2
            layer_abilities.alpha_composite(rd_icons, (x, int(y)))

        unit_card.alpha_composite(apply_drop_shadow(bars, color="#00000033", shadow_size=7), (-20, -20))
        unit_card.alpha_composite(crests)
        unit_card.alpha_composite(apply_drop_shadow(layer_statistics), (-20, -20))
        unit_card.alpha_composite(all_text)
        unit_card.alpha_composite(layer_abilities)

        return unit_card

    def generate_back(self, context):
        data: SongDataUnit = context["data"]

        unit_bg = self.asset_manager.get_unit_bg(data.faction)
        w, h = unit_bg.size
        unit_card = Image.new("RGBA", (w, h))
        unit_card.alpha_composite(unit_bg)
        img = self.asset_manager.get_unit_back_image(data.id)
        unit_card.alpha_composite(img)
        skills_bg = self.asset_manager.get_unit_skills_bg()
        # TODO: Units with subname/quotes
        unit_card.alpha_composite(skills_bg, (893, 166))

        layer_bars = Image.new("RGBA", (w, h))
        layer_bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, corner_bar = self.asset_manager.get_bars(data.faction)
        sb_w, sb_h = small_bar.size
        lb_w, lb_h = large_bar.size
        # TODO: Corner bar
        layer_bars_lower.alpha_composite(large_bar.rotate(270, expand=1).crop((0, lb_w - h, lb_h, lb_w)), (846 - lb_h // 2, 0))
        layer_bars.alpha_composite(small_bar.rotate(90, expand=1), (846 - (lb_h + sb_h) // 2, 0))
        layer_bars.alpha_composite(small_bar.rotate(90, expand=1), (846 + (lb_h - sb_h) // 2, 0))
        layer_bars.alpha_composite(small_bar, (846 + (lb_h - sb_h) // 2, 164))

        layer_crests = Image.new("RGBA", (w, h))
        unit_type = self.asset_manager.get_unit_type(data.icon, data.faction)
        layer_crests.alpha_composite(unit_type, (846 - unit_type.size[0] // 2, h - unit_type.size[1]))
        rd_cost = self.render_cost(data.cost, self.faction_store.highlight_color(data.faction), data.commander)
        layer_crests.alpha_composite(rd_cost, (846 - rd_cost.size[0] // 2, 555))
        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.crop(crest.getbbox())
        crest_size = min(184, int(crest.size[0] * 213 / crest.size[1])), min(213, int(crest.size[1] * 184 / crest.size[0]))
        crest = crest.resize(crest_size)
        crest_x, crest_y = 826 - crest.size[0] // 2, 25
        layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_x, crest_y))

        layer_text = Image.new("RGBA", (w, h))

        names = [TextEntry(data.name.upper(), styles=TextStyle(bold=True, word_spacing=250))]
        if data.title:
            names.append(TextEntry(data.title.upper(), styles=TextStyle(font_size=0.55)))
        paras = [TextEntry(names)]
        if data.fluff and data.fluff.quote:
            paras.append(TextEntry(TextEntry(data.fluff.quote, styles=TextStyle(italic=True, font_size=0.6))))
        entries = TextEntry.from_array(paras, styles=RootStyle(font_color="white", font_size=46, stroke_width=0.2, leading=1000,
                                                               paragraph_padding=200))
        rd_names = self.text_renderer.render(entries, bbox=(460, 165), margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, (940, 0))

        lore = data.fluff and data.fluff.lore or ""
        entries_lore = TextEntry.from_string(lore, styles=RootStyle(font_size=38, italic=True, font_color="#5d4d40", stroke_width=0.1))
        rd_lore = self.text_renderer.render(entries_lore, bbox=(460, 620), margin=Spacing(20), align_x=TextRenderer.ALIGN_LEFT,
                                            align_y=TextRenderer.ALIGN_CENTER)
        layer_text.alpha_composite(rd_lore, (915, 190))

        # TODO: Multiple Restrictions?
        if data.back_text:
            box_text = self.asset_manager.get_text_box(data.faction)
            box_x, box_y = (846 - (lb_h + sb_h) // 2) // 2, 660
            unit_card.alpha_composite(apply_drop_shadow(box_text, shadow_size=10), (box_x - 20 - box_text.width // 2, box_y - 20))
            req_entries = get_requirement_data_for_renderer(data.back_text)
            h_requirements = h - box_y - 40
            rd_requirements = self.text_renderer.render(req_entries, bbox=(box_text.width - 60, h_requirements), margin=Spacing(20),
                                                        align_y=TextRenderer.CENTER_SECTION)
            layer_text.alpha_composite(rd_requirements, (box_x - rd_requirements.width // 2, box_y + 40))
            if data.back_text[0].name:
                box_name = self.render_small_box(data.faction, data.back_text[0].name.upper(), font_color="#5d4d40")
                box_name = apply_drop_shadow(box_name)
                layer_crests.alpha_composite(box_name, (box_x - box_name.width // 2, box_y - (box_name.height - sb_h) // 2))

        unit_card.alpha_composite(apply_drop_shadow(layer_bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
        unit_card.alpha_composite(apply_drop_shadow(layer_bars), (-20, -20))
        unit_card.alpha_composite(apply_drop_shadow(layer_crests), (-20, -20))
        unit_card.alpha_composite(layer_text)

        return unit_card
