import pyglet, yaml, util, math
from pyglet import gl
import os

from key_bindings import *

ROOM_X = 60
ROOM_Y = 45

MOVE_SPEED = 100

def load_materials(material_filename):
    f = open(material_filename)
    raw_materials = yaml.load(f.read())
    f.close()
    materials = {}
    for key, mat in raw_materials.items():
        materials[key] = Material(**mat)
    return materials

def construct_room(room_filename,materials):
    room_file = open(room_filename,"rb")
    name = room_file.readline().strip()
    print name
    room = util.Array2D(60,45)
    for lineno in range(room.y):
        line = room_file.readline().strip("\n")
        for colno in range(room.x):
            mat = line[colno]
            if mat in materials:
                mat = materials[mat]
            else: mat = None
            tile = Block(mat)
            room[colno,lineno] = tile
    room.data.reverse()
    return room

def update_lightmap(room):
    for bx in range(room.x):
        for by in range(room.y):
            block = room[bx,by]
            if block.material != None and block.material.light:
                l = block.material.light
                block.base_light+=l
                for x in range(util.clip_to_range(bx-l,0,room.x),util.clip_to_range(bx+l,0,room.x)):
                    for y in range(util.clip_to_range(by-l,0,room.y),util.clip_to_range(by+l,0,room.y)):
                        if True or bx!=x or by!=y:
                            if check_ray(bx,by,x,y,room):
                                try:
                                    room[x,y].base_light += int(round((l/(((bx-x)**2+(by-y)**2)**block.material.light_dropoff))))
                                except ZeroDivisionError:
                                    pass
                        
    for bx in range(room.x):
        for by in range(room.y):
            room[bx,by].base_light = util.clip_to_range(room[bx,by].base_light,0,255)
    pass
                
def check_ray(x1,y1,x2,y2,room):
    #print "============================================================"
    iy = y1
    if x1 == x2:
        y_step_dir = int(math.copysign(1,y2-y1))
        while y1 != y2:
            y1 += y_step_dir
            if room[x1,y1].material != None and room[x1,y1].material.transparent == 0 and y1 != y2:
                return False
    else:
        m = abs((y1-y2)/float(x1-x2))
        x_step_dir = int(math.copysign(1,x2-x1))
        y_step_dir = int(math.copysign(1,y2-y1))
        count = m
        while y1 != y2 or x1 != x2:
            if count > 1:
                count -= 1
                y1 += y_step_dir
            else:
                count += m
                x1 += x_step_dir
            if room[x1,y1].material != None and room[x1,y1].material.transparent == 0 and (y1 != y2 or iy == y1) and x1 != x2:
                return False
    return True

class MainWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        kwargs['width'] = 960
        kwargs['height'] = 720
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.set_exclusive_keyboard(False)
        pyglet.clock.schedule_interval(self.update, 1/60.0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        
        self.states = []
    
    def push_state(self,state):
        state.parent = self
        if len(self.states):
            self.pop_handlers()
            self.states[-1].deactivate()
        self.states.append(state)
        self.states[-1].activate()
        self.push_handlers(self.states[-1])
    def pop_state(self,state=None):
        self.pop_handlers()
        self.states[-1].deactivate()
        self.states.pop(-1)
        if state != None:
            state.parent = self
            self.states.append(state)
        if len(self.states):
            self.push_handlers(self.states[-1])
            self.states[-1].activate()
        else:
            quit()
            
    def update(self,dt):
        if len(self.states) and hasattr(self.states[-1],"update"):
            self.states[-1].update(dt)
    
    #def __getattr__(self,key):
    #    if key.beginswith("on_") and len(self.states) and hasattr(self.states[-1],key):
    #        return self.states[-1].key
    #    else:
    #        return pyglet.window.Window.__getattr__(key)

class Alison(object):
    def __init__(self,keys,x=0,y=0):
        frames = []
        path = os.path.join("res","alison","fly")
        for file in sorted(os.listdir(path)):
            file = os.path.join(path,file)
            if os.path.isfile(file):
                frames.append(pyglet.image.AnimationFrame(pyglet.image.load(os.path.abspath(os.path.join(file))),0.05))
                frames[-1].image.anchor_x = frames[-1].image.width/2
        
        self.image_right = pyglet.image.Animation(frames)
        self.image_left = self.image_right.get_transform(flip_x=True)
        self.sprite = pyglet.sprite.Sprite(self.image_left,x,y)
        self.sprite.set_position(x,y)
        
        self.keys = keys
        
        self.vx = self.vy = self.dir = 0
        
                
    def update(self,dt):
        print "updating"
        print self.keys
        if self.keys[PLAYER_UP]:
            self.sprite.y += MOVE_SPEED*dt
        if self.keys[PLAYER_DOWN]:
            self.sprite.y -= MOVE_SPEED*dt
        if self.keys[PLAYER_LEFT]:
            if self.dir != 1:
                self.dir = 1
                self.sprite.image = self.image_left
            self.sprite.x -= MOVE_SPEED*dt
        if self.keys[PLAYER_RIGHT]:
            if self.dir != 0:
                self.dir = 0
                self.sprite.image = self.image_right
            self.sprite.x += MOVE_SPEED*dt
    
    def draw(self):
        self.sprite.draw()
        

class State(object):
    def activate(self):
        pass
    def deactivate(self):
        pass
            
class GameState(State):
    def __init__(self):
        materials = load_materials("materials.yaml")
        self.room = construct_room("level.lvl",materials)
        self.bg = pyglet.image.load(os.path.abspath(os.path.join("res","backgrounds","above1.png"))).get_texture()
        update_lightmap(self.room)
        
        self.keys = key.KeyStateHandler()
        
        self.player = Alison(self.keys,200,300)
        
    def activate(self):
        self.parent.push_handlers(self.keys)
    def deactivate(self):
        self.parent.pop_handlers()
        
        
    def update(self,dt):
        self.player.update(dt)
        
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor4ub(*[255,255,255,255])
        self.bg.blit(0,0)

        for x in range(ROOM_X):
            for y in range(ROOM_Y):
                square = self.room[x,y]
                if square.material and square.material.visible and square.material.texture != None:
                    gl.glColor3ub(*square.material.colour)
                    square.material.texture.blit(x*16,y*16)
        
        self.player.draw()        
        
        for x in range(ROOM_X):
            for y in range(ROOM_Y):
                gl.glColor4ub(*[0,0,0,255-self.room[x,y].base_light])
                gl.glRecti(x*16,y*16,x*16+16,y*16+16)
                
                    
                    
        
            

class Material(object):
    def __init__(self,name,visible=True,solid=False,colour=None,texture=None,transparent=False,light_ambient=0,light=0,light_dropoff=0.5,layer=-1):
        self.visible=visible
        self.solid = solid
        self.colour = colour
        self.light = light
        self.light_dropoff = light_dropoff
        self.light_ambient = light_ambient
        self.transparent = transparent
        if texture:
            self.texture = pyglet.image.load(os.path.abspath(os.path.join("res","tiles",texture+".png"))).get_texture()
        else:
            self.texture = None
        
class Block(object):
    def __init__(self, material=None):
        self.material = material
        self.base_light = 0
        if self.material != None:
            self.base_light += material.light_ambient
        self.dyn_light = 0

window = MainWindow()
window.push_state(GameState())
pyglet.app.run()