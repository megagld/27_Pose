#bmystek
import os
import shutil
from wakepy import keep


def set_dirs():
    global data_dir, analysed_dir
    # ustala czy katalogi z danymi i istnieją 
    main_dir = os.getcwd()
    data_dir="{}\\_data\\_detect_all".format(main_dir)
    analysed_dir="{}\\_analysed".format(main_dir)


    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(analysed_dir):
        os.makedirs(analysed_dir)

def run():
    # uwaga - analizowane są wszystkie pliki z katalogu "_detect_all" niezależenie czy są już wczesniejsze analizy 
    main_dir = os.getcwd()

    files_to_analise = []

    for path,_,files in os.walk(data_dir):
        for file in files:
            if '.git' not in file:

                file_to_analyse="{}\\{}".format(path,file)
                folder_to_store=analysed_dir

                # analyse(file_to_analyse,folder_to_store)
                files_to_analise.append((file_to_analyse,folder_to_store))
            else:
                pass
    

    for file_to_analyse,folder_to_store in files_to_analise:
        print(f'files to analise: {len(files_to_analise)}')
        analyse_all(file_to_analyse,folder_to_store)

    

def analyse_all(file_to_analyse,folder_to_store):

    # os.system("python {} --source \"{}\" --device cpu --output_folder \"{}\"".format('pose-estimate_black_katy.py',file_to_analyse,folder_to_store))  
    
    with keep.running() as k:
    # do stuff that takes long time

        os.system("python {} --source \"{}\" --device cpu  --detect_all --output_folder \"{}\"".format('pose-estimate_black_katy_save_only.py',file_to_analyse,folder_to_store))  

if __name__ == "__main__":
    set_dirs()
    run()
