from PIL.Image import Resampling
from generate_utils import *
from song_data import *


class ImageGeneratorNCUs(ImageGenerator):
    def generate(self, context):
        data: SongDataNCU = context["data"]

        background = self.asset_manager.get_bg(data.faction)
        w, h = background.size
        ncu_card = Image.new("RGBA", (w, h))
        ncu_card.alpha_composite(background.rotate(self.faction_store.bg_rotation(data.faction)))
        text_bg = self.asset_manager.get_text_bg()
        text_bg = text_bg.crop((10, 20, text_bg.size[0] - 10, text_bg.size[1] - 5))
        ncu_card.alpha_composite(text_bg, (57, 356))
        portrait = self.asset_manager.get_ncu_img(data.id)
        ncu_card.alpha_composite(portrait, (52, 54))

        bars = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar = self.asset_manager.get_bars(data.faction)
        unit_type = self.asset_manager.get_unit_type(data.icon or "ncu", data.faction)
        decor = self.asset_manager.get_decor(data.faction)

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

        # region cardtext
        sections = []
        for ability in data.abilities:
            section = TextEntry([
                TextEntry(
                    TextEntry(f"**{ability.name.upper()}**", styles=TextStyle(font_color=self.faction_store.text_color(data.faction)))),
                *[TextEntry(TextEntry(e)) for e in ability.effect]
            ])
            sections.append(section)

        section_padding = small_bar.size[1]
        align_y = TextRenderer.CENTER_SECTION if len(sections) > 1 else TextRenderer.ALIGN_TOP
        to_render = TextEntry.from_array(sections, styles=RootStyle(
            font_color="#5d4d40", section_padding=section_padding, font_size=36))
        rendered_card_text = self.text_renderer.render(to_render, bbox=(620, 615), margin=Spacing(20, 15), align_y=align_y,
                                                       linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)
        all_text.alpha_composite(rendered_card_text, ((w - 620) // 2, 367))

        for top, bot in self.text_renderer.get_computed_between():
            center = int(top + (bot - top) / 2) + 367
            bars.alpha_composite(small_bar.crop((0, 0, text_bg.width, 100)), ((w - text_bg.width) // 2, center - small_bar.height // 2))
            bars.alpha_composite(decor, (33, center - decor.height // 2))
            bars.alpha_composite(decor, (673, center - decor.height // 2))
        # endregion cardtext

        # region name
        names = [
            TextEntry(TextEntry(data.name.upper(), styles=TextStyle(leading=850, bold=True)))
        ]
        if data.title is not None:
            names.append(TextEntry(TextEntry(data.title.upper(), styles=TextStyle(font_size=0.6, leading=950, padding=Spacing(0, 40)))))
        name_entries = TextEntry.from_array(names, styles=RootStyle(font_color=self.faction_store.name_color(data.faction), font_size=50,
                                                                    stroke_width=0.1, paragraph_padding=80))
        rd_names = self.text_renderer.render(name_entries, bbox=(362, 160), margin=Spacing(20), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        all_text.alpha_composite(rd_names, (326, 62))
        # endregion name

        entry_version = TextEntry.from_string(data.version, styles=RootStyle(font_size=20, italic=True, leading=1000, tracking=-10,
                                                                             font_color=self.faction_store.name_color(data.faction),
                                                                             stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        all_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        ncu_card.alpha_composite(apply_drop_shadow(bars, color="#00000055", shadow_size=5), (-20, -20))
        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.rotate(-12, expand=1, resample=Resampling.BICUBIC)
        crest = crest.crop(crest.getbbox())
        crest = crest.resize((int(crest.size[0] * 162 / crest.size[1]), 162), resample=Resampling.LANCZOS)
        ncu_card.alpha_composite(apply_drop_shadow(crest, color="#00000055", shadow_size=5), (674 - crest.width, 192))
        ncu_card.alpha_composite(all_text)

        return ncu_card

    def generate_back(self, context):
        data: SongDataNCU = context["data"]
        language = context["meta"].language
        tactics = context["tactics"]

        background = self.asset_manager.get_bg(data.faction)
        w, h = background.size
        ncu_card = Image.new("RGBA", (w, h))
        ncu_card.alpha_composite(background.rotate(self.faction_store.bg_rotation(data.faction)))

        portrait = self.asset_manager.get_ncu_back_img(data.id)
        ncu_card.alpha_composite(portrait, (135, 332))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        bars_upper = Image.new("RGBA", (w, h))
        large_bar, small_bar, corner_bar = self.asset_manager.get_bars(data.faction)
        unit_type = self.asset_manager.get_unit_type(data.icon or "ncu", data.faction)
        decor = self.asset_manager.get_decor(data.faction)
        wb_w, wb_h = corner_bar.size
        lb_w, lb_h = large_bar.size
        sb_w, sb_h = small_bar.size
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
        # bars.alpha_composite(apply_drop_shadow(small_bar.crop((0, 0, 650, 100))), (30, 26))
        bars_upper.alpha_composite(small_bar.crop((0, 0, 650, 100)), (50, 46))
        bars_upper.alpha_composite(decor, (33, 33))
        bars.alpha_composite(decor, (33, 971))
        bars.alpha_composite(decor, (33, 273))
        bars.alpha_composite(decor, (118, 273))
        bars.alpha_composite(decor, (674, 273))
        bars.alpha_composite(decor, (674, 316))
        bars.alpha_composite(decor, (118, 971))
        bars_upper.alpha_composite(decor, (674, 33))
        bars.alpha_composite(decor, (674, 971))

        layer_crests = Image.new("RGBA", (w, h))
        layer_text = Image.new("RGBA", (w, h))

        # TODO: not implemented: more than 1 requirement (as of now there are no ncus with more than 1)
        back_text_y = 812
        if data.back_text or tactics:
            text_bg = self.asset_manager.get_text_bg().crop((0, 0, portrait.width, 180))
            ncu_card.alpha_composite(text_bg, (135, back_text_y))
            bars.alpha_composite(small_bar.crop((0, 0, 560, small_bar.size[1])), (140, back_text_y - sb_h // 2))
            bars.alpha_composite(decor, (98 + (lb_h - decor.width) // 2, back_text_y - decor.height // 2))
            bars.alpha_composite(decor, (674, back_text_y - decor.height // 2))

        if data.back_text:
            if data.back_text[0].name:
                box_name = self.render_small_box(data.faction, data.back_text[0].name.upper(), self.faction_store.text_color(data.faction))
                box_name = apply_drop_shadow(box_name)
                layer_crests.alpha_composite(box_name, (415 - box_name.width // 2, back_text_y - box_name.height // 2))
                bbox = (520, 144)
                back_text_y += 20
            else:
                bbox = (520, 164)
            entries = get_requirement_data_for_renderer(data.back_text)
            rd_requirements = self.text_renderer.render(entries, bbox=bbox, align_y=TextRenderer.CENTER_SECTION, margin=Spacing(20))
            layer_text.alpha_composite(rd_requirements, (155, back_text_y + sb_h // 2))
        elif tactics:
            tactics_to_render = TextEntry.from_array([TextEntry(TextEntry(t.name)) for t in tactics],
                                                     styles=RootStyle(font_size=36, font_color="#5d4d40", italic=True, leading=800,
                                                                      paragraph_padding=300))
            rd_tactics = self.text_renderer.render(tactics_to_render, bbox=(portrait.width - 15, 150), align_y=TextRenderer.ALIGN_TOP,
                                                   align_x=TextRenderer.ALIGN_CENTER, margin=Spacing(20, 10, 10))
            layer_text.alpha_composite(rd_tactics, (146, 15 + back_text_y + sb_h // 2))

            box_cmdr = self.render_commander_box(data.faction, language)
            box_cmdr = apply_drop_shadow(box_cmdr)
            layer_crests.alpha_composite(box_cmdr, (415 - box_cmdr.width // 2, back_text_y - box_cmdr.height // 2))

        box_character = self.render_character_box(data.faction, language)
        layer_crests.alpha_composite(apply_drop_shadow(box_character), (234, 266))
        rendered_cost = self.render_cost(data.cost, self.faction_store.highlight_color(data.faction), data.commander)
        layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (38, 194))
        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.rotate(14, expand=1, resample=Resampling.BICUBIC)
        crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
        crest = crest.resize(crest_size)
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 390 - crest.size[1] // 2
        layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

        names = [
            TextEntry(data.name.upper(), styles=TextStyle(bold=True))
        ]
        if data.title is not None:
            names.append(TextEntry(data.title.upper(), styles=TextStyle(font_size=0.55, padding=Spacing(0, 40))))
        paras = [TextEntry(names)]
        if data.fluff and data.fluff.quote:
            paras.append(TextEntry(TextEntry(data.fluff.quote, styles=TextStyle(font_size=0.6, italic=True))))
        entries = TextEntry.from_array(paras, styles=RootStyle(font_color=self.faction_store.name_color(data.faction), font_size=54,
                                                               stroke_width=0.1, leading=1000, paragraph_padding=300))
        rd_names = self.text_renderer.render(entries, bbox=(540, 224), margin=Spacing(20), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, (147, 62))

        ncu_card.alpha_composite(apply_drop_shadow(bars_lower, shadow_size=5, color="#00000088"), (-20, -20))
        ncu_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))
        ncu_card.alpha_composite(apply_drop_shadow(bars_upper), (-20, -20))
        ncu_card.alpha_composite(layer_crests)
        ncu_card.alpha_composite(layer_text)
        return ncu_card
