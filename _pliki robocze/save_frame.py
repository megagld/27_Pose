import cv2
import os

file_path=r'D:\\Python\26_Rozpoznawanie_4\\cuts\\VID_20241208_124523_013_001.mp4'


videos-[]

# input video
cap = cv2.VideoCapture(file_path)

frame = 1500

cap.set(0,frame)
res, img = cap.read()

for i,j in enumerate(videos):
    cv2.imwrite('.\\data\\ttrain\\{:3d}.jpg'.format(i), img)