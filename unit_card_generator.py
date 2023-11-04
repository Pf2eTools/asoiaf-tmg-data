#!/usr/bin/env python
import csv
import os
import tkinter as tk
import re
import pdb
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter, ImageOps
import sys

#pip install pillow

#ALLICONS = {
#CROWN
#HORSE
#LETTER
#LONGRANGE
#MONEY
#MOVEMENT
#OASIS
#SWORDS
#UNDYING
#WOUND
#}

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
            fonts[font_file.split(".")[0]+'-50'] = ImageFont.truetype(font_path, size=50)
            fonts[font_file.split(".")[0]] = ImageFont.truetype(font_path, size=44)
            fonts[font_file.split(".")[0]+'-40'] = ImageFont.truetype(font_path, size=40)
            fonts[font_file.split(".")[0]+'-35'] = ImageFont.truetype(font_path, size=35)
            fonts[font_file.split(".")[0]+'-30'] = ImageFont.truetype(font_path, size=30)
            fonts[font_file.split(".")[0]+'-25'] = ImageFont.truetype(font_path, size=25)
            print(f"Successfully loaded font: {font_file}")
        except Exception as e:
            print(f"Failed to load font {font_file}: {str(e)}")
    return fonts

def import_csvs_to_dicts(assets_data_folder):
    csv_files = [f for f in os.listdir(assets_data_folder) if f.endswith('.csv')]
    all_data = {}
    for csv_file in csv_files:
        file_path = os.path.join(assets_data_folder, csv_file)
        with open(file_path, mode='r', encoding='utf-8') as f:
            # Read the first line to get the headers
            original_headers = next(csv.reader(f))
            # Replace empty headers with incremental numbers as strings
            headers = [header if header else str(i) for i, header in enumerate(original_headers, 1)]
            # Go back to the start of the file before reading the rest
            f.seek(0)
            # Create a DictReader with the modified headers
            reader = csv.DictReader(f, fieldnames=headers)
            # Skip the original header row, since we already processed it
            next(reader)
            # Convert the content of the CSV file to a list of dictionaries
            data = [row for row in reader]
        all_data[csv_file.split('.')[0]] = data
    return all_data

# I use this so I can load the unit card and get x + y on the card so I can more easily get coordinates of images on click

class ImageEditor:
    modes = [
        "genenerated",
        "original",
        # "overlayed"
    ]

    def __init__(self, master, generated_image, original_image):
        self.master = master
        self.mode = "genenerated"
        master.title("Image Editor")

        cpy_generated = generated_image.copy()
        cpy_generated.putalpha(int(255 * 0.4))
        cpy_original = original_image.copy()
        cpy_original.putalpha(255)
        overlayed = Image.new('RGBA', cpy_original.size)
        overlayed.paste(cpy_original, mask=cpy_original)
        overlayed.paste(cpy_generated, mask=cpy_generated)

        self.tk_images = {
            "genenerated": ImageTk.PhotoImage(generated_image),
            "original": ImageTk.PhotoImage(original_image),
            "overlayed": ImageTk.PhotoImage(overlayed)
        }

        self.label = tk.Label(master, image=self.tk_images[self.mode])
        self.label.pack()

        self.label.bind("<Button-1>", self.log_coordinates)
        self.master.bind("<Key>", self.switch_mode)

    @staticmethod
    def log_coordinates(event):
        x = event.x
        y = event.y
        print(f"Clicked at: {x}, {y}")

    def switch_mode(self, event):
        char = event.char.lower()
        if char == "s":
            ix = self.modes.index(self.mode)
            self.mode = self.modes[(ix + 1) % len(self.modes)]
            self.label.configure(image=self.tk_images[self.mode])


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

def split_on_center_space(text):
    # If the length of the text is less than 10 or there's no space, return the text in a single-item list
    if len(text) < 10 or ' ' not in text:
        return [text]

    # Find the middle index of the string
    middle = len(text) // 2
    left_index = text.rfind(' ', 0, middle)  # Search for space going left from the middle
    right_index = text.find(' ', middle)     # Search for space going right from the middle

    # Determine the closest space to the middle to use as the split point
    # If no space to the left, use the right one; if both exist, choose the closest
    if left_index == -1 or (right_index != -1 and (middle - left_index) > (right_index - middle)):
        split_index = right_index
    else:
        split_index = left_index

    # Split the string into two parts
    part1 = text[:split_index]
    part2 = text[split_index+1:]  # +1 to exclude the space itself

    # Return the parts in a list
    return [part1, part2]

def draw_circle(draw, center, radius, fill):
    """Draws a circle on the ImageDraw object"""
    left_up_point = (center[0] - radius, center[1] - radius)
    right_down_point = (center[0] + radius, center[1] + radius)
    draw.ellipse([left_up_point, right_down_point], fill=fill)

def draw_icon(image, icon, x_current, y_current, max_height):
    # Scale the icon to fit the max_height while maintaining aspect ratio
    aspect_ratio = icon.width / icon.height
    scaled_height = max_height
    scaled_width = int(aspect_ratio * scaled_height)

    # Resize the icon using LANCZOS resampling
    icon = icon.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # Get the coordinates for the icon's top-left corner
    icon_top_left = (x_current, y_current - (scaled_height // 2))  # Center vertically with the text

    # Paste the icon onto the image, using the alpha channel of the icon as the mask
    image.paste(icon, icon_top_left, mask=icon)

    # Return the new x position, which is to the right of the icon we just drew
    return x_current + scaled_width

def draw_markdown_text(image, bold_font, bold_font2, regular_font, title, text_body, color, y_top, x_left, x_right, graphics_folder, padding=2):
    # Initialize the drawing context
    draw = ImageDraw.Draw(image)
    # Draw the title using the bold font
    draw.text((x_left, y_top), title.strip(), font=bold_font, fill=color)
    title_height = bold_font.getmask(title.strip()).getbbox()[3]  # Bottom of the title bbox
    # Update the y-coordinate for the text body
    y_current = y_top + title_height + int(padding * 2)
    # Define the radius of the bullet point
    bullet_radius = 3  # Radius of the bullet point circle
    # Get the height of the regular font which we will use as a line height
    max_height = regular_font.getmask('Hy').getbbox()[3]  # Use 'Hy' to account for descenders and ascenders
    # Split the text body by lines
    lines = [x.strip() for x in text_body.split('\n')]
    for line in lines:
        # Check for bullet points at the start of the line
        if line.startswith('•'):
            # Draw the bullet circle and adjust x_current
            bullet_center = (x_left + bullet_radius, (y_current + bullet_radius + max_height / 2)-5)
            draw_circle(draw, bullet_center, bullet_radius, fill="black")
            x_current = x_left + bullet_radius * 2 + padding
            line = line[1:].lstrip()  # Remove the bullet point and any leading whitespace
        else:
            x_current = x_left
        # Check for markdown bold syntax and split if necessary
        parts = line.split('**')
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This part is bold
                font = bold_font2
            else:
                # This part is regular
                font = regular_font
            # Break the part into words to check for word wrapping
            words = part.split(' ')
            for word in words:
                if '[' in word and ']' in word:
                    # Replace the [STRING] with an icon
                    icon_key = word.split('[')[1].split(']')[0]
                    word = word.split('[')[0]
                    word_bbox = draw.textbbox((x_current, y_current), word, font=font)
                    word_width = word_bbox[2] - word_bbox[0]
                    if x_current + word_width > x_right:
                        # If the word exceeds the line, move to the next line
                        x_current = x_left
                        y_current += max_height + padding
                    # Draw the word
                    draw.text((x_current, y_current), word, font=font, fill="black")
                    x_current += word_width
                    icon = Image.open(f"{graphics_folder}/{icon_key}.png").convert('RGBA')
                    if icon:
                        x_current = draw_icon(image, icon, x_current, y_current+14, max_height+ 18)
                        continue  # Skip the rest of the loop and don't draw this word as text
                word += ' '  # Add space after each word for separation
                word_bbox = draw.textbbox((x_current, y_current), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]
                if x_current + word_width > x_right:
                    # If the word exceeds the line, move to the next line
                    x_current = x_left
                    y_current += max_height + padding
                # Draw the word
                draw.text((x_current, y_current), word, font=font, fill="black")
                x_current += word_width
        # After a line is processed, move to the next line
        y_current += max_height + padding
    return image, y_current

def get_faction_colour(faction):
    faction_colours = {
        "martell": "#9e4c00",
        "neutral": "#3e2a19",
        "nightswatch": "#302a28",
        "stark": "#3b6680",
        "targaryen": "#530818",
        "baratheon": "#904523",
        "bolton": "#7a312b",
        "freefolk": "#8da884",
        "greyjoy": "#10363b",
        "lannister": "#9d1323",
    }
    faction = re.sub(r"[^a-z]", "", faction.lower())
    return faction_colours.get(faction) or "#7FDBFF"

def BuildUnitCardWithData(unit_card, UnitData, units_folder, graphics_folder, AsoiafFonts, AsoiafData):
    canvas = LayeredImageCanvas(unit_card.size[0], unit_card.size[1])
    canvas.add_layer(unit_card, 0, 0, depth=0)
    faction = UnitData['Faction']
    FactionColor = get_faction_colour(faction)
    ArmyAttackAndAbilitiesBorderColor = "Gold"
    ArmyAttackAndAbilitiesBorderColors = {
        "Neutral":"Silver",
        "Night's Watch":"Gold",
        "Stark":"Gold",
        "Targaryen":"Gold",
        "Baratheon":"Silver",
        "Bolton":"Gold",
        "Free Folk":"Gold",
        "Greyjoy":"Gold",
        "Martell":"Gold",
        "Lannister":"Silver",
    }
    if faction in ArmyAttackAndAbilitiesBorderColors:
        ArmyAttackAndAbilitiesBorderColor = ArmyAttackAndAbilitiesBorderColors[faction]
    def attackType(atkstring):
        atktype = "Melee"
        atkrange = False
        if atkstring.startswith("[RL]"):
            atktype = "Ranged"
            atkrange = "Long"
        elif atkstring.startswith("[R]"):
            atktype = "Ranged"
        elif atkstring.startswith("[RS]"):
            atktype = "Ranged"
            atkrange = "Short"
        return atktype, atkrange, atkstring.split(']')[1]
    
    def MakeAttackBar(atkdata, atk_ranks, tohit, xoffset=0, yoffset=0):
        atktype, atkrange, atkText = attackType(atkdata)
        silver_attack_type_sword = Image.open(f"{units_folder}AttackTypeBg{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
        silver_attack_type_border = Image.open(f"{units_folder}AttackType.{atktype}{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
        width, height = [int(x*1.1) for x in silver_attack_type_border.size]
        silver_attack_type_border = silver_attack_type_border.resize((width, height))
        silver_attack_tan_background = Image.open(f"{units_folder}AttackBg{ArmyAttackAndAbilitiesBorderColor}.webp").convert('RGBA')
        silver_attack_dice_background = Image.open(f"{units_folder}DiceBg.webp").convert('RGBA')
        atk_stat_bg_image = Image.open(f"{units_folder}StatBg.webp").convert('RGBA')
        atkColor = "#001a53"
        if atkrange:
            atkColor = "#a71208" # dark red
            range_bg_image = Image.open(f"{graphics_folder}/Range{atkrange}{ArmyAttackAndAbilitiesBorderColor}.png").convert('RGBA')
            canvas.add_layer(range_bg_image, xoffset+90, yoffset+210, depth=4)
        #silver_attack_tan_background
        GBFont = AsoiafFonts.get('Tuff-Italic-30', ImageFont.load_default())
        text_lines_list = split_on_center_space(atkText.upper())
        draw = ImageDraw.Draw(silver_attack_tan_background)
        x,y = [int(x/2) for x in silver_attack_tan_background.size]
        draw_centered_text(draw, (x+10, y - 12), text_lines_list, GBFont, atkColor, line_padding=4)
        #draw.text((17, 17), atkText, font=GBFont, fill=atkColor)
        canvas.add_layer(silver_attack_tan_background, xoffset+60, yoffset+220, depth=0)
        canvas.add_layer(silver_attack_dice_background, xoffset+100, yoffset+293, depth=2)
        draw = ImageDraw.Draw(atk_stat_bg_image)
        GBFont = AsoiafFonts.get('Garamond-Bold',ImageFont.load_default())
        draw.text((17, 17), tohit, font=GBFont, fill="white")
        canvas.add_layer(atk_stat_bg_image, xoffset+83, yoffset+280, depth=3)
        canvas.add_layer(silver_attack_type_border, xoffset+8, yoffset+210, depth=2)
        canvas.add_layer(silver_attack_type_sword, xoffset+20, yoffset+220, depth=1)
        colors = [(74,124,41,240),(231,144,14,240),(207,10,10,240)]
        yoffset += 10
        xoffset += 65
        #Garamond-Bold
        GBSmallFont = AsoiafFonts.get('Garamond-Bold-35',ImageFont.load_default())
        for i in range(len(atk_ranks)):
            #  Image.new('RGBA', [160, 40], (255, 255, 255, 0))
            img = Image.new("RGBA", (34, 34), colors[i])
            draw = ImageDraw.Draw(img)
            draw.text((8, 1), atk_ranks[i], font=GBSmallFont, fill="white")
            canvas.add_layer( add_rounded_corners( img , 4) , xoffset+100, yoffset+293, depth=3)
            xoffset += 42
    if 'Attack 1' in UnitData and UnitData['Attack 1']:
        atk1 = UnitData['Attack 1']
        xoffset = 40
        yoffset = 0
        tohit = UnitData['8']
        atk_ranks = UnitData['9'].split('.')
        MakeAttackBar(atk1, atk_ranks, tohit, xoffset=xoffset, yoffset=yoffset)
    if 'Attack 2' in UnitData and UnitData['Attack 2']:
        atk2 = UnitData['Attack 2']
        xoffset = 40
        yoffset = 200
        tohit = UnitData['11']
        atk_ranks = UnitData['12'].split('.')
        MakeAttackBar(atk2, atk_ranks, tohit, xoffset=xoffset, yoffset=yoffset)
    # AsoiafData
    SkillBottom = Image.open(f"{units_folder}SkillBottom{faction}.webp").convert('RGBA')
    SkillTop = SkillBottom.copy().transpose(Image.FLIP_TOP_BOTTOM)
    SkillDivider = Image.open(f"{units_folder}Divider{faction}.webp").convert('RGBA')
    yAbilityOffset = 35
    dividerOffset = 15
    SkillBarsOffset = 860
    canvas.add_layer( SkillTop , SkillBarsOffset-5, yAbilityOffset - SkillTop.size[1], depth=3)
    unit_card = canvas.render()
    yAbilityOffset += dividerOffset
    if 'Abilities' in UnitData and UnitData['Abilities']:
        all_abilities = [x.strip() for x in UnitData['Abilities'].split('/')]
        for index in range(len(all_abilities)):
            ability = all_abilities[index]
            SkillType = "Order"
            #if not ability.startswith(f"{SkillType}:"):
            # {'Name': 'Order: Hidden Traps', 'Description': '**When an unengaged enemy in Long Range performs any Action, before resolving that Action:**\nChoose 1:\n• That enemy suffers 1 Hit, +1 Hit for each of its remaining ranks.\n• That Enemy suffers -1[MOVEMENT] until the end of the Turn.', 'Icons': '', 'Version': '2021-S01'}
            skilldata = [x for x in AsoiafData['newskills'] if x['Name'] == ability][0]
            GBFont = AsoiafFonts.get('Tuff-Bold-35',ImageFont.load_default())
            TN = AsoiafFonts.get('Tuff-Bold-35',ImageFont.load_default())
            TN30 = AsoiafFonts.get('Tuff-Normal-30',ImageFont.load_default())
            starty = yAbilityOffset+0
            unit_card, yAbilityOffset = draw_markdown_text(unit_card, GBFont, TN, TN30, ability.upper(), skilldata['Description'], FactionColor, yAbilityOffset, 885, 1400, graphics_folder, padding=10)
            midy = starty + int((yAbilityOffset-starty) / 2 )
            if 'Icons' in skilldata and skilldata['Icons']:
                pass
                #unit_card.paste(SkillBottom, (SkillBarsOffset, midy), SkillBottom)
                #unit_card.paste(SkillBottom, (SkillBarsOffset, midy), SkillBottom)
                #└─$ ls -lah ./assets/graphics/Icon* | awk '{print $9}'
                #./assets/graphics/IconCard.png
                #./assets/graphics/IconCheck.png
                #./assets/graphics/IconCrown.png
                #./assets/graphics/IconDefense.png
                #./assets/graphics/IconEdit.png
                #./assets/graphics/IconExclamation.png
                #./assets/graphics/IconEye.png
                #./assets/graphics/IconFaith.png
                #./assets/graphics/IconFire.png
                #./assets/graphics/IconMelee.png
                #./assets/graphics/IconMorale.png
                #./assets/graphics/IconMovement.png
                #./assets/graphics/IconOrder.png
                #./assets/graphics/IconPen.png
                #./assets/graphics/IconPillage.png
                #./assets/graphics/IconQuestion.png
                #./assets/graphics/IconRanged.png
                #./assets/graphics/IconShare.png
                #./assets/graphics/IconVenom.png
                #./assets/graphics/IconWound.png
                #"F" Faith
                #"Fire" Fire 
                #"M" Melee
                #"Morale5" Moral and a stat bar with 5+ in it
                #"M,R" Melee, Ranges
                #"M,V" Melee, Venom
                #"M,W" Melee, Wound
                #null # No icon
                #"P" # Pillage
                #"R"    # Ranged
                #"R,M" Range, Melee
                #"R,W" Ranged, Wounds
                #"V,M" Venom, Melee
                #"W" Wounds
                #"W,M" Wounds melee
            if index < len(all_abilities)-1:
                div = SkillDivider.copy()
                unit_card.paste(div, (SkillBarsOffset - 52, yAbilityOffset), div)
                yAbilityOffset += div.size[1]
                yAbilityOffset += dividerOffset
    unit_card.paste(SkillBottom, (SkillBarsOffset, yAbilityOffset), SkillBottom)
    # pdb.set_trace()
    # {'Faction': 'Stark', 'Name': 'Crannogman Trackers', 'Character': '', 'Cost': '5', 'Type': 'Infantry', 'Spd': '6', 'Attack 1': '[RS]Crannog Bow', '8': '4+', '9': '7.6.4', 'Attack 2': "[M]Tracker's Blade", '11': '4+', '12': '6.4.3', 'Def': '6+', 'Moral': '7+', 'Abilities': 'Order: Hidden Traps /\nOrder: Mark Target', 
    #SkillFaithSilver.webp
    #SkillFireSilver.webp
    #SkillOrderGold.webp
    #SkillOrderSilver.webp
    #SkillPillageGold.webp
    #SkillPillageSilver.webp
    #SkillVenomGold.webp
    #SkillWoundsGold.webp
    #SkillWoundsSilver.webp
    
    # Retrieve font text
    # Tuff-Italic appears to be the 2021 numbering on left side of card and for the attack name (Long Sword etc...)
    # Tuff-Bold appears to be for title of abilities (in red) and keywords (in black)
    # Tuff-Normal for all other ability text
    draw = ImageDraw.Draw(unit_card)
    GaramondBoldFont = AsoiafFonts.get('Garamond-Bold', ImageFont.load_default())
    draw.text((183, 86), UnitData['Spd'], font=GaramondBoldFont, fill="white")
    draw.text((175, 630), UnitData['Def'], font=GaramondBoldFont, fill="white")
    draw.text((375, 630), UnitData['Moral'], font=GaramondBoldFont, fill="white")
    # Version Text:
    # Create an image for the text
    text_image = Image.new('RGBA', [160, 40], (255, 255, 255, 0))  # transparent background
    text_draw = ImageDraw.Draw(text_image)
    # Draw the text onto this image (consider using textsize to determine size dynamically)
    VersionFont = AsoiafFonts.get('Tuff-Italic-25', ImageFont.load_default())
    text_draw.text((0, 0), UnitData['Version'], font=VersionFont, fill="white")
    # Rotate the text image
    rotated_text_image = text_image.rotate(90, expand=1)
    # Paste the rotated text image onto your main image (consider using the alpha channel for proper transparency)
    unit_card.paste(rotated_text_image, (rotated_text_image.width - 10, unit_card.size[1] - rotated_text_image.height - 20), rotated_text_image)
    # "Abilities"
    # "Attack 1"
    # "Attack 2"
    TuffBoldFont = AsoiafFonts.get('Tuff-Bold-50', ImageFont.load_default()) 
    TuffBoldFontSmall = AsoiafFonts.get('Tuff-Bold-25', ImageFont.load_default()) 
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
    tactics_folder=f"{assets_folder}Tactics/"
    attachments_folder=f"{assets_folder}Attachments/"
    graphics_folder = f"{assets_folder}graphics"
    UnitCardsOutputDir  = "./unitscards/"
    if not os.path.exists(UnitCardsOutputDir):
        os.mkdir(UnitCardsOutputDir)
    AsoiafData = import_csvs_to_dicts(data_folder) # contains the keys: attachments,boxes,ncus,newskills,rules,special,tactics,units
    #SelectedUnitCardData = [x for x in AsoiafData['units'] if x['Name'] == "Gregor Clegane, The Mountain That Rides"][0]
    #SelectedUnitCardData = [x for x in AsoiafData['units'] if x['Name'] == "Lannister Crossbowmen"][0]
    SelectedUnitCardData = [x for x in AsoiafData['units'] if x['Name'] == "Crannogman Trackers"][0]
    unit_card = BuildUnitCardFactionBackground(SelectedUnitCardData, units_folder, graphics_folder)
    unit_card = BuildUnitCardWithData(unit_card, SelectedUnitCardData, units_folder, graphics_folder, AsoiafFonts, AsoiafData)
    #pdb.set_trace()
    # This is just for viewing / debugging purposes. Can click to get coordinates on image:
    unit_card_output_path = os.path.join(UnitCardsOutputDir, f"{SelectedUnitCardData['Id'].replace(' ', '_')}.png")
    unit_card.save(unit_card_output_path)
    # If You Want to View the Card AND click debug to find positioning uncommont these lines:
    root = tk.Tk()
    app = ImageEditor(root, unit_card, unit_card)
    root.mainloop()


if __name__ == "__main__":
    main()
