import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from tkcalendar import Calendar
from PIL import ImageTk
from manager import *
import datetime
import random
from uuid import uuid4

class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.bind('<Configure>', self.update_values)

        manager.checkboxes_changed.trace_add("write", self.update_view)


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

    def paste_image(self) -> None:
        self.image_id = self.create_image(
            self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:

        if not manager.clip.image:
            return

        self.delete_previous_image()

        self.source_image = manager.clip.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()

    def update_view(self, *_) -> None:
        # aktualizuje klatkę do wyświetlenia

        manager.clip.display_frame(manager.frame_to_display,
                                   manager.draws_states,
                                   manager.swich_id)

        self.open_image()


class Frame_right_top(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        ttk.Button(self, text='reload classes', comman=manager.reload_classes
                   ).grid(row=0, column=0, padx=5, pady=5,  sticky='EWNS')
        ttk.Button(self, text='load file', comman=manager.load_file
                   ).grid(row=2, column=2)

        ttk.Separator(self, orient='vertical'
                    ).grid(column=3, row=0, rowspan=3, sticky='ns')
        ttk.Button(self, text='frame count -', command=lambda *args: manager.frame_cnt_change(-1)
                   ).grid(row=1, column=5, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='frame count +', command=lambda *args: manager.frame_cnt_change(+1)
                   ).grid(row=1, column=6, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=7, row=0, rowspan=3, sticky='ns')
        ttk.Button(self, text='bike rotation +1', command=lambda *args: manager.bike_rotation_change(1)
                   ).grid(row=0, column=8, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +5', command=lambda *args: manager.bike_rotation_change(5)
                   ).grid(row=1, column=8, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +10', command=lambda *args: manager.bike_rotation_change(10)
                   ).grid(row=2, column=8, padx=5, pady=5, sticky='EWNS')

        ttk.Button(self, text='bike rotation -1', command=lambda *args: manager.bike_rotation_change(-1)
                   ).grid(row=0, column=10, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -5', command=lambda *args: manager.bike_rotation_change(-5)
                   ).grid(row=1, column=10, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -10', command=lambda *args: manager.bike_rotation_change(-10)
                   ).grid(row=2, column=10, padx=5, pady=5, sticky='EWNS')

        ttk.Button(self, text='set ang', comman=manager.set_ang
                   ).grid( row=1, column=9, padx=5, pady=5, sticky='EWNS')
        ttk.Separator(self, orient='vertical'
                    ).grid(column=11, row=0, rowspan=3, sticky='ns')

        ttk.Button(self, text='make clip', comman=manager.make_clip
                   ).grid(row=0, column=2, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='save frame as jpg', comman=manager.save_frame
                   ).grid(row=1, column=2, padx=5, pady=5, sticky='EWNS')

        ttk.Button(self, text='count drawing times', comman=manager.count_drawing_times
                   ).grid(row=1, column=0, padx=5, pady=5, sticky='EWNS')

        manager.file_to_load = tk.StringVar()
        manager.file_to_load.set("Select From List")

        manager.combo_list = ttk.Combobox(self,
                                       width=40,
                                       textvariable=manager.file_to_load,
                                       postcommand=manager.reload_file_list)
        manager.combo_list.grid(row=2, column=0, padx=5, pady=5, columnspan=2)

        # do skończenia!!!

        # cal = Calendar()
        # date = cal.datetime.today() + cal.timedelta(days=2)

        # de = tb.DateEntry(self).grid(row = 2, column = 0, padx = 5, pady = 5)

        # de.calevent_create(date, 'Reminder 2', 'reminder')


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

        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-3>", self._on_button_3)

    
    def _on_mousewheel(self, event):
        print(event)
        if event.delta==-120:
            manager.frame_cnt_change(-5)
        elif event.delta==120:
            manager.frame_cnt_change(+5)

    def _on_button_3(self,event):
        # print(event)
        manager.frame_cnt_change(1)


if __name__ == '__main__':

    # tworzy obiekt zarządzajacy całością
    manager = Manager()

    # tworzy główne okno
    window = Window()
    window.mainloop()
