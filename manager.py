import importlib
import classes
import os
from uuid import uuid4
import file_manager

class Manager:
    def __init__(self):

        self.clip_a = None
        self.frame_to_display = 0
        
        self.clip_b = None
        self.clip_b_clip_frame_to_display = 0
        self.swich_id = uuid4()

        # tworzy obiekt ze stanem pozycji do wyświetlenia
        self.draws_states = DrawsStates()

        # obiekt tworzony razem z Combobox w widgecie - nazwa pliku do stworzenia clipu
        self.date_a = None
        self.time_a = None
        self.count_a = None
        self.date_b = None
        self.time_b = None
        self.count_b = None
        self.file_a_to_load = None
        self.file_b_to_load = None

        # obiekty tworzone po stworzeniu głównego okna:
 
        # switch do kontroli checkboxów
        self.checkboxes_changed = None

        # suwak
        self.scale = None

        # głowny obraz do wyświetlania
        self.canvas = None

        # manager plików
        self.avilable_files = file_manager.VideoFiles()

        # listy rozwijana
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

        if self.time_a.get() in ("Select file number",'-'):
            return  

        if self.date_a.get() == 'unclassified':            
            video_file = self.avilable_files.dropdown_lists_data['unclassified'][self.time_a.get()]
        
        else:
            video_file = self.handy_files_dict_a[self.count_a.get()]

        self.filename = video_file.name

        self.load_path = video_file.file_path
        
        self.clip_a=classes.Clip(self.filename, self.load_path)

        self.speed_factor.set(self.clip_a.speed_factor)
        self.obstacle_length.set(self.clip_a.obstacle_length)

        self.calc_scale_range()
        self.scale.set(self.clip_a.scale_range_min)

        if self.date_b.get() == 'unclassified':            
            video_file = self.avilable_files.dropdown_lists_data['unclassified'][self.time_b.get()]

        else:
            video_file = self.handy_files_dict_b[self.count_b.get()]

        self.video_file_b_filename = video_file.name

        self.video_file_b_load_path = video_file.file_path

        self.clip_b = classes.Clip(self.video_file_b_filename, self.video_file_b_load_path)
        
        self.clip_b.compare_clip = True



        # if self.count_b.get() != "Select file number":  

        #     compare_video_file = self.handy_files_dict_b[self.count_b.get()]

        #     print(compare_video_file.name)

        #     self.compare_filename = compare_video_file.name

        #     self.compare_load_path = compare_video_file.file_path
            
        #     self.compare_clip=classes.Clip(self.compare_filename, self.compare_load_path)
            
        #     self.compare_clip.compare_clip = True
            
        #     print(self.compare_clip.name)

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

    def set_ang(self):
        self.clip_a.bike_ang_cor.append((self.frame_to_display,
                                          self.clip_a.frames[self.frame_to_display].bike_rotation))

    def make_clip(self):
        self.clip_a.make_video_clip(self.draws_states, self.compare_clip, self.swich_id)

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


class LeftFrameWidgets:
    def __init__(self):
        # pozycje do wyświetlenia jako checkboxy
        self.labels_to_display  =   ['',
                            'main_frame_draw_state',
                            'main_frame_background_draw_state',
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
        self.main_frame_background_draw_state           = True
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
