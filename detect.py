#bmystek
import os
import shutil
from wakepy import keep


def set_dirs():
    global data_dir, analysed_dir
    # ustala czy katalogi z danymi i istnieją 
    main_dir = os.getcwd()
    data_dir="{}\\_data".format(main_dir)
    analysed_dir="{}\\_analysed".format(main_dir)


    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(analysed_dir):
        os.makedirs(analysed_dir)

def run():
    # ustalenie które pliki są już przeanalizowane
    main_dir = os.getcwd()
    _,_,analysed_files=list(os.walk(analysed_dir))[0]

    files_to_analise = []

    for path,_,files in os.walk(data_dir):
        for file in files:
            tmp_file_name = file.replace('.mp4','_kpts.json')
            
            if tmp_file_name not in analysed_files and '.git' not in file:

                file_to_analyse="{}\\{}".format(path,file)
                folder_to_store=analysed_dir

                # analyse(file_to_analyse,folder_to_store)
                files_to_analise.append((file_to_analyse,folder_to_store))
            else:
                pass
    

    for file_to_analyse,folder_to_store in files_to_analise:
        print(f'files to analise: {len(files_to_analise)}')
        analyse(file_to_analyse,folder_to_store)

    

def analyse(file_to_analyse,folder_to_store):

    # os.system("python {} --source \"{}\" --device cpu --output_folder \"{}\"".format('pose-estimate_black_katy.py',file_to_analyse,folder_to_store))  
    
    with keep.running() as k:
    # do stuff that takes long time

        os.system("python {} --source \"{}\" --device cpu --output_folder \"{}\"".format('pose-estimate_black_katy_save_only.py',file_to_analyse,folder_to_store))  


if __name__ == "__main__":
    set_dirs()
    run()
