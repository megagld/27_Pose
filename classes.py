import os
import json
import cv2
import numpy as np
import math
from unidecode import unidecode
from PIL import Image, ImageTk
from ffprobe import FFProbe
from general_bm import letterbox_calc
from functions import *

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

def get_mid(kpts, sk_id_1, sk_id_2):
    # zwraca punkt środkowy między dwoma punktami szkieletu
    steps = 3
    pos_x_1, pos_y_1 = (kpts[(sk_id_1 - 1) * steps]), (
                        kpts[(sk_id_1 - 1) * steps + 1])
    pos_x_2, pos_y_2 = (kpts[(sk_id_2 - 1) * steps]), (
                        kpts[(sk_id_2 - 1) * steps + 1] )

    return Point((pos_x_2 + pos_x_1) / 2, (pos_y_2 + pos_y_1) / 2)

class Point:
    def __init__(self, pos_x, pos_y, sk_id=None):
        self.sk_id = sk_id

        self.x = pos_x
        self.y = pos_y
        self.pos = (self.x, self.y)

        self.x_disp = int(pos_x)
        self.y_disp = int(pos_y)
        self.pos_disp   = (self.x_disp, self.y_disp)

class Frame:
    def __init__(self, frame_count, frame_time, kpts, frame_offsets):

        self.frame_count        = frame_count
        self.frame_time         = frame_time
        self.kpts               = kpts
        self.detected           = kpts != []
        self.skeleton_points    = {}

        self.right_knee_ang     = None
        self.right_hip_ang      = None
        self.right_elbow_ang    = None

        self.left_knee_ang      = None
        self.left_hip_ang       = None
        self.left_elbow_ang     = None

        self.trace_point        = None
        self.center_of_gravity  = None
        self.center_of_bar      = None
        self.stack_reach_len    = None
        self.stack_reach_ang    = None
        self.bike_rotation      = None
        self.side_view_size     = None
        self.size_factor        = None

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

        self.update_data()

    def update_data(self):
        if self.detected:

            # organizuje pomierzone punkty kpts w słownik gdzie key= id szkieletu, a value= obiekt Point
            self.organize_skeleton_points()

            # oblicza kąty między zadanymi punktami, zestawia je w zmiennych self.___.ang
            self.calc_ang()

            # DO ANALIZY CZY LEPIEJ DAĆ ŚRODEK MIĘDZY PUNKTAMI CZY PUNKTY Z JEDNEJ STRONY
            # skorygować o zmianę jeśli film jest nagrywany z lewej strony roweru
            # może dodać zmienną - info o kierunku poruszania sie roweru i na tej podstawie która strona jest nagrywana

            self.trace_point        = self.skeleton_points[17]
            self.center_of_gravity  = self.skeleton_points[13]
            self.center_of_bar      = self.skeleton_points[11]

            # self.trace_point = self.get_mid(self.kpts, 16, 17)
            # self.center_of_gravity = self.get_mid(self.kpts,12, 13)
            # self.center_of_bar = self.get_mid(self.kpts, 10, 11)

            self.stack_reach_len    = get_dist(self.trace_point, 
                                               self.center_of_bar)

            self.stack_reach_ang    = self.stack_reach_ang_calc(self.trace_point, 
                                                                self.center_of_bar)

            self.calc_bike_rotation()
            self.calc_side_view_size()
            self.calc_size_factor()

    def organize_skeleton_points(self):
        # tworzy słownik ze współrzędnymi punktów szkieletu
        # koryguje wspórzędne o to że rozpoznanie było na zmienionym formacie filmu - letterbox

        steps = 3
        for sk_id in range(1, 18):
            pos_x   =   (self.kpts[(sk_id - 1) * steps])     + self.left_ofset
            pos_y   =   (self.kpts[(sk_id - 1) * steps + 1]) + self.top_offset

            self.skeleton_points[sk_id] = Point(pos_x, 
                                                pos_y, 
                                                sk_id)

    def calc_ang(self):
        # tworzy słownik z danymi do wykresów

        # punkty obliczenia kątów
        # wierzchołek kąta trzeba podać w środku listy (b)
        # kąty są mierzone do 180 st. (!)

        angs_list = {
            "right_knee_ang": [13, 15, 17],
            "left_knee_ang": [12, 14, 16],
            "right_hip_ang": [7, 13, 15],
            "left_hip_ang": [6, 12, 14],
            "right_elbow_ang": [7, 9, 11],
            "left_elbow_ang": [6, 8, 10],
        }

        for name, (a, b, c) in angs_list.items():

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
            calculated_ang = angle_between_vectors(u, v)[1]

            setattr(self, name, calculated_ang)

    def draw_skeleton(self, image, skeleton_to_display=None, points_to_display=None, delta_x=0, delta_y=0):

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

                # ustalenie wsp i przesunięcie punktów o delta_x delta_y
                x_coord, y_coord = (
                    self.skeleton_points[kid].x_disp + delta_x,
                    self.skeleton_points[kid].y_disp + delta_y,
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

                # ustalenie wsp i przesunięcie punktów o delta_x delta_y

                pos1 = (
                    self.skeleton_points[sk[0]].x_disp + delta_x,
                    self.skeleton_points[sk[0]].y_disp + delta_y,
                )
                pos2 = (
                    self.skeleton_points[sk[1]].x_disp + delta_x,
                    self.skeleton_points[sk[1]].y_disp + delta_y,
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

    def draw_skeleton_right(self, image, delta_x=0, delta_y=0):
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

        self.draw_skeleton(image, skeleton_right_side, points_to_display, delta_x=delta_x, delta_y=delta_y)

    def draw_skeleton_left(self, image, delta_x=0, delta_y=0):
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

        self.draw_skeleton(image, skeleton_left_side, points_to_display, delta_x=delta_x, delta_y=delta_y)

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

    def draw_side_view(self, image, draws_states):

        # boczne okno może być wyświetlane tylko jeśli jest wykryty szkielet
        if self.detected:

            # określenie zakresu do wyświetlenia

            # ustalenie punktów wycinka
            pose_y_cor = 0
            x, y, w, h = (
                self.trace_point.x_disp-self.side_view_size,
                self.trace_point.y_disp-pose_y_cor-self.side_view_size,
                self.side_view_size*2,
                self.side_view_size*2)

            # określenie średnicy koła do wyświetlenia bocznego obrazu

            x_circle = image.shape[1]- self.side_view_size
            y_circle = self.side_view_size

            # obraz boczny

            # maska dla obrazu bocznego

            sub_mask_rect = np.ones(image.shape, dtype=np.uint8) * 0

            cv2.circle(sub_mask_rect,(x_circle,y_circle),self.side_view_size, (255,255,255),-1)

            if draws_states.side_frame_background_draw_state:

            # wycięcie obrazu bocznego z głównej klatki image

                if any((x < 0,
                    (x + self.side_view_size * 2) > image.shape[1],
                    y < 0,
                    (x + self.side_view_size * 2) > image.shape[1])):

                    sub_crop_rect = self.crop_extended(image, x, y, w, h)

                else:
                    sub_crop_rect = image[y : y + h,
                                        x : x + w].copy()
            else:
                sub_crop_rect = np.ones((w,h,3), dtype=np.uint8) * 0


            sub_rect = np.ones(image.shape, dtype=np.uint8) * 0

            # rysowanie elementów wg draws_states

            self.draw_side_view_items(sub_crop_rect, 
                                      draws_states, 
                                      delta_x = -1 * x, 
                                      delta_y = -1 * y)

            # obrót wycinka

            rot_res = cv2.getRotationMatrix2D((self.side_view_size,self.side_view_size), self.bike_rotation, 1)

            img_rot = cv2.warpAffine(sub_crop_rect,rot_res,(2*self.side_view_size,2*self.side_view_size))

            # wklejenie zdjęcia na boku na czarny podkład sub_rect

            x_place = image.shape[1]-2*self.side_view_size
            y_place = 0

            sub_rect[y_place : y_place + h, x_place : x_place + w] = img_rot

            # wycinanie bocznego rysunku wg maski

            result = np.where(sub_mask_rect==0, image, sub_rect)

            # wklejanie rezultatu na główny obraz

            x,y,_ = image.shape
            image[0:x, 0:y] = result

            # rysowanie ramki wokół bocznego rysunka

            cv2.circle(image,(x_circle,y_circle),self.side_view_size, (0,0,0),5)

    def crop_extended(self, image, x, y, w, h):

        sub_crop_rect = np.ones((2*self.side_view_size,2*self.side_view_size,3), dtype=np.uint8) * 0

        # rozszerzenie wycinka jeśli wychodzi poza zakres image na wartości ujemne lub poza rozmiar

        ext_x_min = x * (x < 0)
        ext_x_max = (image.shape[1] -(x + 2*self.side_view_size)) * ((x + self.side_view_size * 2) > image.shape[1])

        ext_y_min = y * (y < 0)
        ext_y_max = (image.shape[0] - (y + 2*self.side_view_size)) * ((y + self.side_view_size * 2) > image.shape[0])

        tmp_x = x - ext_x_min
        tmp_y = y - ext_y_min

        tmp_w = w + ext_x_min + ext_x_max
        tmp_h = h + ext_y_min + ext_y_max

        tmp_sub_crop_rect = image[tmp_y : tmp_y + tmp_h,
                                    tmp_x : tmp_x + tmp_w].copy()

        sub_crop_rect[-1 * ext_y_min : -1 * ext_y_min + tmp_h,
                        -1 * ext_x_min : -1 * ext_x_min + tmp_w] = tmp_sub_crop_rect
        
        return sub_crop_rect

    def calc_side_view_size(self):
        self.side_view_size=250  

    def calc_bike_rotation(self):
        self.bike_rotation = self.bike_stack_reach_ang - self.stack_reach_ang

    def calc_size_factor(self):
        # temat do ogarnięcia!!!!
        self.size_factor = 0.15
        # self.size_factor=self.stack_reach_len/self.bike_stack_reach_len

    def draw_side_view_items(self, sub_crop_rect, draws_states, delta_x=0, delta_y=0):

        if draws_states.side_wheel_base_line_draw_state:
            self.draw_wheelbase_line(sub_crop_rect, delta_x, delta_y)
        if draws_states.side_head_leading_line_draw_state:
            self.draw_head_leading_line(sub_crop_rect, delta_x, delta_y)
        if draws_states.side_skeleton_draw_state:
            self.draw_skeleton(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)
        if draws_states.side_skeleton_right_draw_state:
            self.draw_skeleton_right(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)
        if draws_states.side_skeleton_left_draw_state:
            self.draw_skeleton_left(sub_crop_rect, delta_x=delta_x, delta_y=delta_y)

    def draw_head_leading_line(self, image, delta_x=0, delta_y=0):

        if self.detected:

            # określenie wsp. punktu głowy

            crop_head_point = transform_point(self.skeleton_points[1], delta_x, delta_y)

            # oblicznie wsp. rzednych lini wiodoącej na wycinku
            x1 = x2 = crop_head_point.x_disp
            y1 = 0
            y2 = image.shape[1]

            start_point = Point(x1, y1)
            end_point = Point(x2, y2)

            # obrót lini wiodocej wzgledem głowy o kąt obrotu roweru
            start_point = rotate_point(crop_head_point,
                                           start_point,
                                           math.radians(self.bike_rotation))
            end_point = rotate_point(crop_head_point,
                                         end_point,
                                         math.radians(self.bike_rotation))

            # rysuj linie wiodącą głowy
            cv2.line(image, start_point.pos_disp, end_point.pos_disp, (255, 128, 0), thickness=2)

    def draw_wheelbase_line(self, image, delta_x=0, delta_y=0):

        if self.detected:

            central_point           = self.trace_point
            center_of_back_wheel    = transform_point(central_point, -self.bike_chain_stay*self.size_factor, 0)
            center_of_front_wheel   = transform_point(central_point, (-self.bike_chain_stay+self.bike_wheel_base)*self.size_factor, 0)

            # obliczenie kąta obrotu roweru w stosunku do poziomu
            # wartość dodatnia oznacza obrót zgodnie z ruchem wskazówek zegara

            center_of_back_wheel=rotate_point(central_point, center_of_back_wheel, math.radians(self.bike_rotation))
            center_of_front_wheel=rotate_point(central_point, center_of_front_wheel, math.radians(self.bike_rotation))

            center_of_back_wheel=transform_point(center_of_back_wheel, delta_x, delta_y)
            center_of_front_wheel=transform_point(center_of_front_wheel, delta_x, delta_y)

            # rysuj linie bazy kół

            cv2.line(image, center_of_back_wheel.pos_disp, center_of_front_wheel.pos_disp, (255, 128, 0), thickness=3)

            # rysuje koła na końcu bazy kół

            # cv2.circle(image, center_of_back_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)
            # cv2.circle(image, center_of_front_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)

class Clip:
    def __init__(self, vid_name):

        self.name           = vid_name
        self.vid_path       = f"{os.getcwd()}\\_data\\{self.name}"
        self.kpts_json_path = f"{os.getcwd()}\\_analysed\\{self.name.replace('.mp4','_kpts.json')}"

        self.cap = cv2.VideoCapture(self.vid_path)

        # dane do korekty pozycji x y punktów - ze wzgledu na zmianę formatu video do rozpoznawania "letterbox"

        self.left_ofset = 0
        self.top_offset = 0
        self.frame_offsets = self.left_ofset, self.top_offset
        self.calc_frame_offset()

        # zestawia wszyskie klatki clipu

        self.frames = {}
        self.colect_frames()

        self.frames_amount = len(self.frames)

        # dane do wykresów i linii
        self.avilable_charts = {
            "right_knee_ang_chart": {
                "chart_description": "prawe kolano [st.]",
                "range_min": 17,
                "range_max": 180,
                "reverse": False,
            },
            "left_knee_ang_chart": {
                "chart_description": "lewe kolano [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
            },
            "right_hip_ang_chart": {
                "chart_description": "prawe biodro [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
            },
            "left_hip_ang_chart": {
                "chart_description": "lewe biodro [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
            },
            "right_elbow_ang_chart": {
                "chart_description": "prawy łokieć [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
            },
            "left_elbow_ang_chart": {
                "chart_description": "lewy łokieć [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
            },
            "stack_reach_len_chart": {
                "chart_description": "odległość stack/reach [m]",
                "range_min": 50,
                "range_max": 120,
                "reverse": False,
            },
            "stack_reach_ang_chart": {
                "chart_description": "kąt stack/reach [st.]",
                "range_min": 0,
                "range_max": 90,
                "reverse": False,
            },
        }
        self.charts = {}
        self.generate_charts_data()

        self.avilable_lines = {
            "trace_line": {
                "line_description": "linia trasy",
                "frame_atr": 'trace_point',
                'line_color': (137, 126, 23)
            },
            "center_of_gravity_line": {
                "line_description": "inia środka ciężkości",
                "frame_atr": 'center_of_gravity',
                'line_color': (20, 126, 23)  
            },
        }
        self.lines = {}
        self.generate_lines_data()

        # ustawienia do rysowania wykresów
        self.chart_y_pos = 750
        self.chart_height = 90

        # ustala zakres dla widgeta Scale

        self.scale_range_min = 0
        self.scale_range_max = self.frames_amount-1
        self.calculate_scale_range()

    def calculate_scale_range(self):
        # zakres suwaka ma być od pierwszej do ostaniej klatki na której jest wykryty szkielet
        self.scale_range_min = min(i for i,j in self.frames.items() if j.detected)
        self.scale_range_max = max(i for i,j in self.frames.items() if j.detected)

    def calc_frame_offset(self):

        self.cap.set(0, 1)
        _, img = self.cap.read()
        frame_width = int(self.cap.get(3))

        self.left_ofset, self.top_offset = letterbox_calc(img, 
                                                          (frame_width), 
                                                          stride=64, 
                                                          auto=True)

    def colect_frames(self):

        # zestawia klatki w słownik gdzie key=numer klatki (od 0) a value= obiekt klatki Frame

        with open(self.kpts_json_path, "r") as f:
            data = json.load(f)

        for frame_count, data in enumerate(data.items()):

            frame_time, kpts = data
            frame_time = float(frame_time)

            self.frames[frame_count] = Frame(frame_count,
                                             frame_time,
                                             kpts,
                                             self.frame_offsets)

    def generate_charts_data(self):
        # tworzenie obiektu wykresu
        for chart_name, chart_setup in self.avilable_charts.items():

            # sam pusty obiekt i jego setup:
            self.charts[chart_name] = Chart(
                name=chart_name,
                chart_description=chart_setup["chart_description"],
                range_min=chart_setup["range_min"],
                range_max=chart_setup["range_max"],
                reverse=chart_setup["reverse"],
            )

            # dodanie do wykresu punkty z kolejnych klatek:
            tmp_chart_points_dict   =   {}

            for frame_number, frame_obj in self.frames.items():
                if frame_obj.detected:  # jeśli szkielet został wykryty na klatce

                    # tworzenie nazwy zmiennej do pobrania z obiektu klatki
                    frame_variable_name = chart_name.replace("_chart", "")

                    x_pos = frame_obj.skeleton_points[17].x_disp
                    y_pos = int(getattr(frame_obj, frame_variable_name))

                    tmp_chart_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.charts[chart_name].chart_points = tmp_chart_points_dict

    def draw_line(self, image, line_to_draw, color=(0, 0, 0), thickness=3):
        # rysowanie wykresu
        for line in line_to_draw:

            pos_1, pos_2 = line

            cv2.line(image, pos_2, pos_1, color, thickness)

    def draw_charts(self, image, draws_states, frame_number):

        # ustalenie które wykresy mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości wykresów  i zestawienie obiektów wykresów

        charts_to_draw = []

        # iteracja po dostępnych obiektach wykresów i porównanie z obiektem stan druku 'draws_states'
        for chart_name in self.charts.keys():
            chart_name_draw_state_atr = chart_name+'_draw_state'
            if getattr(draws_states, chart_name_draw_state_atr) == True:
                charts_to_draw.append(self.charts[chart_name])

        charts_amount = len(charts_to_draw)

        if charts_amount == 0: return

        # rysowanie podkładu i lini ograniczajacych

        if draws_states.charts_background_draw_state == True:
            self.draw_charts_base(image, charts_amount)

        # rysowanie lini wykresów

        for chart_number, chart in enumerate(charts_to_draw):

            chart.generate_line_data(self.chart_y_pos, chart_number)
            line_to_draw = chart.chart_line

            # setup
            line_thickness = 2
            line_color = (255, 128, 0)

            self.draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        # rysowanie opisów

        if draws_states.charts_descriptions_draw_state == True:

            for chart_number, chart in enumerate(charts_to_draw):

                self.draw_charts_descriptions(image, chart_number, chart, frame_number)

    def generate_lines_data(self):

        # tworzenie obiektu lini
        for line_name, line_setup in self.avilable_lines.items():
            # sam pusty obiekt i jego setup:
            self.lines[line_name] = Line(
                name=line_name,
                line_description = line_setup["line_description"],
                color = line_setup["line_color"]
            )

            # dodanje do lini punkty z kolejnych klatek:
            tmp_line_points_dict = {}

            for frame_number, frame_obj in self.frames.items():
                if frame_obj.detected:  # jeśli szkielet został wykryty na klatce

                    # tworzenie nazwy zmiennej do pobrania z obiektu klatki
                    frame_variable_name = line_setup["frame_atr"]

                    x_pos = frame_obj.skeleton_points[17].x_disp
                    y_pos = int(getattr(frame_obj, frame_variable_name).y_disp)

                    tmp_line_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.lines[line_name].line_points = tmp_line_points_dict

    def draw_charts_base(self, image, charts_amount):

        # rysowanie tła wykresu
        # ustalenie położenia w pionie
        background_delta_y_1 = self.chart_y_pos
        background_delta_y_2 = self.chart_y_pos + (charts_amount  * self.chart_height)

        # ustalenie współrzędnych punktów wykresu
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

        # rysowanie linii ograniczajacych wykres
        # setup
        chart_frame_color = (0, 0, 0)
        chart_frame_thickness = 2

        for line_numer in range(charts_amount+1):

            pos_1 = 0, background_delta_y_1 + (line_numer * self.chart_height)
            pos_2 = image.shape[1], background_delta_y_1 + (line_numer * self.chart_height)

            cv2.line(image, pos_1, pos_2, chart_frame_color, thickness=chart_frame_thickness)

    def draw_charts_descriptions(self, image, chart_number, chart, frame_number):

        # opis wykresu

        # setup
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8
        text_color = (0, 0, 0)
        thickness = 2

        # ustalenie tekstu głównego opisu do wyświetlenia i jego pozycji
        # - do zmiany tak żeby się wyświetlały polskie znaki
        main_description = unidecode(chart.chart_description)

        x_pos = 20
        y_pos = self.chart_y_pos + chart_number * self.chart_height + 25

        main_description_loc = (x_pos, y_pos)

        cv2.putText(
            image,
            main_description,
            main_description_loc,
            font,
            fontScale,
            text_color,
            thickness,
        )

        # opisy, tylko jeśli na ekranie jest wykryty szkielet tj. obiekt chart ma dane dla klatki
        try:
            x_pos = chart.chart_points[frame_number].x_disp + 20
            y_pos = self.chart_y_pos + (chart_number + 1) * self.chart_height - 20

            chart_value_description = str(chart.chart_points[frame_number].y_disp)

            chart_value_description_loc = (x_pos, y_pos)

            cv2.putText(
                image,
                chart_value_description,
                chart_value_description_loc,
                font,
                fontScale,
                text_color,
                thickness,
            )
        except:
            pass

    def draw_leading_line(self, image, frame_number):
        # rysowanie linie wiodącej dla klatki, jeśli w ogóle jest szkielet
        if self.frames[frame_number].detected == True:

            # leading line setup
            leading_line_color = (255, 128, 0)
            leading_line_thickness= 2

            pos_1 = self.frames[frame_number].trace_point.x_disp, 0
            pos_2 = self.frames[frame_number].trace_point.x_disp, image.shape[0]

            cv2.line(image, pos_1, pos_2, leading_line_color, thickness=leading_line_thickness)

    def draw_lines(self, image, draws_states):

        # ustalenie które linie mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości lini  i zestawienie obiektów wykresów

        # iteracja po dostępnych obiektach lini i porównanie z obiektem stan druku 'draws_states'
        for line_name, line in self.lines.items():
            line_name_draw_state_atr = line_name + '_draw_state'
            if getattr(draws_states, line_name_draw_state_atr) == True:

                line.generate_line_data()
                line_to_draw = line.line_line

                # setup
                line_thickness = 3
                line_color = line.line_color

                self.draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        # do analizy czy nie lepiej pokazać rzeczywistą odległość kostka- biodro, 
        # zamiast odległosci w pionie, bo na wykresie myli

    def display_frame(self, frame_number, draws_states):

        # tworzenie gównej klatki

        self.cap.set(1, frame_number)

        _, image = self.cap.read()

        # rysowenie widoku boczego

        if draws_states.side_frame_draw_state:
            self.frames[frame_number].draw_side_view(image, draws_states)
            
        # rysowanie lini trasy/ środek ciężkości itp.
        
        self.draw_lines(image, draws_states)

        # rysowanie lini pomocniczej

        if draws_states.leading_line_draw_state == True:
            self.draw_leading_line(image, frame_number)

        # rysowanie szkieletów na głównym widoku
        if draws_states.main_skeleton_right_draw_state == True:
            self.frames[frame_number].draw_skeleton_right(image)

        if draws_states.main_skeleton_left_draw_state == True:
            self.frames[frame_number].draw_skeleton_left(image)

        if draws_states.main_skeleton_draw_state == True:
            self.frames[frame_number].draw_skeleton(image)

        # rysowanie wykresów

        self.draw_charts(image, draws_states, frame_number)

        self.montage_clip_image = image

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # convert frame to RGB

        self.image = image

        self.image = Image.fromarray(image)


    def make_video_clip(self, draws_states):

        output_folder = "_clips"

        output_video_clip_file = "{}\\{}".format(
            output_folder, self.name.replace(".mp4", "_analized.mp4")
        )

        out = cv2.VideoWriter(
            output_video_clip_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080)
        )

        for frame_number in range(self.frames_amount - 1):

            self.display_frame(frame_number, draws_states)

            out.write(self.montage_clip_image)  # writing the video frame

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

class Frame_widgets:
    def __init__(self):
        # pozycje do wyświetlenia jako checkboxy
        self.labels_to_display  =   ['',
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

class Chart:
    def __init__(self,
                 name,
                 chart_description=None,
                 range_min=None,
                 range_max=None,
                 reverse=None):

        # podstawowe dane ustawień wykresu
        self.name = name
        self.chart_description = chart_description
        self.range_min = range_min
        self.range_max = range_max
        self.reverse = reverse

        self.chart_height = self.range_max - self.range_min

        # dane wykresu
        self.chart_points   =   None
        self.chart_line     =   []

    def generate_line_data(self, chart_y_pos=0, chart_number=0):
        #  zebranie danych do rysowania lini wykresu
        # pobranie danych

        self.chart_line.clear()

        frames_numbers = sorted(i for i in self.chart_points.keys())

        for frame in frames_numbers[1:]:

            # jeśli dane dla obu klatek występują to:
            try:
                pos_1 = self.chart_points[frame - 1]
                pos_2 = self.chart_points[frame]

                if self.reverse == True:
                    # jeśli wykres ma być odwrócont tj. mniejsze wartosci u góry:
                    # korekta - odwócenie wykresu do góry nogami,
                    # przesunięcie w pionie i ograniczenie zakresu
                    delta_y = chart_y_pos - self.range_min + (chart_number * self.chart_height)

                    pos_1 = (self.chart_points[frame - 1].x_disp,
                            self.chart_points[frame - 1].y_disp + delta_y)
                    
                    pos_2 = (self.chart_points[frame].x_disp,
                            self.chart_points[frame].y_disp + delta_y)
                else:
                    # korekta
                    # przesunięcie w pionie i ograniczenie zakresu
                    delta_y = chart_y_pos + self.range_max + (chart_number * self.chart_height)

                    pos_1 = (self.chart_points[frame - 1].x_disp,
                            -1 * self.chart_points[frame - 1].y_disp + delta_y)
                    
                    pos_2 = (self.chart_points[frame].x_disp,
                            -1 * self.chart_points[frame].y_disp + delta_y)

                self.chart_line.append((pos_1, pos_2))
            except:
                pass

class Line:

    def __init__(
        self,
        name,
        line_description=None,
        color=(0,0,0)):

        # podstawowe dane ustawień wykresu
        self.name = name
        self.line_description = line_description
        self.line_color = color

        # dane lini
        self.line_points   =   None
        self.line_line     =   []

    def generate_line_data(self):
        # zebranie danych do rysowania lini 
        # pobranie danych

        self.line_line.clear()

        frames_numbers = sorted(i for i in self.line_points.keys())

        for frame in frames_numbers[1:]:

            # jeśli dane dla obu klatek występują to:
            try:
                pos_1 = self.line_points[frame - 1].pos
                pos_2 = self.line_points[frame].pos

                self.line_line.append((pos_1, pos_2))

            except:
                pass
