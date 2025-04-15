import cv2 as cv
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
import json
from const import *
from abc import ABC, abstractmethod
from pathlib import Path


class ImageLoader:
    def __init__(self, path):
        self.path = path

    def get_pil(self):
        return Image.open(self.path).convert("RGBA")

    def get_cv(self):
        img_cv = cv.imread(self.path, -1)
        _, _, channels = img_cv.shape
        # creating an alpha channel
        if channels != 4:
            img_cv = cv.cvtColor(img_cv, cv.COLOR_RGB2RGBA)

        return img_cv


class ImageSaver:
    def __init__(self, path):
        self.path = path

    def save(self, image):
        print(f"Writing image to {self.path}...")
        cv.imwrite(self.path, image)


class ImageCropper:
    def __init__(self, load_image, save_image, shape):
        self.load_image = load_image
        self.save_image = save_image
        self.shape = shape
        self.did_write = False

        self.root = None
        self.canvas = None
        self.canvas_image = None
        self.scale = 1
        self.width, self.height = 0, 0
        self.image_tk = None

    def create_ui(self):
        self.root = tk.Tk()
        self.root.title(self.load_image.path)
        self.root.focus_force()
        image = self.load_image.get_pil()
        self.scale = min(2.5, (self.root.winfo_screenwidth() - 400) / image.width, (self.root.winfo_screenheight() - 400) / image.height)
        self.width = int(image.width * self.scale)
        self.height = int(image.height * self.scale)
        self.image_tk = ImageTk.PhotoImage(image.resize((self.width, self.height)), master=self.root)

        frame_settings = tk.Frame(self.root, height=self.height, width=200)
        frame_settings.pack(side="right")

        label_text = [
            'Click+Drag to create and move area.',
            'Right click to unset the area.',
            'Press "S" to crop and save the image;',
            '"W" to exit the current job;',
            '"Q" to quit the program.'
        ]
        tk.Label(frame_settings, text="\n".join(label_text)).pack()

        # self.mode = tk.StringVar()
        # tk.Radiobutton(frame_settings,
        #                anchor="e",
        #                variable=self.mode,
        #                value=Rectangle.name,
        #                text=Rectangle.name.capitalize(),
        #                command=self.on_radio).pack()
        # tk.Radiobutton(frame_settings,
        #                anchor="e",
        #                variable=self.mode,
        #                value=Circle.name,
        #                text=Circle.name.capitalize(),
        #                command=self.on_radio).pack()
        # tk.Radiobutton(frame_settings,
        #                anchor="e",
        #                variable=self.mode,
        #                value=Square.name,
        #                text=Square.name.capitalize(),
        #                command=self.on_radio).pack()
        # self.mode.set(self.shape.name)

        self.canvas = tk.Canvas(self.root, height=self.height, width=self.width)
        self.canvas.pack(fill="both")
        self.canvas_image = self.canvas.create_image(0, 0, image=self.image_tk, anchor="nw")
        self.shape.set_scale(self.scale)
        self.shape.set_canvas(self.canvas)

        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Key>", self.on_key)
        self.root.wait_window()

    # def on_radio(self):
    #     self.shape.destroy()
    #     self.shape = Shape.from_string(self.mode.get(), {})
    #     self.shape.set_canvas(self.canvas)

    def on_click(self, evt):
        x = int(evt.x)
        y = int(evt.y)
        self.shape.draw(x, y)

    def on_right_click(self, evt):
        self.shape.destroy()

    def on_drag(self, evt):
        x = int(evt.x)
        y = int(evt.y)
        self.shape.move(x, y)

    def on_release(self, evt):
        self.shape.release()

    def on_key(self, evt):
        char = evt.char.lower()
        if char == "s":
            self.save()
            self.root.destroy()
        elif char == "w":
            self.root.destroy()
        elif char == "q" or char == "\x1b":
            raise SystemExit

    def save(self):
        cropped = self.shape.get_crop(self.load_image.get_cv())
        self.did_write = True
        self.save_image.save(cropped)

    def get_shape_coords(self):
        if not self.did_write:
            return None
        return self.shape.get_coords()


class Shape(ABC):
    def __init__(self):
        self.scale_tk = 1
        self.preview = None
        self.canvas = None
        self.released = False

    @abstractmethod
    def set_scale(self, scale):
        pass

    @abstractmethod
    def set_canvas(self, canvas):
        pass

    def destroy(self):
        if self.preview is not None:
            self.canvas.delete(self.preview)
            self.preview = None
        self.released = False

    @abstractmethod
    def draw(self, x, y):
        pass

    def move(self, x, y):
        if self.released:
            self._do_move(x, y)
        else:
            self._resize(x, y)

    @abstractmethod
    def _do_move(self, x, y):
        pass

    @abstractmethod
    def _resize(self, x, y):
        pass

    @abstractmethod
    def release(self):
        pass

    @abstractmethod
    def get_crop(self, image):
        pass

    @abstractmethod
    def get_coords(self):
        pass


class Circle(Shape):
    name = "circle"

    def __init__(self, coords):
        super().__init__()
        self.x = coords.get("x", 0)
        self.y = coords.get("y", 0)
        self.r = coords.get("r", 0)
        self.border_tk = None
        self.token_loader = ImageLoader("./assets/tokens/border.png")

    def set_scale(self, scale):
        self.scale_tk = scale
        self.x = int(self.x * scale)
        self.y = int(self.y * scale)
        self.r = int(self.r * scale)

    def set_canvas(self, canvas):
        self.canvas = canvas
        if self.r != 0:
            self.draw(self.x, self.y, self.r)
            self.release()

    def draw(self, x, y, r=10):
        if self.released:
            r = self.r
        self.x = x
        self.y = y
        self.r = r
        self.preview = self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="red")

    def _do_move(self, x, y):
        self.x = x
        self.y = y
        r = self.r
        self.canvas.coords(self.preview, x - r, y - r, x + r, y + r)

    def _resize(self, dx, dy):
        r = self.r = int(np.linalg.norm(np.array([self.x - dx, self.y - dy])))
        x, y = self.x, self.y
        self.canvas.coords(self.preview, x - r, y - r, x + r, y + r)

    def release(self):
        self.released = True
        if self.preview is not None:
            self.canvas.delete(self.preview)
            self.preview = None
        border = self.token_loader.get_pil()
        border = border.crop(border.getbbox()).resize((2 * self.r, 2 * self.r), resample=Image.LANCZOS)
        self.border_tk = ImageTk.PhotoImage(border)
        self.canvas.create_image(self.x, self.y, image=self.border_tk, anchor="c")

    def destroy(self):
        super().destroy()
        self.x = 0
        self.y = 0
        self.r = 0
        self.border_tk = None

    def get_crop(self, img):
        # cba doing this in cv
        token_pil = self.token_loader.get_pil()
        token_pil = token_pil.crop(token_pil.getbbox())
        token_cv = cv.cvtColor(np.array(token_pil), cv.COLOR_RGBA2BGRA)
        # we assume the token is a square image below, so pad it here
        diff = np.abs(token_cv.shape[0] - token_cv.shape[1])
        pad_top, pad_bot = (diff // 2 + diff % 2, diff // 2) if token_cv.shape[0] < token_cv.shape[1] else (0, 0)
        pad_right, pad_left = (diff // 2 + diff % 2, diff // 2) if token_cv.shape[0] > token_cv.shape[1] else (0, 0)
        token_cv = cv.copyMakeBorder(token_cv, pad_top, pad_bot, pad_left, pad_right, cv.BORDER_CONSTANT, value=(0, 0, 0, 0))

        # resize image
        out_size = token_cv.shape[0] - token_cv.shape[0] % 2
        r = out_size // 2
        img = cv.copyMakeBorder(img, r, r, r, r, cv.BORDER_CONSTANT, value=(0, 0, 0, 0))
        scale = out_size / ((self.r / self.scale_tk) * 2)
        resized = cv.resize(img, (int(scale * img.shape[1]), int(scale * img.shape[0])), interpolation=cv.INTER_AREA)
        center = [int((self.y / self.scale_tk + r) * scale), int((self.x / self.scale_tk + r) * scale)]

        # crop images to size
        cropped_img = resized[center[0] - r:center[0] + r, center[1] - r:center[1] + r]
        cropped_token = token_cv[out_size - 2 * r:out_size, out_size - 2 * r:out_size]

        # add the background
        bg = TOKEN_BG
        if bg is not None:
            if type(bg) is tuple:
                background = np.zeros((out_size, out_size, 4), np.uint8)
                background[:] = (bg[2], bg[1], bg[0], 255)
            else:
                background = cv.imread(bg, -1)
                if background.shape[2] != 4:
                    background = cv.cvtColor(background, cv.COLOR_RGB2RGBA)
            cropped_img = alpha_composite(cropped_img, background, out_size)

        # mask original image
        mask = np.zeros((out_size, out_size), np.uint8)
        cv.circle(mask, (r, r), r - 2, (255, 255, 255), -1)
        masked = cv.bitwise_and(cropped_img, cropped_img, mask=mask)

        # add token border to image
        out = alpha_composite(cropped_token, masked, out_size)
        return out

    def get_coords(self):
        return {
            "x": int(self.x / self.scale_tk),
            "y": int(self.y / self.scale_tk),
            "r": int(self.r / self.scale_tk),
        }


# https://en.wikipedia.org/wiki/Alpha_compositing#Description
def alpha_composite(foreground, background, size):
    alpha_fg = foreground[:, :, 3] / 255.0
    alpha_bg = background[:, :, 3] / 255.0
    alpha0 = alpha_fg + alpha_bg * (1.0 - alpha_fg)
    added = np.zeros((size, size, 4), np.uint8)
    for c in range(0, 3):
        added[:, :, c] = (alpha_fg * foreground[:, :, c] + alpha_bg * background[:, :, c] * (1.0 - alpha_fg)) / alpha0
    added[:, :, 3] = alpha0[:, :] * 255
    return added


class Rectangle(Shape):
    name = "rectangle"

    def __init__(self, coords):
        super().__init__()
        self.x = coords.get("x", 0)
        self.y = coords.get("y", 0)
        self.w = w = coords.get("w", 0)
        self.h = h = coords.get("h", 0)
        self.aspect_ratio = coords.get("aspect", 0 if h == 0 else w / h)

    def set_scale(self, scale):
        self.scale_tk = scale
        self.x = int(self.x * scale)
        self.y = int(self.y * scale)
        self.w = int(self.w * scale)
        self.h = int(self.h * scale)

    def set_canvas(self, canvas):
        self.canvas = canvas
        if self.w != 0 and self.h != 0:
            self.draw(self.x, self.y, self.w, self.h)
            self.release()

    def draw(self, x, y, w=10, h=10):
        if self.released:
            return
        self.x = x
        self.y = y
        self.w = w
        self.h = h = h if self.aspect_ratio == 0 else int(w / self.aspect_ratio)
        self.preview = self.canvas.create_rectangle(x, y, x + w, y + h, outline="red")

    def _do_move(self, x, y):
        w = self.w
        h = self.h
        x = self.x = x - w // 2
        y = self.y = y - h // 2
        self.canvas.coords(self.preview, x, y, x + w, y + h)

    def _resize(self, dx, dy):
        w = self.w = dx - self.x
        h = self.h = dy - self.y if self.aspect_ratio == 0 else int((dx - self.x) / self.aspect_ratio)
        x = self.x
        y = self.y
        self.canvas.coords(self.preview, x, y, x + w, y + h)

    def release(self):
        # FIXME: fix xywh if dragged from lower right corner
        self.released = True

    def destroy(self):
        super().destroy()
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def get_crop(self, img):
        x = int(self.x / self.scale_tk)
        y = int(self.y / self.scale_tk)
        h = int(self.h / self.scale_tk)
        w = int(self.w / self.scale_tk)
        cropped_img = img[y:y + h, x:x + w]
        return cropped_img

    def get_coords(self):
        return {
            "x": int(self.x / self.scale_tk),
            "y": int(self.y / self.scale_tk),
            "w": int(self.w / self.scale_tk),
            "h": int(self.h / self.scale_tk),
        }


class Square(Rectangle):
    name = "square"

    def __init__(self, coords):
        x = coords.get("x", 0)
        y = coords.get("y", 0)
        a = coords.get("a", 0)
        super().__init__({"x": x, "y": y, "w": a, "h": a, "aspect": 1})

    def get_coords(self):
        return {
            "x": int(self.x / self.scale_tk),
            "y": int(self.y / self.scale_tk),
            "a": int(self.w / self.scale_tk),
        }

    def get_crop(self, img):
        x = int(self.x / self.scale_tk)
        y = int(self.y / self.scale_tk)
        h = int(self.h / self.scale_tk)
        w = int(self.w / self.scale_tk)
        cropped_img = img[y:y + h, x:x + w]
        normalized = cv.resize(cropped_img, (273, 273), interpolation=cv.INTER_AREA)
        return normalized


def generate_portraits(data, coords_data, outpath=f"./portraits/round"):
    Path(outpath).mkdir(parents=True, exist_ok=True)

    def get_default_coords(data_type, obj):
        if data_type == "units":
            return {"x": 360, "y": 175, "r": 175}
        elif data_type == "attachments" and obj.get("statistics", {}).get("commander"):
            return {"x": 300, "y": 150, "r": 140}
        elif data_type == "attachments":
            return {"x": 240, "y": 200, "r": 180}
        elif data_type == "ncus":
            return {"x": 280, "y": 140, "r": 135}

        return {"x": 0, "y": 0, "r": 0}

    for key in ["units", "attachments", "ncus"]:
        for data_object in data[key]:
            item_id = data_object["id"]
            coords_exist = coords_data.get(item_id, {}).get("round") is not None
            if MODE == MODE_NEW and coords_exist:
                continue
            default_coords = get_default_coords(key, data_object)
            coords = coords_data.get(item_id, {}).get("round", default_coords)
            loader = ImageLoader(f"./assets/warcouncil/{key}/{item_id}b.png")
            saver = ImageSaver(f"{outpath}/{item_id}.png")
            shape = Circle(coords)
            cropper = ImageCropper(loader, saver, shape)
            if MODE == MODE_ALL or not coords_exist:
                cropper.create_ui()
            elif MODE == MODE_REWRITE:
                cropper.save()
            if cropper.get_shape_coords() is not None:
                coords_data[item_id] = coords_data.get(item_id, {})
                coords_data[item_id]["round"] = cropper.get_shape_coords()


def generate_portraits_square(data, coords_data, outpath=f"./portraits/square"):
    Path(outpath).mkdir(parents=True, exist_ok=True)

    def get_default_coords(data_type, obj):
        if data_type == "units":
            return {"x": 360, "y": 175, "r": 175}
        elif data_type == "attachments" and obj.get("statistics", {}).get("commander"):
            return {"x": 300, "y": 150, "r": 140}
        elif data_type == "attachments":
            return {"x": 240, "y": 200, "r": 180}
        elif data_type == "ncus":
            return {"x": 280, "y": 140, "r": 135}

        return {"x": 0, "y": 0, "r": 0}

    for key in ["units", "attachments", "ncus"]:
        for data_object in data[key]:
            item_id = data_object["id"]
            coords = coords_data.get(item_id, {}).get("square")
            coords_exist = coords is not None
            if MODE == MODE_NEW and coords_exist:
                continue
            default_coords = get_default_coords(key, data_object)
            if coords is None:
                coords = {k: v for k, v in coords_data.get(item_id, {}).get("portrait", default_coords).items()}
                coords["a"] = coords["r"] * 2
                coords["x"] = max(5, coords["x"] - coords["r"])
                coords["y"] = max(5, coords["y"] - coords["r"])
            loader = ImageLoader(f"./assets/warcouncil/{key}/{item_id}b.png")
            saver = ImageSaver(f"{outpath}/{item_id}.jpg")
            shape = Square(coords)
            cropper = ImageCropper(loader, saver, shape)
            if MODE == MODE_ALL or not coords_exist:
                cropper.create_ui()
            elif MODE == MODE_REWRITE:
                cropper.save()
            if cropper.get_shape_coords() is not None:
                coords_data[item_id] = coords_data.get(item_id, {})
                coords_data[item_id]["square"] = cropper.get_shape_coords()


def generate_standees(data, coords_data, outpath=f"./portraits/standees"):
    Path(outpath).mkdir(parents=True, exist_ok=True)
    for key in ["units", "attachments", "ncus"]:
        if key == "units":
            default_portrait = {"x": 200, "y": 30, "w": 540, "h": 770}
        elif key == "attachments":
            default_portrait = {"x": 90, "y": 15, "w": 535, "h": 763}
        else:
            default_portrait = {"x": 139, "y": 10, "w": 317, "h": 454}

        for data_object in data[key]:
            item_id = data_object["id"]
            coords_exist = coords_data.get(item_id, {}).get("standee") is not None
            if MODE == MODE_NEW and coords_exist:
                continue
            loader = ImageLoader(f"./assets/warcouncil/{key}/{item_id}b.png")
            saver = ImageSaver(f"{outpath}/{item_id}.jpg")
            portrait_coords = coords_data.get(item_id, {}).get("standee", default_portrait)
            shape = Rectangle(portrait_coords)
            cropper = ImageCropper(loader, saver, shape)
            if MODE == MODE_ALL or not coords_exist:
                cropper.create_ui()
            elif MODE == MODE_REWRITE:
                cropper.save()
            if cropper.get_shape_coords() is not None:
                coords_data[item_id] = coords_data.get(item_id, {})
                coords_data[item_id]["standee"] = cropper.get_shape_coords()


def main():
    portraits_path = f"./portraits/portraits.json"
    with open(portraits_path, encoding="utf-8") as pd:
        coords_data = json.load(pd)

    for faction in FACTIONS:
        full_path = f"{DATA_PATH}/en/{faction}.json"
        with open(full_path, encoding="utf-8") as json_data:
            data = json.load(json_data)

        generate_portraits(data, coords_data)
        generate_portraits_square(data, coords_data)
        generate_standees(data, coords_data)

    with open(portraits_path, "w", encoding="utf-8") as pd:
        json.dump(coords_data, pd, indent=4)


# CONFIG ###################################################################################################################################
TOKEN_BG = None                                            # Uncomment this line for transparent backgrounds
# TOKEN_BG = (94, 0, 0)                                      # Uncomment this line for solid color (R,G,B) backgrounds

# if data: write without ui
MODE_REWRITE = "rewrite"
# if data: skip
MODE_NEW = "new"
# if data: ui
MODE_ALL = "all"
# if not data: ui
# (default behavior)

MODE = MODE_NEW
############################################################################################################################################

if __name__ == "__main__":
    main()
