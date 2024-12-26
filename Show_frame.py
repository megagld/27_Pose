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

    def run(self):    

        # pobiera dane z okienek
        self.file =       self.entry_state[3].get()
        self.frame =       int(self.entry_state[5].get())
        
        self.show_frame()
    

    def show_frame(self):

        self.vid=classes.Clip(self.file)
        self.vid.display_frame(self.frame)
        self.orinal_image=self.vid.image

        self.image=ImageTk.PhotoImage(self.orinal_image)

        # Put it in the display window
        img_label = ttk.Label(self, image=self.image)
        img_label.image = self.vid.img_to_tk
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