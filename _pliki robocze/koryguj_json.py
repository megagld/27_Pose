import json
import cv2
import os


# muszą być katalogi tmp i tmp\\_ready
# plki analizuje pliki z tmp

def cor_json(json_org_file_name, json_new_file_name, vid_file_name):

    # json_org_file_name='D:\\Python\\27_Pose\\_tmp\\VID_20241231_125439_007_kpts.json'
    # json_new_file_name='D:\\Python\\27_Pose\\_tmp\\_ready\\VID_20241231_125439_007_kpts.json'
    # vid_file_name='D:\\Python\\27_Pose\\_data\\VID_20241231_125439_007.mp4'

    # dane z analizy pozycji
    with open(json_org_file_name, 'r') as f:
        json_org_data = json.load(f)
        # json_org_data=słownik

    # dane z pliku video - timestamp i numeracja klatek

    cap = cv2.VideoCapture(vid_file_name)
    frame_times={}
    # key=numer kaltki, value=czas

    frame_no = 0
    while(cap.isOpened()):
        frame_exists, curr_frame = cap.read()
        if frame_exists:
            frame_times[frame_no] = cap.get(cv2.CAP_PROP_POS_MSEC)
        else:
            break
        frame_no += 1

    cap.release()

    # zmiana kluczy w json_org_data ze str na int
    json_org_data={int(i):j for i,j in json_org_data.items()}

    # zmiana kluczy z numerów klatek na ich czasy i dodanie czasów dla klatek bez rozpoznania

    output_data={}

    for frame_number, frame_time in frame_times.items():
        try:
            output_data[frame_time]=json_org_data[frame_number]
        except:
            output_data[frame_time]=[]

    # zapis do nowego pliku:

    with open(json_new_file_name, "w") as jsonfile:
        json.dump(output_data, jsonfile)



def run():
    main_dir = os.getcwd()
    data_dir="{}\\_data".format(main_dir)
    tmp_dir="{}\\_tmp".format(main_dir)
    ready_dir="{}\\_tmp\\_ready".format(main_dir)

    # ustalenie które pliki są już skorygowane
    _,cor_files,_=list(os.walk(ready_dir))[0]

    for path,_,files in os.walk(tmp_dir):
        for file in files:
            if file not in cor_files and '_ready' not in path:

                json_org_file_name="{}\\{}".format(tmp_dir,file)
                json_new_file_name="{}\\{}".format(ready_dir,file)
                vid_file_name="{}\\{}".format(data_dir,file.replace('_kpts.json','.mp4'))

                try:
                    cor_json(json_org_file_name, json_new_file_name, vid_file_name)
                    print(file+' gotowe.')
                except:
                    print(file+' nie wykonane.')
            else:
                pass

run()