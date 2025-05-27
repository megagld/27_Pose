import importlib
import classes
import os
from uuid import uuid4
import file_manager
import cv2
import tkinter as tk


class Manager:
    def __init__(self):

        self.clip_a = ClipTkinterData()

        self.frame_to_display = 0
        
        self.clip_b = ClipTkinterData()
        self.clip_b_clip_frame_to_display = 0
        self.swich_id = uuid4()

        # tworzy obiekt ze stanem pozycji do wyświetlenia
        self.draws_states_a = DrawsStates()
        self.draws_states_b = DrawsStates()

        # obiekt tworzony razem z Combobox w widgecie - nazwa pliku do stworzenia clipu
        self.date_a = None
        self.time_a = None
        self.count_a = None
        self.date_b = None
        self.time_b = None
        self.count_b = None
        self.file_a_to_load = None
        self.file_b_to_load = None

        self.rotation_angle = None

        # obiekty tworzone po stworzeniu głównego okna:
 
        # switch do kontroli checkboxów
        self.checkboxes_changed = None

        # suwak
        self.scale = None

        # głowny obraz do wyświetlania
        self.canvas = None

        # manager plików
        self.avilable_files = file_manager.VideoFiles()

        # listy rozwijane
        self.avilable_files.get_dates()
        self.files = self.avilable_files.dropdown_list_dates
        self.combo_list_date_a = None
        self.combo_list_time_a = None
        self.combo_list_count_a = None

        self.combo_list_date_b = None
        self.combo_list_time_b = None
        self.combo_list_count_b = None

        self.speed_factor = None
        self.obstacle_length = None

    def init_tk_objects(self):
        self.clip_a.init_tk_objects()
        self.clip_b.init_tk_objects()

        self.speed_factor = tk.IntVar()
        self.obstacle_length = tk.IntVar()


        # do usunięcia
        # **********************************
        self.clip_a.date.set("2025-02-09")
        self.clip_a.time.set("13:25:12")
        self.clip_a.count.set("003")

        self.clip_b.date.set("2025-03-12")
        self.clip_b.time.set("14:38:46")
        self.clip_b.count.set("005")
        # **********************************

    def frame_cnt_change(self, amount):

        self.frame_to_display += amount
        self.frame_to_display = min(
            self.frame_to_display, 
            self.clip_a.scale_range_max)
        self.frame_to_display = max(
            self.frame_to_display, 
            self.clip_a.scale_range_min)
        self.scale.set(self.frame_to_display)

    def count_drawing_times(self):

        self.frame_cnt_change(1)
        self.clip_a.draw_times_table_in_terminal()

    def load_file(self):

        if self.clip_a.time.get() in ("Select file number",'-'):
            return  

        if self.clip_a.date.get() == 'unclassified':            
            video_file = self.avilable_files.dropdown_lists_data['unclassified'][self.clip_a.time.get()]
        
        else:
            video_file = self.handy_files_dict_a[self.clip_a.count.get()]

        self.filename = video_file.name

        self.load_path = video_file.file_path
        
        self.clip_a.clip=classes.Clip(self.filename, self.load_path)

        self.speed_factor.set(self.clip_a.speed_factor)
        self.obstacle_length.set(self.clip_a.obstacle_length)

        self.calc_scale_range()
        self.scale.set(self.clip_a.scale_range_min)

        try:

            if self.date_b.get() == 'unclassified':            
                video_file = self.avilable_files.dropdown_lists_data['unclassified'][self.time_b.get()]

            else:
                video_file = self.handy_files_dict_b[self.count_b.get()]

            self.video_file_b_filename = video_file.name

            self.video_file_b_load_path = video_file.file_path

            self.clip_b = classes.Clip(self.video_file_b_filename, self.video_file_b_load_path)
            
            self.clip_b.compare_clip = True
            
        except:
            pass

    def calc_scale_range(self):

        self.scale_from = self.clip_a.scale_range_min
        self.scale_to = self.clip_a.scale_range_max

        self.scale.config(from_=self.scale_from)
        self.scale.config(to=self.scale_to)

    def bike_rotation_change(self, amount):
        self.swich_id = uuid4()
        self.clip_a.frames[self.frame_to_display].bike_rotation += amount
        self.canvas.update_view()
        self.scale.set(self.frame_to_display)  # po co to? do kontroli

    def img_rotation_change(self, amount):
        self.swich_id = uuid4()
        self.clip_b.rotation_angle += amount
        self.canvas.update_view()
        self.scale.set(self.frame_to_display)  # po co to? do kontroli

    def set_ang(self):
        self.clip_a.bike_ang_cor.append((self.frame_to_display,
                                          self.clip_a.frames[self.frame_to_display].bike_rotation))

    # def make_clip(self):
    #     self.clip_a.make_video_clip(self.draws_states_a, self.draws_states_a, self.swich_id)

    def save_frame(self):
        self.clip_a.save_frame(self.frame_to_display)

    def set_dates_list_a(self):

        self.combo_list_date_a['values'] = self.avilable_files.dropdown_list_dates

        self.combo_list_count_a['values'] = []

        self.time_a.set("Select time")
        self.count_a.set("Select file number")

    def set_times_list_a(self):

        try:
            self.avilable_files.get_times(self.date_a.get())
            self.combo_list_time_a['values'] = self.avilable_files.dropdown_list_times
            self.count_a.set("Select file number")
        except:
            print('błąd przy pobieraniu czasów')

    def set_counts_list_a(self):
        try:
            self.avilable_files.get_counts(self.date_a.get(), self.time_a.get())
            self.combo_list_count_a['values'] = self.avilable_files.dropdown_list_counts
            self.handy_files_dict_a = self.avilable_files.make_handy_files_dict(self.date_a.get(), 
                                                                                self.time_a.get())
        except:
            print('błąd przy pobieraniu liczników')

    def set_dates_list_b(self):

        self.combo_list_date_b['values'] = self.avilable_files.dropdown_list_dates

        self.combo_list_count_b['values'] = []

        self.time_b.set("Select time")
        self.count_b.set("Select file number")

    def set_times_list_b(self):

        try:
            self.avilable_files.get_times(self.date_b.get())
            self.combo_list_time_b['values'] = self.avilable_files.dropdown_list_times
            self.count_b.set("Select file number")
        except:
            print('błąd przy pobieraniu czasów')

    def set_counts_list_b(self):

        try:
            self.avilable_files.get_counts(self.date_b.get(), self.time_b.get())
            self.combo_list_count_b['values'] = self.avilable_files.dropdown_list_counts
            self.handy_files_dict_b = self.avilable_files.make_handy_files_dict(self.date_b.get(), 
                                                                    self.time_b.get())

        except:
            print('błąd przy pobieraniu liczników')

    def set_compare_counts_list(self):

        try:
            self.avilable_files.get_counts(self.date_a.get(), self.time_a.get())
            self.combo_list_compare_count['values'] = self.avilable_files.dropdown_list_counts
        except:
            print('błąd przy pobieraniu liczników pliku do porównania')

    def reload_classes(self):

        importlib.reload(classes)
        self.load_file()

    def update_view(self, x) -> None:

        self.frame_to_display = int(float(x))
        self.canvas.update_view()

    def set_brakout_point(self, x, y):

        self.clip_a.brakout_point = classes.Point(x, y)
        self.clip_a.calc_max_jump_height()
        self.update_view(self.frame_to_display)
        self.clip_a.save_brakout_point()

    def update_values(self, event):

        self.clip_a.speed_factor = self.speed_factor.get()
        self.clip_a.obstacle_length = self.obstacle_length.get()
        self.clip_a.charts['speed_chart'].speed_factor = self.clip_a.speed_factor
        self.clip_a.charts['speed_chart'].calc_min_max()
        self.clip_a.calc_max_jump_height()
        self.swich_id = uuid4()
        self.scale.set(self.frame_to_display)

    def make_source_image(self):

        try:
            x_offset = self.clip_a.brakout_point.x_disp - self.clip_b.brakout_point.x_disp
            y_offset = self.clip_a.brakout_point.y_disp - self.clip_b.brakout_point.y_disp
            frame_number_shift = self.clip_b.brakout_point_frame - self.clip_a.brakout_point_frame
        except:
            x_offset, y_offset = 0, 0

        if self.draws_states_a.main_frame_draw_state == True and self.draws_states_b.main_frame_draw_state == False:
            self.clip_a.display_frame(frame_number = self.frame_to_display,
                                         draws_states = self.draws_states_a,
                                         compare_clip = None,
                                         swich_id = self.swich_id)
            self.source_image = self.clip_a.image
            self.montage_clip_image = self.clip_a.montage_clip_image
            print('a')

        if self.draws_states_a.main_frame_draw_state == False and self.draws_states_b.main_frame_draw_state == True:
            self.clip_b.display_frame(frame_number = self.frame_to_display + frame_number_shift,
                                         draws_states = self.draws_states_b,
                                         compare_clip = None,
                                         swich_id = self.swich_id,
                                         x_offset = x_offset,
                                         y_offset = y_offset)
            self.source_image = self.clip_b.image
            self.montage_clip_image = self.clip_b.montage_clip_image

            print('b')

        if self.draws_states_a.main_frame_draw_state == True and self.draws_states_b.main_frame_draw_state == True:
            self.clip_a.display_frame(frame_number = self.frame_to_display,
                                         draws_states = self.draws_states_a,
                                         compare_clip = self.clip_b,
                                         swich_id = self.swich_id)
            self.source_image = self.clip_a.image
            self.montage_clip_image = self.clip_a.montage_clip_image

            print('ab')

    def make_video_clip(self):

        output_folder = "_clips"

        output_video_clip_file = "{}\\{}".format(
            output_folder, self.clip_a.name.replace(".mp4", "_analized.mp4")
        )

        out = cv2.VideoWriter(
            output_video_clip_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080)
        )

        for frame_number in range(self.scale_from-5, self.scale_to+6):

            self.frame_to_display = frame_number

            self.make_source_image()

            out.write(self.montage_clip_image)  # writing the video frame

        import time
        time.sleep(20)

        file_from = f'{os.getcwd()}\\{output_video_clip_file}'
        file_to = file_from.replace('.mp4','_60fps.mp4')

        print(file_from)
        print(file_to)
        print(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        os.system(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        print(f"{self.clip_a.name} gotowe.")   
        self.frame_to_display = 0



class LeftFrameWidgets:
    def __init__(self):
        # pozycje do wyświetlenia jako checkboxy
        self.labels_to_display  =   ['',
                            'main_frame_draw_state',
                            'main_frame_raw_view_draw_state',
                            '',
                            'main_frame_description',
                            '',
                            'main_skeleton_draw_state',
                            'main_skeleton_right_draw_state',
                            'main_skeleton_left_draw_state',
                            '',
                            'right_knee_ang_chart_draw_state',
                            'right_hip_ang_chart_draw_state',
                            'right_elbow_ang_chart_draw_state',
                            'left_knee_ang_chart_draw_state',
                            'left_hip_ang_chart_draw_state',
                            'left_elbow_ang_chart_draw_state',
                            '',
                            'stack_reach_len_chart_draw_state',
                            'stack_reach_ang_chart_draw_state',
                            'speed_chart_draw_state',
                            '',
                            'charts_background_draw_state',
                            'charts_descriptions_draw_state',
                            'leading_line_draw_state',
                            '',
                            'trace_line_draw_state',
                            'center_of_gravity_line_draw_state',
                            '',
                            'brakout_point_draw_state',
                            'speed_factor_verification_draw_state',
                            '',
                            'side_frame_draw_state',
                            'side_frame_background_draw_state',
                            '',
                            'side_skeleton_draw_state',
                            'side_skeleton_right_draw_state',
                            'side_skeleton_left_draw_state',
                            '',
                            'side_wheel_base_line_draw_state',
                            'side_head_leading_line_draw_state',
                            '',
                            'compare_clip_draw_state'
                            ]


class DrawsStates:
    # ustala co ma być wyświetlane
    def __init__(self):

        #główna klatka
        self.main_frame_draw_state                      = True
        self.main_frame_raw_view_draw_state             = False
        self.main_frame_description                     = True

        # szkielet
        self.main_skeleton_draw_state                   = False
        self.main_skeleton_right_draw_state             = True
        self.main_skeleton_left_draw_state              = False

        # wykresy
        # kąty zgięcia
        self.right_knee_ang_chart_draw_state            = True
        self.right_hip_ang_chart_draw_state             = True
        self.right_elbow_ang_chart_draw_state           = False
        self.left_knee_ang_chart_draw_state             = False
        self.left_hip_ang_chart_draw_state              = False
        self.left_elbow_ang_chart_draw_state            = False

        # inne
        self.stack_reach_len_chart_draw_state           = False
        self.stack_reach_ang_chart_draw_state           = False
        self.speed_chart_draw_state                     = True

        # tło wykresów
        self.charts_background_draw_state               = True
        self.speed_factor_verification_draw_state       = False

        # opisy wykresów
        self.charts_descriptions_draw_state             = True

        # linia wiodąca pionowa, pomocnicza
        self.leading_line_draw_state                    = True

        # linie na głównej klatce
        self.trace_line_draw_state                      = True
        self.center_of_gravity_line_draw_state          = False

        self.brakout_point_draw_state                   = True

        #################################################
        # boczny widok - wycięta klatka
        self.side_frame_draw_state                      = False
        self.side_frame_background_draw_state           = True

        # szkielet na bocznym widoku
        self.side_skeleton_draw_state                   = False
        self.side_skeleton_right_draw_state             = True
        self.side_skeleton_left_draw_state              = False   

        # linia bazy kół na bocznym widoku
        self.side_wheel_base_line_draw_state            = True

        # pionowa linia wiodąca - głowa
        self.side_head_leading_line_draw_state          = True

        # klip do porównania

        self.compare_clip_draw_state                    = False


class ClipTkinterData:
    def __init__(self):

        # listy rozwijane
        self.combo_list_date = None
        self.combo_list_time = None
        self.combo_list_count = None

        # dane do tworzenia nazwy pliku do załadownia
        self.date = None
        self.time = None
        self.count = None

        # nazwa pliku
        self.file_to_load = None

        # clip
        self.clip = None

        # obiekt draw state
        self.draws_states = None

        self.frame_to_display = None

        self.rotation_angle = None

    def init_tk_objects(self):
        self.date = tk.StringVar()
        self.time = tk.StringVar()
        self.count = tk.StringVar()

        # self.date.set("Select date")
        # self.time.set("Select time")
        # self.count.set("Select file number")

        self.rotation_angle = tk.IntVar()


        

