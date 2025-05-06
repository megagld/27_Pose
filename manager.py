import importlib
import classes
import os


class Manager:
    def __init__(self):

        self.clip = None
        self.frame_to_display = 0

        # tworzy obiekt ze stanem pozycji do wyświetlenia
        self.draws_states = DrawsStates()

        # obiekt tworzony razem z Combobox w widgecie - nazwa pliku do stworzenia clipu
        self.file_to_load = None

        # obiekty tworzone po stworzeniu głównego okna:

        # switch do kontroli checkboxów
        self.checkboxes_changed = None

        # suwak
        self.scale = None

        # głowny obraz do wyświetlania
        self.canvas = None

        # lista rozwijana
        self.combo_list = None


    def reload_clip(self):
            
        self.filename = self.file_to_load.get()

        if self.filename !="Select From List":
        
            self.clip=classes.Clip(f'{self.filename}.mp4')

    def frame_cnt_change(self, amount):

        self.frame_to_display += amount
        self.frame_to_display = min(
            self.frame_to_display, 
            self.clip.scale_range_max)
        self.frame_to_display = max(
            self.frame_to_display, 
            self.clip.scale_range_min)
        self.scale.set(self.frame_to_display)

    def count_drawing_times(self):

        self.frame_cnt_change(1)
        self.clip.draw_times_table_in_terminal()

    def load_file(self):

        self.reload_clip()
        self.calc_scale_range()
        self.scale.set(self.clip.scale_range_min)

    def calc_scale_range(self):

        self.scale_from = self.clip.scale_range_min
        self.scale_to = self.clip.scale_range_max

        self.scale.config(from_=self.scale_from)
        self.scale.config(to=self.scale_to)

    def bike_rotation_change(self, amount):
        self.clip.frames[self.frame_to_display].bike_rotation += amount
        self.canvas.open_image()
        self.scale.set(self.frame_to_display)  # po co to? do kontroli

    def set_ang(self):
        self.clip.bike_ang_cor.append((self.frame_to_display,
                                          self.clip.frames[self.frame_to_display].bike_rotation))

    def make_clip(self):
        self.clip.make_video_clip(self.draws_states)

    def save_frame(self):
        self.clip.save_frame(self.frame_to_display)

    def reload_file_list(self):

        self.get_files_list()
        self.combo_list['values'] = self.files_list

    def get_files_list(self):

        self.files_list = []

        input_dir = os.getcwd()
        input_data_dir = '{}\\{}'.format(input_dir, '_data')
        input_analized_dir = '{}\\{}'.format(input_dir, '_analysed')

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

    def reload_classes(self):

        importlib.reload(classes)
        self.load_file()

    def update_view(self, x) -> None:

        self.frame_to_display = int(float(x))
        self.canvas.update_view()


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
                            'side_frame_draw_state',
                            'side_frame_background_draw_state',
                            '',
                            'side_skeleton_draw_state',
                            'side_skeleton_right_draw_state',
                            'side_skeleton_left_draw_state',
                            '',
                            'side_wheel_base_line_draw_state',
                            'side_head_leading_line_draw_state'
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

        # opisy wykresów
        self.charts_descriptions_draw_state             = True

        # linia wiodąca pionowa, pomocnicza
        self.leading_line_draw_state                    = True

        # linie na głównej klatce
        self.trace_line_draw_state                      = True
        self.center_of_gravity_line_draw_state          = False

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
