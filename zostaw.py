import PIL.Image
import tkinter as tk
from PIL import ImageTk
from tkinter.filedialog import askopenfilename

class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.bind('<Configure>', self.update_values)
    
    def update_values(self, *_) -> None:
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None: return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()

    def delete_previous_image(self) -> None:
        if self.image is None: return
        self.delete(self.image_id)
        self.image = self.image_id = None

    def resize_image(self) -> None:
        image_width, image_height = self.source_image.size
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        ratio = min(width_ratio, height_ratio)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)
        scaled_image = self.source_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)

    def paste_image(self) -> None:
        self.image_id = self.create_image(self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:
        if not (filename := askopenfilename()): return

        self.delete_previous_image()
        self.source_image = PIL.Image.open(filename)
        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()


class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.canvas = CanvasImage(self, relief='sunken', bd=2)
        tk.Button(self, text='Abrir imagen', comman=self.canvas.open_image).pack()
        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)


if __name__ == '__main__':
    window = Window()
    window.mainloop()