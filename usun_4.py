import os
import json

name='PXL_20241218_130613481_cutted_02_007.mp4'

kpts_json_path=f'{os.getcwd()}\\_analysed\\{name.replace('.mp4','_kpts.json')}'

with open(kpts_json_path, 'r') as f:
    data = json.load(f)

tmp=0
for i,j in enumerate(data.keys()):
    delta=float(j)-tmp
    print(f'{i} : {round(float(j),1)}      {round(delta)}')
    tmp=float(j)