from PIL.Image import Resampling
from generate_utils import *
from song_data import *


class ImageGeneratorSpecials(ImageGenerator):
    def generate(self, context, is_back=False):
        data: SongDataSpecials = context["data"]
        side = (data.back if is_back else None) or data.front
        style = side.get("style", "default")

        if data.category == "objective":
            return self.generate_objective_mission(context)
        elif data.category == "mission":
            return self.generate_objective_mission(context)
        elif data.category == "siege-attacker":
            return self.generate_objective_mission(context)
        elif data.category == "siege-defender":
            return self.generate_objective_mission(context)

        if style == "commander":
            return self.generate_commander(context, is_back)
        if style == "zone":
            return self.generate_zone(context, is_back)
        if style == "sunspear":
            return self.generate_sunspear(context, is_back)

        background = self.asset_manager.get_bg(data.faction)
        w, h = background.size
        special_card = Image.new("RGBA", (w, h))
        special_card.alpha_composite(background.rotate(self.faction_store.bg_rotation(data.faction)))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar_original = self.asset_manager.get_bars(data.faction)
        weird_bar = Image.new("RGBA", (weird_bar_original.height, weird_bar_original.height))
        weird_bar.alpha_composite(weird_bar_original)
        weird_bar.alpha_composite(weird_bar_original.rotate(270, expand=1), (weird_bar_original.width, 0))
        decor = self.asset_manager.get_decor(data.faction)
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
        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.crop(crest.getbbox())
        crest_size = min(158, int(crest.width * 182 / crest.height)), min(182, int(crest.height * 158 / crest.width))
        crest = crest.resize(crest_size)
        if side.get("crests") == 1:
            crest_x, crest_y = (w - crest.width) // 2, h_divider - crest.height // 2
            layer_crests.alpha_composite(crest, (crest_x, crest_y))
        elif side.get("crests") == 2:
            crest_l = ImageOps.mirror(crest).rotate(16, expand=1, resample=Resampling.BICUBIC)
            crest_r = crest.rotate(-16, expand=1, resample=Resampling.BICUBIC)
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
            names = [TextEntry(TextEntry(data.name.upper(), styles=TextStyle(leading=1000, bold=True)))]
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
                image = self.asset_manager.get_special_back_image(data.id, (inner_w, inner_h_bot))
            else:
                image = self.asset_manager.get_special_image(data.id, (inner_w, inner_h_bot))
            special_card.alpha_composite(image.crop((0, 0, inner_w, inner_h_bot)), (bbox_bot[0], bbox_bot[1]))

        entry_version = TextEntry.from_string(data.version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                        tracking=-10, stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        layer_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        special_card.alpha_composite(apply_drop_shadow(bars_lower), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(bars, color="#00000044"), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(layer_crests), (-20, -20))
        special_card.alpha_composite(layer_text)

        return special_card

    def generate_back(self, context):
        return self.generate(context, is_back=True)

    def generate_zone(self, context, is_back):
        data: SongDataSpecials = context["data"]
        side = (data.back if is_back else None) or data.front

        if is_back:
            if data.front.get("icon"):
                background = self.asset_manager.get_special_back_image("blankzone")
            else:
                background = self.asset_manager.get_special_back_image(data.id)
        else:
            if side.get("icon"):
                background = self.asset_manager.get_special_image("blankzone")
            else:
                background = self.asset_manager.get_special_image(data.id)
        special_card = Image.new("RGBA", background.size)
        w, h = special_card.size
        special_card.alpha_composite(background)

        layer_text = Image.new("RGBA", (w, h))
        if not is_back:
            name_entries = TextEntry.from_string(data.name.upper(), styles=RootStyle(font_color="#5b4a43", font_size=64, stroke_width=0.1,
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

        if side.get("icon") and not is_back:
            icon_entry = TextEntry.from_string(side.get("icon"), styles=RootStyle(font_color="#5b4a43", font_size=88))
            rd_icon = self.text_renderer.render(icon_entry, bbox=(180, 180), margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER)
            icon_bbox = rd_icon.getbbox()
            rd_icon = rd_icon.crop((icon_bbox[0], 0, icon_bbox[2], rd_icon.height))
            layer_text.alpha_composite(rd_icon, ((w - rd_icon.width) // 2 - 4, 500))

        special_card.alpha_composite(layer_text)

        return special_card

    def generate_sunspear(self, context, is_back):
        data: SongDataSpecials = context["data"]
        side = (data.back if is_back else None) or data.front

        if is_back:
            background = self.asset_manager.get_special_back_image(data.id)
        else:
            background = self.asset_manager.get_special_image(data.id)
        special_card = Image.new("RGBA", background.size)
        w, h = special_card.size
        special_card.alpha_composite(background)

        layer_text = Image.new("RGBA", (w, h))
        if is_back:
            bbox_names = (312, 152)
        else:
            bbox_names = (624, 74)
        name_entries = TextEntry.from_string(data.name.upper(), styles=RootStyle(font_color="white", font_size=50, stroke_width=0.1, bold=True,
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
            entry_version = TextEntry.from_string(data.version, styles=RootStyle(font_size=20, italic=True, font_color="white",
                                                                                 leading=1000, tracking=-10, stroke_width=0))
            rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                                   align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
            layer_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        special_card.alpha_composite(layer_text)

        return special_card

    def generate_commander(self, context, is_back):
        language = context["meta"].language
        data: SongDataSpecials = context["data"]
        side = (data.back if is_back else None) or data.front

        cmdr_data = side.get("data")
        title = cmdr_data.get("title")
        quote = cmdr_data.get("quote")
        tactics = cmdr_data.get("tactics")

        background = self.asset_manager.get_bg(data.faction)
        w, h = background.size
        special_card = Image.new("RGBA", (w, h))
        special_card.alpha_composite(background.rotate(self.faction_store.bg_rotation(data.faction)))

        if is_back:
            portrait = self.asset_manager.get_special_back_image(data.id)
        else:
            portrait = self.asset_manager.get_special_image(data.id)
        special_card.alpha_composite(portrait, (148, 292))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, corner_bar = self.asset_manager.get_bars(data.faction)
        decor = self.asset_manager.get_decor(data.faction)
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

        box_character = self.render_character_box(data.faction, language)
        layer_crests.alpha_composite(apply_drop_shadow(box_character), (429 - box_character.width // 2, 212))

        rendered_cost = self.render_cost(cmdr_data.get("cost", 0), self.faction_store.highlight_color(data.faction), True)
        layer_crests.alpha_composite(apply_drop_shadow(rendered_cost), (78 - rendered_cost.width // 2, 764))
        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.rotate(14, expand=1, resample=Resampling.BICUBIC)
        crest_size = min(198, int(crest.size[0] * 228 / crest.size[1])), min(228, int(crest.size[1] * 198 / crest.size[0]))
        crest = crest.resize(crest_size)
        crest_resize_x, crest_resize_y = 121 - crest.size[0] // 2, 290 - crest.size[1] // 2

        layer_crests.alpha_composite(apply_drop_shadow(crest), (crest_resize_x, crest_resize_y))

        unit_type = self.asset_manager.get_unit_type(cmdr_data.get("type"), data.faction)
        layer_crests.alpha_composite(apply_drop_shadow(unit_type), (78 - unit_type.width // 2, h - unit_type.size[1] - 20))

        names = [TextEntry(cmdr_data.get("name", data.name).upper(), styles=TextStyle(bold=True, word_spacing=250))]
        if title is not None:
            names.append(TextEntry(title.upper(), styles=TextStyle(font_size=0.55)))
        paras = [TextEntry(names)]
        if quote:
            paras.append(TextEntry(TextEntry(quote, styles=TextStyle(italic=True, font_size=0.6))))
        entries = TextEntry.from_array(paras, styles=RootStyle(font_color="white", font_size=54, stroke_width=0.1, leading=1000,
                                                               paragraph_padding=300))
        rd_names = self.text_renderer.render(entries, bbox=(572, 180), margin=Spacing(10), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, (168, 28))

        box_text = self.asset_manager.get_text_box(data.faction)
        box_commander = self.render_commander_box(data.faction, language)
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

    def generate_objective_mission(self, context):
        data: SongDataSpecials = context["data"]
        side = data.front

        if data.category == "mission":
            background = self.asset_manager.get_blank_mission()
            name_color = "#9b7425"
            text_color = "#215b34"
            name_text = data.name.upper()
            title_text = side.get("title")
            offset = 0
        elif data.category == "objective":
            background = self.asset_manager.get_blank_objective()
            name_color = "#7b7060"
            text_color = "#14607e"
            name_text = data.name.upper()
            title_text = side.get("title")
            offset = 0
        elif data.category == "siege-attacker":
            background = self.asset_manager.get_blank_siege_attacker()
            name_color = "#9a1e14"
            text_color = "#635f54"
            # TODO? Perhaps don't hardcode these
            name_text = "ATTACKER"
            title_text = data.name.upper()
            offset = 58
        elif data.category == "siege-defender":
            background = self.asset_manager.get_blank_siege_defender()
            name_color = "#302a28"
            text_color = "#635f54"
            name_text = "DEFENDER"
            title_text = data.name.upper()
            offset = 58
        else:
            raise ValueError(f"Enexpected category '{data.category}'")

        special_card = Image.new("RGBA", background.size)
        w, h = special_card.size
        special_card.alpha_composite(background)

        layer_text = Image.new("RGBA", (w, h))

        name_entries = TextEntry.from_string(name_text, styles=RootStyle(font_size=32, bold=True, font_color=name_color, tracking=10))
        rd_name = self.text_renderer.render(name_entries, bbox=(230 + offset, 30), margin=Spacing(2), align_y=TextRenderer.ALIGN_CENTER, align_x=TextRenderer.ALIGN_CENTER)
        layer_text.alpha_composite(rd_name, (130, 90))

        title = []
        if title_text is not None:
            title.append(TextEntry(TextEntry(title_text, styles=TextStyle(font_color=name_color, padding=Spacing(8), bold=True, tracking=10))))
        text = [TextEntry(TextEntry(e)) for e in side.get("text")]
        section = [TextEntry([*title, *text])]
        text_entries = TextEntry.from_array(section, styles=RootStyle(font_color=text_color, font_size=32, leading=1300))
        rd_text = self.text_renderer.render(text_entries, bbox=(335 + offset, 536), margin=Spacing(20), align_x=TextRenderer.ALIGN_CENTER,
                                            align_y=TextRenderer.ALIGN_CENTER, linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)
        layer_text.alpha_composite(rd_text, (75, 136))

        special_card.alpha_composite(layer_text)

        return special_card


    def generate_faction(self, faction):
        background = self.asset_manager.get_bg(faction)
        w, h = background.size
        special_card = Image.new("RGBA", (w, h))
        special_card.alpha_composite(background.rotate(self.faction_store.bg_rotation(faction)))

        bars = Image.new("RGBA", (w, h))
        bars_lower = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar_original = self.asset_manager.get_bars(faction)
        weird_bar = Image.new("RGBA", (weird_bar_original.height, weird_bar_original.height))
        weird_bar.alpha_composite(weird_bar_original)
        weird_bar.alpha_composite(weird_bar_original.rotate(270, expand=1), (weird_bar_original.width, 0))
        decor = self.asset_manager.get_decor(faction)
        small_bar_crop = small_bar.crop((0, 0, 650, 100))

        h_divider = int((971 - 33) * 0.3) + 54
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

        layer_text = Image.new("RGBA", (w, h))
        names = [TextEntry(TextEntry(self.faction_store.get_rendered(faction).upper(), styles=TextStyle(leading=1000, bold=True)))]
        name_entries = TextEntry.from_array(names, styles=RootStyle(font_color="white", font_size=54, stroke_width=0.1))
        name_bbox = (bbox_top[2] - bbox_top[0] - 20, bbox_top[3] - bbox_top[1] - 20)
        rd_names = self.text_renderer.render(name_entries, bbox=name_bbox, margin=Spacing(20), align_y=TextRenderer.ALIGN_CENTER,
                                             linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        layer_text.alpha_composite(rd_names, ((w - rd_names.width) // 2, 64))

        layer_crests = Image.new("RGBA", (w, h))
        crest = self.asset_manager.get_crest(faction)
        crest = crest.crop(crest.getbbox())
        crest_size = min(252, int(crest.width * 298 / crest.height)), min(298, int(crest.height * 252 / crest.width))
        crest = crest.resize(crest_size)
        crest_x, crest_y = (w - crest.width) // 2, bbox_bot[1] - crest.height // 2 + inner_h_bot // 2
        layer_crests.alpha_composite(crest, (crest_x, crest_y))

        special_card.alpha_composite(apply_drop_shadow(bars_lower), (-20, -20))
        special_card.alpha_composite(apply_drop_shadow(bars, color="#00000066"), (-20, -20))
        special_card.alpha_composite(layer_text)
        special_card.alpha_composite(apply_drop_shadow(layer_crests), (-20, -20))

        return special_card


def gen_faction_images():
    from song_data import FACTIONS
    from asset_manager import AssetManager
    am = AssetManager()
    gen = ImageGeneratorSpecials(am, TextRenderer(am))
    for faction in FACTIONS:
        print(f"Generating {faction}.png...")
        card = gen.generate_faction(faction)
        card.save(f"./generated/en/{faction}/{faction}.png")


if __name__ == "__main__":
    gen_faction_images()
