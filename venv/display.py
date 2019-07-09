
import Tkinter as tk
import PIL.Image as Image
import PIL.ImageTk as itk

from objects import Object
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
    def __init__(self, env, root = tk.Tk(), title='Robot Vacuum Simulation', cellwidth=50, n=10):
        update(self, cellwidth=cellwidth, running=False, delay=1.0)
        self.root = root
        self.running = 0
        self.delay = 0.0
        self.env = env
        self.cellwidth = cellwidth
        tk.Frame.__init__(self, None, width=min((cellwidth + 2) * env.width,self.root.winfo_screenwidth()),
                          height=min((cellwidth + 2) * env.height, self.root.winfo_screenheight()))
        self.root.title(title)

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

        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.canvas.xview)
        vbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=self.canvas.yview)
        self.canvas.config(width=(cellwidth + 1) * env.width, height=(cellwidth + 1) * env.height)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)


        # Canvas click handlers (1 = left, 2 = middle, 3 = right)
        self.canvas.bind('<Button-1>', self.left)  ## What should this do?
        self.canvas.bind('<Button-2>', self.edit_objects)
        self.canvas.bind('<Button-3>', self.edit_objects)
        if cellwidth:
            c = self.canvas
            for i in range(1, env.width + 1):
                c.create_line(0, i * (cellwidth + 1), env.height * (cellwidth + 1), i * (cellwidth + 1))
                c.pack(expand=1, fill='both')
            for j in range(1,env.height + 1):
                c.create_line(j * (cellwidth + 1), 0, j * (cellwidth + 1), env.width * (cellwidth + 1))
                c.pack(expand=1, fill='both')
        self.pack()

        self.class2file = {'':'', 'RandomReflexAgent':'robot-%s',
                       'Dirt':'dirt',
                       'Wall':'wall'}
        self.file2image = {'':None, 'robot-right':itk.PhotoImage(Image.open('img/robot-right.png').resize((40,40))),
                       'robot-left':itk.PhotoImage(Image.open('img/robot-left.png').resize((40,40))),
                       'robot-up':itk.PhotoImage(Image.open('img/robot-up.png').resize((40,40))),
                       'robot-down':itk.PhotoImage(Image.open('img/robot-down.png').resize((40,40))),
                       'dirt':itk.PhotoImage(Image.open('img/dirt.png').resize((40,19))),
                       'wall':itk.PhotoImage(Image.open('img/wall.png').resize((40,40)))}
        # note up and down are switched, since (0,0) is in the upper left
        self.orientation = {(1,0): 'right', (-1,0): 'left', (0,-1): 'up', (0,1): 'down'}

        self.canvas.config(scrollregion=(0, 0, (self.cellwidth + 1) * self.env.width, (self.cellwidth + 1) * self.env.height))

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
        loc = (event.x / (self.cellwidth + 1), event.y / (self.cellwidth + 1))
        objs = self.env.find_at(Object, loc)
        if not objs: objs = 'Nothing'
        print 'Cell (%s, %s) contains %s' %  (loc[0], loc[1], objs)

    def edit_objects(self, event):
        '''Choose an object within radius and edit its fields.'''
        pass

    def object_to_image(self,obj):
        if hasattr(obj, 'heading'):
            return self.file2image[self.class2file.get(getattr(obj, '__name__', obj.__class__.__name__),'') % self.orientation[obj.heading]]
        else:
            return self.file2image[self.class2file.get(getattr(obj, '__name__', obj.__class__.__name__),'')]

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
                    self.canvas.move(obj.image, (obj.location[0]+(IMAGE_X_OFFSET + (obj.id!='')*IMAGEID_X_OFFSET))*(self.cellwidth + 1)-old_loc[0],
                                                    (obj.location[1]+IMAGE_Y_OFFSET + (obj.id!='')*IMAGEID_Y_OFFSET)*(self.cellwidth + 1)-old_loc[1])
                else:
                    self.canvas.itemconfig(obj.image, state='hidden')
            else:
                obj.image = self.canvas.create_image((obj.location[0] + (IMAGE_X_OFFSET + (obj.id!='')*IMAGEID_X_OFFSET)) * (self.cellwidth + 1),
                                                        (obj.location[1] + (IMAGE_Y_OFFSET + (obj.id!='')*IMAGEID_Y_OFFSET)) * (self.cellwidth + 1),
                                                        image=self.object_to_image(obj), tag=getattr(obj, '__name__', obj.__class__.__name__))

            if hasattr(obj, 'id_image') and obj.id_image:
                if isinstance(obj.location, tuple):
                    old_loc = self.canvas.coords(obj.id_image)
                    self.canvas.move(obj.id_image, (obj.location[0] + ID_X_OFFSET) * (self.cellwidth + 1) - old_loc[0],
                                     (obj.location[1] + ID_Y_OFFSET) * (self.cellwidth + 1) - old_loc[1])
                else:
                    self.canvas.itemconfig(obj.id_image, state='hidden')
            else:
                obj.id_image = self.canvas.create_text((obj.location[0] + ID_X_OFFSET) * (self.cellwidth + 1),
                                                     (obj.location[1] + ID_Y_OFFSET) * (self.cellwidth + 1),
                                                     text=obj.id, anchor='nw', tag=getattr(obj, '__name__', obj.__class__.__name__))

        self.canvas.tag_lower('Dirt')
#______________________________________________________________________________
