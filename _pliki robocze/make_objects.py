import os
import json
import classes
import cv2


# with open('_analysed/PXL_20241218_121042417_000.mp4/PXL_20241218_121042417_000_kpts.json', 'r') as f:
#   data = json.load(f)


# # tworzenie obiektów klatek

# frames=[]

# frames_to_store=[i for i in data.keys()]

# for frame,kpts in data.items():
#     frames.append(classes.Frame(int(frame),kpts))

# # tworzenie obiektu klipu 

# video='_analysed/PXL_20241218_121042417_000.mp4/PXL_20241218_121042417_000.mp4'
vid_name='VID_20241231_125439_014.mp4'

vid=classes.Clip(vid_name)
vid.display_frame(20)

# print(vid.org_vid_prop.height)
# print(vid.org_vid_prop.width)
# print(vid.org_vid_prop.duration_ts)
# print(vid.org_vid_prop.frames)




# # video testowe - pozycja punków
# vid_name='r.mp4'
# vid=classes.Clip(vid_name)

# vid.display_frame(3)


pass