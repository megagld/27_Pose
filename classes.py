import os
import json
from utils.datasets import letterbox
import cv2
import numpy as np

class Point():
    def __init__(self,sk_id,pos_x,pos_y,pos_z):
        self.sk_id=sk_id
        self.x=pos_x
        self.y=pos_y
        self.z=pos_z
        self.x_disp=int(pos_x)
        self.y_disp=int(pos_y)
        self.z_disp=int(pos_z)

class Frame():
    def __init__(self,frame_count,kpts):
        self.frame_count=frame_count
        self.kpts=kpts
        self.detected=False
        self.skeleton_points={}
        self.organize_points()

    def organize_points(self):
        steps=3
        if self.kpts:
            self.detected=True
            for sk_id in range(17):
                pos_x, pos_y, pos_z = (self.kpts[sk_id*steps]), (self.kpts[sk_id*steps+1]), (self.kpts[sk_id*steps+2])
                self.skeleton_points[sk_id+1]=Point(sk_id+1, pos_x, pos_y, pos_z)

    def draw_skeleton(self,image):

        skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12],
            [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3],
            [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]
        
        points_to_display=list(range(1,17))

        #Plot the skeleton and keypointsfor coco datatset
        palette = np.array([[255, 128, 0], [255, 153, 51], [255, 178, 102],
                            [230, 230, 0], [255, 153, 255], [153, 204, 255],
                            [255, 102, 255], [255, 51, 255], [102, 178, 255],
                            [51, 153, 255], [255, 153, 153], [255, 102, 102],
                            [255, 51, 51], [153, 255, 153], [102, 255, 102],
                            [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0],
                            [255, 255, 255]])
        
        pose_limb_color = palette[[9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
        pose_kpt_color = palette[[16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
        radius = 5
        num_kpts = 17

        for kid in range(1,18):
                r, g, b = pose_kpt_color[kid]
                x_coord, y_coord = self.skeleton_points[kid].x_disp, self.skeleton_points[kid].y_disp
                if not (x_coord % 640 == 0 or y_coord % 640 == 0):
                    if kid+1 in points_to_display:
                        cv2.circle((image, x_coord, y_coord), radius, (int(r), int(g), int(b)), -1)

            # for sk_id, sk in enumerate(skeleton_prawa):
            #     r, g, b = pose_limb_color[sk_id]
            #     pos1 = (int(kpts[(sk[0]-1)*steps]), int(kpts[(sk[0]-1)*steps+1]))
            #     pos2 = (int(kpts[(sk[1]-1)*steps]), int(kpts[(sk[1]-1)*steps+1]))
            #     if steps == 3:
            #         conf1 = kpts[(sk[0]-1)*steps+2]
            #         conf2 = kpts[(sk[1]-1)*steps+2]
            #         if conf1<0.5 or conf2<0.5:
            #             continue
            #     if pos1[0]%640 == 0 or pos1[1]%640==0 or pos1[0]<0 or pos1[1]<0:
            #         continue
            #     if pos2[0] % 640 == 0 or pos2[1] % 640 == 0 or pos2[0]<0 or pos2[1]<0:
            #         continue
            #     cv2.line(im, pos1, pos2, (int(r), int(g), int(b)), thickness=3) 


class Clip():
    def __init__(self,vid_name):
        self.name=vid_name
        self.vid_path=f'{os.getcwd()}\\_analysed\\{self.name}\\{self.name}'

        self.org_vid_prop=OrginalVideoProperitier(self.vid_path)

        self.frames=None
        self.add_frames()

        self.charts=None
    
    def add_frames(self):

        kpts_json_path=f'{os.getcwd()}\\_analysed\\{self.name}\\{self.name.replace('.mp4','_kpts.json')}'

        with open(kpts_json_path, 'r') as f:
            data = json.load(f)
            
        self.frames=[Frame(int(frame),kpts) for frame,kpts in data.items()]
    
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

        cv2.imshow("input", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class OrginalVideoProperitier():
    def __init__(self,vid_path):
        pass
        