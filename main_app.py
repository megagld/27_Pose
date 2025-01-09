import PIL.Image
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from PIL import ImageTk
import classes

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

    def print_size(self) -> None:
        if self.image is None: return
        print('x'*10)
        print('image_size'+str(self.source_image.size))
        print('self.size :'+str(self.width)+"x"+str(self.height))
        print('x'*12)

    def paste_image(self) -> None:
        self.image_id = self.create_image(self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:
        # if not (filename := askopenfilename()): return

        self.delete_previous_image()

        self.master.master.clip.display_frame(self.master.master.frame_to_display,
                                              self.master.master.draws_states)
        self.source_image = self.master.master.clip.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()

class Frame_right(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.width = self.winfo_width()

        self.scale_range = self.master.clip.frames_amount-1

        self.var = None

        self.canvas = CanvasImage(self, relief='sunken', bd=2)
        tk.Button(self, text='ładuj obraz', comman=self.canvas.open_image).pack()
        tk.Button(self, text='canva size', comman=self.canvas.print_size).pack()
        tk.Button(self, text='frame size', comman=self.print_size).pack()
        tk.Button(self, text='frame count +', comman=self.frame_cnt_forward).pack()
        tk.Button(self, text='frame count -', comman=self.frame_cnt_back).pack()
        tk.Button(self, text='make clip', comman=self.make_clip).pack()

        self.scale=ttk.Scale(self, variable = self.var, orient='horizontal', to=self.scale_range, command=self.update_view)

        self.scale.pack(side="top", fill="x", expand=False)

        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)

    def update_view(self,x) -> None:
        self.master.frame_to_display=int(float(x))
        self.canvas.open_image()

    def print_size(self) -> None:       
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        print('x'*10)
        print('self.size :'+str(self.width)+"x"+str(self.height))
        print('x'*12)
        print('ttttttttttttttttt')
        print(self.master.draws_states.main_frame_draw_state)

    def frame_cnt_forward(self):
        self.master.frame_to_display+=1
        self.master.frame_to_display=min(self.master.frame_to_display, self.scale_range)
        self.canvas.open_image()
        self.scale.set(self.master.frame_to_display)

    def frame_cnt_back(self):
        self.master.frame_to_display-=1
        self.master.frame_to_display=max(0, self.master.frame_to_display)
        self.canvas.open_image()
        self.scale.set(self.master.frame_to_display)

    def make_clip(self):
        self.master.clip.make_video_clip()

class Frame_left(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.create_widgets()

    def create_widgets(self): 

        # obiekt zestawiający dane z lewej ramki - teksty do wyświetlenia i checkboxy oraz ich stan
        self.left_frame_widgets     = classes.Frame_widgets()
        self.labels                 = self.left_frame_widgets.labels_to_display

        self.checkboxes_variables   = {}

        # rysowanie checkboxów z opisami. Checkboxy powstają na podstawie 
        # labeli i są zestawiane na podstawie ich tekstu. Key = tekst labela
       
        for label in self.labels:
            # dostosowuje nazwę do wyświetlenia
            text_to_display = label.replace('_draw_state', '').replace('_', ' ').capitalize()

            if label!='':
                self.checkboxes_variables[label]  = tk.IntVar()
                ttk.Checkbutton(self, 
                                text=text_to_display,
                                bootstyle="success, round-toggle",
                                variable = self.checkboxes_variables[label], 
                                command=self.update_draws_states).pack(side='top',
                                                                        anchor='nw',
                                                                            padx=10)
            else:
                ttk.Label(self, text=text_to_display).pack()

        # ustalanie ich stanu checkboxów
        self.update_checkboxes_states()

    def update_checkboxes_states(self):
        # zaznacza checkboxy wg stanu z draw_states
        for checkbox_name, checkbox_variable in self.checkboxes_variables.items():
            checkbox_variable.set(getattr(self.master.draws_states, checkbox_name))

    def update_draws_states(self):
        # aktualizuje obiekt draws_states wg stanu checkboksów i przeładowuje wyświetlaną klatkę
        for checkbox_name, checkbox_variable in self.checkboxes_variables.items():
            setattr(self.master.draws_states, checkbox_name, checkbox_variable.get())
        
        # przeładowuje wyświetlaną klatkę

        # self.master.frame_2.canvas.open_image()

class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ustala styl widgetów

        tb.Style().configure('Roundtoggle.Toolbutton', font=('Helvetica', 16))

        # twórz obiekt clipu

        self.play=False

        self.filename='VID_20241214_134111_004.mp4'
        self.frame_to_display=20

        self.clip=classes.Clip(self.filename)
        
        # twórz obiekt ze stanem pozycji do wyświetlenia

        self.draws_states = classes.Draws_states()

        # twórz okno

        self.minsize(800, 600)
        
        self.frame_1 = Frame_left(self).pack(side='left', fill='both', expand=False)
        self.frame_2 = Frame_right(self).pack(side='right', fill='both', expand=True)


if __name__ == '__main__':
    window = Window()
    window.mainloop()