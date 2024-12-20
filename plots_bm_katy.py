
import cv2
import numpy as np
import math

def angle_between_vectors(u, v):
    dot_product = sum(i*j for i, j in zip(u, v))
    norm_u = math.sqrt(sum(i**2 for i in u))
    norm_v = math.sqrt(sum(i**2 for i in v))
    cos_theta = dot_product / (norm_u * norm_v)
    angle_rad = math.acos(cos_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_rad, angle_deg

def plot_skeleton_kpts_bm(im, kpts, steps, orig_shape=None):


    # object details
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1
    color = (255, 0, 0)
    thickness = 2

    #Plot the skeleton and keypointsfor coco datatset
    palette = np.array([[255, 128, 0], [255, 153, 51], [255, 178, 102],
                        [230, 230, 0], [255, 153, 255], [153, 204, 255],
                        [255, 102, 255], [255, 51, 255], [102, 178, 255],
                        [51, 153, 255], [255, 153, 153], [255, 102, 102],
                        [255, 51, 51], [153, 255, 153], [102, 255, 102],
                        [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0],
                        [255, 255, 255]])

    skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12],
                [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3],
                [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]

    skeleton_prawa = [  [17, 15], [15, 13],
                        [7, 13], 
                        [7, 9], [9, 11],
                        [5, 7], [3,5], [1,3]]
    
    points_to_display=[1,3,5,7,9,11,13,15,17]

    pose_limb_color = palette[[9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
    pose_kpt_color = palette[[16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
    radius = 5
    num_kpts = len(kpts) // steps

    for kid in range(num_kpts):
        r, g, b = pose_kpt_color[kid]
        x_coord, y_coord = kpts[steps * kid], kpts[steps * kid + 1]
        if not (x_coord % 640 == 0 or y_coord % 640 == 0):
            if steps == 3:
                conf = kpts[steps * kid + 2]
                if conf < 0.5:
                    continue
            if kid+1 in points_to_display:
                cv2.circle(im, (int(x_coord), int(y_coord)), radius, (int(r), int(g), int(b)), -1)

    for sk_id, sk in enumerate(skeleton_prawa):
        r, g, b = pose_limb_color[sk_id]
        pos1 = (int(kpts[(sk[0]-1)*steps]), int(kpts[(sk[0]-1)*steps+1]))
        pos2 = (int(kpts[(sk[1]-1)*steps]), int(kpts[(sk[1]-1)*steps+1]))
        if steps == 3:
            conf1 = kpts[(sk[0]-1)*steps+2]
            conf2 = kpts[(sk[1]-1)*steps+2]
            if conf1<0.5 or conf2<0.5:
                continue
        if pos1[0]%640 == 0 or pos1[1]%640==0 or pos1[0]<0 or pos1[1]<0:
            continue
        if pos2[0] % 640 == 0 or pos2[1] % 640 == 0 or pos2[0]<0 or pos2[1]<0:
            continue
        cv2.line(im, pos1, pos2, (int(r), int(g), int(b)), thickness=3)
        # cv2.putText(im, str(sk[0]), pos1, font, fontScale, color, thickness)
        # cv2.putText(im, str(sk[1]), pos2, font, fontScale, color, thickness)

def calc_angs(kpts,steps):

    pkt_to_vectors=[[17,15,13],[11,9,7],[15,13,7]]

    frame_x_pos = [int(kpts[(17-1)*steps])]

    stored_angs=[]

    for i,j in enumerate(pkt_to_vectors):

        sk=j[0]
        kostka = (int(kpts[(sk-1)*steps]), int(kpts[(sk-1)*steps+1]))
        sk=j[1]
        kolano = (int(kpts[(sk-1)*steps]), int(kpts[(sk-1)*steps+1]))
        sk=j[2]
        biodro = (int(kpts[(sk-1)*steps]), int(kpts[(sk-1)*steps+1]))

        wektor_piszczel=[kostka[0]-kolano[0],kostka[1]-kolano[1]]
        wektor_udo=[kolano[0]-biodro[0],kolano[1]-biodro[1]]
        
        kat_ugiecia_kolan=angle_between_vectors(wektor_piszczel,wektor_udo)
        stored_angs.append(kat_ugiecia_kolan[1])

    return frame_x_pos+stored_angs

def polt_angs(im, steps,stored_angs, orig_shape=None, color=(255, 128, 0)):

    podklad=[[0,800],[0,1080],[1920,1080],[1920,800]]
    podklad = np.array(podklad)
    cv2.fillPoly(im, [podklad], color=(115,200,221))

    # object details
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1
    # color = (0, 255, 0)
    thickness = 2

    delta_y=800

    wykresy=['kolano','lokiec','biodro']
    
    opis='kat zgiecia [st.]:'
    lok_opis_wykresu=(30,delta_y-30)
    cv2.putText(im, opis, lok_opis_wykresu, font, fontScale, color, thickness)


    for i,j in enumerate(stored_angs[-1][1:]):
        lok_opis_wykresu=(stored_angs[-1][0]+30,delta_y+90*i+80)
        text=str(180-int(j))
        cv2.putText(im, text, lok_opis_wykresu, font, fontScale, color, thickness)
        
        lok_opis_wykresu=(30,delta_y+90*i+80)
        opis=wykresy[i]
        cv2.putText(im, opis, lok_opis_wykresu, font, fontScale, color, thickness)

   
    # wykresy
    if len(stored_angs)>1:
        for frame,data in enumerate(stored_angs):
            for plot_cnt,ang in enumerate(data[1:]):

                pos_1=stored_angs[frame-1][0],int(stored_angs[frame-1][plot_cnt+1]+delta_y+90*plot_cnt)
                if frame==0:
                    pos_2=pos_1
                else:
                    pos_2=stored_angs[frame][0],int(ang+delta_y+90*plot_cnt)
                
                cv2.line(im, pos_1, pos_2, color, thickness=3)

                cv2.line(im, (0,delta_y+90*plot_cnt), (1920,delta_y+90*plot_cnt), color, thickness=2)
                cv2.line(im, (0,delta_y+90*(plot_cnt+1)), (1920,delta_y+90*(plot_cnt+1)), color, thickness=2)

        cv2.line(im, (stored_angs[-1][0],0), (stored_angs[-1][0],1088), color, thickness=2) #usunąć
        
def plot_trace(im, steps,trace, orig_shape=None, color=(255, 128, 0)):

    if len(trace)>1:
        for i in range(len(trace)-1):
            pos_1=trace[i]
            pos_2=trace[i+1]
            cv2.line(im, pos_1, pos_2, color, thickness=3)
    