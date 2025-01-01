import os
import json
from utils.datasets import letterbox
import cv2
import numpy as np
import math
from unidecode import unidecode


def angle_between_vectors(u, v):
    dot_product = sum(i*j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    angle_rad = math.acos(cos_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_rad, angle_deg

class Point():
    def __init__(self,sk_id,pos_x,pos_y):
        self.sk_id=sk_id
        self.x=pos_x
        self.y=pos_y
        self.x_disp=int(pos_x)
        self.y_disp=int(pos_y)

class Frame():
    def __init__(self,frame_count,kpts):
        self.frame_count=frame_count
        self.kpts=kpts
        self.detected=False
        self.skeleton_points={}
        self.organize_points()
        self.angs={}
        self.calc_ang()
        self.trace_point=self.get_mid(16,17)
        self.center_of_gravity=self.get_mid(12,13)
        self.stack_reach_len=self.get_dist(self.trace_point,self.center_of_gravity)

    def get_mid(self,sk_id_1,sk_id_2):
        steps=3
        pos_x_1, pos_y_1= (self.kpts[(sk_id_1-1)*steps]), (self.kpts[(sk_id_1-1)*steps+1])
        pos_x_2, pos_y_2= (self.kpts[(sk_id_2-1)*steps]), (self.kpts[(sk_id_2-1)*steps+1])

        return (pos_x_2+pos_x_1)//2,(pos_y_2+pos_y_1)//2
    
    def get_dist(self,pkt_1, pkt_2):
        pos_x_1, pos_y_1= pkt_1
        pos_x_2, pos_y_2= pkt_2

        return int(((pos_x_2-pos_x_1)**2+(pos_y_2-pos_y_1)**2)**0.5)

    def organize_points(self):
        steps=3
        if self.kpts:
            self.detected=True
            for sk_id in range(1,18):
                pos_x, pos_y = (self.kpts[(sk_id-1)*steps]), (self.kpts[(sk_id-1)*steps+1])
                self.skeleton_points[sk_id]=Point(sk_id, pos_x, pos_y)

    def draw_skeleton(self,image,skeleton_to_display=None, points_to_display=None):

        # cały szkielet
        skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12],
            [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3],
            [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]
        
        key_points=list(range(1,18))
        
        # części szkieletu do wyświetlenia
        if not skeleton_to_display:
            skeleton_to_display=skeleton

        if not points_to_display:
            points_to_display=key_points

        #Plot the skeleton and keypointsfor coco datatset
        palette = np.array([[255, 128, 0], [255, 153, 51], [255, 178, 102],
                            [230, 230, 0], [255, 153, 255], [153, 204, 255],
                            [255, 102, 255], [255, 51, 255], [102, 178, 255],
                            [51, 153, 255], [255, 153, 153], [255, 102, 102],
                            [255, 51, 51], [153, 255, 153], [102, 255, 102],
                            [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0],
                            [255, 255, 255]])
        
        pose_limb_color = palette[[0, 9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
        pose_kpt_color = palette[[0, 16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
        radius = 4

        for kid in key_points:
                r, g, b = pose_kpt_color[kid]
                x_coord, y_coord = self.skeleton_points[kid].x_disp, self.skeleton_points[kid].y_disp
                if not (x_coord % 640 == 0 or y_coord % 640 == 0):
                    if kid in points_to_display:
                        cv2.circle(image, (x_coord, y_coord), radius, (int(r), int(g), int(b)), -1)

        for sk_id, sk in enumerate(skeleton,1):
            r, g, b = pose_limb_color[sk_id]

            pos1 = self.skeleton_points[sk[0]].x_disp, self.skeleton_points[sk[0]].y_disp
            pos2 = self.skeleton_points[sk[1]].x_disp, self.skeleton_points[sk[1]].y_disp

            if pos1[0]%640 == 0 or pos1[1]%640==0 or pos1[0]<0 or pos1[1]<0:
                continue
            if pos2[0] % 640 == 0 or pos2[1] % 640 == 0 or pos2[0]<0 or pos2[1]<0:
                continue
            if sk in skeleton_to_display:
                cv2.line(image, pos1, pos2, (int(r), int(g), int(b)), thickness=2) 

    def draw_skeleton_right_side(self,image):
        skeleton_right_side = [ [17, 15], [15, 13],
                                [7, 13], 
                                [7, 9], [9, 11],
                                [5, 7], [3,5], [1,3]]
                
        points_to_display=[1,3,5,7,9,11,13,15,17]

        self.draw_skeleton(image, skeleton_right_side, points_to_display)

    def draw_skeleton_left_side(self,image):
        skeleton_left_side = [ [16, 14], [14, 12],
                            [6, 12], 
                            [6, 8], [8, 10],
                            [4, 6], [2,4], [1,2]]
            
        points_to_display=[1,2,4,6,8,10,12,14,16]

        self.draw_skeleton(image, skeleton_left_side, points_to_display)

    def calc_ang(self):

        # punkty obliczenia kątów
        # dodać kąty pozycji tułów/poziom i głowa/kosta/rower
        # wierzchołek kąta trzeba podać w środku listy (b)
        # kąty są mierzone do 180 st. (!)

        ang_list={'right_knee':[13,15,17],
                'left_knee':[12,14,16],
                'right_hip':[7,13,15],
                'left_hip':[6,12,14],
                'right_elbow':[7,9,11],
                'left_elbow':[6,8,10]}

        for name,(a,b,c) in ang_list.items():

            # tworzenie wektorów:
            u=( self.skeleton_points[a].x-self.skeleton_points[b].x,    
                self.skeleton_points[a].y-self.skeleton_points[b].y)       
            v=( self.skeleton_points[c].x-self.skeleton_points[b].x,    
                self.skeleton_points[c].y-self.skeleton_points[b].y)         

            # obliczneie kąta miedzy wektorami
            ang_to_add=angle_between_vectors(u, v)[1]

            self.angs[name]=ang_to_add

class Clip():
    def __init__(self,vid_name):
        self.name=vid_name
        self.vid_path=f'{os.getcwd()}\\_analysed\\{self.name}\\{self.name}'

        self.org_vid_prop=OrginalVideoProperitier(self.vid_path)

        self.frames={}
        self.add_frames()

        # dane do wykresów i linii
        self.charts={}
        self.generate_data_charts()

        self.lines={}
        self.generate_data_lines()
        
        # ustawienia do rysowania wykresów
        self.chart_y_pos=750
        self.chart_height=90

        self.draw_background=True
        self.draw_leading_line=True
        
        self.charts_state={'right_knee_chart':[True,(90,180),True],
                            'left_knee_chart':[True,(90,180),True],
                            'right_hip_chart':[True,(90,180),True],
                            'left_hip_chart':[False,(90,180),True],
                            'right_elbow_chart':[False,(90,180),True],
                            'left_elbow_chart':[False,(90,180),True]}
        
        # ustawienia rysowania linii
        self.lines_state={'trace_chart':False,
                    'center_of_gravity_chart':False}

    
    def add_frames(self):

        kpts_json_path=f'{os.getcwd()}\\_analysed\\{self.name}\\{self.name.replace('.mp4','_kpts.json')}'

        with open(kpts_json_path, 'r') as f:
            data = json.load(f)
            
        for frame,kpts in data.items():
            self.frames[int(frame)]=Frame(int(frame),kpts)
    
    def generate_data_charts(self):

        # kąty zgięcia łokci, kolan i bioder    
        self.charts={'right_knee_chart':{'name':'prawe kolano [st.]'},
                        'left_knee_chart':{'name':'lewe kolano [st.]'},
                        'right_hip_chart':{'name':'prawe biodro [st.]'},
                        'left_hip_chart':{'name':'lewe biodro [st.]'},
                        'right_elbow_chart':{'name':'prawy łokieć [st.]'},
                        'left_elbow_chart':{'name':'lewy łokieć [st.]'}}
        
        for charts in self.charts.keys():
            for frame,frame_obj in self.frames.items():
                self.charts[charts][frame]=[frame_obj.skeleton_points[17].x_disp,int(frame_obj.angs[charts[:-6]])]

    def generate_data_lines(self):
        # linie trasy (wg punktu kostki 17 i 16) i środka ciężkości (biodro1 13 i 12)
        self.lines['trace_chart']={'name':'linia trasy'}
        self.lines['center_of_gravity_chart']={'name':'linia środka ciężkości'}

    def draw_charts(self,image, frame_number):
       
        chart_index=0
        charts_lines_to_draw=[]

        for chart_name,chart_state_data in self.charts_state.items():
            state, chart_range, rev_chart = chart_state_data
            if state:

                # rysowanie podkładu

                self.draw_chart_base(image, chart_name, chart_index,
                                chart_range,
                                frame_number=frame_number)

                # zebranie danych do rysowania lini wykresu
                # pobranie danych
                data_to_draw=self.charts[chart_name]

                frames=sorted(i for i in data_to_draw.keys() if type(i)==int)

                tmp_store=[]
                for frame in frames[1:]:

                    pos_1=self.charts[chart_name][frame-1]
                    pos_2=self.charts[chart_name][frame]

                    # korekta - odwócenie wykresu do góry nogami, przesunięcie w pionie i ograniczenie zakresu         

                    delta_y=self.chart_y_pos+chart_range[1]+chart_index*self.chart_height

                    pos_1=self.charts[chart_name][frame-1][0], -1 * self.charts[chart_name][frame-1][1] + delta_y
                    pos_2=self.charts[chart_name][frame][0], -1 * self.charts[chart_name][frame][1] + delta_y

                    tmp_store.append((pos_1,pos_2))

                charts_lines_to_draw.append(tmp_store)
                
                chart_index+=1

        # rysowanie linii wykresów
        for line_to_draw in charts_lines_to_draw:
            self.draw_line(image, line_to_draw, color=(255, 128, 0))

    def draw_line(self, image, line_to_draw, color=(0, 0, 0), thickness=3):
        # rysowanie wykresu
        for line in line_to_draw:

            pos_1, pos_2 = line

            cv2.line(image, pos_2, pos_1, color, thickness)

    def draw_chart_base(self,image, chart_name, chart_index,
                   chart_range,
                   color=(115,200,221),
                   frame_number=None):
        
        # rysowanie tła wykresu
        background_delta_y_1=self.chart_y_pos+(chart_index)*self.chart_height
        background_delta_y_2=self.chart_y_pos+(chart_index+1)*self.chart_height
        
        podklad=[[0,background_delta_y_1],[0,background_delta_y_2],
                 [image.shape[1],background_delta_y_2],
                 [image.shape[1],background_delta_y_1]]
        
        podklad = np.array(podklad)
        if self.draw_background:
            cv2.fillPoly(image, [podklad], color)

        # rysowanie lini ograniczajacych wykres
        chart_frame_color=(0,0,0)
        pos_1=0,background_delta_y_1
        pos_2=image.shape[1],background_delta_y_1

        cv2.line(image, pos_1, pos_2, chart_frame_color, thickness=2)

        pos_1=0,background_delta_y_2
        pos_2=image.shape[1],background_delta_y_2

        cv2.line(image, pos_1, pos_2, chart_frame_color, thickness=2)

        # opis wykresu

        # object details
        # tytuł
        font = cv2.FONT_HERSHEY_SIMPLEX 
        fontScale = 0.8
        text_color=(0,0,0)
        thickness = 2
        text=unidecode(self.charts[chart_name]['name']) # - do zmiany tak żeby się wyświetlały polskie znaki
        lok_opis_wykresu=(20,background_delta_y_1+25)
        
        cv2.putText(image, text, lok_opis_wykresu, font, fontScale, text_color, thickness)
        # wartość

        lok_opis_wykresu=(self.charts[chart_name][frame_number][0]+20, background_delta_y_1+25)
        text=str(self.charts[chart_name][frame_number][1])
        cv2.putText(image, text, lok_opis_wykresu, font, fontScale, text_color, thickness)

        # rysowanie linie wiodącej dla klatki
        if self.draw_leading_line and frame_number:

            leading_line_color=(0,0,0)
            
            pos_1=self.charts[chart_name][frame_number][0],0
            pos_2=self.charts[chart_name][frame_number][0],image.shape[0]

            cv2.line(image, pos_1, pos_2, leading_line_color, thickness=2)

    def display_frame(self,frame_number):
        #funkcja robocza - do usunięcia
           
        cap = cv2.VideoCapture(self.vid_path)

        print(self.vid_path)

        frame_width = int(cap.get(3))
        cap.set(1,frame_number)
        res, orig_image = cap.read()
 
        image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB) #convert frame to RGB
        image = letterbox(orig_image, (frame_width), stride=64, auto=True)[0]

        self.frames[frame_number].draw_skeleton(image)

        self.draw_charts(image, frame_number)

        off_height, off_width = image.shape[:2]
        off_height //= 2
        off_width //= 2
        image = cv2.resize(image,(off_width, off_height))
        
        self.tmp=orig_image

        from PIL import Image, ImageTk

        screen = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        im = Image.fromarray(screen)
        self.image = Image.fromarray(screen)

        self.img_to_tk = ImageTk.PhotoImage(image=self.image) 
        
        print('x')

        # cv2.imshow("input", image)
        # cv2.moveWindow("input",1920,0)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


class OrginalVideoProperitier():
    def __init__(self,vid_path):
        pass
        