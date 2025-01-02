
import cv2
import numpy as np


def plot_skeleton_kpts_bm(im, kpts, steps, orig_shape=None, delta=False):

    # rysuj tło dla szkielatu

    x_rec,y_rec=300,400
    x_rec_delta,y_rec_delta=orig_shape[1]-x_rec,orig_shape[0]-y_rec
    points = np.array([[x_rec_delta,y_rec_delta],
                       [x_rec_delta,y_rec_delta+y_rec],
                       [x_rec_delta+x_rec,y_rec_delta+y_rec],
                       [x_rec_delta+x_rec,y_rec_delta]],
                  dtype=np.int32)

    cv2.fillPoly(im, [points], (224,255,255))

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

    # cały szkielet
    # skeleton = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12],
    #             [7, 13], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3],
    #             [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]]
    
    # same nogi
    # skeleton = [[16, 14], [14, 12], [17, 15], [15, 13]]

    # sama prawa strona
    skeleton = [[17, 15], [15, 13], 
            [7, 13], [7, 9], [9, 11], [3, 5], [5, 7],[3,1]]


    points_to_draw=[]
    for i in skeleton:
        points_to_draw.append(i[0])
        points_to_draw.append(i[1])
    points_to_draw=set(points_to_draw)


    pose_limb_color = palette[[9, 9, 9, 9, 7, 7, 7, 0, 0, 0, 0, 0, 16, 16, 16, 16, 16, 16, 16]]
    pose_kpt_color = palette[[16, 16, 16, 16, 16, 0, 0, 0, 0, 0, 0, 9, 9, 9, 9, 9, 9]]
    radius = 5
    num_kpts = len(kpts) // steps

    # przesuniecie postaci, względem prawej stopy (#17, index 16)
    if delta==True:
        # wsp.lewej stopy:
        x_17,y_17=kpts[steps * 16], kpts[steps * 16 + 1]

        # przesuniecie postaci do środka klatki
        delta_x=orig_shape[1]//2-x_17
        delta_y=orig_shape[0]//2-y_17

        # przesuniecie postaci do środka tła

        delta_x=-x_17+x_rec_delta+x_rec//2
        delta_y=-y_17+y_rec_delta+y_rec//2+100


    else:
        delta_x=0
        delta_y=0


    for kid in range(num_kpts):
        r, g, b = pose_kpt_color[kid]
        x_coord, y_coord = kpts[steps * kid]+delta_x, kpts[steps * kid + 1]+delta_y
        if not (x_coord % 640 == 0 or y_coord % 640 == 0):
            if steps == 3:
                conf = kpts[steps * kid + 2]
                if conf < 0.5:
                    continue
            if kid-1 in points_to_draw:
                cv2.circle(im, (int(x_coord), int(y_coord)), radius, (int(r), int(g), int(b)), -1)
                # if kid==16:
                #     cv2.putText(im, 'x'+str(int(x_coord)), (int(x_coord), int(y_coord)), font, fontScale, color, thickness)
                #     cv2.putText(im, 'y'+str(int(y_coord)), (int(x_coord), int(y_coord+50)), font, fontScale, color, thickness)

    for sk_id, sk in enumerate(skeleton):
        r, g, b = pose_limb_color[sk_id]
        pos1 = (int(kpts[(sk[0]-1)*steps]+delta_x), int(kpts[(sk[0]-1)*steps+1]+delta_y))
        pos2 = (int(kpts[(sk[1]-1)*steps]+delta_x), int(kpts[(sk[1]-1)*steps+1]+delta_y))
        if steps == 3:
            conf1 = kpts[(sk[0]-1)*steps+2]
            conf2 = kpts[(sk[1]-1)*steps+2]
            if conf1<0.5 or conf2<0.5:
                continue
        if pos1[0]%640 == 0 or pos1[1]%640==0 or pos1[0]<0 or pos1[1]<0:
            continue
        if pos2[0] % 640 == 0 or pos2[1] % 640 == 0 or pos2[0]<0 or pos2[1]<0:
            continue
        cv2.line(im, pos1, pos2, (int(r), int(g), int(b)), thickness=2)
        # cv2.putText(im, str(sk[0]), pos1, font, fontScale, color, thickness)
        # cv2.putText(im, str(sk[1]), pos2, font, fontScale, color, thickness)
        # if sk[0]==17:
        #     cv2.putText(im, 'x'+str(pos1[0]), pos1, font, fontScale, color, thickness)
        #     cv2.putText(im, 'y'+str(pos1[1]), (pos1[0],pos1[1]+50), font, fontScale, color, thickness)





