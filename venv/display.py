
import Tkinter as tk

from utils import *

#______________________________________________________________________________

def DisplayObject(obj):
    obj.image = None
    obj.image_source = ''
    return obj

class EnvFrame(tk.Frame):
    def __init__(self, env, title='AIMA GUI', cellwidth=50, n=10):
        update(self, cellwidth=cellwidth, running=False, delay=1.0)
        self.n = n
        self.running = 0
        self.delay = 1.0
        self.env = env
        self.cellwidth = cellwidth
        tk.Frame.__init__(self, None, width=(cellwidth + 2) * n, height=(cellwidth + 2) * n)
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
        self.canvas = tk.Canvas(self, width=(cellwidth + 1) * n,
                                height=(cellwidth + 1) * n, background="white")
        self.canvas.bind('<Button-1>', self.left)  ## What should this do?
        self.canvas.bind('<Button-2>', self.edit_objects)
        self.canvas.bind('<Button-3>', self.edit_objects)
        if cellwidth:
            c = self.canvas
            for i in range(1, n + 1):
                c.create_line(0, i * cellwidth, n * cellwidth, i * cellwidth)
                c.create_line(i * cellwidth, 0, i * cellwidth, n * cellwidth)
                c.pack(expand=1, fill='both')
        self.pack()
        self.images = {'':None, 'robot-right':tk.PhotoImage(file='img/robot-right.gif'),
                       'robot-left':tk.PhotoImage(file='img/robot-left.gif'),
                       'robot-up':tk.PhotoImage(file='img/robot-up.gif'),
                       'robot-down':tk.PhotoImage(file='img/robot-down.gif'),
                       'dirt':tk.PhotoImage(file='img/dirt (40x19).gif')}
        # note up and down are switched, since (0,0) is in the upper left
        self.orientation = {(1,0): 'robot-right', (-1,0): 'robot-left', (0,-1): 'robot-up', (0,1): 'robot-down'}

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

    def configure_display(self):
        for obj in self.env.objects:
            obj = DisplayObject(obj)
        self.update_display()

    def update_display(self):
        for obj in self.env.objects:
            if hasattr(obj, 'image') and obj.image:
                if isinstance(obj.location, tuple):
                    if hasattr(obj, 'heading'):
                        self.canvas.itemconfig(obj.image, image=self.images[self.orientation[obj.heading]])
                    old_loc = self.canvas.coords(obj.image)
                    self.canvas.move(obj.image, (obj.location[0]+0.5)*self.cellwidth-old_loc[0], (obj.location[1]+0.5)*self.cellwidth-old_loc[1])
                else:
                    self.canvas.itemconfig(obj.image, state='hidden')
            else:
                obj.image = self.canvas.create_image((obj.location[0] + 0.5) * self.cellwidth,
                                                        (obj.location[1] + 0.5) * self.cellwidth,
                                                        image=self.images[obj.image_source])

#______________________________________________________________________________
