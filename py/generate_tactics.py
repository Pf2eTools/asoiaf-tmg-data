from PIL.Image import Resampling

from generate_utils import *
from song_data import *


class ImageGeneratorTactics(ImageGenerator):
    def generate(self, context):
        data: SongDataTactics = context["data"]
        commander: SongDataAttachment = context["commander"]

        if data.commander and commander is None:
            print(f"WARNING: {data.name} ({data.id}) commander {data.commander.id} was not found")

        tactics_bg = self.asset_manager.get_bg(data.faction)
        w, h = tactics_bg.size
        tactics_bg2 = self.asset_manager.get_text_bg()
        tactics_card = Image.new("RGBA", (w, h))
        tactics_card.alpha_composite(tactics_bg.rotate(self.faction_store.bg_rotation(data.faction)))
        tactics_card.alpha_composite(tactics_bg2, (47, 336))

        if commander is not None:
            cmdr_image = self.asset_manager.get_tactics_commmander_img(commander.id)
            tactics_card.alpha_composite(cmdr_image, (-1, -2))

        bars = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar = self.asset_manager.get_bars(data.faction)

        bars.alpha_composite(large_bar.rotate(180), (-96, 252))
        if commander is not None:
            bars.paste(Image.new("RGBA", (646, 82), (0, 0, 0, 0)), (55, 246))

        bars.alpha_composite(ImageOps.flip(weird_bar.rotate(270, expand=1)), (242 - weird_bar.size[1], 25))
        bars.alpha_composite(weird_bar.rotate(270, expand=1), (242 - weird_bar.size[1], -95))
        if commander is not None:
            bars.alpha_composite(large_bar.rotate(90, expand=1), (240, 235 - large_bar.size[0]))
            bars.alpha_composite(weird_bar.rotate(90, expand=1), (323, 25))
            bars.alpha_composite(ImageOps.flip(weird_bar.rotate(90, expand=1)), (323, -95))
            bars.alpha_composite(small_bar.rotate(90, expand=1), (234, 255 - small_bar.size[0]))
            bars.alpha_composite(small_bar.rotate(90, expand=1), (314, 255 - small_bar.size[0]))
        else:
            bars.alpha_composite(weird_bar.rotate(90, expand=1), (243, 25))
            bars.alpha_composite(ImageOps.flip(weird_bar.rotate(90, expand=1)), (243, -95))
            bars.alpha_composite(small_bar.rotate(90, expand=1), (234, 255 - small_bar.size[0]))

        if commander is None:
            bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1])), (46, 336))
            bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1])), (687, 336))
        else:
            bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (46, 246))
            bars.alpha_composite(small_bar.rotate(90, expand=1).crop((0, 0, 100, tactics_bg2.size[1] + 82)), (687, 246))
        bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)), ((w - tactics_bg2.size[0]) // 2, 985))
        bars.alpha_composite(small_bar, (0, 246))
        bars.alpha_composite(small_bar, (0, 328))

        decor = self.asset_manager.get_decor(data.faction)
        bars.alpha_composite(decor, (33, 316))
        bars.alpha_composite(decor, (673, 316))
        bars.alpha_composite(decor, (33, 971))
        bars.alpha_composite(decor, (673, 971))
        if commander is not None:
            bars.alpha_composite(decor, (33, 232))
            bars.alpha_composite(decor, (673, 232))

        all_text = Image.new("RGBA", (w, h))

        name_max_w = 440 if commander is None else 392
        name_entry = TextEntry.from_string(data.name.upper(), styles=RootStyle(bold=True, font_size=50, leading=940, font_color=self.faction_store.name_color(data.faction)))
        rd_name = self.text_renderer.render(name_entry, bbox=(name_max_w, 200), align_y=TextRenderer.ALIGN_CENTER, margin=Spacing(10),
                                            linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        if commander:
            name_x, name_y = (tactics_bg.width - rd_name.width) // 2 + 170, 136 - rd_name.height // 2
            all_text.alpha_composite(rd_name, (name_x, name_y))
        else:
            name_x, name_y = (w - rd_name.width) // 2 + 138, 140 - rd_name.height // 2
            all_text.alpha_composite(rd_name, (name_x, name_y))

        if commander is not None:
            commander_name = data.commander.name or commander.name
            commander_title = data.commander.title or commander.title

            rd_cmdr_name = self.text_renderer.render_cmdr_name(commander_name, commander_title, bbox=(622, 66),
                                                               align_y=TextRenderer.ALIGN_CENTER, margin=Spacing(5),
                                                               styles=RootStyle(font_size=32, font_color=self.faction_store.name_color(data.faction),
                                                                                leading=1000))
            all_text.alpha_composite(rd_cmdr_name, ((tactics_bg.size[0] - 622) // 2, 262))

        section_padding = small_bar.height
        align_y = TextRenderer.CENTER_SECTION if len(data.text) > 1 else TextRenderer.ALIGN_TOP
        entries = self.get_data_for_renderer(data.text, self.faction_store.text_color(data.faction), section_padding)
        rd_card_text = self.text_renderer.render(entries, bbox=(620, 635), align_y=align_y, margin=Spacing(15, 30), scale_margin=15/50,
                                                 linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)

        all_text.alpha_composite(rd_card_text, ((w - 620) // 2, 347))

        for top, bot in self.text_renderer.get_computed_between():
            center = int(top + (bot - top) / 2) + 347
            bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                                 ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, center - small_bar.size[1] // 2))
            bars.alpha_composite(decor, (33, center - decor.size[1] // 2))
            bars.alpha_composite(decor, (673, center - decor.size[1] // 2))

        entry_version = TextEntry.from_string(data.version, styles=RootStyle(font_size=20, italic=True, leading=1000, tracking=-10,
                                                                             font_color=self.faction_store.name_color(data.faction),
                                                                             stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        all_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        tactics_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))

        crest = self.asset_manager.get_crest(data.faction)
        crest = crest.crop(crest.getbbox())
        crest = crest.resize(((189 + crest.size[0]) // 2, int(crest.size[1] * ((189 + crest.size[0]) / 2) / crest.size[0])))
        if commander is None:
            crest_rot = crest.rotate(16, expand=1, resample=Resampling.BILINEAR)
            crest_rot_x, crest_rot_y = 175 - crest_rot.size[0] // 2, 181 - crest_rot.size[1] // 2
            tactics_card.alpha_composite(apply_drop_shadow(crest_rot), (crest_rot_x, crest_rot_y))
        else:
            crest_resize = crest.resize((int(crest.size[0] * 0.68), int(crest.size[1] * 0.68)))
            crest_resize_x, crest_resize_y = 264 - crest_resize.size[0] // 2, 175 - crest_resize.size[1] // 2
            tactics_card.alpha_composite(apply_drop_shadow(crest_resize), (crest_resize_x, crest_resize_y))

        tactics_card.alpha_composite(all_text)

        return tactics_card

    @staticmethod
    def get_data_for_renderer(text_sections, color, section_padding):
        sections = []
        text: TacticsText
        for text in text_sections:
            paras = []
            if text.trigger:
                paras.append(TextEntry(TextEntry(text.trigger, styles=TextStyle(bold=True, font_color=color))))

            if text.effect:
                for paragraph in text.effect:
                    paras.append(TextEntry(TextEntry(paragraph)))

            if text.remove:
                paras.append(TextEntry(TextEntry(text.remove, styles=TextStyle(bold=True, font_color="#5d4d40"))))

            sections.append(TextEntry(paras))

        return TextEntry.from_array(sections, styles=RootStyle(font_size=39, font_color="#5d4d40", section_padding=section_padding))
