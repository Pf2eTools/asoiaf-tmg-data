import bpy
import json


FACTIONS = [
    "martell",
    "brotherhood",
    "lannister",
    "greyjoy",
    "freefolk",
    "bolton",
    "baratheon",
    "targaryen",
    "stark",
    "nightswatch",
    "neutral"
]


def get_full_name(obj):
    name = obj.get("name")
    subname = obj.get("subname")
    uid = obj.get("id")
    if subname:
        return f"{name}-{subname}.{uid}"
    else:
        return f"{name}.{uid}"


def edit_mats(obj, image_id, faction):
    front_mat = obj.data.materials[0]
    back_mat = obj.data.materials[1]

    bpy.ops.image.open(filepath=f"{BASE_IMAGE_PATH}/{faction}/{image_id}.jpg")
    bpy.ops.image.open(filepath=f"{BASE_IMAGE_PATH}/{faction}/{image_id}b.jpg")
    front_mat.node_tree.nodes["Image Texture"].image = bpy.data.images[f"{image_id}.jpg"]
    back_mat.node_tree.nodes["Image Texture"].image = bpy.data.images[f"{image_id}b.jpg"]


def gen_card_objects():
    d = 0.25
    y = 0

    for faction in FACTIONS:
        y += d
        x = 0
        with open(f"{BASE_DATA_PATH}/{faction}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, items in data.items():
            if key == "specials" or key == "tactics":
                continue
            elif key == "units":
                obj_to_copy = bpy.data.objects[TEMPLATE_UNITS]
            else:
                obj_to_copy = bpy.data.objects[TEMPLATE_SMALL]

            for item in items:
                new_obj = obj_to_copy.copy()
                new_obj.name = get_full_name(item)
                new_obj.data = obj_to_copy.data.copy()
                new_obj.data.materials[0] = obj_to_copy.data.materials[0].copy()
                new_obj.data.materials[0].name = item.get("id") + ".front"
                new_obj.data.materials[1] = obj_to_copy.data.materials[1].copy()
                new_obj.data.materials[0].name = item.get("id") + ".back"
                edit_mats(new_obj, item.get("id"), faction)
                new_obj.location[0] = x
                new_obj.location[1] = y
                x += d
                bpy.context.collection.objects.link(new_obj)


# Create template objects. Make sure the materials for the cards are ordered front, back, side.
# This script copies template objects and edits the materials to set the card images on the Image Texture node.
TEMPLATE_UNITS = "UnitCard"
TEMPLATE_SMALL = "SmallCard"
BASE_IMAGE_PATH = "D:/Stuff/Programming/asoiaf-tmg-data/generated/en"
BASE_DATA_PATH = "D:/Stuff/Programming/asoiaf-tmg-data/data/en"

if __name__ == "__main__":
    gen_card_objects()