import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from PIL import ImageTk
from manager import *
from uuid import uuid4

class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0

        self.resized_image_width = 0
        self.resized_image_height = 0
        
        self.orginal_image_width = 0
        self.orginal_image_height = 0

        self.bind('<Configure>', self.update_values)

        manager.checkboxes_changed.trace_add("write", self.update_view)
        
        self.bind("<Button-1>", self._on_button_1)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-3>", self._on_button_3)
        self.bind("<Button-2>", self._on_button_2)

    def _on_button_1(self,event):

        # względna pozycja x myszy na obnrazie przeskalowanym
        relative_mouse_position = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width
        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position * self.orginal_image_width

        for frame_count, frame in manager.clip_a.frames.items():
            if frame.detected and frame.trace_point.x > absolut_mouse_position_x:
                manager.frame_to_display = frame_count
                break

        # manager.frame_to_display = 100
        manager.scale.set(manager.frame_to_display)

    def _on_button_3(self,event):

        manager.frame_cnt_change(1)
        
    def _on_button_2(self,event):

        # względna pozycja x myszy na obnrazie przeskalowanym
        relative_mouse_position_x = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width
        relative_mouse_position_y = (event.y - (self.height-self.resized_image_height)/2)/self.resized_image_height

        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position_x * self.orginal_image_width
        absolut_mouse_position_y = relative_mouse_position_y * self.orginal_image_height

        if 0 < absolut_mouse_position_x < self.orginal_image_width and 0 < absolut_mouse_position_y < self.orginal_image_height:
            manager.swich_id = uuid4()
            manager.set_brakout_point(absolut_mouse_position_x, 
                                      absolut_mouse_position_y)
            

        # manager.frame_to_display = 100
        manager.scale.set(manager.frame_to_display)

    def _on_mousewheel(self, event):

        if event.delta==-120:
            manager.frame_cnt_change(-5)
        elif event.delta==120:
            manager.frame_cnt_change(+5)
    
    def update_values(self, *_) -> None:

        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None:
            return
        self.delete_previous_image()
        self.resize_image()
        self.paste_image()

    def delete_previous_image(self) -> None:
        if self.image is None:
            return
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

        self.resized_image_width = new_width
        self.resized_image_height = new_height

        self.orginal_image_width = image_width
        self.orginal_image_height = image_height

    def paste_image(self) -> None:
        self.image_id = self.create_image(
            self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:

        if not manager.clip_a.image:
            return

        self.delete_previous_image()

        self.source_image = manager.clip_a.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()

    def update_view(self, *_) -> None:
        # aktualizuje klatkę do wyświetlenia

        manager.clip_a.display_frame(manager.frame_to_display,
                                   manager.draws_states,
                                   manager.clip_b,
                                   manager.swich_id)

        self.open_image()


class Frame_right_top(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        manager.date_a = tk.StringVar()
        manager.time_a = tk.StringVar()
        manager.count_a = tk.StringVar()
        manager.date_b = tk.StringVar()
        manager.time_b = tk.StringVar()
        manager.count_b = tk.StringVar()
        manager.speed_factor = tk.IntVar()
        manager.obstacle_length = tk.IntVar()

        manager.date_a.set("Select date")
        manager.time_a.set("Select time")
        manager.count_a.set("Select file number")

        manager.date_b.set("Select date")
        manager.time_b.set("Select time")
        manager.count_b.set("Select file number")

        # manager.compare.set("Select file to compare number")
        manager.speed_factor.set(None)
        manager.obstacle_length.set(None)

        #################################
        manager.combo_list_date_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.date_a,
                                        postcommand=manager.set_dates_list_a)
        manager.combo_list_date_a.grid(row=0,column=0, padx=5,pady=5)

        manager.combo_list_time_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.time_a,
                                        postcommand=manager.set_times_list_a)
        manager.combo_list_time_a.grid(row=1,column=0, padx=5,pady=5)

        manager.combo_list_count_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.count_a,
                                        postcommand=manager.set_counts_list_a)
        manager.combo_list_count_a.grid(row=2,column=0, padx=5,pady=5)

        manager.combo_list_date_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.date_b,
                                        postcommand=manager.set_dates_list_b)
        manager.combo_list_date_b.grid(row=0,column=1, padx=5,pady=5)

        manager.combo_list_time_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.time_b,
                                        postcommand=manager.set_times_list_b)
        manager.combo_list_time_b.grid(row=1,column=1, padx=5,pady=5)

        manager.combo_list_count_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.count_b,
                                        postcommand=manager.set_counts_list_b)
        manager.combo_list_count_b.grid(row=2,column=1, padx=5,pady=5)


        # manager.combo_list_compare_count = ttk.Combobox(self,
        #                                 width=25,
        #                                 textvariable=manager.compare,
        #                                 postcommand=manager.set_compare_counts_list)
        # manager.combo_list_compare_count.grid(row=2,column=2, padx=5,pady=5)
        

        ttk.Button(self, text='load file', comman=manager.load_file
                   ).grid(row=2, column=3, padx=5, pady=5,  sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                    ).grid(column=2, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='reload classes', comman=manager.reload_classes
                   ).grid(row=0, column=3, padx=5, pady=5,  sticky='EWNS')

        ttk.Button(self, text='count drawing times', comman=manager.count_drawing_times
                   ).grid(row=1, column=3, padx=5, pady=5, sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                    ).grid(column=4, row=0, rowspan=3, sticky='ns')
        #################################

        ttk.Button(self, text='make clip', comman=manager.make_clip
                   ).grid(row=0, column=5, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='save frame as jpg', comman=manager.save_frame
                   ).grid(row=1, column=5, padx=5, pady=5, sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                     ).grid(column=6, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='frame count -', command=lambda *args: manager.frame_cnt_change(-1)
                   ).grid(row=1, column=7, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='frame count +', command=lambda *args: manager.frame_cnt_change(+1)
                   ).grid(row=1, column=8, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=9, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='bike rotation +1', command=lambda *args: manager.bike_rotation_change(1)
                   ).grid(row=0, column=10, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +5', command=lambda *args: manager.bike_rotation_change(5)
                   ).grid(row=1, column=10, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +10', command=lambda *args: manager.bike_rotation_change(10)
                   ).grid(row=2, column=10, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='set ang', comman=manager.set_ang
                   ).grid( row=1, column=11, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -1', command=lambda *args: manager.bike_rotation_change(-1)
                   ).grid(row=0, column=12, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -5', command=lambda *args: manager.bike_rotation_change(-5)
                   ).grid(row=1, column=12, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -10', command=lambda *args: manager.bike_rotation_change(-10)
                   ).grid(row=2, column=12, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=13, row=0, rowspan=3, sticky='ns')
        #################################

        ttk.Label(self,
                  text='speed factor :',
                  ).grid(row=0, column=14, padx=5, pady=5, sticky='ENS')
        ttk.Label(self,
            text='obstacle length :',
            ).grid(row=1, column=14, padx=5, pady=5, sticky='ENS')

        ttk.Entry(self,
                  textvariable=manager.speed_factor,
                  ).grid(row=0, column=15, padx=5, pady=5, sticky='EWNS')
        ttk.Entry(self,
                  textvariable=manager.obstacle_length,
                  ).grid(row=1, column=15, padx=5, pady=5, sticky='EWNS')
        ttk.Separator(self, orient='vertical'
                    ).grid(column=16, row=0, rowspan=3, sticky='ns')
        #################################
        
        self.bind_all("<Return>", manager.update_values)

class Frame_right_bottom(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        manager.scale = ttk.Scale(self,
                                  orient='horizontal',
                                  command=manager.update_view)
        manager.scale.pack(side="top",
                           fill="x",
                           expand=False,
                           padx=0,
                           pady=5)

        manager.canvas = CanvasImage(self, 
                                     relief='sunken', 
                                     bd=2)
        manager.canvas.pack(expand=True, 
                            fill='both', 
                            padx=0, 
                            pady=5)


class Frame_left(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.create_widgets()

    def create_widgets(self):

        # tworzy switch do aktualizacji klatki po zmianie checkboxów,
        # zmienia się w lewym Frame, a funkcja zbindowana jest w canvie

        manager.checkboxes_changed = tk.BooleanVar()

        # obiekt zestawiający dane z lewej ramki - teksty do wyświetlenia i checkboxy oraz ich stan
        self.left_frame_widgets = LeftFrameWidgets()
        self.labels = self.left_frame_widgets.labels_to_display

        self.checkboxes_variables = {}

        # rysowanie checkboxów z opisami. Checkboxy powstają na podstawie
        # labeli i są zestawiane na podstawie ich tekstu. Key = tekst labela

        for label in self.labels:
            # dostosowuje nazwę do wyświetlenia - todo: dodać polskie tłumaczenia np.jako słownik
            text_to_display = label.replace(
                '_draw_state', '').replace('_', ' ').capitalize()

            if label != '':
                self.checkboxes_variables[label] = tk.IntVar()
                ttk.Checkbutton(self,
                                text=text_to_display,
                                bootstyle="round-toggle",
                                variable=self.checkboxes_variables[label],
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
            checkbox_variable.set(getattr(manager.draws_states, checkbox_name))

    def update_draws_states(self):
        # aktualizuje obiekt draws_states wg stanu checkboksów i przeładowuje wyświetlaną klatkę
        for checkbox_name, checkbox_variable in self.checkboxes_variables.items():
            setattr(manager.draws_states, checkbox_name,
                    checkbox_variable.get())

        # zmienia stan zmiennej dającej sygnal że stan chceckboxów sie zmienił
        
        manager.swich_id = uuid4()
        manager.checkboxes_changed.set(not manager.checkboxes_changed)

class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ustala styl widgetów

        style = tb.Style('minty')

        # tworzy okno i podokna

        self.minsize(800, 600)

        self.frame_left = Frame_left(self).pack(
            side='left',
            fill='both',
            expand=False)

        self.frame_right_top = Frame_right_top(self).pack(
            fill='both')

        self.frame_right_bottom = Frame_right_bottom(self).pack(
            fill='both',
            expand=True)


if __name__ == '__main__':

    # tworzy obiekt zarządzajacy całością
    manager = Manager()

    # tworzy główne okno
    window = Window()
    window.mainloop()
