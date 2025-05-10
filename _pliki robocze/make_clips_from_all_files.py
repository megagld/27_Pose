import os
import classes

# tworzy obiekt draws_states
draws_states = classes.Draws_states()

# zebrabnie danych
vid_folder_path = f"{os.getcwd()}\\_data"
for path,_,files in os.walk(vid_folder_path):
    for file in files:
        if file.endswith(".mp4"):
            vid_path = f"{os.getcwd()}\\_data\\{file}"
            print(vid_path)
            try:
                clip=classes.Clip(file)
                clip.make_video_clip(draws_states)
                print(f"{file} gotowe.")
            except:
                print(f"{file} błędne.")

