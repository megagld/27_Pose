import os

# directory/folder path
dir_path = '_clips'
# dir_path = 'tmp'


# list to store files
input_paths = []

# Iterate directory
for file_path in os.listdir(dir_path)[::-1]:
    # check if current file_path is a file
    if os.path.isfile(os.path.join(dir_path, file_path)):
        # add filename to list
        file_from=f'{os.getcwd()}\\{dir_path}\\{file_path}'
        file_to = file_from.replace('.mp4','_60fps.mp4')

        os.system(f"ffmpeg -y -i {file_from} -vf fps=60 {file_to}")
