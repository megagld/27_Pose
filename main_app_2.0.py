import PIL.Image
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from tkcalendar import Calendar
from PIL import ImageTk
import classes
from timeit import default_timer as timer
import importlib
import os

# global frame_to_display, clip, draws_states, file_to_load, filename, canvas, scale, checkboxes_changed

class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image   = None
        self.image_id       = None
        self.image          = None

        self.width, self.height         = 0, 0
        self.center_x, self.center_y    = 0, 0
        self.bind('<Configure>', self.update_values)

        checkboxes_changed.trace_add("write", self.update_view)

    def update_values(self, *_) -> None:

        self.width         = self.winfo_width()
        self.height        = self.winfo_height()
        self.center_x      = self.width//2
        self.center_y      = self.height//2

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
        # if not (filename := askopenfilename()): return

        if not clip.image: return

        self.delete_previous_image()
        
        self.source_image = clip.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()
        
    def update_view(self, *_) -> None:
        # aktualizuje klatkę do wyświetlenia
        clip.display_frame(frame_to_display,
                           draws_states)
        
        self.open_image()

class Frame_right(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)


        self.frame_right_top = Frame_right_top(self).pack(side='top', fill='both', expand=False)
        self.frame_right_bottom = Frame_right_bottom(self).pack(side='bottom', fill='both', expand=True)


class Frame_right_top(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.width = self.winfo_width()


        ttk.Button(self, text='reload classes', comman=self.reload).grid(row = 0, column = 0)
        ttk.Button(self, text='load file', comman=self.load_file).grid(row = 2, column = 3)   

        ttk.Button(self, text='frame count -', command=lambda *args: self.frame_cnt_change(-1)).grid(row = 2, column = 4, padx = 5, pady = 5)     
        ttk.Button(self, text='frame count +', command=lambda *args: self.frame_cnt_change(+1)).grid(row = 2, column = 5, padx = 5, pady = 5)

        ttk.Button(self, text='bike rotation +5', command=lambda *args: self.bike_rotation_change(5)).grid(row = 0, column = 3, padx = 5, pady = 5)
        ttk.Button(self, text='bike rotation +1', command=lambda *args: self.bike_rotation_change(1)).grid(row = 1, column = 3, padx = 5, pady = 5)
        ttk.Button(self, text='bike rotation -1', command=lambda *args: self.bike_rotation_change(-1)).grid(row = 0, column = 5, padx = 5, pady = 5)
        ttk.Button(self, text='bike rotation -5', command=lambda *args: self.bike_rotation_change(-5)).grid(row = 1, column = 5, padx = 5, pady = 5)

        ttk.Button(self, text='set ang', comman=self.set_ang).grid(row = 1, column = 4, padx = 5, pady = 5)

        ttk.Button(self, text='make clip', comman=self.make_clip).grid(row = 0, column = 2, padx = 5, pady = 5)
        ttk.Button(self, text='save frame as jpg', comman=self.save_frame).grid(row = 1, column = 2, padx = 5, pady = 5)

        ttk.Button(self, text='count drawing times', comman=self.count_drawing_times).grid(row = 1, column = 0, padx = 5, pady = 5)     

        self.combo_list = ttk.Combobox(self, 
                                       width = 40,
                                       textvariable = file_to_load,
                                       postcommand = self.reload_file_list)
        self.combo_list.grid(row = 2, column = 1, padx = 5, pady = 5, columnspan=2)

        # do skończenia!!!

        # cal = Calendar()
        # date = cal.datetime.today() + cal.timedelta(days=2)

        de = tb.DateEntry(self).grid(row = 2, column = 0, padx = 5, pady = 5)

        # de.calevent_create(date, 'Reminder 2', 'reminder')

    def count_drawing_times(self):
        self.frame_cnt_change(1)
        clip.draw_times_table_in_terminal()

    def load_file(self):
        self.master.master.load_file()
        self.calc_scale_range()
        scale.set(clip.scale_range_min)

    def reload_file_list(self):

        self.get_files_list()
        self.combo_list['values'] = self.files_list

    def calc_scale_range(self):
        self.scale_from = clip.scale_range_min
        self.scale_to = clip.scale_range_max

        scale.config(from_=self.scale_from)
        scale.config(to=self.scale_to)

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
        clip=classes.Clip(filename)

    def update_view(self,x) -> None:
        global frame_to_display

        frame_to_display=int(float(x))
        canvas.update_view()

    def frame_cnt_change(self,amount):
        global frame_to_display
        frame_to_display+=amount
        frame_to_display=min(frame_to_display, clip.scale_range_max)
        frame_to_display=max(frame_to_display, clip.scale_range_min)
        scale.set(frame_to_display)

    def bike_rotation_change(self, amount):
        clip.frames[frame_to_display].bike_rotation+=amount
        canvas.open_image()
        scale.set(frame_to_display)

    def set_ang(self):
        clip.bike_ang_cor.append((frame_to_display, 
                                      clip.frames[frame_to_display].bike_rotation))

    def make_clip(self):
        clip.make_video_clip(draws_states)

    def save_frame(self):
        clip.save_frame(frame_to_display)

class Frame_right_bottom(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        global scale
        self.var = None
        scale = ttk.Scale(self,
                          variable=self.var, orient='horizontal',
                          command=self.update_view)
        scale.pack(side="top", fill="x", expand=False, padx=0, pady=5)
        
        global canvas
        canvas = CanvasImage(self, relief='sunken', bd=2)
        canvas.pack(expand=True, fill='both', padx=0, pady=5)

        
    def update_view(self,x) -> None:
        global frame_to_display

        frame_to_display=int(float(x))
        canvas.update_view()


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
            # dostosowuje nazwę do wyświetlenia - todo: dodać polskie tłumaczenia np.jako słownik
            text_to_display = label.replace('_draw_state', '').replace('_', ' ').capitalize()

            if label!='':
                self.checkboxes_variables[label]  = tk.IntVar()
                ttk.Checkbutton(self, 
                                text=text_to_display,
                                bootstyle="round-toggle",
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
            checkbox_variable.set(getattr(draws_states, checkbox_name))

    def update_draws_states(self):
        # aktualizuje obiekt draws_states wg stanu checkboksów i przeładowuje wyświetlaną klatkę
        for checkbox_name, checkbox_variable in self.checkboxes_variables.items():
            setattr(draws_states, checkbox_name, checkbox_variable.get())
        
        # zmienia stan zmiennej dającej sygnal że stan chceckboxów sie zmienił

        checkboxes_changed.set(not checkboxes_changed)

class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ustala styl widgetów

        # tb.Style().configure('Roundtoggle.Toolbutton', font=('Helvetica', 16))
        style = tb.Style('minty')

        global file_to_load
        file_to_load = tk.StringVar() 
        file_to_load.set("Select From List")
       
        # tworzy obiekt ze stanem pozycji do wyświetlenia

        global draws_states
        draws_states = classes.Draws_states()

        # tworzy switch do aktualizacji klatki po zmianie checkboxów, 
        # zmienia się w lewy Frame, a funkcja zbindowana jest w canvie

        global checkboxes_changed
        checkboxes_changed = tk.BooleanVar()

        # tworzy okno

        self.minsize(800, 600)
        
        self.frame_left = Frame_left(self).pack(side='left', fill='both', expand=False)
        self.frame_right = Frame_right(self).pack(side='right', fill='both', expand=True)

    def load_file(self):


        if file_to_load.get()!="Select From List":
            
            global clip
            global filename

            filename = file_to_load.get()
            
            filename=f'{filename}.mp4'

            clip=classes.Clip(filename)

if __name__ == '__main__':
    window = Window()
    window.mainloop()