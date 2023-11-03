#!/usr/bin/env python
import csv
import os
import tkinter as tk
import pdb
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter

#pip install pillow

def add_rounded_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, "white")
    w,h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(90), (0, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(180), (w - rad, h - rad))
    alpha.paste(circle.crop((0, 0, rad, rad)).rotate(270), (w - rad, 0))
    alpha.paste(255, (rad, 0, w - rad, h - rad))
    alpha.paste(255, (0, rad, rad, h - rad))
    alpha.paste(255, (w - rad, rad, w, h - rad))
    alpha.paste(255, (rad, rad, w - rad, h - rad))

    im = im.convert("RGBA")
    im.putalpha(alpha)

    return im

def load_fonts(fonts_folder):
    font_files = [f for f in os.listdir(fonts_folder) if f.lower().endswith(('.otf', '.ttf'))]
    fonts = {}
    for font_file in font_files:
        try:
            font_path = os.path.join(fonts_folder, font_file)
            font = ImageFont.truetype(font_path, size=44)  # You can specify the font size here
            fonts[font_file.split(".")[0]] = font
            fonts[font_file.split(".")[0]+'-smaller'] = ImageFont.truetype(font_path, size=30)
            print(f"Successfully loaded font: {font_file}")
        except Exception as e:
            print(f"Failed to load font {font_file}: {str(e)}")
    return fonts


def import_csvs_to_dicts(assets_data_folder):
    # Step 2: Get the list of all CSV files in the specified directory
    csv_files = [f for f in os.listdir(assets_data_folder) if f.endswith('.csv')]
    # Main dictionary to store the content of all CSV files
    all_data = {}
    # Step 3: Iterate over the list of CSV files
    for csv_file in csv_files:
        # Create the full path to the CSV file
        file_path = os.path.join(assets_data_folder, csv_file)
        # Open the CSV file
        with open(file_path, mode='r', encoding='utf-8') as f:
            # Create a CSV DictReader object
            reader = csv.DictReader(f)
            # Convert the content of the CSV file to a list of dictionaries
            data = [row for row in reader]
        # Step 4: Store the list of dictionaries in the main dictionary
        all_data[csv_file.split('.')[0]] = data
    return all_data

# I use this so I can load the unit card and get x + y on the card so I can more easily get coordinates of images on click

class ImageEditor:
    def __init__(self, master, unit_card_image):
        self.master = master
        master.title("Image Editor")

        self.unit_card_image = unit_card_image
        self.tk_image = ImageTk.PhotoImage(self.unit_card_image)
        
        self.label = tk.Label(master, image=self.tk_image)
        self.label.pack()

        self.label.bind("<Button-1>", self.log_coordinates)

    def log_coordinates(self, event):
        x = event.x
        y = event.y
        print("Clicked at:", x, y)


def draw_centered_text(draw, position, text_lines_list, font, fill, line_padding=0):
    """
    Draw multi-line text centered at the specified position.

    :param draw: ImageDraw object.
    :param position: Tuple (x, y) representing the position to center the text at.
    :param text: The text to draw.
    :param font: The font to use.
    :param fill: Color to use for the text.
    :param padding: Padding between lines of text.
    """
    total_height = sum([font.getbbox(line)[3] - font.getbbox(line)[1] for line in text_lines_list]) + line_padding * (len(text_lines_list) - 1)

    x, y = position
    y -= total_height / 2  # Adjust y-coordinate to start drawing from.

    for line in text_lines_list:
        text_width, text_height = font.getbbox(line)[2], font.getbbox(line)[3] - font.getbbox(line)[1]
        draw.text((x - text_width / 2, y), line, font=font, fill=fill)
        y += text_height + line_padding


def BuildUnitCard(UnitData, units_folder, AsoiafFonts, unit_card_output_dir, debug=False):
    """
    AsoiafFonts = 
    {'StoneTypeFoundry-Tuff-Bold': '', 'LXGWWenKaiGB-Regular': '', 'StoneTypeFoundry-Tuff-Italic': '', 
    'Tuff-Bold': '', 'StoneTypeFoundry-Tuff-Normal': '', 'Iansui0': '', 'StoneTypeFoundry-Tuff-SemiboldItalic': '', 
    'Tuff-Normal': '', 'StoneTypeFoundry-Tuff-BoldItalic': '', 'MaterialIcons-Regular': '', 
    'StoneTypeFoundry-Tuff-Semibold': '', 'Garamond-Bold': '', 'Tuff-BoldItalic': '', 'Tuff-Italic': ''}

    UnitData = 
    {'Faction': 'Lannister', 'Name': 'Lannister Guardsmen', 'Character': '', 'Cost': '5', 'Type': 'Infantry', 
    'Spd': '4', 'Attack 1': '[M]Long Sword', '': '', 'Attack 2': '', 'Def': '3+', 'Moral': '7+', 
    'Abilities': 'Order: Lannister Supremacy', 'Requirements': '', 'Boxes': 'SIF001/SIF001/SIF001B/SIF001B/SIF201', 
    'Id': '10101', 'Version': '2021', 'Requirement Text': '', 'Quote': '', 
    'Lore': ''}
    """

    def add_debug_border(image):
        if debug:
            draw = ImageDraw.Draw(image)
            for i in range(image.size[0]):
                draw.point((i, 0), fill="black")
                draw.point((i, image.size[1] - 1), fill="black")
            for i in range(image.size[1]):
                draw.point((0, i), fill="black")
                draw.point((image.size[0] - 1, i), fill="black")
        return image

    faction = UnitData['Faction'].replace(' ','') # faction file names dont include spaces
    UnitType = UnitData['Type'].replace(' ','')
    # Images points of origin are always top-left most corner of the loaded image.
    unit_faction_bg_image = Image.open(f"{units_folder}UnitBg{faction}.jpg").convert('RGBA')
    top_left_red_gold_bar = Image.open(f"{units_folder}Bar{faction}.webp").convert('RGBA')
    large_bar = Image.open(f"{units_folder}LargeBar{faction}.webp").convert('RGBA')
    next_red_gold_bar_below = Image.open(f"{units_folder}Bar{faction}.webp").convert('RGBA')
    movement_foot_image = Image.open(f"{units_folder}Movement.webp").convert('RGBA')
    movement_foot_stat_bg_image = Image.open(f"{units_folder}StatBg.webp").convert('RGBA')

    # Attack Bar
    # These will actually probably be pulled from the unit data and plugged in dynamically.
    silver_attack_type_sword = Image.open(f"{units_folder}AttackTypeBgSilver.webp").convert('RGBA')
    silver_attack_type_border = Image.open(f"{units_folder}AttackType.MeleeSilver.webp").convert('RGBA')
    silver_attack_tan_background = Image.open(f"{units_folder}AttackBgSilver.webp").convert('RGBA')
    silver_attack_dice_background = Image.open(f"{units_folder}DiceBg.webp").convert('RGBA')
    melee_attack_stat_bg_image = movement_foot_stat_bg_image.copy()

    # Shield and morale stuff
    shield_top_gold_bar = next_red_gold_bar_below.copy()
    shield_large_bar = large_bar.copy()
    shield_next_gold_bar = next_red_gold_bar_below.copy()
    shield_image = Image.open(f"{units_folder}Defense.webp").convert('RGBA')
    shield_stat_bg_image = movement_foot_stat_bg_image.copy()
    morale_image = Image.open(f"{units_folder}Morale.webp").convert('RGBA')
    morale_stat_bg_image = movement_foot_stat_bg_image.copy()

    #First Vertical Gold bar left of portrait
    # Have to rotate them
    left_onleft_vertical_gold_bar = next_red_gold_bar_below.copy().rotate(90, expand=True)
    large_onleft_vertical_gold_bar = large_bar.copy().rotate(90, expand=True)
    right_onleft_vertical_gold_bar = next_red_gold_bar_below.copy().rotate(90, expand=True)
    #Unit Type on bottom of the left side portrait gold bar
    unit_type_image = Image.open(f"{units_folder}UnitType.{UnitType}{faction}.webp").convert('RGBA')

    # Unit Portrait Stuff
    left_bottom_gold_corner = Image.open(f"{units_folder}Corner{faction}.webp").convert('RGBA')
    right_bottom_gold_corner = left_bottom_gold_corner.copy().transpose(Image.FLIP_LEFT_RIGHT)
    left_gold_corner_top = left_bottom_gold_corner.copy().transpose(Image.FLIP_TOP_BOTTOM)
    right_gold_corner = left_gold_corner_top.copy().transpose(Image.FLIP_LEFT_RIGHT)
    unit_portrait = Image.open(f"{units_folder}{UnitData['Id']}.jpg").convert('RGBA')
    portrait_attachment_on_middleof_trim = Image.open(f"./assets/graphics/attachment{faction}.png").convert('RGBA')
    faction_crest = Image.open(f"{units_folder}Crest{faction}.webp").convert('RGBA')

    # Gold bars to the right of the portrait:
    left_onright_vertical_gold_bar = left_onleft_vertical_gold_bar.copy()
    large_onright_vertical_gold_bar = large_onleft_vertical_gold_bar.copy()
    right_onright_vertical_gold_bar = right_onleft_vertical_gold_bar.copy()

    # Skill Panel
    skill_panel_bottom = Image.open(f"{units_folder}SkillBottom{faction}.webp").convert('RGBA')
    skill_panel_separator = Image.open(f"{units_folder}Divider{faction}.webp").convert('RGBA')
    skill_panel_top = skill_panel_bottom.copy().transpose(Image.FLIP_TOP_BOTTOM)
    skills_tan_background_for_text = Image.open(f"{units_folder}SkillsBg.webp").convert('RGBA')

    # Actually probably need to parse unit data to dynamically pull these
    # In units folder
    additional_images_to_load = """
    AttackBgGold.webp
    AttackBgSilver.webp
    AttackTypeBgGold.webp
    AttackTypeBgSilver.webp
    AttackType.MeleeGold.webp
    AttackType.MeleeSilver.webp
    AttackType.RangedGold.webp
    AttackType.RangedSilver.webp
    CostGoldCommander.webp
    CostGoldRegular.webp
    CostSilverCommander.webp
    CostSilverRegular.webp
    SkillFaithSilver.webp
    SkillFireSilver.webp
    SkillOrderGold.webp
    SkillOrderSilver.webp
    SkillPillageGold.webp
    SkillPillageSilver.webp
    SkillVenomGold.webp
    SkillWoundsGold.webp
    SkillWoundsSilver.webp
    """
    # In assets/graphics/ folder, some of these are used by the app and not are cards. Will need to check in on them:
    # Like for sure RangeShortSilver.png etc...
    additional_images_to_check = """
    AppBGHeader.jpg
    AppBGNone.jpg
    ArmyError.png
    ArmyOk.png
    AttachmentArrow.png
    barNone.png
    Bar.png
    BGCollection.webp
    BGContent.jpg
    bgCount.png
    BGCreateArmy.jpg
    BGStart.jpg
    BGText.png
    Bt2.png
    BtArrow.png
    BtBGLeft.png
    BtBGRight.png
    BtCreateArmy.png
    BtGold.png
    Bt.png
    CROWN.png
    HeaderBar0.png
    HeaderBar1.png
    HeaderBar2.png
    HeaderDecoration.png
    HORSE.png
    IconCard.png
    IconCheck.png
    IconCrown.png
    IconDefense.png
    IconEdit.png
    IconExclamation.png
    IconEye.png
    IconFaith.png
    IconFire.png
    IconMelee.png
    IconMorale.png
    IconMovement.png
    IconOrder.png
    IconPen.png
    IconPillage.png
    IconQuestion.png
    IconRanged.png
    IconShare.png
    IconVenom.png
    IconWound.png
    LETTER.png
    Logo.webp
    LONGRANGE.png
    MONEY.png
    MOVEMENT.png
    OASIS.png
    RangeLongGold.png
    RangeLongSilver.png
    RangeShortGold.png
    RangeShortSilver.png
    SmallBtBGBlue.png
    SmallBtBGGreen.png
    SmallBtBGPurple.png
    SmallBtBGRed.png
    SmallBtBow.png
    SmallBtFrame.png
    SmallBtSword.png
    SquareBorder.png
    SWORDS.png
    ToggleOff.png
    ToggleOn.png
    UNDYING.png
    UnitTypeCavalry.png
    UnitTypeInfantry.png
    UnitTypeMonster.png
    UnitTypeNCU.png
    UnitTypeNone.png
    UnitTypeSiegeEngine.png
    WOUND.png
    """
    

    # This does nothing if you dont uncomment pass debug true. I only add to see where images are. Which are which
    #unit_faction_bg_image = add_debug_border(unit_faction_bg_image)
    #top_left_red_gold_bar = add_debug_border(top_left_red_gold_bar)
    #large_bar = add_debug_border(large_bar)
    #next_red_gold_bar_below = add_debug_border(next_red_gold_bar_below)
    #movement_foot_image = add_debug_border(movement_foot_image)
    #movement_foot_stat_bg_image = add_debug_border(movement_foot_stat_bg_image)

    # Create unit card
    unit_card = Image.new('RGBA', unit_faction_bg_image.size)
    
    # Place images on unit card
    unit_card.paste(unit_faction_bg_image, (0, 0), unit_faction_bg_image)
    yOffset = 60
    #yOffset += top_left_red_gold_bar.size[1]
    unit_card.paste(large_bar, (0, yOffset), large_bar)
    unit_card.paste(top_left_red_gold_bar, (0, yOffset), top_left_red_gold_bar)
    # Adjust the positions below according to your layout requirements
    yOffset += large_bar.size[1] - next_red_gold_bar_below.size[1]
    unit_card.paste(next_red_gold_bar_below, (0, yOffset), next_red_gold_bar_below)
    yOffset -= large_bar.size[1]
    xoffset = 30 + movement_foot_image.size[0]
    unit_card.paste(movement_foot_stat_bg_image, (xoffset, yOffset + int(movement_foot_stat_bg_image.size[0]/4)), movement_foot_stat_bg_image)
    xoffset = 50
    unit_card.paste(movement_foot_image, (xoffset, yOffset), movement_foot_image)

    # Add text
    draw = ImageDraw.Draw(unit_card)
    # Retrieve font text
    # Tuff-Italic appears to be the 2021 numbering on left side of card and for the attack name (Long Sword etc...)
    # Tuff-Bold appears to be for title of abilities (in red) and keywords (in black)
    # Tuff-Normal for all other ability text
    GaramondBoldFont = AsoiafFonts.get('Garamond-Bold', ImageFont.load_default()) # this should be the correct font for stat lines
    draw.text((175, 85), UnitData['Spd'], font=GaramondBoldFont, fill="white")
    TuffBoldFont = AsoiafFonts.get('Tuff-Bold', ImageFont.load_default()) # this should be the correct font for unit name
    text_lines_list = UnitData['Name'].upper().split(' ') # Lannister Guardsmen Gits split into multiple lines
    draw_centered_text(draw, (550, 715), text_lines_list, TuffBoldFont, "white", line_padding=10)
    # Apply rounded corners with a radius of 20
    unit_card = add_rounded_corners(unit_card, 20)
    # Save image
    unit_card_output_path = os.path.join(unit_card_output_dir, f"{UnitData['Id'].replace(' ', '_')}.png")
    unit_card.save(unit_card_output_path)
    #unit_card.show()
    return unit_card

def add_shadow(original_image, shadow_size, shadow_strength, sides=('left', 'top', 'right', 'bottom')):
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')
    original_width, original_height = original_image.size
    # Calculate new image size
    new_width = original_width + shadow_size * ('left' in sides) + shadow_size * ('right' in sides)
    new_height = original_height + shadow_size * ('top' in sides) + shadow_size * ('bottom' in sides)
    # Create a new image with the new size and a transparent background
    new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    # Create the shadow gradient
    shadow_gradient = [i * (255 - shadow_strength) // shadow_size for i in range(shadow_size)]
    # Create the shadow on each side
    for side in sides:
        for i, alpha in enumerate(shadow_gradient):
            if side == 'left':
                band = Image.new('RGBA', (1, original_height), (0, 0, 0, alpha))
                new_image.paste(band, (i, shadow_size * ('top' in sides)))
            elif side == 'right':
                band = Image.new('RGBA', (1, original_height), (0, 0, 0, alpha))
                new_image.paste(band, (new_width - i - 1, shadow_size * ('top' in sides)))
            elif side == 'top':
                band = Image.new('RGBA', (original_width, 1), (0, 0, 0, alpha))
                new_image.paste(band, (shadow_size * ('left' in sides), i))
            elif side == 'bottom':
                band = Image.new('RGBA', (original_width, 1), (0, 0, 0, alpha))
                new_image.paste(band, (shadow_size * ('left' in sides), new_height - i - 1))
    # Place the original image on top of the shadow
    original_position = (shadow_size * ('left' in sides), shadow_size * ('top' in sides))
    new_image.paste(original_image, original_position, original_image)
    return new_image

class LayeredImageCanvas:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = []

    def add_layer(self, image, x, y, depth):
        self.layers.append({
            'image': image,
            'x': x,
            'y': y,
            'depth': depth
        })
        # Sort layers by depth so that higher depth layers are rendered last (on top)
        self.layers.sort(key=lambda layer: layer['depth'])

    def render(self):
        # Create a blank canvas
        canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        for layer in self.layers:
            canvas.paste(layer['image'], (layer['x'], layer['y']), layer['image'])
        return canvas

def BuildUnitCardFactionBackground(UnitData, units_folder, graphics_folder):
    faction = UnitData['Faction'].replace(' ','') # faction file names dont include spaces
    UnitType = UnitData['Type'].replace(' ','')
    # Images points of origin are always top-left most corner of the loaded image.
    unit_faction_bg_image = Image.open(f"{units_folder}UnitBg{faction}.jpg").convert('RGBA')
    
    shadow_size = 4
    shadow_strength = 125

    # Left most bar
    top_left_red_gold_bar = Image.open(f"{units_folder}Bar{faction}.webp").convert('RGBA')
    large_bar = Image.open(f"{units_folder}LargeBar{faction}.webp").convert('RGBA')
    next_red_gold_bar_below = Image.open(f"{units_folder}Bar{faction}.webp").convert('RGBA')

    # Shield and morale stuff
    shield_top_gold_bar = next_red_gold_bar_below.copy()
    shield_large_bar = large_bar.copy()
    shield_next_gold_bar = next_red_gold_bar_below.copy()

    #First Vertical Gold bar left of portrait
    # Have to rotate them
    left_onleft_vertical_gold_bar = next_red_gold_bar_below.copy().rotate(90, expand=True)
    large_onleft_vertical_gold_bar = large_bar.copy().rotate(90, expand=True)
    right_onleft_vertical_gold_bar = next_red_gold_bar_below.copy().rotate(90, expand=True)
    #Unit Type on bottom of the left side portrait gold bar

    # Unit Portrait Stuff
    left_bottom_gold_corner = Image.open(f"{units_folder}Corner{faction}.webp").convert('RGBA')
    right_bottom_gold_corner = left_bottom_gold_corner.copy().transpose(Image.FLIP_LEFT_RIGHT)
    left_gold_corner_top = left_bottom_gold_corner.copy().transpose(Image.FLIP_TOP_BOTTOM)
    right_gold_corner = left_gold_corner_top.copy().transpose(Image.FLIP_LEFT_RIGHT)
    unit_portrait = Image.open(f"{units_folder}{UnitData['Id']}.jpg").convert('RGBA')
    portrait_attachment_on_middleof_trim = Image.open(f"{graphics_folder}/attachment{faction}.png").convert('RGBA')
    faction_crest = Image.open(f"{units_folder}Crest{faction}.webp").convert('RGBA')

    # Tan Skills Background:
    skills_tan_background_for_text = Image.open(f"{units_folder}SkillsBg.webp").convert('RGBA')

    # Gold bars to the right of the portrait:
    left_onright_vertical_gold_bar = left_onleft_vertical_gold_bar.copy()
    large_onright_vertical_gold_bar = large_onleft_vertical_gold_bar.copy()
    right_onright_vertical_gold_bar = right_onleft_vertical_gold_bar.copy()

    leftFirstVertBarXOffset = 190
    topBarYOffset = 60
    bottomBarYOffset = 600

    # Custom Canvas Class so I dont have to worry about layering in order
    canvas = LayeredImageCanvas(unit_faction_bg_image.size[0], unit_faction_bg_image.size[1])

    # Create our image to draw to
    unit_card = Image.new('RGBA', unit_faction_bg_image.size)
    #unit_card.paste(unit_faction_bg_image, (0, 0), unit_faction_bg_image) # background first
    canvas.add_layer(unit_faction_bg_image, 0, 0, depth=0)

    # Add Shadows To Objects
    top_left_red_gold_bar = add_shadow(top_left_red_gold_bar, shadow_size, shadow_strength, sides=('top', 'bottom')) # ('left', 'top', 'right', 'bottom')
    next_red_gold_bar_below = add_shadow(next_red_gold_bar_below, shadow_size, shadow_strength, sides=('top', 'bottom'))
    large_bar = add_shadow(large_bar, shadow_size, shadow_strength, sides=('top', 'bottom'))

    shield_large_bar = add_shadow(shield_large_bar, shadow_size, shadow_strength, sides=('top', 'bottom'))
    shield_top_gold_bar = add_shadow(shield_top_gold_bar, shadow_size, shadow_strength, sides=('top', 'bottom'))
    shield_next_gold_bar = add_shadow(shield_next_gold_bar, shadow_size, shadow_strength, sides=('top', 'bottom'))

    large_onleft_vertical_gold_bar = add_shadow(large_onleft_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))
    left_onleft_vertical_gold_bar = add_shadow(left_onleft_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))
    right_onleft_vertical_gold_bar = add_shadow(right_onleft_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))

    # Drawing Top Left Horozontal Gold Bar
    top_left_red_gold_bar = top_left_red_gold_bar.crop( (0, 0, leftFirstVertBarXOffset, top_left_red_gold_bar.size[1]) )
    next_red_gold_bar_below = next_red_gold_bar_below.crop( (0, 0, leftFirstVertBarXOffset, next_red_gold_bar_below.size[1]) )
    large_bar = large_bar.crop( (0, 0, leftFirstVertBarXOffset, large_bar.size[1]) )
    # After cropping, we draw
    yOffset = topBarYOffset+0
    canvas.add_layer(large_bar, 0, yOffset, depth=1)
    yOffset -= top_left_red_gold_bar.size[1] - (shadow_size*2)
    canvas.add_layer(top_left_red_gold_bar, 0, yOffset+4, depth=2)
    yOffset += large_bar.size[1] + top_left_red_gold_bar.size[1] - (shadow_size*4)
    canvas.add_layer(next_red_gold_bar_below, 0, yOffset-4, depth=2)
    yOffset -= large_bar.size[1]
    unit_card = add_rounded_corners(unit_card, 20)

    # Drawing Bottom Left Horo Gold Bar
    shield_large_bar = shield_large_bar.crop( (0, 0, leftFirstVertBarXOffset, shield_large_bar.size[1]) ) # (left, top, right, bottom)
    shield_top_gold_bar = shield_top_gold_bar.crop( (0, 0, leftFirstVertBarXOffset, shield_top_gold_bar.size[1]) )
    shield_next_gold_bar = shield_next_gold_bar.crop( (0, 0, leftFirstVertBarXOffset, shield_next_gold_bar.size[1]) )
    # After cropping, we draw
    yOffset = bottomBarYOffset+0
    xtraYOffset = 7
    canvas.add_layer(shield_large_bar, 0, yOffset+xtraYOffset, depth=1)
    yOffset -= shield_top_gold_bar.size[1] - (shadow_size*2)
    canvas.add_layer(shield_top_gold_bar, 0, yOffset+4+xtraYOffset, depth=2)
    yOffset += shield_large_bar.size[1] + shield_top_gold_bar.size[1] - (shadow_size*4)
    canvas.add_layer(shield_next_gold_bar, 0, yOffset-4+xtraYOffset, depth=2)

    # Draw First Vertical Gold bar left of portrait
    xOffset = leftFirstVertBarXOffset+(shadow_size*2)
    yOffset = 0
    canvas.add_layer(large_onleft_vertical_gold_bar, xOffset, yOffset, depth=1)
    xOffset -= left_onleft_vertical_gold_bar.size[0] - (shadow_size*2)
    canvas.add_layer(left_onleft_vertical_gold_bar, xOffset, yOffset, depth=2)
    xOffset += large_onleft_vertical_gold_bar.size[0] + left_onleft_vertical_gold_bar.size[0]
    yOffset -= int(large_onleft_vertical_gold_bar.size[0]/1.75)
    canvas.add_layer(unit_portrait, xOffset-shadow_size, yOffset, depth=0)
    xOffset -= (shadow_size*4)
    canvas.add_layer(right_onleft_vertical_gold_bar, xOffset, 0, depth=2)

    # Unit Portrait Stuff
    xOffset += (shadow_size*3)
    yOffset +=  unit_portrait.size[1]
    #unit_card.paste(left_bottom_gold_corner, (xOffset, yOffset), left_bottom_gold_corner)
    canvas.add_layer(left_bottom_gold_corner, xOffset, yOffset, depth=1)
    xOffset += left_bottom_gold_corner.size[0] + (shadow_size*1)
    canvas.add_layer(right_bottom_gold_corner, xOffset, yOffset, depth=1)
    frameYOffset = -46
    canvas.add_layer(right_gold_corner, xOffset, frameYOffset, depth=1)
    xOffset -= left_bottom_gold_corner.size[0] + (shadow_size*1)
    canvas.add_layer(left_gold_corner_top, xOffset, frameYOffset, depth=1)
    canvas.add_layer(portrait_attachment_on_middleof_trim, 510, 632, depth=2)
    width, height = [int(x*0.55) for x in faction_crest.size]
    faction_crest = faction_crest.rotate(-8)
    scaled_faction_crest = faction_crest.resize((width, height))
    canvas.add_layer(scaled_faction_crest, 610, 506, depth=3)

    # Gold bars to the right of the portrait:
    left_onright_vertical_gold_bar = add_shadow(left_onright_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))
    large_onright_vertical_gold_bar = add_shadow(large_onright_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))
    right_onright_vertical_gold_bar = add_shadow(right_onright_vertical_gold_bar, shadow_size, shadow_strength, sides=('left', 'right'))
    canvas.add_layer(left_onright_vertical_gold_bar, 745, 0, depth=2)
    canvas.add_layer(large_onright_vertical_gold_bar, 745+(shadow_size*4), 0, depth=1)
    canvas.add_layer(right_onright_vertical_gold_bar, 825+(shadow_size*5), 0, depth=2)
    canvas.add_layer(skills_tan_background_for_text, 825+(shadow_size*6), 0, depth=1)

    #Foot Movement Placement
    movement_foot_image = Image.open(f"{units_folder}Movement.webp").convert('RGBA')
    movement_foot_stat_bg_image = Image.open(f"{units_folder}StatBg.webp").convert('RGBA')

    # Shield and morale stuff
    shield_top_gold_bar = next_red_gold_bar_below.copy()
    shield_large_bar = large_bar.copy()
    shield_next_gold_bar = next_red_gold_bar_below.copy()
    shield_image = Image.open(f"{units_folder}Defense.webp").convert('RGBA')
    shield_stat_bg_image = movement_foot_stat_bg_image.copy()
    morale_image = Image.open(f"{units_folder}Morale.webp").convert('RGBA')
    morale_stat_bg_image = movement_foot_stat_bg_image.copy()

    # unit type
    unit_type_image = Image.open(f"{units_folder}UnitType.{UnitType}{faction}.webp").convert('RGBA')

    canvas.add_layer(movement_foot_image, 56, 48, depth=4)
    canvas.add_layer(movement_foot_stat_bg_image, 156, 66, depth=3)

    canvas.add_layer(shield_image, 56, 595, depth=4)
    canvas.add_layer(shield_stat_bg_image, 156, 613, depth=3)
    xmore = 100
    canvas.add_layer(morale_image, 156+xmore, 595, depth=4)
    canvas.add_layer(morale_stat_bg_image, 256+xmore, 613, depth=3)
    canvas.add_layer(unit_type_image, 196, 665, depth=2)
    return canvas.render()

def split_name_string(s):
    # Split the string by comma if it exists
    if ',' in s:
        return s.split(','), True
    # Split the string if it's longer than 18 characters
    if len(s) > 18:
        # Find the middle index of the string
        middle_idx = len(s) // 2
        # Search for the nearest space character to the middle
        left_space = s.rfind(' ', 0, middle_idx)  # search space to the left of the middle
        right_space = s.find(' ', middle_idx)  # search space to the right of the middle
        # Determine which space character is closer to the middle
        if left_space == -1:  # if there's no space to the left of the middle
            split_idx = right_space
        elif right_space == -1:  # if there's no space to the right of the middle
            split_idx = left_space
        else:
            # Choose the space that's closer to the middle
            split_idx = left_space if (middle_idx - left_space) < (right_space - middle_idx) else right_space
        # Split the string at the chosen space
        return [s[:split_idx], s[split_idx+1:]], False
    # If string doesn't need splitting
    return [s], False

def BuildUnitCardWithData(unit_card, UnitData, units_folder, graphics_folder, AsoiafFonts):
    canvas = LayeredImageCanvas(unit_card.size[0], unit_card.size[1])
    canvas.add_layer(unit_card, 0, 0, depth=0)

    unit_card = canvas.render()
    draw = ImageDraw.Draw(unit_card)
    GaramondBoldFont = AsoiafFonts.get('Garamond-Bold', ImageFont.load_default())
    draw.text((183, 86), UnitData['Spd'], font=GaramondBoldFont, fill="white")
    TuffBoldFont = AsoiafFonts.get('Tuff-Bold', ImageFont.load_default()) 
    TuffBoldFontSmall = AsoiafFonts.get('Tuff-Bold-smaller', TuffBoldFont.size-10) 
    #print(UnitData)
    text_lines_list, hadAComma = split_name_string(UnitData['Name'].upper())
    if not hadAComma:
        draw_centered_text(draw, (530, 744), text_lines_list, TuffBoldFont, "white", line_padding=10)
    else:
        draw_centered_text(draw, (530, 744), [text_lines_list[0]], TuffBoldFont, "white", line_padding=10)
        draw_centered_text(draw, (530, 744 + TuffBoldFont.size ), [text_lines_list[1]], TuffBoldFontSmall, "white", line_padding=10)
    unit_card = add_rounded_corners(unit_card, 20)
    return unit_card

def main():
    # Currently, this assumes you are running it from the assets/flutter_assets folder
    assets_folder="./assets/"
    fonts_dir=f"./fonts/"
    AsoiafFonts = load_fonts(fonts_dir)
    data_folder=f"{assets_folder}data/"
    units_folder=f"{assets_folder}Units/"
    graphics_folder = f"{assets_folder}graphics"
    unit_card_output_dir = "./"
    AsoiafData = import_csvs_to_dicts(data_folder) # contains the keys: attachments,boxes,ncus,newskills,rules,special,tactics,units
    #LannisterGuardsmenUnitData = [x for x in AsoiafData['units'] if x['Name'] == "Gregor Clegane, The Mountain That Rides"][0]
    #LannisterGuardsmenUnitData = [x for x in AsoiafData['units'] if x['Name'] == "Lannister Crossbowmen"][0]
    LannisterGuardsmenUnitData = [x for x in AsoiafData['units'] if x['Name'] == "Crannogman Trackers"][0]
    #pdb.set_trace()
    unit_card = BuildUnitCardFactionBackground(LannisterGuardsmenUnitData, units_folder, graphics_folder)
    unit_card = BuildUnitCardWithData(unit_card, LannisterGuardsmenUnitData, units_folder, graphics_folder, AsoiafFonts)
    #unit_card = BuildUnitCard(LannisterGuardsmenUnitData, units_folder, AsoiafFonts, unit_card_output_dir, debug=False)
    # This is just for viewing / debugging purposes. Can click to get coordinates on image:
    unit_card_output_path = os.path.join(unit_card_output_dir, f"{LannisterGuardsmenUnitData['Id'].replace(' ', '_')}.png")
    unit_card.save(unit_card_output_path)
    root = tk.Tk()
    app = ImageEditor(root, unit_card)
    root.mainloop()


if __name__ == "__main__":
    main()
