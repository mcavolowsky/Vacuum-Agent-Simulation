
import Tkinter as tk

from utils import *

IMAGE_X_OFFSET = 0.5
IMAGE_Y_OFFSET = 0.5

IMAGEID_X_OFFSET = 0.05
IMAGEID_Y_OFFSET = 0.05

ID_X_OFFSET = 0.03
ID_Y_OFFSET = 0.0

#______________________________________________________________________________

def DisplayObject(obj):
    obj.image = None
    obj.id_image = None
    return obj

class EnvFrame(tk.Frame):
    def __init__(self, env, title='AIMA GUI', cellwidth=50, n=10):
        update(self, cellwidth=cellwidth, running=False, delay=1.0)
        self.n = n
        self.running = 0
        self.delay = 1.0
        self.env = env
        self.cellwidth = cellwidth
        tk.Frame.__init__(self, None, width=(cellwidth + 2) * env.width, height=(cellwidth + 2) * env.height)
        # self.title(title)
        # Toolbar
        toolbar = tk.Frame(self, relief='raised', bd=2)
        toolbar.pack(side='top', fill='x')
        for txt, cmd in [('Step >', self.next_step), ('Run >>', self.run),
                         ('Stop [ ]', self.stop)]:
            tk.Button(toolbar, text=txt, command=cmd).pack(side='left')
        tk.Label(toolbar, text='Delay').pack(side='left')
        scale = tk.Scale(toolbar, orient='h', from_=0.0, to=10, resolution=0.5,
                         command=lambda d: setattr(self, 'delay', d))
        scale.set(self.delay)
        scale.pack(side='left')
        # Canvas for drawing on
        self.canvas = tk.Canvas(self, width=(cellwidth + 1) * env.width,
                                height=(cellwidth + 1) * env.height, background="white")
        self.canvas.bind('<Button-1>', self.left)  ## What should this do?
        self.canvas.bind('<Button-2>', self.edit_objects)
        self.canvas.bind('<Button-3>', self.edit_objects)
        if cellwidth:
            c = self.canvas
            for i in range(1, env.width + 1):
                c.create_line(0, i * cellwidth, env.height * cellwidth, i * cellwidth)
                c.pack(expand=1, fill='both')
            for j in range(1,env.height +1):
                    c.create_line(j * cellwidth, 0, j * cellwidth, env.width * cellwidth)
                    c.pack(expand=1, fill='both')
        self.pack()

        self.class2file = {'':'', 'RandomReflexAgent':'img/robot-%s.gif',
                       'Dirt':'img/dirt.gif',
                       'Wall':'img/wall.gif'}
        self.file2image = {'':None, 'img/robot-right.gif':tk.PhotoImage(file='img/robot-right.gif'),
                       'img/robot-left.gif':tk.PhotoImage(file='img/robot-left.gif'),
                       'img/robot-up.gif':tk.PhotoImage(file='img/robot-up.gif'),
                       'img/robot-down.gif':tk.PhotoImage(file='img/robot-down.gif'),
                       'img/dirt.gif':tk.PhotoImage(file='img/dirt.gif'),
                       'img/wall.gif':tk.PhotoImage(file='img/wall.gif')}
        # note up and down are switched, since (0,0) is in the upper left
        self.orientation = {(1,0): 'right', (-1,0): 'left', (0,-1): 'up', (0,1): 'down'}

    def background_run(self):
        if self.running:
            self.env.step()
            self.update_display()

            ms = int(1000 * max(float(self.delay), 0.5))
            self.after(ms, self.background_run)

    def run(self):
        print 'run'
        self.running = 1
        self.background_run()

    def next_step(self):
        self.env.step()
        self.update_display()

    def stop(self):
        print 'stop'
        self.running = 0

    def left(self, event):
        print 'left at ', event.x / 50, event.y / 50

    def edit_objects(self, event):
        '''Choose an object within radius and edit its fields.'''
        pass

    def object_to_image(self,obj):
        if hasattr(obj, 'heading'):
            return self.file2image[self.class2file[getattr(obj, '__name__', obj.__class__.__name__)] % self.orientation[obj.heading]]
        else:
            return self.file2image[self.class2file[getattr(obj, '__name__', obj.__class__.__name__)]]

    def configure_display(self):
        for obj in self.env.objects:
            obj = DisplayObject(obj)
        self.update_display()

    def update_display(self):
        for obj in self.env.objects:
            if hasattr(obj, 'image') and obj.image:
                if isinstance(obj.location, tuple):
                    self.canvas.itemconfig(obj.image, image=self.object_to_image(obj))

                    old_loc = self.canvas.coords(obj.image)
                    self.canvas.move(obj.image, (obj.location[0]+(IMAGE_X_OFFSET + (obj.id!='')*IMAGEID_X_OFFSET))*self.cellwidth-old_loc[0],
                                                    (obj.location[1]+IMAGE_Y_OFFSET + (obj.id!='')*IMAGEID_Y_OFFSET)*self.cellwidth-old_loc[1])
                else:
                    self.canvas.itemconfig(obj.image, state='hidden')
            else:
                obj.image = self.canvas.create_image((obj.location[0] + (IMAGE_X_OFFSET + (obj.id!='')*IMAGEID_X_OFFSET)) * self.cellwidth,
                                                        (obj.location[1] + (IMAGE_Y_OFFSET + (obj.id!='')*IMAGEID_Y_OFFSET)) * self.cellwidth,
                                                        image=self.object_to_image(obj))

            if hasattr(obj, 'id_image') and obj.id_image:
                if isinstance(obj.location, tuple):
                    old_loc = self.canvas.coords(obj.id_image)
                    self.canvas.move(obj.id_image, (obj.location[0] + ID_X_OFFSET) * self.cellwidth - old_loc[0],
                                     (obj.location[1] + ID_Y_OFFSET) * self.cellwidth - old_loc[1])
                else:
                    self.canvas.itemconfig(obj.id_image, state='hidden')
            else:
                obj.id_image = self.canvas.create_text((obj.location[0] + ID_X_OFFSET) * self.cellwidth,
                                                     (obj.location[1] + ID_Y_OFFSET) * self.cellwidth,
                                                     text=obj.id, anchor='nw')

#______________________________________________________________________________
