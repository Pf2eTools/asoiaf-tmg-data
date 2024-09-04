from image_editor import ImageEditor
from generate_utils import *


class ImageGeneratorTactics(ImageGenerator):
    def generate(self, data):
        name = data.get("name")
        statistics = data.get("statistics")
        faction = statistics.get("faction")
        card_text = statistics.get("text")
        version = statistics.get("version")
        commander_id = statistics.get("commander_id")
        commander_name = statistics.get("commander_name")
        commander_subname = statistics.get("commander_subname")

        tactics_bg = self.asset_manager.get_bg(faction)
        w, h = tactics_bg.size
        tactics_bg2 = self.asset_manager.get_text_bg()
        tactics_card = Image.new("RGBA", (w, h))
        tactics_card.alpha_composite(tactics_bg.rotate(get_faction_bg_rotation(faction)))
        tactics_card.alpha_composite(tactics_bg2, (47, 336))

        if commander_id is not None:
            cmdr_image = self.asset_manager.get_tactics_commmander_img(commander_id)
            tactics_card.alpha_composite(cmdr_image, (-1, -2))

        bars = Image.new("RGBA", (w, h))
        large_bar, small_bar, weird_bar = self.asset_manager.get_bars(faction)

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

        decor = self.asset_manager.get_decor(faction)
        bars.alpha_composite(decor, (33, 316))
        bars.alpha_composite(decor, (673, 316))
        bars.alpha_composite(decor, (33, 971))
        bars.alpha_composite(decor, (673, 971))
        if commander_id is not None:
            bars.alpha_composite(decor, (33, 232))
            bars.alpha_composite(decor, (673, 232))

        all_text = Image.new("RGBA", (w, h))

        name_max_w = 440 if commander_name is None else 392
        name_entry = TextEntry.from_string(name.upper(), styles=RootStyle(bold=True, font_size=50, leading=940, font_color="white"))
        rd_name = self.text_renderer.render(name_entry, bbox=(name_max_w, 200), align_y=TextRenderer.ALIGN_CENTER, margin=Spacing(10),
                                            linebreak_algorithm=TextRenderer.LINEBREAK_NAME)
        if commander_name is not None:
            name_x, name_y = (tactics_bg.width - rd_name.width) // 2 + 170, 136 - rd_name.height // 2
            all_text.alpha_composite(rd_name, (name_x, name_y))
        else:
            name_x, name_y = (w - rd_name.width) // 2 + 138, 140 - rd_name.height // 2
            all_text.alpha_composite(rd_name, (name_x, name_y))

        if commander_name is not None:
            rd_cmdr_name = self.text_renderer.render_cmdr_name(commander_name, commander_subname, bbox=(622, 66),
                                                               align_y=TextRenderer.ALIGN_CENTER, margin=Spacing(5),
                                                               styles=RootStyle(font_size=32, font_color="white", leading=1000))
            all_text.alpha_composite(rd_cmdr_name, ((tactics_bg.size[0] - 622) // 2, 262))

        section_padding = small_bar.height
        align_y = TextRenderer.CENTER_SECTION if len(card_text) > 1 else TextRenderer.ALIGN_TOP
        entries = self.get_data_for_renderer(card_text, get_faction_text_color(faction), section_padding)
        rd_card_text = self.text_renderer.render(entries, bbox=(620, 635), align_y=align_y, margin=Spacing(15, 30), scale_margin=15/50,
                                                 linebreak_algorithm=TextRenderer.LINEBREAK_OPTIMAL)

        all_text.alpha_composite(rd_card_text, ((w - 620) // 2, 347))

        for top, bot in self.text_renderer.get_computed_between():
            center = int(top + (bot - top) / 2) + 347
            bars.alpha_composite(small_bar.crop((0, 0, tactics_bg2.size[0], 100)),
                                 ((tactics_bg.size[0] - tactics_bg2.size[0]) // 2, center - small_bar.size[1] // 2))
            bars.alpha_composite(decor, (33, center - decor.size[1] // 2))
            bars.alpha_composite(decor, (673, center - decor.size[1] // 2))

        entry_version = TextEntry.from_string(version, styles=RootStyle(font_size=20, italic=True, font_color="white", leading=1000,
                                                                        tracking=-10, stroke_width=0))
        rd_version = self.text_renderer.render(entry_version, bbox=(100, 25), align_y=TextRenderer.ALIGN_BOTTOM,
                                               align_x=TextRenderer.ALIGN_LEFT, supersample=1.0, margin=Spacing(0, 5))
        all_text.alpha_composite(rd_version.rotate(90, expand=1), (19, h - 170))

        tactics_card.alpha_composite(apply_drop_shadow(bars), (-20, -20))

        crest = self.asset_manager.get_crest(faction)
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

    @staticmethod
    def get_data_for_renderer(card_text, color, section_padding):
        sections = []
        for trigger_effect in card_text:
            paras = []
            trigger = trigger_effect.get("trigger")
            if trigger is not None:
                paras.append(TextEntry(TextEntry(trigger, styles=TextStyle(bold=True, font_color=color))))

            for paragraph in trigger_effect.get("effect", []):
                paras.append(TextEntry(TextEntry(paragraph)))

            remove = trigger_effect.get("remove")
            if remove is not None:
                paras.append(TextEntry(TextEntry(remove, styles=TextStyle(bold=True, font_color="#5d4d40"))))

            sections.append(TextEntry(paras))

        return TextEntry.from_array(sections, styles=RootStyle(font_size=39, font_color="#5d4d40", section_padding=section_padding))


def main():
    from asset_manager import AssetManager
    justice = {
        "id": "40601",
        "name": "Baratheon Justice",
        "statistics": {
            "version": "S04",
            "faction": "baratheon",
            "text": [
                {
                    "trigger": "After an enemy completes an Attack:",
                    "effect": [
                        "The Attacker gains 1 Condition token.",
                        "If you Control [CROWN] or [LETTER], they gain +1 token."
                    ]
                }
            ]
        }
    }
    wealth = {
        "id": "40620",
        "name": "Wealth And Charisma",
        "statistics": {
            "version": "2021",
            "faction": "baratheon",
            "text": [
                {
                    "trigger": "When a friendly NCU Claims a zone:",
                    "effect": [
                        "Replace that zone's effect with:",
                        "*Choose 1:*",
                        "*• Restore 3 Wounds (total) across any number of friendly Combat Units.*",
                        "*• Remove all Condition tokens from each friendly Combat Unit. For each token removed, deal 1 enemy engaged with that unit 1 Wound.*"
                    ]
                }
            ],
            "commander_id": "20601",
            "commander_name": "Renly Baratheon",
            "commander_subname": "The Charismatic Heir"
        }
    }
    flight = {
        "id": "40729",
        "name": "Dragon's Flight",
        "statistics": {
            "version": "2021-S03",
            "faction": "targaryen",
            "text": [
                {
                    "trigger": "When an enemy ends a move in Short Range of Daenerys' unit:",
                    "effect": [
                        "Target 1 friendly Drogon, Rhaegal, or Viserion unit. It performs 1 Maneuver Action."
                    ]
                },
                {
                    "trigger": "Start of any Turn:",
                    "effect": [
                        "Draw 1 Tactics card."
                    ]
                }
            ],
            "commander_id": "20714",
            "commander_name": "Daenerys Targaryen",
            "commander_subname": "Mother Of Dragons"
        }
    }
    data = flight
    am = AssetManager()
    gen = ImageGeneratorTactics(am, TextRenderer(am))
    statistics = data.get("statistics")
    faction = statistics.get("faction")
    card = gen.generate(data)
    org = Image.open(f"./generated/en/{faction}/tactics/{data['id']}.jpg").convert("RGBA")
    editor = ImageEditor(card, org)


if __name__ == "__main__":
    main()
