import PIL.Image
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk
import classes

class CanvasImage(tk.Canvas):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.source_image = None
        self.image_id = None
        self.image = None

        self.width, self.height = 0, 0
        self.center_x, self.center_y = 0, 0
        self.bind('<Configure>', self.update_values)
    
    def update_values(self, *_) -> None:
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        self.center_x = self.width//2
        self.center_y = self.height//2

        if self.image is None: return
        self.delete_previous_image()
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

    def print_size(self) -> None:
        if self.image is None: return
        print('x'*10)
        print('image_size'+str(self.source_image.size))
        print('self.size :'+str(self.width)+"x"+str(self.height))
        print('x'*12)

    def paste_image(self) -> None:
        self.image_id = self.create_image(self.center_x, self.center_y, image=self.image)

    def open_image(self) -> None:
        # if not (filename := askopenfilename()): return

        self.delete_previous_image()

        self.master.master.clip.display_frame(self.master.master.frame_to_display)
        self.source_image = self.master.master.clip.image

        self.image = ImageTk.PhotoImage(self.source_image)

        self.resize_image()
        self.paste_image()

class Frame_right(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        self.width = self.winfo_width()

        self.scale_range = self.master.clip.frames_amount-1

        self.var = None

        self.canvas = CanvasImage(self, relief='sunken', bd=2)
        tk.Button(self, text='ładuj obraz', comman=self.canvas.open_image).pack()
        tk.Button(self, text='canva size', comman=self.canvas.print_size).pack()
        tk.Button(self, text='frame size', comman=self.print_size).pack()
        tk.Button(self, text='frame count +', comman=self.frame_cnt_forward).pack()
        tk.Button(self, text='frame count -', comman=self.frame_cnt_back).pack()
        tk.Button(self, text='make clip', comman=self.make_clip).pack()

        self.scale=ttk.Scale(self, variable = self.var, orient='horizontal', to=self.scale_range, command=self.update_view)

        self.scale.pack(side="top", fill="x", expand=False)

        self.canvas.pack(expand=True, fill='both', padx=10, pady=10)

    def update_view(self,x) -> None:
        self.master.frame_to_display=int(float(x))
        self.canvas.open_image()
        # print(x)

    def print_size(self) -> None:       
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        print('x'*10)
        print('self.size :'+str(self.width)+"x"+str(self.height))
        print('x'*12)

    def frame_cnt_forward(self):
        self.master.frame_to_display+=1
        self.master.frame_to_display=min(self.master.frame_to_display, self.scale_range)
        self.canvas.open_image()
        self.scale.set(self.master.frame_to_display)

    def frame_cnt_back(self):
        self.master.frame_to_display-=1
        self.master.frame_to_display=max(0, self.master.frame_to_display)
        self.canvas.open_image()
        self.scale.set(self.master.frame_to_display)

    def play_stop(self):

        self.master.play=not self.master.play

        print(self.master.play)

        self.play_video()

    def play_video(self):
        # if self.play == True:
        #     # while True:
        #     self.master.frame_to_display+=1
        #     self.master.frame_to_display%=(self.master.clip.frames_amount-20)
        #         # print(self.master.frame_to_display)
        #         # self.canvas.open_image()
        #     print(self.master.frame_to_display)
        # else:
        #     pass
        pass

    def make_clip(self):
        self.master.clip.make_video_clip()


class Frame_left(tk.Frame):
    def __init__(self, master: tk.Tk, **kwargs):
        super().__init__(master, **kwargs)

        # tk.Button(self, text='frame size', comman=self.print_size).pack(expand=False, fill='both', padx=10, pady=10)
        self.create_widgets()

    def print_size(self) -> None:
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        print('x'*10)
        print('self.size :'+str(self.width)+"x"+str(self.height))
        print('x'*12)

    def create_widgets(self):
        
        #set labels
        texts=['',
                'Wykresy:',
                'zgięcie prawego kolana',
                'zgięcie prawego biodra',
                'zgięcie prawego łokcia',
                '',
                'zgięcię lewego kolana',
                'zgięcie lewego biodra',
                'zgięcie lewego łokcia']
        
        self.texts_state={}

        for i,j in enumerate(texts):
            label = ttk.Label(self, text=j,font=('helvetica', 10))
            label.grid(column=0, row=i, sticky=tk.W, padx=15)
            self.texts_state[i]=label

        # set entry
        entrys=['',
                '',
                'checkbox',
                'checkbox',
                'checkbox',
                '',
                'checkbox',
                'checkbox',
                'checkbox']
        
        self.entry_state={}

        for i,j in enumerate(entrys):
            if j=='':
                entry = ttk.Label(self, text=j,font=('helvetica', 10))
                entry.grid(column=0, row=i, sticky=tk.E, padx=5)
            elif j=='checkbox':
                self.var = tk.IntVar(value=0)
                entry=tk.Checkbutton(self,variable=self.var)
            elif j=='button':
                entry=tk.Button(text='Oznacz pdfy', command=self.run, bg='brown', fg='white', font=('helvetica', 10, 'bold'),width=16)
            elif j=='progresbar':
                entry=ttk.Progressbar(self, orient='horizontal',mode='determinate', length=140)
            else:
                entry = ttk.Entry(self,textvariable=j,width=30)
                entry.insert(-1, j)

            entry.grid(column=1, row=i, sticky=tk.E, padx=5)
            self.entry_state[i]=entry

class Window(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # twórz obiekt clipu

        self.play=False

        self.filename='PXL_20241218_121042417_000.mp4'
        self.frame_to_display=20

        self.clip=classes.Clip(self.filename)

        # twórz okno

        self.minsize(800, 600)
        self.frame_1 = Frame_left(self).pack(side='left', fill='both', expand=False)
        self.frame_2 = Frame_right(self).pack(side='right', fill='both', expand=True)

        self.delay = 30
        if self.play==True:
            self.frame_to_display+=1
            print(self.frame_to_display)
        if self.frame_2:
            self.update()
            print('update')
        
    
    def update(self):
        self.frame_2.canvas.open_image()
        self.after(self.delay, self.update)
        pass


if __name__ == '__main__':
    window = Window()
    window.mainloop()