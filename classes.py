import os
import json
import cv2
import numpy as np
import math
import scipy.interpolate
from unidecode import unidecode
from PIL import Image, ImageTk
from ffprobe import FFProbe
from general_bm import letterbox_calc
import scipy
import copy
import time
from tabulate import tabulate
import tkinter as tk
import ujson

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

def draw_line(image, line_to_draw, color=(0, 0, 0), thickness=3):

    if isinstance(line_to_draw, dict):     
        line_to_draw = [point for _,point in sorted(line_to_draw.items())]

    # rysowanie wykresu na podstawie listy punktów

    for x_axis_point in range(len(line_to_draw)-1):

        pos_1 = line_to_draw[x_axis_point]
        pos_2 = line_to_draw[x_axis_point+1]

        pos_1 = pos_1.disp_pos()             
        pos_2 = pos_2.disp_pos()      

        cv2.line(image, pos_1, pos_2, color, thickness)
   
    
class Point:
    def __init__(self, pos_x, pos_y, sk_id=None):
        self.sk_id = sk_id

        self.x = pos_x
        self.y = pos_y
        self.pos = (self.x, self.y)

        self.x_disp = int(self.x)
        self.y_disp = int(self.y)
        self.pos_disp   = (self.x_disp, self.y_disp)

    def disp_pos(self):
        return (int(self.x), int(self.y))


class Frame:
    def __init__(self, frame_count, frame_time, kpts, frame_offsets):

        self.image              = None
        self.image_to_draw      = None
        self.swich_id           = None

        self.frame_count        = frame_count
        self.frame_time         = frame_time
        self.kpts               = kpts
        self.detected           = kpts != []
        self.skeleton_points    = {}

        self.previous_frame     = None
        self.speed_factor       = None

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
        self.speed              = 30

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

    def calc_speed(self):
        # odległość

        self.speed_dist_px = get_dist(self.trace_point, self.previous_frame.trace_point)

        self.speed_dist_m = self.speed_dist_px / self.speed_factor

        # czas
        self.speed_time = self.frame_time - self.previous_frame.frame_time

        # prędkość
        self.speed = int((self.speed_dist_m/self.speed_time) * 3600)

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

    def draw_side_view(self, image, draws_states, scale_factor=1):

        # restet wielkości okna - zostawić funkcję do rozbudowania o opcję zmieny z poziomu programu
        self.calc_side_view_size()

        # boczne okno może być wyświetlane tylko jeśli jest wykryty szkielet
        if self.detected:

            self.side_view_size = int(self.side_view_size * scale_factor)
            # określenie zakresu do wyświetlenia

            # ustalenie punktów wycinka
            pose_y_cor = 0
            x, y, w, h = (
                int(self.trace_point.x) - self.side_view_size,
                int(self.trace_point.y) - pose_y_cor - self.side_view_size,
                self.side_view_size * 2,
                self.side_view_size * 2
            )

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
        self.size_factor = 0.25
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
            x1 = x2 = crop_head_point.x
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

            line_to_draw = [start_point, end_point]

            draw_line(image, line_to_draw, color=(255, 4, 0), thickness=3)

    def draw_wheelbase_line(self, image, delta_x=0, delta_y=0):

        # dodać skalowanie o scale vector

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

            line_to_draw = [center_of_back_wheel, center_of_front_wheel]

            draw_line(image, line_to_draw, color=(255, 4, 0), thickness=3)

            # rysuje koła na końcu bazy kół

            # cv2.circle(image, center_of_back_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)
            # cv2.circle(image, center_of_front_wheel.disp, int(self.bike_wheel_size/2*self.size_factor), (0,0,0), thickness=2)

    def draw_leading_line(self, image):
        # rysowanie linie wiodącej dla klatki, jeśli w ogóle jest szkielet
        if self.detected:

            # leading line setup
            leading_line_color = (0, 0, 0)
            leading_line_thickness= 2

            pos_1 = Point(self.trace_point.x, 0)
            pos_2 = Point(self.trace_point.x, image.shape[0])

            line_to_draw = [pos_1,pos_2]

            draw_line(image, line_to_draw, color=leading_line_color, thickness=leading_line_thickness)


class Clip:
    def __init__(self, vid_name, file_path):

        self.name           = vid_name
        self.vid_path       = file_path
        self.kpts_json_path = f"{os.getcwd()}\\_analysed\\{self.name.replace('.mp4','_kpts.json')}"

        self.cap = cv2.VideoCapture(self.vid_path)

        self.draws_times = []

        # dane do korekty pozycji x y punktów - ze wzgledu na zmianę formatu video do rozpoznawania "letterbox"

        self.left_ofset = 0
        self.top_offset = 0
        self.frame_offsets = self.left_ofset, self.top_offset
        self.calc_frame_offset()

        # ustalenie współczynnika wysokości obrazu (wg rozdzielczości) - bazowy to 1080p
        self.frame_height = None
        self.frame_hight_factor = None
        self.calc_frame_hight_factor()

        # zestawia wszyskie klatki clipu

        self.frames = {}
        self.colect_frames()

        self.frames_amount = len(self.frames)

        # współczynnik długość w pikselach/metry  - do obliczania prędkości

        self.speed_factor =139
    
        # 139 - dobry na pierwszy stolok- zweryfikowane
        # 148  -  wartość przyjmowana do 03.2025  dla pierwszego stolika
        # 180px = 1,22m = 147,5 - pierwszy stolik
        # 170 - dorn 

        self.obstacle_length = 4.7 # [m]

        self.max_speed = 0
        self.brakout_point = None
        self.max_jump_height = None

        self.read_brakout_point()

        # aktualizuje klatki o obiekty poprzedzajace i generuje dane o prędkości

        self.update_frames()

        # dane do wykresów i linii
        self.avilable_charts = {
            "speed_chart": {
                "chart_description": "prędkość [km/h]",
                "range_min": 15,
                "range_max": 45,
                "reverse": False,
                "base_scale":2,
                "smoothed":True
            },
            "right_knee_ang_chart": {
                "chart_description": "prawe kolano [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_knee_ang_chart": {
                "chart_description": "lewe kolano [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "right_hip_ang_chart": {
                "chart_description": "prawe biodro [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_hip_ang_chart": {
                "chart_description": "lewe biodro [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "right_elbow_ang_chart": {
                "chart_description": "prawy łokieć [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "left_elbow_ang_chart": {
                "chart_description": "lewy łokieć [st.]",
                "range_min": 90,
                "range_max": 180,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "stack_reach_len_chart": {
                "chart_description": "odległość stack/reach [m]",
                "range_min": 50,
                "range_max": 120,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            },
            "stack_reach_ang_chart": {
                "chart_description": "kąt stack/reach [st.]",
                "range_min": 0,
                "range_max": 90,
                "reverse": False,
                "base_scale":1,
                "smoothed":False
            }
        }
        self.charts = {}
        self.generate_charts_data()
        
        self.bike_ang_cor = []

        self.avilable_lines = {
            "trace_line": {
                "line_description": "linia trasy",
                "frame_atr": 'trace_point',
                'line_color': (56, 231, 255)
            },
            "center_of_gravity_line": {
                "line_description": "inia środka ciężkości",
                "frame_atr": 'center_of_gravity',
                'line_color': (56, 231, 255)
            },
        }
        self.lines = {}
        self.generate_lines_data()

        # ustala zakres dla widgetu Scale

        self.scale_range_min = 0
        self.scale_range_max = self.frames_amount-1
        self.calculate_scale_range()

    def add_time_counter(self, description):
        self.draws_times.append([description,time.time()])

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

    def calc_frame_hight_factor(self):

        self.cap.set(0, 1)
        self.frame_height = int(self.cap.get(4))
        self.frame_hight_factor = self.frame_height/1080

    def colect_frames(self):

        # zestawia klatki w słownik gdzie key=numer klatki (od 0) a value= obiekt klatki Frame

        with open(self.kpts_json_path, "r") as f:
            data = json.load(f)

        for frame_count, data in enumerate(data.items(),start=0):

            frame_time, kpts = data
            frame_time = float(frame_time)

            self.frames[frame_count] = Frame(frame_count,
                                             frame_time,
                                             kpts,
                                             self.frame_offsets)
            
        success,image = self.cap.read() 
        frame_count = 1
        while success:
            try:
                success,image = self.cap.read() 
                self.frames[frame_count].image = image
            except:
                print(str(frame_count)+" błąd")
            frame_count += 1

    def update_frames(self):
        for frame in self.frames.values():
            try:
                frame.previous_frame = self.frames[frame.frame_count-1]
                frame.speed_factor = self.speed_factor
                frame.calc_speed()

            except:
                pass
    
    def read_brakout_point(self):
        # parse json 
        _brakout_points_path = f"{os.getcwd()}\\_analysed\\_brakout_points.json"
        with open(_brakout_points_path, "r") as f:
            data = json.load(f)
        
        main_vid_name = self.name[:18]
        
        if main_vid_name in (data.keys()):
            x, y= data[main_vid_name]
            self.brakout_point = Point(x, y)

    def save_brakout_point(self):
        main_vid_name = self.name[:18]
        _brakout_points_path = f"{os.getcwd()}\\_analysed\\_brakout_points.json"
        with open(_brakout_points_path, "r") as f:
            data = json.load(f)

        data[main_vid_name] = self.brakout_point.pos_disp

        with open(_brakout_points_path, 'w') as f:
            json.dump(data, f)
        
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
                base_scale=chart_setup["base_scale"],
                smoothed=chart_setup["smoothed"]
                )

            # dodanie do wykresu punkty z kolejnych klatek:
            tmp_chart_points_dict   =   {}

            for frame_number, frame_obj in self.frames.items():
                if frame_obj.detected:  # jeśli szkielet został wykryty na klatce

                    # tworzenie nazwy zmiennej do pobrania z obiektu klatki
                    frame_variable_name = chart_name.replace("_chart", "")

                    x_pos = int(frame_obj.skeleton_points[17].x)
                    y_pos = int(getattr(frame_obj, frame_variable_name))

                    tmp_chart_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.charts[chart_name].chart_points = tmp_chart_points_dict
        



            # generowanie danych wykresu

            if self.charts[chart_name].smoothed == True:
                self.charts[chart_name].generate_spline_data()

            # wykonanie kopii obiektów z punktami do wyświetlenia - żeby przyspieszyć generowanie dany później
            
            self.charts[chart_name].chart_points_to_draw = copy.deepcopy(self.charts[chart_name].chart_points)
            self.charts[chart_name].chart_points_smoothed_to_draw = copy.deepcopy(self.charts[chart_name].chart_points_smoothed)

    def draw_charts(self, image, draws_states, frame_number):

        # ustalenie które wykresy mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości wykresów  i zestawienie obiektów wykresów
        

        charts_to_draw = []

        self.add_time_counter('czyszczenie listy wykresów')

        # iteracja po dostępnych obiektach wykresów i porównanie z obiektem stan druku 'draws_states'
        for chart_name in self.charts.keys():
            chart_name_draw_state_atr = chart_name+'_draw_state'
            if getattr(draws_states, chart_name_draw_state_atr) == True:
                charts_to_draw.append(self.charts[chart_name])

        if not charts_to_draw: return

        self.add_time_counter('iteracja po wykresach')

        # generowanie danych wykresów

        # oblicznie pozycji y pierwszego wykresu
        charts_area_height = 0
        for chart in charts_to_draw:
            charts_area_height += (chart.range_max - chart.range_min) * self.frame_hight_factor * chart.base_scale

        charts_y_pos = self.frame_height - int(charts_area_height)

        # generowanie danych wykresów dla konkretnych miejsc na obrazie

        for chart in charts_to_draw:

            chart.chart_y_pos = charts_y_pos
            chart.scale_factor = self.frame_hight_factor
            chart.chart_height = (chart.range_max - chart.range_min) * int(self.frame_hight_factor) * chart.base_scale

            chart.generate_line_to_draw(chart.chart_points,
                                        chart.chart_points_to_draw)

            charts_y_pos += chart.chart_height

        self.add_time_counter('generowanie danych wykresów')

        # rysowanie bazy i linii ograniczajacych wykres

        if draws_states.charts_background_draw_state == True:

            for chart in charts_to_draw:

                self.draw_charts_base(image, chart)

        self.add_time_counter('rysowanie bazy i lini ograniczajach')

        # rysowanie linii wykresów

        for chart in charts_to_draw:

            if chart.smoothed == False:
                # setup
                line_thickness = int(2 * self.frame_hight_factor)
                line_color = (255, 128, 0)
            else:
                # setup
                line_thickness = int(1 * self.frame_hight_factor)
                line_color = (80, 80, 80)

            draw_line(image, chart.chart_points_to_draw, color=line_color, thickness=line_thickness)

        self.add_time_counter('rysowanie linii wykresów')

        # rysowanie spline wykresów - tylko dla prędkości !!!! - test

        if draws_states.speed_chart_draw_state == True:

            self.add_time_counter('przed generuje dane do krzywej')
        
            # generuje dane wygładzonej krzywej wykresu
            self.charts['speed_chart'].generate_smoothed_line_to_draw()

            self.add_time_counter('po generuje dane do krzywej')

            # self.charts['speed_chart'].generate_line_to_draw(self.charts['speed_chart'].chart_points_smoothed)
            line_to_draw = self.charts['speed_chart'].chart_points_smoothed_to_draw

            self.add_time_counter('rysowanie linii wykresów')

            # setup
            line_thickness = 2
            line_color = (255, 128, 0)

            draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        self.add_time_counter('rysowanie linii spline speed')
            
        # rysowanie opisów

        if draws_states.charts_descriptions_draw_state == True:

            for chart in charts_to_draw:

                self.draw_charts_descriptions(image, chart, frame_number)

        self.add_time_counter('rysowanie opisów')
            
         

        # rysowanie spline wykresów


        # for chart_number, chart in enumerate(charts_to_draw):

        #     chart.generate_spline_data(chart.chart_y_pos, chart_number)
        #     spline_to_draw = chart.chart_spline

        #     # setup
        #     line_thickness = 2
        #     line_color = (255, 128, 0)

        #     (image, spline_to_draw, color=line_color, thickness=line_thickness)
        
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

                    x_pos = int(frame_obj.skeleton_points[17].x)
                    y_pos = int(getattr(frame_obj, frame_variable_name).y)

                    tmp_line_points_dict[frame_number] = Point(x_pos, y_pos)

                else:
                    pass

            self.lines[line_name].line_points = tmp_line_points_dict
           
            # wykonanie kopii obiektów z punktami do wyświetlenia - żeby przyspieszyć generowanie dany później
            
            self.lines[line_name].line_points_to_draw = copy.deepcopy(self.lines[line_name].line_points)
            self.lines[line_name].line_points_to_draw_to_draw = copy.deepcopy(self.lines[line_name].line_points_to_draw)

    def draw_brakout_point(self, image, draws_states):
        if self.brakout_point:
            # setup
            radius = 20
            thickness = 2
            color = (0, 0, 0)
            cross_size = radius * 0.75

            # współrzędne krzyża
            cross_x_start = transform_point(self.brakout_point, -cross_size, 0)
            cross_x_end   = transform_point(self.brakout_point,  cross_size, 0)

            cross_y_start = transform_point(self.brakout_point, 0, -cross_size)
            cross_y_end   = transform_point(self.brakout_point, 0,  cross_size)

            cross_hor = [cross_x_start, cross_x_end]
            cross_vert = [cross_y_start, cross_y_end]

            # rysowanie na image
            cv2.circle(image, self.brakout_point.pos_disp, radius, color=color, thickness=thickness) 
            draw_line(image, cross_hor, color=color, thickness= thickness)
            draw_line(image, cross_vert, color=color, thickness= thickness)


            # rysowanie na image - krzyża do sprawdzanie poprawnośći przyjętego wsp.
            if draws_states.speed_factor_verification_draw_state:
                delta = self.speed_factor * self.obstacle_length

                cross_x_start = transform_point(cross_x_start, delta, 0)
                cross_x_end   = transform_point(cross_x_end,  delta, 0)

                cross_y_start = transform_point(cross_y_start, delta, 0)
                cross_y_end   = transform_point(cross_y_end, delta, 0)

                cross_hor = [cross_x_start, cross_x_end]
                cross_vert = [cross_y_start, cross_y_end]

                circle = transform_point(self.brakout_point, delta, 0).pos_disp

                cv2.circle(image, circle, radius, color=color, thickness=thickness) 
                draw_line(image, cross_hor, color=color, thickness= thickness)
                draw_line(image, cross_vert, color=color, thickness= thickness)

    def draw_charts_base(self, image, chart):

        # rysowanie tła wykresu
        # ustalenie współrzędnych punktów wykresu
        x, y, w, h = (
            0,
            chart.chart_y_pos,
            image.shape[1],
            chart.chart_height,
        )
        sub_img = image[y : y + h, x : x + w]
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

        # Putting the image back to its position
        image[y : y + h, x : x + w] = res

        # rysowanie linii ograniczajacych wykres
        # setup
        chart_frame_color = (0, 0, 0)
        chart_frame_thickness = int(2 * chart.scale_factor)

        for line_numer in range(2):

            pos_1 = Point(0, chart.chart_y_pos + line_numer * chart.chart_height)
            pos_2 = Point(w, chart.chart_y_pos + line_numer * chart.chart_height)

            line_to_draw = [pos_1, pos_2]

            draw_line(image, line_to_draw, chart_frame_color, thickness=chart_frame_thickness)

    def draw_charts_descriptions(self, image, chart, frame_number):

        # opis wykresu

        # setup
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8 * self.frame_hight_factor
        text_color = (0, 0, 0)
        thickness = int(2 * self.frame_hight_factor)

        # ustalenie tekstu głównego opisu do wyświetlenia i jego pozycji
        # - do zmiany tak żeby się wyświetlały polskie znaki

        main_description = unidecode(chart.chart_description)

        x_pos = int(20 * self.frame_hight_factor)
        y_pos = chart.chart_y_pos + int(25 * self.frame_hight_factor)

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
        # jeśli wykres jest wygładzony to opis wg chart_points_smoothed

        try:
            x_pos = int(chart.chart_points[frame_number].x) + int(20 * self.frame_hight_factor)
            y_pos = chart.chart_y_pos + chart.chart_height - int(20 * self.frame_hight_factor)

            if chart.smoothed == True:
                
                for point in chart.chart_points_smoothed:
                    if int(point.x) == int(self.frames[frame_number].trace_point.x):
                        chart_value_description = str(round(point.y))
                        break

            else:
                chart_value_description = str(round(chart.chart_points[frame_number].y))

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

    def draw_lines(self, image, draws_states):

        # ustalenie które linie mają być wyświetlane na podstawie obiektu Draws_states
        # ustalenie ilości lini  i zestawienie obiektów wykresów

        # iteracja po dostępnych obiektach lini i porównanie z obiektem stan druku 'draws_states'
        for line_name, line in self.lines.items():
            line_name_draw_state_atr = line_name + '_draw_state'
            if getattr(draws_states, line_name_draw_state_atr) == True:

                # line.line_points_to_draw = line.generate_line_to_draw(line.line_points)
                line_to_draw = line.line_points_to_draw

                # setup
                line_thickness = 2
                line_color = line.line_color

                draw_line(image, line_to_draw, color=line_color, thickness=line_thickness)

        # do analizy czy nie lepiej pokazać rzeczywistą odległość kostka- biodro, 
        # zamiast odległosci w pionie, bo na wykresie myli

    def draw_main_frame_description(self,image, frame):

        # setup
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.8 * self.frame_hight_factor
        text_color = (56, 231, 255)
        text_color = (0, 0, 0)

        thickness = int(2 * self.frame_hight_factor)

        # ustalenie tekstu głównego opisu do wyświetlenia i jego pozycji
        # - do zmiany tak żeby się wyświetlały polskie znaki
        try:
            speed_dist = round(frame.speed_dist_m,3)
            speed_time = round(frame.speed_time,1)
        except:
            speed_dist = 0
            speed_time = 0

        try:
            self.max_speed = round(self.charts['speed_chart'].max_val)
            self.min_speed = round(self.charts['speed_chart'].min_val)
            self.delta = self.max_speed - self.min_speed

        except:
            self.max_speed = '-'
            self.min_speed = '-'
            self.delta = '-'

        # ustalenie max wysokości skoku
        if self.brakout_point != None:
            self.max_jump_height = self.brakout_point.y - min(point.y for point in self.lines["trace_line"].line_points.values())
            self.max_jump_height = int(self.max_jump_height / self.speed_factor * 100)
        else:
            self.max_jump_height = '-'


        # main_description = [f'czas - {round(frame.frame_time)} [ms]',
        #                     f'klatka - {frame.frame_count}/{self.frames_amount}',
        #                     f'{speed_dist} [m]/{speed_time} [ms]',
        #                     f'V max/min - {self.max_speed}/{self.min_speed} [km/h]',
        #                     f'wsp. dlugosci - {self.speed_factor} [px/metr]'
        #                     ]

        main_description = ['{:04d} [ms] | {:03d}/{} | {:.3f} [m]/{} [ms] | {} [px/metr]'.format(
                                    round(frame.frame_time),
                                    frame.frame_count,
                                    self.frames_amount,
                                    speed_dist,
                                    speed_time,
                                    self.speed_factor),

                            f'V max/min/delta : {self.max_speed} / {self.min_speed} / {self.delta} [km/h] | jump height : {self.max_jump_height} [cm]'
                            ]

        # rysowanie podkładu
        x, y, w, h = (
            0,
            0,
            int(935 * self.frame_hight_factor),
            int(50 * len(main_description) * self.frame_hight_factor),
            )
        sub_img = image[y : y + h, x : x + w]
        white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 255

        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

        # Putting the image back to its position
        image[y : y + h, x : x + w] = res

        for row, text in enumerate(main_description):

            x_pos = int(40 * self.frame_hight_factor)
            y_pos = int((40 + 50 * row) * self.frame_hight_factor)

            main_description_loc = (x_pos, y_pos)

            cv2.putText(
                image,
                text,
                main_description_loc,
                font,
                fontScale,
                text_color,
                thickness,
            )

    def draw_times_table_in_terminal(self):

        main_description = []
        
        reference_time = self.draws_times[0][1]*1000

        for data in self.draws_times:
            data+=[round(1000*(data[1])-reference_time,2)]
            main_description.append(f'{data[0]} - {data[2]} [ms]')
            reference_time  = 1000 * (data[1])

        start_time = self.draws_times[0][1]*1000
        end_time = self.draws_times[-1][1]*1000

        self.draws_times.append(['całość',',',round(end_time-start_time,2)])

        print(tabulate([[i[0],i[2]] for i in self.draws_times], showindex="always"))

        self.draws_times.pop(-1)

    def display_frame(self, frame_number, draws_states, swich_id=False):

        # jeżeli nie było zmiany swich_id to obraz zostaje pobrany z obiektu Frame,
        # jeżeli była zmiana - obraz jest tworzony, a potem zapisany do obiektu Frame

        self.draws_times = []

        if  swich_id == self.frames[frame_number].swich_id:


            self.add_time_counter('start - to samo id')

            self.image = self.frames[frame_number].image_to_draw

            self.add_time_counter('koniec - to samo id')

        else:

            self.frames[frame_number].swich_id = swich_id

            self.add_time_counter('start')

            image = copy.deepcopy(self.frames[frame_number].image)

            self.add_time_counter('kopia image')
            
            # rysowenie widoku bocznego

            if draws_states.side_frame_draw_state:
                self.frames[frame_number].draw_side_view(image, draws_states, self.frame_hight_factor)
            
            self.add_time_counter('rysowanie widoku bocznego')
                        
            # rysowanie punktu wybicia
            
            if draws_states.brakout_point_draw_state == True:
                self.draw_brakout_point(image, draws_states)

            # rysowanie lini trasy/ środek ciężkości itp.
            
            self.draw_lines(image, draws_states)
            self.add_time_counter('linie trasy')

            # rysowanie lini pomocniczej - wiodącej

            if draws_states.leading_line_draw_state == True:
                self.frames[frame_number].draw_leading_line(image)
            
            self.add_time_counter('linia pomocnicza')

            # rysowanie szkieletów na głównym widoku
            if draws_states.main_skeleton_right_draw_state == True:
                self.frames[frame_number].draw_skeleton_right(image)

            if draws_states.main_skeleton_left_draw_state == True:
                self.frames[frame_number].draw_skeleton_left(image)

            if draws_states.main_skeleton_draw_state == True:
                self.frames[frame_number].draw_skeleton(image)

            self.add_time_counter('szkielety na glownej')

            # rysowanie wykresów

            self.draw_charts(image, draws_states, frame_number)

            self.add_time_counter('wykresy')

            # rysowanie głównego opisu na ramce

            if draws_states.main_frame_description == True:
                self.draw_main_frame_description(image, self.frames[frame_number])
            
            self.add_time_counter('opis glowny')

            # tworzenie ostatecznego obrazu

            self.montage_clip_image = image

            self.cv2_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # convert frame to RGB

            self.image = Image.fromarray(self.cv2_image)

            self.frames[frame_number].image_to_draw = self.image

            self.add_time_counter('obróbka ostatecznego obrazu')

    def make_video_clip(self, draws_states, swich_id):

        output_folder = "_clips"

        output_video_clip_file = "{}\\{}".format(
            output_folder, self.name.replace(".mp4", "_analized.mp4")
        )

        out = cv2.VideoWriter(
            output_video_clip_file, cv2.VideoWriter_fourcc(*"mp4v"), 30, (1920, 1080)
        )

        for frame_number in range(1, self.frames_amount):

            self.display_frame(frame_number, draws_states)

            out.write(self.montage_clip_image)  # writing the video frame

        import time
        time.sleep(20)

        file_from = f'{os.getcwd()}\\{output_video_clip_file}'
        file_to = file_from.replace('.mp4','_60fps.mp4')

        print(file_from)
        print(file_to)
        print(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        os.system(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")

        print(f"{self.name} gotowe.")

    def save_frame(self, frame_to_display):

        output_folder = "_clips"

        output_frame_file = "{}\\{}_{:03d}.jpg".format(
            output_folder,
            self.name.replace(".mp4", ""),
            frame_to_display
        )
        print(output_frame_file)

        # self.display_frame(frame_to_display, draws_states)

        cv2.imwrite(output_frame_file, self.montage_clip_image)

        print(f"{self.name} gotowe.")


class Chart:
    def __init__(self,
                 name,
                 chart_description = None,
                 range_min = None,
                 range_max = None,
                 reverse = None,
                 smoothed = None,
                 base_scale = 1):

        # podstawowe dane ustawień wykresu
        self.name = name
        self.chart_description = chart_description
        self.range_min = range_min
        self.range_max = range_max
        self.reverse = reverse
        self.base_scale = base_scale #przeskalowanie wartości wykresu przy wyświetlaniu (niezależna od rozdzielczości)
        self.smoothed = smoothed

        # dane wykresu
        self.chart_points   =   None    # słownik z key = klatka clipu, value = Point (!)
        self.chart_points_smoothed   =   None   # lista z Point

        self.max_val = None
        self.min_val = None

        # dane dla przyjętego obrazu
        self.chart_y_pos = None
        self.chart_height = None
        self.scale_factor = None
        
        self.chart_points_to_draw = None    
        self.chart_points_smoothed_to_draw   =   None

        self.draws_times = []

    def generate_line_to_draw(self, source, target):
        
        if isinstance(target, dict):     

            for frame, point in target.items():
                # skalowanie wykresu
                point.y = source[frame].y * self.scale_factor * self.base_scale

                # redukcja do wartości minimalnej
                point.y = point.y - self.range_min * self.scale_factor * self.base_scale
                    
                # odwracanie wykresu
                if not self.reverse:
                    point.y = -1 * point.y + (self.range_max - self.range_min) * self.scale_factor * self.base_scale
                
                # ustalenie pozycji wykresu
                point.y = point.y + self.chart_y_pos

        else: # jeśli dane są w listach
            for source_point, target_point in zip(source, target):
                # skalowanie wykresu
                target_point.y = source_point.y * self.scale_factor * self.base_scale
    
                # redukcja do wartości minimalnej
                target_point.y = target_point.y - self.range_min * self.scale_factor * self.base_scale
                    
                # odwracanie wykresu
                if not self.reverse:
                    target_point.y = -1 * target_point.y + (self.range_max - self.range_min) * self.scale_factor * self.base_scale
                
                # ustalenie pozycji wykresu
                target_point.y = target_point.y + self.chart_y_pos

    def generate_spline_data(self):

        # przygpotowanie punktów do oblicznia splina ( x musi być rosnący !
        # pobranie danych

        all_x, all_y = [], []

        for point in [point for _,point in sorted(self.chart_points.items())]:

            all_x.append(point.x)
            all_y.append(point.y)

        # usunięcie 4 początkowych i 2 koncowych punktów  - zazwyczaj są niedokładne   

        x = np.array(all_x[4:-2])
        y = np.array(all_y[4:-2])

        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.linear_model import LinearRegression
        
        #specify degree of _ for polynomial regression model
        #include bias=False means don't force y-intercept to equal zero
        poly = PolynomialFeatures(degree=4, include_bias=False)

        #reshape data to work properly with sklearn
        poly_features = poly.fit_transform(x.reshape(-1, 1))

        #fit polynomial regression model
        poly_reg_model = LinearRegression()
        poly_reg_model.fit(poly_features, y)

        # ustalenie wartości dla osi x i oblicznie y wg. fit polynomial
        x_range = np.array(range(min(all_x), max(all_x)))
        
        y_pred_values = poly_reg_model.predict(poly.fit_transform(x_range.reshape(-1, 1)))

        self.chart_points_smoothed = [Point(x,y) for x,y in zip(x_range, y_pred_values)]

        # aktualizacja danych o max i min
        self.calc_min_max()

    def generate_smoothed_line_to_draw(self):

        # przeskalowanie krzywej do wyświetlanego obrazu

        self.generate_line_to_draw(self.chart_points_smoothed,
                                   self.chart_points_smoothed_to_draw)

    def calc_min_max(self):
        # oblicza prędkość max dla pierwszej połowy odcinka (na dojezdzie)
        # oblicza prędkość min z pominięciem początku i końca (+-0,5m)

        try:
            if self.smoothed == True:
                self.max_val = max(point.y for point in self.chart_points_smoothed[:len(self.chart_points_smoothed)//2])
                self.min_val = min(point.y for point in self.chart_points_smoothed[3:-3])
            else:
                self.max_val = max(point.y for point in self.chart_points.values()[:len(self.chart_points.values())//2])
                self.min_val = min(point.y for point in self.chart_points.values()[3:-3])
        except:
            pass

    def add_time_counter(self, description):
        self.draws_times.append([description,time.time()])

    def draw_times_table_in_terminal(self):

        main_description = []
        
        reference_time = self.draws_times[0][1]*1000

        for data in self.draws_times:
            data+=[round(1000*(data[1])-reference_time,2)]
            main_description.append(f'{data[0]} - {data[2]} [ms]')
            reference_time  = 1000 * (data[1])

        start_time = self.draws_times[0][1]*1000
        end_time = self.draws_times[-1][1]*1000

        self.draws_times.append(['całość',',',round(end_time-start_time,2)])

        print(tabulate([[i[0],i[2]] for i in self.draws_times], showindex="always"))

        self.draws_times.pop(-1)
        self.draws_times =[]
    

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
        self.line_points   =   None    # słownik z key = klatka clipu, value = Point (!)
        self.line_points_smoothed   =   None   # lista z Point

        self.max_val = None
        self.min_val = None

        # dane dla przyjętego obrazu
        self.scale_factor = None
        
        self.line_points_to_draw = None    
        self.line_points_smoothed_to_draw   =   None
