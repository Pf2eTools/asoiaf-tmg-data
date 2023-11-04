import tkinter as tk
from PIL import Image, ImageTk


class ImageEditor:
    modes = [
        "genenerated",
        "original",
        "overlayed"
    ]

    def __init__(self, generated_image, original_image):
        self.root = tk.Tk()
        self.mode = "genenerated"
        self.root.title("Image Editor")
        self.root.focus_force()

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

        self.label = tk.Label(self.root, image=self.tk_images[self.mode])
        self.label.pack()

        self.label.bind("<Button-1>", self.log_coordinates)
        self.root.bind("<Key>", self.switch_mode)
        self.root.mainloop()

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
