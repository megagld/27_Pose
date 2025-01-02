#bmystek
import os
import io
import shutil
import tkinter as tk
from tkinter import ttk
import json
import os
from wakepy import keep
from tkinter import ttk
import tkinter as tk
import classes
from PIL import Image, ImageTk
import PIL.Image



class App(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # root window
        row_c=8
        row_height=25
        cols=[150,250]
        prop=cols[0]//cols[1]

        root_width=sum(cols)+600
        root_height=row_c*row_height+600

        # root = tk.Tk()
        self.geometry('{}x{}'.format(root_width,root_height))
        self.title('Wyświetl klatkę')
        self.resizable(1, 1)
        
        # configure the grid
        self.columnconfigure(0, weight=prop)
        self.columnconfigure(1, weight=1)

        #image setup
        self.source_image = None
        self.image_id = None
        self.image = None

        self.create_widgets()
        self.bind('<Configure>', self.update_values)

    def update_values(self, *_) -> None:
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None: return
        # self.delete_previous_image()
        self.resize_image()
        self.paste_image()

    def delete_previous_image(self) -> None:
        if self.image is None: return
        self.delete(self.image_id)
        self.image = self.image_id = None

    def resize_image(self) -> None:
        image_width, image_height = self.source_image.size
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        ratio = min(width_ratio, height_ratio)

        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)
        scaled_image = self.source_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)
    
    def paste_image(self) -> None:
        # self.image_id = self.create_image(self.center_x, self.center_y, image=self.image)

        self.image_id = ttk.Label(self, image=self.image)
        self.image_id.grid(column=0, row=8, columnspan=2)

    def open_image(self) -> None:

        import classes
        self.frame=classes.Clip(self.file)
        self.frame.display_frame(self.frame_count)
        self.source_image=self.frame.image

        # self.delete_previous_image()

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()
















    def run(self):    

        # pobiera dane z okienek
        self.file =       self.entry_state[3].get()
        self.frame_count =       int(self.entry_state[5].get())
        
        # self.vid=classes.Clip(self.file)
        # self.vid.display_frame(self.frame_count)
        # self.orinal_image=self.vid.image
        self.open_image()
    




    def show_frame(self, *_) -> None:
        
        image_width, image_height = self.orinal_image.width,self.orinal_image.height
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        width_ratio = self.width / image_width
        height_ratio = self.height / image_height
        ratio = min(width_ratio, height_ratio)
        new_width = int(image_width * ratio)-200
        new_height = int(image_height * ratio)-200
        scaled_image = self.orinal_image.resize((new_width, new_height))
        self.image = ImageTk.PhotoImage(scaled_image)

        print(image_height)
        # self.image=ImageTk.PhotoImage(self.orinal_image)

        # Put it in the display window
        img_label = ttk.Label(self, image=self.image)
        # img_label.image = self.vid.img_to_tk
        img_label.grid(column=0, row=8, columnspan=2)

        print(self.winfo_geometry())

    def update_image(self):
        
        self.image_width = self.winfo_width()//2
        self.image_height = self.winfo_height()//2
        # self.center_x = self.width//2
        # self.center_y = self.height//2

        self.image=ImageTk.PhotoImage(self.orinal_image)
        self.image.resize((100,50))

        # Put it in the display window
        img_label = ttk.Label(self, image=self.image)
        img_label.image = self.vid.img_to_tk
        img_label.grid(column=0, row=8, columnspan=2)


    def create_widgets(self):
        #set labels
        texts=['',
            '',
            '',
            'Plik:',
            '',
            'Klatka/czas [ms]:',
            '']
        self.texts_state={}

        for i,j in enumerate(texts):
            label = ttk.Label(self, text=j,font=('helvetica', 10))
            label.grid(column=0, row=i, sticky=tk.E, padx=5)
            self.texts_state[i]=label

        # set entry
        entrys=['',
            'button',
            '',
            'PXL_20241218_121042417_000.mp4',
            '',
            '60',
            '']
        self.entry_state={}

        for i,j in enumerate(entrys):
            if j=='':
                entry = ttk.Label(self, text=j,font=('helvetica', 10))
                entry.grid(column=0, row=i, sticky=tk.E, padx=5)
            elif j=='checkbox':
                self.var = tk.IntVar(value=1)
                entry=tk.Checkbutton(self,variable=self.var)
            elif j=='button':
                entry=tk.Button(text='Wyświetl klatkę', command=self.run, bg='brown', fg='white', font=('helvetica', 10, 'bold'),width=16)
            elif j=='progresbar':
                entry=ttk.Progressbar(self, orient='horizontal',mode='determinate', length=140)
            else:
                entry = ttk.Entry(self,textvariable='',width=30)
                entry.insert(-1, j)

            entry.grid(column=1, row=i, sticky=tk.W, padx=5)
            self.entry_state[i]=entry

    def parse_files(self):
        input_dir = os.getcwd()

        self.lista_plikow=[]

        for path,_,files in os.walk(input_dir):
            for mp4_file in files:
                if mp4_file.endswith(".mp4"):
                    self.lista_plikow.append([path.split('\\')[-1],mp4_file])

if __name__ == "__main__":
    app = App()
    app.mainloop()