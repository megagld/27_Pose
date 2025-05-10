import PIL.Image
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from PIL import ImageTk
import classes_old as classes
from timeit import default_timer as timer
import importlib
import os


class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image   = None
        self.image_id       = None
        self.image          = None

        self.width, self.height         = 0, 0
        self.center_x, self.center_y    = 0, 0
        self.bind('<Configure>', self.update_values)

        self.master.master.checkboxes_changed.trace_add("write", self.update_view)

    def update_values(self, *_) -> None:
        start = timer()

        self.width         = self.winfo_width()
        self.height        = self.winfo_height()
        self.center_x      = self.width//2
        self.center_y      = self.height//2

        if self.image is None: return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()

        end = timer()
        # print(f'{self.master.master.frame_to_display}:{end - start}')

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
        # if not (filename := askopenfilename()): return

        if not self.master.master.clip.image: return

        self.delete_previous_image()
        
        self.source_image = self.master.master.clip.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()
        
    def update_view(self, *_) -> None:
        # aktualizuje klatkę do wyświetlenia
        self.master.master.clip.display_frame(self.master.master.frame_to_display,
                                              self.master.master.draws_states)
        
        self.open_image()

class Frame_right(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.clip = self.master.clip

        self.width = self.winfo_width()

        self.var = None

        self.get_files_list()

        self.canvas = CanvasImage(self, relief='sunken', bd=2)
        tk.Button(self, text='reload classes', comman=self.reload).pack()
        tk.Button(self, text='reload obraz', comman=self.canvas.update_view).pack()
        tk.Button(self, text='frame count +', command=lambda *args: self.frame_cnt_change(1)).pack()        
        tk.Button(self, text='frame count -', command=lambda *args: self.frame_cnt_change(-1)).pack()

        tk.Button(self, text='bike rotation +5', command=lambda *args: self.bike_rotation_change(5)).pack()
        tk.Button(self, text='bike rotation +1', command=lambda *args: self.bike_rotation_change(1)).pack()
        tk.Button(self, text='bike rotation -1', command=lambda *args: self.bike_rotation_change(-1)).pack()
        tk.Button(self, text='bike rotation -5', command=lambda *args: self.bike_rotation_change(-5)).pack()

        tk.Button(self, text='set ang', comman=self.set_ang).pack()

        tk.Button(self, text='make clip', comman=self.make_clip).pack()
        tk.Button(self, text='save frame as jpg', comman=self.save_frame).pack()

        tk.Button(self, text='load file', comman=self.load_file).pack()    
        tk.Button(self, text='count drawing times', comman=self.count_drawing_times).pack()        

        self.combo_list = ttk.Combobox(self, width = 40, textvariable = self.master.file_to_load, values=self.files_list)
        self.combo_list.pack()

        self.scale=ttk.Scale(self, 
                             variable = self.var, orient='horizontal', 
                             command=self.update_view)

        self.scale.pack(side="top", fill="x", expand=False)

        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)


    def count_drawing_times(self):
        self.frame_cnt_change(1)
        self.master.clip.draw_times_table_in_terminal()

    def load_file(self):
        self.master.load_file()
        self.calc_scale_range()
        self.scale.set(self.master.clip.scale_range_min)

    def calc_scale_range(self):
        self.scale_from = self.master.clip.scale_range_min
        self.scale_to = self.master.clip.scale_range_max

        self.scale.config(from_=self.scale_from)
        self.scale.config(to=self.scale_to)

    def get_files_list(self):

        self.files_list = []

        input_dir = os.getcwd()
        input_data_dir = '{}\\{}'.format(input_dir,'_data')
        input_analized_dir = '{}\\{}'.format(input_dir,'_analysed')

        data_files = []
        analized_files = []

        # pobiera pliki z katalogu _data
        for i in next(os.walk(input_data_dir), (None, None, []))[2]:
            if i.endswith('.mp4'):
                data_files.append(i[:-4])
            
        # pobiera pliki z katalogu _analized
        for i in next(os.walk(input_analized_dir), (None, None, []))[2]:
            if i.endswith('.json'):
                analized_files.append(i[:-10])
        
        for data_file in data_files:
            if data_file in analized_files:
                self.files_list.append(data_file)
        
        print(f'Pliki z gotową analizą: {len(self.files_list)}')

    def reload(self):
        importlib.reload(classes) 
        self.master.clip=classes.Clip(self.master.filename)

    def update_view(self,x) -> None:
        self.master.frame_to_display=int(float(x))
        self.canvas.update_view()

    def frame_cnt_change(self,amount):
        self.master.frame_to_display+=amount
        self.master.frame_to_display=min(self.master.frame_to_display, self.master.clip.scale_range_max)
        self.master.frame_to_display=max(self.master.frame_to_display, self.master.clip.scale_range_min)
        self.scale.set(self.master.frame_to_display)

    def bike_rotation_change(self, amount):
        self.master.clip.frames[self.master.frame_to_display].bike_rotation+=amount
        self.canvas.open_image()
        self.scale.set(self.master.frame_to_display)

    def set_ang(self):
        self.master.clip.bike_ang_cor.append((self.master.frame_to_display, 
                                      self.master.clip.frames[self.master.frame_to_display].bike_rotation))
        print(self.master.clip.bike_ang_cor)

    def make_clip(self):
        self.master.clip.make_video_clip(self.master.draws_states)

    def save_frame(self):
        self.master.clip.save_frame(self.master.frame_to_display)

class Frame_left(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.clip = self.master.clip

        self.create_widgets()

    def create_widgets(self): 

        # obiekt zestawiający dane z lewej ramki - teksty do wyświetlenia i checkboxy oraz ich stan
        self.left_frame_widgets     = classes.Frame_widgets()
        self.labels                 = self.left_frame_widgets.labels_to_display

        self.checkboxes_variables   = {}

        # rysowanie checkboxów z opisami. Checkboxy powstają na podstawie 
        # labeli i są zestawiane na podstawie ich tekstu. Key = tekst labela
       
        for label in self.labels:
            # dostosowuje nazwę do wyświetlenia - todo: dodać polskie tłumaczenia np.jako słownik
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
        
        # zmienia stan zmiennej dającej sygnal że stan chceckboxów sie zmienił

        self.master.checkboxes_changed.set(not self.master.checkboxes_changed)

class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.clip = None

        # ustala styl widgetów

        tb.Style().configure('Roundtoggle.Toolbutton', font=('Helvetica', 16))

        self.file_to_load = tk.StringVar() 
        self.file_to_load.set("Select From List")
       
        # tworzy obiekt ze stanem pozycji do wyświetlenia

        self.draws_states = classes.Draws_states()

        # tworzy switch do aktualizacji klatki po zmianie checkboxów, 
        # zmienia się w lewy Frame, a funkcja zbindowana jest w canvie

        self.checkboxes_changed = tk.BooleanVar()

        # tworzy okno

        self.minsize(800, 600)
        
        self.frame_left = Frame_left(self).pack(side='left', fill='both', expand=False)
        self.right = Frame_right(self).pack(side='right', fill='both', expand=True)

    def load_file(self):

        if self.file_to_load.get()!="Select From List":

            self.filename = self.file_to_load.get()
            
            self.filename=f'{self.filename}.mp4'

            self.frame_to_display=0

            self.clip=classes.Clip(self.filename)

if __name__ == '__main__':
    window = Window()
    window.mainloop()