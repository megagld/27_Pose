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

        main_manager.checkboxes_changed.trace_add("write", self.update_view)
        
        self.bind("<Button-1>", self._on_button_1)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-3>", self._on_button_3)
        self.bind("<Button-2>", self._on_button_2)

    def _on_button_1(self,event):

        # względna pozycja x myszy na obnrazie przeskalowanym
        relative_mouse_position = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width
        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position * self.orginal_image_width

        for frame_count, frame in main_manager.clip_a.frames.items():
            if frame.detected and frame.trace_point.x > absolut_mouse_position_x:
                main_manager.frame_to_display = frame_count
                break

        # main_manager.frame_to_display = 100
        main_manager.scale.set(main_manager.frame_to_display)

    def _on_button_3(self,event):

        main_manager.frame_cnt_change(1)
        
    def _on_button_2(self,event):

        # względna pozycja x myszy na obnrazie przeskalowanym
        relative_mouse_position_x = (event.x - (self.width-self.resized_image_width)/2)/self.resized_image_width
        relative_mouse_position_y = (event.y - (self.height-self.resized_image_height)/2)/self.resized_image_height

        # bezwzględna pozycja myszy na obrazie orginalnym
        absolut_mouse_position_x = relative_mouse_position_x * self.orginal_image_width
        absolut_mouse_position_y = relative_mouse_position_y * self.orginal_image_height

        if 0 < absolut_mouse_position_x < self.orginal_image_width and 0 < absolut_mouse_position_y < self.orginal_image_height:
            main_manager.swich_id = uuid4()
            main_manager.set_brakout_point(absolut_mouse_position_x, 
                                      absolut_mouse_position_y)
            

        # main_manager.frame_to_display = 100
        main_manager.scale.set(main_manager.frame_to_display)

    def _on_mousewheel(self, event):

        if event.delta==-120:
            main_manager.frame_cnt_change(-5)
        elif event.delta==120:
            main_manager.frame_cnt_change(+5)
    
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

        if not main_manager.clip_a.image:
            return

        self.delete_previous_image()

        # self.source_image = main_manager.clip_a.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()

    def update_view(self, *_) -> None:
        # aktualizuje klatkę do wyświetlenia
        main_manager.make_source_image()

        self.source_image = main_manager.source_image

        self.open_image()


class Frame_right_top(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        main_manager.date_a = tk.StringVar()
        main_manager.time_a = tk.StringVar()
        main_manager.count_a = tk.StringVar()
        main_manager.date_b = tk.StringVar()
        main_manager.time_b = tk.StringVar()
        main_manager.count_b = tk.StringVar()
        main_manager.speed_factor = tk.IntVar()
        main_manager.obstacle_length = tk.IntVar()
        main_manager.rotation_angle = tk.IntVar()

        # main_manager.date_a.set("Select date")
        # main_manager.time_a.set("Select time")
        # main_manager.count_a.set("Select file number")

        # main_manager.date_b.set("Select date")
        # main_manager.time_b.set("Select time")
        # main_manager.count_b.set("Select file number")


        main_manager.date_a.set("2025-02-09")
        main_manager.time_a.set("13:25:12")
        main_manager.count_a.set("003")

        main_manager.date_b.set("2025-03-12")
        main_manager.time_b.set("14:38:46")
        main_manager.count_b.set("005")

        # main_manager.compare.set("Select file to compare number")
        main_manager.speed_factor.set(None)
        main_manager.obstacle_length.set(None)

        #################################
        main_manager.combo_list_date_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.date_a,
                                        postcommand=manager.set_dates_list_a)
        main_manager.combo_list_date_a.grid(row=0,column=0, padx=5,pady=5)

        main_manager.combo_list_time_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.time_a,
                                        postcommand=manager.set_times_list_a)
        main_manager.combo_list_time_a.grid(row=1,column=0, padx=5,pady=5)

        main_manager.combo_list_count_a = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.count_a,
                                        postcommand=manager.set_counts_list_a)
        main_manager.combo_list_count_a.grid(row=2,column=0, padx=5,pady=5)

        main_manager.combo_list_date_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.date_b,
                                        postcommand=manager.set_dates_list_b)
        main_manager.combo_list_date_b.grid(row=0,column=1, padx=5,pady=5)

        main_manager.combo_list_time_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.time_b,
                                        postcommand=manager.set_times_list_b)
        main_manager.combo_list_time_b.grid(row=1,column=1, padx=5,pady=5)

        main_manager.combo_list_count_b = ttk.Combobox(self,
                                        width=25,
                                        textvariable=manager.count_b,
                                        postcommand=manager.set_counts_list_b)
        main_manager.combo_list_count_b.grid(row=2,column=1, padx=5,pady=5)

        #################################

        ttk.Button(self, text='load file', comman=manager.load_file
                   ).grid(row=2, column=2, padx=5, pady=5,  sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                    ).grid(column=3, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='reload classes', comman=manager.reload_classes
                   ).grid(row=0, column=5, padx=5, pady=5,  sticky='EWNS')

        ttk.Button(self, text='count drawing times', comman=manager.count_drawing_times
                   ).grid(row=1, column=5, padx=5, pady=5, sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                    ).grid(column=6, row=0, rowspan=3, sticky='ns')
        #################################

        ttk.Button(self, text='make clip', comman=manager.make_video_clip
                   ).grid(row=0, column=7, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='save frame as jpg', comman=manager.save_frame
                   ).grid(row=1, column=7, padx=5, pady=5, sticky='EWNS')
        
        ttk.Separator(self, orient='vertical'
                     ).grid(column=8, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='frame count -', command=lambda *args: main_manager.frame_cnt_change(-1)
                   ).grid(row=1, column=9, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='frame count +', command=lambda *args: main_manager.frame_cnt_change(+1)
                   ).grid(row=1, column=10, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=11, row=0, rowspan=3, sticky='ns')
        #################################
        
        ttk.Button(self, text='bike rotation +1', command=lambda *args: main_manager.bike_rotation_change(1)
                   ).grid(row=0, column=12, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +5', command=lambda *args: main_manager.bike_rotation_change(5)
                   ).grid(row=1, column=12, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation +10', command=lambda *args: main_manager.bike_rotation_change(10)
                   ).grid(row=2, column=12, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='set ang', comman=manager.set_ang
                   ).grid( row=1, column=13, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -1', command=lambda *args: main_manager.bike_rotation_change(-1)
                   ).grid(row=0, column=14, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -5', command=lambda *args: main_manager.bike_rotation_change(-5)
                   ).grid(row=1, column=14, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='bike rotation -10', command=lambda *args: main_manager.bike_rotation_change(-10)
                   ).grid(row=2, column=14, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=15, row=0, rowspan=3, sticky='ns')
        #################################

        ttk.Label(self,
                  text='speed factor :',
                  ).grid(row=0, column=16, padx=5, pady=5, sticky='ENS')
        ttk.Label(self,
            text='obstacle length :',
            ).grid(row=1, column=16, padx=5, pady=5, sticky='ENS')

        ttk.Entry(self,
                  textvariable=manager.speed_factor,
                  ).grid(row=0, column=17, padx=5, pady=5, sticky='EWNS')
        ttk.Entry(self,
                  textvariable=manager.obstacle_length,
                  ).grid(row=1, column=17, padx=5, pady=5, sticky='EWNS')
        ttk.Separator(self, orient='vertical'
                    ).grid(column=18, row=0, rowspan=3, sticky='ns')
        #################################
                
        ttk.Button(self, text='image rotation +1', command=lambda *args: main_manager.img_rotation_change(+1)
                   ).grid(row=1, column=19, padx=5, pady=5, sticky='EWNS')
        ttk.Button(self, text='image rotation -1', command=lambda *args: main_manager.img_rotation_change(-1)
                   ).grid(row=2, column=19, padx=5, pady=5, sticky='EWNS')

        ttk.Separator(self, orient='vertical'
                    ).grid(column=20, row=0, rowspan=3, sticky='ns')
        #################################
        
        self.bind_all("<Return>", main_manager.update_values)


class Frame_right_bottom(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        main_manager.scale = ttk.Scale(self,
                                  orient='horizontal',
                                  command=manager.update_view)
        main_manager.scale.pack(side="top",
                           fill="x",
                           expand=False,
                           padx=0,
                           pady=5)

        main_manager.canvas = CanvasImage(self, 
                                     relief='sunken', 
                                     bd=2)
        main_manager.canvas.pack(expand=True, 
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

        main_manager.checkboxes_changed = tk.BooleanVar()

        # obiekt zestawiający dane z lewej ramki - teksty do wyświetlenia i checkboxy oraz ich stan
        self.left_frame_widgets = LeftFrameWidgets()
        self.labels = self.left_frame_widgets.labels_to_display

        self.checkboxes_variables_a = {}
        self.checkboxes_variables_b = {}

        # rysowanie checkboxów z opisami. Checkboxy powstają na podstawie
        # labeli i są zestawiane na podstawie ich tekstu. Key = tekst labela
        
        ttk.Label(self,
                text='A',
                anchor="center"
                ).grid(column=0,
                        row=0,
                        padx=(5,0))
        ttk.Label(self,
                text='B',
                ).grid(column=1,
                        row=0,
                        padx=(5,0),
                        sticky = 'NW')
        
        for row_count, label in enumerate(self.labels, start=1):
            # dostosowuje nazwę do wyświetlenia - todo: dodać polskie tłumaczenia np.jako słownik
            text_to_display = label.replace(
                '_draw_state', '').replace('_', ' ').capitalize()

            if label != '':
                self.checkboxes_variables_a[label] = tk.IntVar()
                ttk.Checkbutton(self,
                                text='',
                                bootstyle="round-toggle",
                                variable=self.checkboxes_variables_a[label],
                                command=self.update_draws_states).grid(column=0,
                                                                       row=row_count,
                                                                       padx=(5,0))
                self.checkboxes_variables_b[label] = tk.IntVar()

                ttk.Checkbutton(self,
                                text=text_to_display,
                                bootstyle="round-toggle",
                                variable=self.checkboxes_variables_b[label],
                                command=self.update_draws_states).grid(column=1,
                                                                       row=row_count,
                                                                       sticky='W',
                                                                       padx=(0,5))
            else:
                ttk.Label(self, text=text_to_display).grid(column=0,
                                                           row=row_count)

        # ustalanie ich stanu checkboxów
        self.update_checkboxes_states()

    def update_checkboxes_states(self):

        # zaznacza checkboxy wg stanu z draw_states
        for checkbox_name, checkbox_variable in self.checkboxes_variables_a.items():
            checkbox_variable.set(getattr(main_manager.draws_states_a, checkbox_name))

        for checkbox_name, checkbox_variable in self.checkboxes_variables_b.items():
            checkbox_variable.set(getattr(main_manager.draws_states_b, checkbox_name))

    def update_draws_states(self):
        # aktualizuje obiekt draws_states wg stanu checkboksów i przeładowuje wyświetlaną klatkę
        for checkbox_name, checkbox_variable in self.checkboxes_variables_a.items():
            setattr(main_manager.draws_states_a, checkbox_name,
                    checkbox_variable.get())
        
        for checkbox_name, checkbox_variable in self.checkboxes_variables_b.items():
            setattr(main_manager.draws_states_b, checkbox_name,
                    checkbox_variable.get())
            
        # zmienia stan zmiennej dającej sygnal że stan chceckboxów sie zmienił
        
        main_manager.swich_id = uuid4()
        main_manager.checkboxes_changed.set(not main_manager.checkboxes_changed)
