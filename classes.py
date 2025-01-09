import os
import json
import cv2
import numpy as np
import math
from unidecode import unidecode
from PIL import Image, ImageTk
from ffprobe import FFProbe
from general_bm import letterbox_calc

def angle_between_vectors(u, v):
    dot_product = sum(i * j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    angle_rad = math.acos(cos_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_rad, angle_deg

def rotate_point(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox, oy = origin.x, origin.y
    px, py = point.x, point.y

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)

    return Point(qx, qy)

def transform_point(origin, delta_x, delta_y):

    ox, oy = origin.x, origin.y

    qx = ox + delta_x
    qy = oy + delta_y

    return Point(qx, qy)

def get_dist(pkt_1, pkt_2):
    # zwraca dystans między dwoma punktami
    pos_x_1, pos_y_1 = pkt_1.x, pkt_1.y
    pos_x_2, pos_y_2 = pkt_2.x, pkt_2.y

    return ((pos_x_2 - pos_x_1) ** 2 + (pos_y_2 - pos_y_1) ** 2) ** 0.5

class Point:
    def __init__(self, pos_x, pos_y, sk_id=None):
        self.sk_id = sk_id
        self.x = pos_x
        self.y = pos_y
        self.x_disp = int(pos_x)
        self.y_disp = int(pos_y)
        self.disp   = (self.x_disp, self.y_disp)

class Frame:
    def __init__(self, frame_count, frame_time, kpts, frame_offsets):

        self.frame_count = frame_count
        self.frame_time = frame_time
        self.kpts = kpts
        self.detected = kpts != []
        self.skeleton_points = {}
        self.angs = {}
        self.trace_point = None
        self.center_of_gravity = None
        self.center_of_bar = None
        self.stack_reach_len = None
        self.stack_reach_ang = None

        # real bike geometry
        self.bike_reach_len       = 485
        self.bike_stack_len       = 645
        self.bike_stack_reach_len = (self.bike_reach_len**2+self.bike_stack_len**2)**0.5  # wprowadzić pomiar albo dopasować
        self.bike_stack_reach_ang = math.degrees(math.atan(self.bike_stack_len/self.bike_reach_len))  # wprowadzić pomiar albo dopasować
        self.bike_real_s_r_ang    = 10  #korekta kąta ze względu na to że pomiar dotyczy nie dokładnie reachu i stacku
        self.bike_stack_reach_ang+= self.bike_real_s_r_ang

        self.bike_chain_stay = 428  # wprowadzić pomiar albo dopasować
        self.bike_wheel_base = 1243  # wprowadzić pomiar albo dopasować
        self.bike_wheel_size = 27.5*25.4

        self.frame_offsets = frame_offsets
        self.left_ofset = -1 * self.frame_offsets[0]
        self.top_offset = -1 * self.frame_offsets[1]

        self.update_data_if_detected()

    def update_data_if_detected(self):
        if self.detected:
            self.organize_points()
            self.calc_ang()

            # DO ANALIZY CZY LEPIEJ DAĆ ŚRODEK MIĘDZY PUNKTAMI CZY PUNKTY Z JEDNEJ STRONY 

            self.trace_point = self.skeleton_points[17]
            self.center_of_gravity = self.skeleton_points[13]
            self.center_of_bar = self.skeleton_points[11]

            # self.trace_point = self.get_mid(16, 17)
            # self.center_of_gravity = self.get_mid(12, 13)
            # self.center_of_bar = self.get_mid(10, 11)

            self.stack_reach_len = get_dist(self.trace_point, self.center_of_bar)
            self.stack_reach_ang = self.stack_reach_ang_calc(
                self.trace_point, self.center_of_bar
            )

    def get_mid(self, sk_id_1, sk_id_2):
        # zwraca punkt środkowy między dwoma punktami szkieletu
        steps = 3
        pos_x_1, pos_y_1 = (self.kpts[(sk_id_1 - 1) * steps]), (
                            self.kpts[(sk_id_1 - 1) * steps + 1])
        pos_x_2, pos_y_2 = (self.kpts[(sk_id_2 - 1) * steps]), (
                            self.kpts[(sk_id_2 - 1) * steps + 1] )

        return Point((pos_x_2 + pos_x_1) / 2, (pos_y_2 + pos_y_1) / 2)

    def organize_points(self):
        # tworzy słownik ze współrzędnymi punktów szkieletu
        steps = 3
        if self.kpts:
            self.detected = True
            for sk_id in range(1, 18):
                pos_x, pos_y = (self.kpts[(sk_id - 1) * steps]) + self.left_ofset, (
                    self.kpts[(sk_id - 1) * steps + 1]
                ) + self.top_offset
                self.skeleton_points[sk_id] = Point(pos_x, pos_y, sk_id)

    def draw_skeleton(self, image, skeleton_to_display=None, points_to_display=None):

        if self.detected:

            # rysuje wybrany szkielet na zadanym obrazie

            # cały szkielet
            skeleton = [
                [16, 14],
                [14, 12],
                [17, 15],
                [15, 13],
                [12, 13],
                [6, 12],
                [7, 13],
                [6, 7],
                [6, 8],
                [7, 9],
                [8, 10],
                [9, 11],
                [2, 3],
                [1, 2],
                [1, 3],
                [2, 4],
                [3, 5],
                [4, 6],
                [5, 7],
            ]

            key_points = list(range(1, 18))

            # części szkieletu do wyświetlenia
            if not skeleton_to_display:
                skeleton_to_display = skeleton

            if not points_to_display:
                points_to_display = key_points

            # Plot the skeleton and keypointsfor coco datatset
            palette = np.array(
                [
                    [255, 128, 0],
                    [255, 153, 51],
                    [255, 178, 102],
                    [230, 230, 0],
                    [255, 153, 255],
                    [153, 204, 255],
                    [255, 102, 255],
                    [255, 51, 255],
                    [102, 178, 255],
                    [51, 153, 255],
                    [255, 153, 153],
                    [255, 102, 102],
                    [255, 51, 51],
                    [153, 255, 153],
                    [102, 255, 102],
                    [51, 255, 51],
                    [0, 255, 0],
                    [0, 0, 255],
                    [255, 0, 0],
                    [255, 255, 255],
                ]
            )

            pose_limb_color = palette[
                [0, 9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]
            ]
            pose_kpt_color = palette[
                [0, 16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]
            ]
            radius = 4

            for kid in key_points:
                r, g, b = pose_kpt_color[kid]
                x_coord, y_coord = (
                    self.skeleton_points[kid].x_disp,
                    self.skeleton_points[kid].y_disp,
                )
                if not (x_coord % 640 == 0 or y_coord % 640 == 0):
                    if kid in points_to_display:
                        cv2.circle(
                            image,
                            (x_coord, y_coord),
                            radius,
                            (int(r), int(g), int(b)),
                            -1,
                        )

            for sk_id, sk in enumerate(skeleton, 1):
                r, g, b = pose_limb_color[sk_id]

                pos1 = (
                    self.skeleton_points[sk[0]].x_disp,
                    self.skeleton_points[sk[0]].y_disp,
                )
                pos2 = (
                    self.skeleton_points[sk[1]].x_disp,
                    self.skeleton_points[sk[1]].y_disp,
                )

                if (
                    pos1[0] % 640 == 0
                    or pos1[1] % 640 == 0
                    or pos1[0] < 0
                    or pos1[1] < 0
                ):
                    continue
                if (
                    pos2[0] % 640 == 0
                    or pos2[1] % 640 == 0
                    or pos2[0] < 0
                    or pos2[1] < 0
                ):
                    continue
                if sk in skeleton_to_display:
                    cv2.line(image, pos1, pos2, (int(r), int(g), int(b)), thickness=2)

    def draw_skeleton_right_side(self, image):
        # rysuje prawą stronę szkieletu
        skeleton_right_side = [
            [17, 15],
            [15, 13],
            [7, 13],
            [7, 9],
            [9, 11],
            [5, 7],
            [3, 5],
            [1, 3],
        ]

        points_to_display = [1, 3, 5, 7, 9, 11, 13, 15, 17]

        self.draw_skeleton(image, skeleton_right_side, points_to_display)

    def draw_skeleton_left_side(self, image):
        # rysuje lewą stronę szkieletu

        skeleton_left_side = [
            [16, 14],
            [14, 12],
            [6, 12],
            [6, 8],
            [8, 10],
            [4, 6],
            [2, 4],
            [1, 2],
        ]

        points_to_display = [1, 2, 4, 6, 8, 10, 12, 14, 16]

        self.draw_skeleton(image, skeleton_left_side, points_to_display)

    def calc_ang(self):
        # tworzy słownik z danymi do wykresów

        # punkty obliczenia kątów
        # dodać kąty pozycji tułów/poziom i głowa/kosta/rower
        # wierzchołek kąta trzeba podać w środku listy (b)
        # kąty są mierzone do 180 st. (!)

        ang_list = {
            "right_knee": [13, 15, 17],
            "left_knee": [12, 14, 16],
            "right_hip": [7, 13, 15],
            "left_hip": [6, 12, 14],
            "right_elbow": [7, 9, 11],
            "left_elbow": [6, 8, 10],
        }

        for name, (a, b, c) in ang_list.items():

            # tworzenie wektorów:
            u = (
                self.skeleton_points[a].x - self.skeleton_points[b].x,
                self.skeleton_points[a].y - self.skeleton_points[b].y,
            )
            v = (
                self.skeleton_points[c].x - self.skeleton_points[b].x,
                self.skeleton_points[c].y - self.skeleton_points[b].y,
            )

            # obliczneie kąta miedzy wektorami
            ang_to_add = angle_between_vectors(u, v)[1]

            self.angs[name] = ang_to_add

    def stack_reach_ang_calc(self, trace_point, center_of_bar):

        # pomiar kąta względem poziomu - przeciwnie do wskazówek zegara
        # tworzenie wektorów:

        u = (
            center_of_bar.x - trace_point.x,
            center_of_bar.y - trace_point.y,
        )
        v = (1, 0)

        ang_to_add = angle_between_vectors(u, v)[1]

        return ang_to_add

    def draw_wheelbase_line(self, image):

        size_factor=self.stack_reach_len/self.bike_stack_reach_len

        central_point           = self.trace_point
        center_of_back_wheel    = transform_point(central_point, -self.bike_chain_stay*size_factor, 0)
        center_of_front_wheel   = transform_point(central_point, (-self.bike_chain_stay+self.bike_wheel_base)*size_factor, 0)
        
        # obliczenie kąta obrotu roweru w stosunku do poziomu
        # wartość dodatnia oznacza obrót zgodnie z ruchem wskazówek zegara

        bike_rotation = self.bike_stack_reach_ang - self.stack_reach_ang

        center_of_back_wheel=rotate_point(central_point, center_of_back_wheel, math.radians(bike_rotation))
        center_of_front_wheel=rotate_point(central_point, center_of_front_wheel, math.radians(bike_rotation))

        # rysuj linie bazy kół

        cv2.line(image, center_of_back_wheel.disp, center_of_front_wheel.disp, (0,0,0), thickness=2)

        # rysuje koła na końcu bazy kół

        # cv2.circle(image, center_of_back_wheel.disp, int(self.bike_wheel_size/2*size_factor), (0,0,0), thickness=2)
        # cv2.circle(image, center_of_front_wheel.disp, int(self.bike_wheel_size/2*size_factor), (0,0,0), thickness=2)


        # cv2.line(image, (0,0), central_point.disp, (0,0,0), thickness=2)

    def draw_side_view(self,image):

        # https://stackoverflow.com/questions/73130538/efficiently-rotate-image-and-paste-into-a-larger-image-using-numpy-and-opencv/
        # https://stackoverflow.com/questions/61516526/how-to-use-opencv-to-crop-circular-image
        # https://stackoverflow.com/questions/75554603/how-to-insert-a-picture-in-a-circle-using-opencv

        if self.detected:
            # określenie zakresu do wyświetlenia
            wielkosc_wycinka=200
            pose_y_cor = 0
            
            x, y, w, h = (
                int(self.trace_point.x-wielkosc_wycinka),
                int(self.trace_point.y-pose_y_cor-wielkosc_wycinka),
                wielkosc_wycinka*2,
                wielkosc_wycinka*2,
            )
            sub_img = image[y : y + h, x : x + w]
            white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

            # res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)
            res = cv2.addWeighted(sub_img, 1, white_rect, 0, 1.0)

            bike_rotation = self.bike_stack_reach_ang - self.stack_reach_ang

            rot_res = cv2.getRotationMatrix2D((wielkosc_wycinka,wielkosc_wycinka), bike_rotation, 1)

            img_rot = cv2.warpAffine(res,rot_res,(2*wielkosc_wycinka,2*wielkosc_wycinka))

            # wklejenie zdjęcia na boku

            x_place = image.shape[1]-2*wielkosc_wycinka
            y_place = 0

            image[y_place : y_place + h, x_place : x_place + w] = img_rot

class Clip:
    def __init__(self, vid_name):
        self.name = vid_name
        self.vid_path = f"{os.getcwd()}\\_data\\{self.name}"

        self.cap = cv2.VideoCapture(self.vid_path)

        # dane do korekty pozycji x y punktów - ze wzgledu na zmianę formatu video do rozpoznawania "letterbox"

        self.left_ofset = 0
        self.top_offset = 0
        self.frame_offsets = self.left_ofset, self.top_offset
        self.calc_frame_offset()

        # self.org_vid_prop=OrginalVideoProperitier(self.vid_path)

        self.frames = {}
        self.add_frames()

        self.frames_amount = len(self.frames)

        # dane do wykresów i linii
        self.charts = {}
        self.generate_data_charts()
        self.generate_data_stack_reach_len()
        self.generate_data_stack_reach_ang()

        self.lines = {}
        self.generate_data_lines()

        # ustawienia do rysowania wykresów
        self.chart_y_pos = 750
        self.chart_height = 90

        self.draw_background        = True
        self.draw_leading_line      = True
        self.draw_side_view_state   = True

        self.charts_state = {
            "right_knee_chart": [True, (90, 180), True],
            "left_knee_chart": [False, (90, 180), True],
            "right_hip_chart": [False, (90, 180), True],
            "left_hip_chart": [False, (90, 180), True],
            "right_elbow_chart": [False, (90, 180), True],
            "left_elbow_chart": [False, (90, 180), True],
            "stack_reach_len": [True, (50, 120), False],
            "stack_reach_ang": [True, (0, 90), True],
        }

        # ustawienia rysowania linii
        self.lines_state = {"trace_line": False, "center_of_gravity_line": False}

    def calc_frame_offset(self):

        self.cap.set(0, 1)
        _, img = self.cap.read()
        frame_width = int(self.cap.get(3))

        self.left_ofset, self.top_offset = letterbox_calc(
            img, (frame_width), stride=64, auto=True
        )

    def add_frames(self):

        kpts_json_path = (
            f"{os.getcwd()}\\_analysed\\{self.name.replace('.mp4','_kpts.json')}"
        )

        with open(kpts_json_path, "r") as f:
            data = json.load(f)

        for frame_count, data in enumerate(data.items()):

            # frame_time, kpts = data

            # do zmiany!!!!!!!!!!!!!!!!
            frame_time, kpts = data
            frame_time = float(frame_time)
            # do zmiany!!!!!!!!!!!!!!!!

            self.frames[frame_count] = Frame(
                frame_count, frame_time, kpts, self.frame_offsets
            )

    def generate_data_charts(self):

        # kąty zgięcia łokci, kolan i bioder
        self.charts = {
            "right_knee_chart": {"name": "prawe kolano [st.]"},
            "left_knee_chart": {"name": "lewe kolano [st.]"},
            "right_hip_chart": {"name": "prawe biodro [st.]"},
            "left_hip_chart": {"name": "lewe biodro [st.]"},
            "right_elbow_chart": {"name": "prawy łokieć [st.]"},
            "left_elbow_chart": {"name": "lewy łokieć [st.]"},
        }

        for charts in self.charts.keys():
            for frame, frame_obj in self.frames.items():
                if frame_obj.detected:
                    self.charts[charts][frame] = [
                        frame_obj.skeleton_points[17].x_disp,
                        int(frame_obj.angs[charts[:-6]]),
                    ]
                else:
                    self.charts[charts][frame] = None

    def generate_data_stack_reach_len(self):
        # wykres pomocniczy do sprawdzania czy video i rozpoznanie pozwala na ustalenie pozycji roweru. Mierzy odległość kostka-ręka 17-13

        self.charts["stack_reach_len"] = {"name": "reach_stack_len [m]"}

        for frame, frame_obj in self.frames.items():
            if frame_obj.detected and frame_obj.stack_reach_len != None:
                self.charts["stack_reach_len"][frame] = [
                    frame_obj.skeleton_points[17].x_disp,
                    int(frame_obj.stack_reach_len),
                ]
            else:
                self.charts["stack_reach_len"][frame] = None

    def generate_data_stack_reach_ang(self):
        # wykres pomocniczy do sprawdzania czy video i rozpoznanie pozwala na ustalenie pozycji roweru. Mierzy kat pochynia lini kostka-ręka 17-13

        self.charts["stack_reach_ang"] = {"name": "reach_stack_ang [st.]"}

        for frame, frame_obj in self.frames.items():
            if frame_obj.detected and frame_obj.stack_reach_ang != None:
                self.charts["stack_reach_ang"][frame] = [
                    frame_obj.skeleton_points[17].x_disp,
                    int(frame_obj.stack_reach_ang),
                ]
            else:
                self.charts["stack_reach_ang"][frame] = None

    def generate_data_lines(self):
        # linie trasy (wg punktu kostki 17 i 16) i środka ciężkości (biodro 13 i 12)
        self.lines["trace_line"] = {"name": "linia trasy"}
        self.lines["center_of_gravity_line"] = {"name": "linia środka ciężkości"}

        for frame, frame_obj in self.frames.items():
            if frame_obj.detected:
                self.lines["trace_line"][frame] = [
                    frame_obj.skeleton_points[17].x_disp,
                    int(frame_obj.trace_point.y),
                ]
            else:
                self.lines["trace_line"][frame] = None

        for frame, frame_obj in self.frames.items():
            if frame_obj.detected:
                self.lines["center_of_gravity_line"][frame] = [
                    frame_obj.skeleton_points[17].x_disp,
                    int(frame_obj.center_of_gravity.y),
                ]
            else:
                self.lines["center_of_gravity_line"][frame] = None

    def draw_charts(self, image, frame_number):

        chart_index = 0
        charts_lines_to_draw = []

        for chart_name, chart_state_data in self.charts_state.items():
            state, chart_range, rev_chart = chart_state_data
            if state:

                # rysowanie podkładu

                self.draw_chart_base(
                    image,
                    chart_name,
                    chart_index,
                    chart_range,
                    frame_number=frame_number,
                )

                # zebranie danych do rysowania lini wykresu
                # pobranie danych
                data_to_draw = self.charts[chart_name]

                frames = sorted(i for i in data_to_draw.keys() if type(i) == int)

                tmp_store = []
                for frame in frames[1:]:

                    pos_1 = self.charts[chart_name][frame - 1]
                    pos_2 = self.charts[chart_name][frame]

                    # jeśli dane dla obu klatek występują to:
                    if all((pos_1, pos_2)):
                        # korekta - odwócenie wykresu do góry nogami, przesunięcie w pionie i ograniczenie zakresu

                        delta_y = (
                            self.chart_y_pos
                            + chart_range[1]
                            + chart_index * self.chart_height
                        )

                        pos_1 = (
                            self.charts[chart_name][frame - 1][0],
                            -1 * self.charts[chart_name][frame - 1][1] + delta_y,
                        )
                        pos_2 = (
                            self.charts[chart_name][frame][0],
                            -1 * self.charts[chart_name][frame][1] + delta_y,
                        )

                        tmp_store.append((pos_1, pos_2))

                charts_lines_to_draw.append(tmp_store)

                chart_index += 1

        # rysowanie linii wykresów
        for line_to_draw in charts_lines_to_draw:
            self.draw_line(image, line_to_draw, color=(255, 128, 0))

    def draw_trace(self, image, frame_number):
        # zebranie danych do rysowania lini wykresu
        # pobranie danych
        data_to_draw = self.lines["trace_line"]
        lines_to_draw = []

        frames = sorted(i for i in data_to_draw.keys() if type(i) == int)

        tmp_store = []
        for frame in frames[1:]:

            pos_1 = self.lines["trace_line"][frame - 1]
            pos_2 = self.lines["trace_line"][frame]

            # jeśli dane dla obu klatek występują to:
            if all((pos_1, pos_2)):

                pos_1 = self.lines["trace_line"][frame - 1]
                pos_2 = self.lines["trace_line"][frame]

                tmp_store.append((pos_1, pos_2))

        lines_to_draw.append(tmp_store)

        # rysowanie linii trasy
        for line_to_draw in lines_to_draw:
            self.draw_line(image, line_to_draw, color=(137, 126, 23))

        data_to_draw = self.lines["center_of_gravity_line"]
        lines_to_draw = []

        frames = sorted(i for i in data_to_draw.keys() if type(i) == int)

        tmp_store = []
        for frame in frames[1:]:

            pos_1 = self.lines["center_of_gravity_line"][frame - 1]
            pos_2 = self.lines["center_of_gravity_line"][frame]

            # jeśli dane dla obu klatek występują to:
            if all((pos_1, pos_2)):

                pos_1 = self.lines["center_of_gravity_line"][frame - 1]
                pos_2 = self.lines["center_of_gravity_line"][frame]

                tmp_store.append((pos_1, pos_2))

        lines_to_draw.append(tmp_store)

        # rysowanie linii środka cieżkości
        # na razie nie rysuje - do analizy czy nie lepiej pokazać rzeczywistą odległość kostka- biodro, zamiast odległosci w pionie, bo na wykresie myli
        # for line_to_draw in lines_to_draw:
        #     self.draw_line(image, line_to_draw, color=(20, 126, 23))

    def draw_line(self, image, line_to_draw, color=(0, 0, 0), thickness=3):
        # rysowanie wykresu
        for line in line_to_draw:

            pos_1, pos_2 = line

            cv2.line(image, pos_2, pos_1, color, thickness)

    def draw_chart_base(
        self,
        image,
        chart_name,
        chart_index,
        chart_range,
        color=(115, 200, 221, 50),
        frame_number=None,
    ):

        # rysowanie tła wykresu
        background_delta_y_1 = self.chart_y_pos + (chart_index) * self.chart_height
        background_delta_y_2 = self.chart_y_pos + (chart_index + 1) * self.chart_height

        # podklad=[[0,background_delta_y_1],[0,background_delta_y_2],
        #          [image.shape[1],background_delta_y_2],
        #          [image.shape[1],background_delta_y_1]]

        # podklad = np.array(podklad)
        if self.draw_background:
            x, y, w, h = (
                0,
                background_delta_y_1,
                image.shape[1],
                background_delta_y_2 - background_delta_y_1,
            )
            sub_img = image[y : y + h, x : x + w]
            white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

            res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

            # Putting the image back to its position
            image[y : y + h, x : x + w] = res
            # cv2.fillPoly(image, [podklad], color)

        # rysowanie lini ograniczajacych wykres
        chart_frame_color = (0, 0, 0)
        pos_1 = 0, background_delta_y_1
        pos_2 = image.shape[1], background_delta_y_1

        cv2.line(image, pos_1, pos_2, chart_frame_color, thickness=2)

        pos_1 = 0, background_delta_y_2
        pos_2 = image.shape[1], background_delta_y_2

        cv2.line(image, pos_1, pos_2, chart_frame_color, thickness=2)

        # opis wykresu

        # object details
        # tytuł
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8
        text_color = (0, 0, 0)
        thickness = 2
        try:
            text = unidecode(
                self.charts[chart_name]["name"]
            )  # - do zmiany tak żeby się wyświetlały polskie znaki
            lok_opis_wykresu = (20, background_delta_y_1 + 25)
        except:
            pass
        cv2.putText(
            image, text, lok_opis_wykresu, font, fontScale, text_color, thickness
        )

        # opisy, tylko jeśli na ekranie jest wykryty szkielet
        if self.frames[frame_number].detected:
            # wartość

            try:
                lok_opis_wykresu = (
                    self.charts[chart_name][frame_number][0] + 20,
                    background_delta_y_1 + 25,
                )
            except:
                text = "x"
            text = str(self.charts[chart_name][frame_number][1])
            cv2.putText(
                image, text, lok_opis_wykresu, font, fontScale, text_color, thickness
            )

            # rysowanie linie wiodącej dla klatki
            if self.draw_leading_line and frame_number:

                leading_line_color = (0, 0, 0)

                pos_1 = self.charts[chart_name][frame_number][0], 0
                pos_2 = self.charts[chart_name][frame_number][0], image.shape[0]

                cv2.line(image, pos_1, pos_2, leading_line_color, thickness=2)

    def display_frame(self, frame_number):

        self.cap.set(1, frame_number)

        _, image = self.cap.read()

        self.frames[frame_number].draw_skeleton_right_side(image)

        self.frames[frame_number].draw_wheelbase_line(image)

        self.frames[frame_number].draw_side_view(image)

        self.draw_trace(image, frame_number)

        self.draw_charts(image, frame_number)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # convert frame to RGB

        self.image = image

        self.image = Image.fromarray(image)

    def make_video_clip(self):

        output_folder = "_clips"

        output_video_clip_file = "{}\\{}".format(
            output_folder, self.name.replace(".mp4", "_analized.mp4")
        )

        out = cv2.VideoWriter(
            output_video_clip_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080)
        )

        for frame_number in range(self.frames_amount - 1):

            self.cap.set(1, frame_number)
            _, image = self.cap.read()

            self.frames[frame_number].draw_skeleton_right_side(image)

            self.draw_charts(image, frame_number)

            out.write(image)  # writing the video frame

        print(f"{self.name} gotowe.")

class Draws_states:
    # ustala co ma być wyświetlane
    def __init__(self):

        #główna klatka
        self.main_frame_draw_state                      = True
        self.main_frame_background_draw_state           = True

        # szkielet
        self.main_skeleton_draw_state                   = False
        self.main_skeleton_right_draw_state             = True
        self.main_skeleton_left_draw_state              = False

        # wykresy
        # kąty zgięcia
        self.right_knee_ang_chart_draw_state            = True
        self.right_hip_ang_chart_draw_state             = True
        self.right_elbow_ang_chart_draw_state           = True
        self.left_knee_ang_chart_draw_state             = False
        self.left_hip_ang_chart_draw_state              = False
        self.left_elbow_ang_chart_draw_state            = False

        # inne
        self.stack_reach_len_chart_draw_state           = False
        self.stack_reach_ang_chart_draw_state           = False
        self.speed_chart_draw_state                     = False

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
        self.side_frame_draw_state                      = True
        self.side_frame_background_draw_state           = True

        # szkielet na bocznym widoku
        self.side_skeleton_draw_state                   = False
        self.side_skeleton_right_draw_state             = True
        self.side_skeleton_left_draw_state              = False   

        # linia bazy kół na bocznym widoku
        self.side_wheel_base_line_draw_state            = True

        # pionowa linia wiodąca - głowa
        self.side_head_leading_line_draw_state          = True

        #################################################
        # pozycje do wyświetlenia jako checkboxy
        self.checkboxes = ['',
            'main_frame_draw_state',
            'main_frame_background_draw_state',
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
            'side_head_leading_line_draw_state']