#bmystek
import os
import shutil

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
    _,analysed_files,_=list(os.walk(analysed_dir))[0]

    for path,_,files in os.walk(data_dir):
        for file in files:
            if file not in analysed_files and '.git' not in file:
                file_to_analyse="{}\\{}".format(data_dir,file)
                folder_to_store="{}\\{}".format(analysed_dir,file)

                os.makedirs("{}\\{}".format(analysed_dir,file))

                analyse(file_to_analyse,folder_to_store)
            else:
                pass

def analyse(file_to_analyse,folder_to_store):

    # os.system("python {} --source \"{}\" --device cpu --output_folder \"{}\"".format('pose-estimate_black_katy.py',file_to_analyse,folder_to_store))  

    os.system("python {} --source \"{}\" --device cpu --output_folder \"{}\"".format('pose-estimate_black_katy_save_only.py',file_to_analyse,folder_to_store))  


if __name__ == "__main__":
    set_dirs()
    run()
