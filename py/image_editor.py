import tkinter as tk
from PIL import ImageTk


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

        overlayed = self.overlay_images(generated_image, original_image)

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
    def overlay_images(top_layer, background):
        copy = top_layer.copy().convert("RGBA")
        copy.putalpha(int(255 * 0.4))
        overlayed = background.copy().convert("RGBA")
        overlayed.alpha_composite(copy)
        return overlayed


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
