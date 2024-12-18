import cv2
import os

for path,_,files in os.walk('D:\\Python\\26_Rozpoznawanie_4\\cuts\\'):

    for file in files:
        print('x')
        if '.@__thumb' not in path:

            video_file_name='{}{}'.format(path,file)
            # frame_file_name=video_file_name.replace('mp4','jpg') 
            # input video
            cap = cv2.VideoCapture(video_file_name)

            frame = 1000

            cap.set(0,frame)
            res, img = cap.read()

            save_path='D:\\Python\\26_Rozpoznawanie_4\\cuts\\_frames\\_exta_{}'.format(file.replace('mp4','jpg'))

            cv2.imwrite(save_path, img)
