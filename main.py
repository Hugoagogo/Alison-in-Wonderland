import pyglet, yaml, util, math
from pyglet import gl
from pyglet.window import key
import os

ROOM_X = 60
ROOM_Y = 45

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
    for lineno in range(ROOM_Y):
        line = room_file.readline().strip("\n")
        for colno in range(ROOM_X):
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
                for x in range(util.clip_to_range(bx-l,0,room.x),util.clip_to_range(bx+l,0,room.y)):
                    for y in range(util.clip_to_range(by-l,0,room.y),util.clip_to_range(bx+l,0,room.y)):
                        if True or bx!=x or by!=y:
                            if check_ray(bx,by,x,y,room):
                                try:
                                    room[x,y].base_light += int(round((l/(((bx-x)**2+(by-y)**2)**0.5))))
                                except:
                                    pass
                        
    for bx in range(room.x):
        for by in range(room.y):
            room[bx,by].base_light = util.clip_to_range(room[bx,by].base_light,0,255)
    pass
                
def check_ray(x1,y1,x2,y2,room):
    if x1 != x2:
        m = float(y1-y2)/(x1-x2)
        lsy1 = None
        lsy2 = None
        for sx in range(x1,x2,math.copysign(1,x2-x1)):
            sy1 = int(math.ceil(m*(sx-x1) + y1))
            sy2 = int(math.floor(m*(sx-x1) + y1))
            if lsy1 == None and lsy2 == None:
                lsy1, lsy2 = sy1, sy2
            for dy1, dy2 in zip(range(sy1,lsy1,math.copysign(1,lsy1-sy1)),range(sy2,lsy2,math.copysign(1,lsy2-sy2))):
                if room[sx,dy1].material != None and room[sx,dy1].material.solid and room[sx,dy2].material != None and room[sx,dy2].material.solid and sx != x1:
                    return False
                
            
    else:
        for sy in range(y1,y2,math.copysign(1,y2-y1)):
            if room[x1,sy].material != None and room[x1,sy].material.solid and sy!= y1:
                return False
    return True

class MainWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        kwargs['width'] = 960
        kwargs['height'] = 720
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.set_exclusive_keyboard(False)
        pyglet.clock.schedule_interval(lambda _: None, 0)
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
    
    #def __getattr__(self,key):
    #    if key.beginswith("on_") and len(self.states) and hasattr(self.states[-1],key):
    #        return self.states[-1].key
    #    else:
    #        return pyglet.window.Window.__getattr__(key)
            
class State(object):
    def activate(self):
        pass
    def deactivate(self):
        pass
            
class GameState(State):
    def __init__(self):
        materials = load_materials("materials.yaml")
        self.room = construct_room("level.lvl",materials)
        update_lightmap(self.room)
        
    def on_draw(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        for x in range(ROOM_X):
            for y in range(ROOM_Y):
                square = self.room[x,y]
                if square.material and square.material.texture != None:
                    gl.glColor4ub(*square.material.colour+[square.base_light])
                    square.material.texture.blit(x*16,y*16)
        
            

class Material(object):
    def __init__(self,name,visible=True,solid=False,colour=None,opacity=255,texture=None,light=0,layer=-1):
        self.visible=visible
        self.solid = solid
        self.colour = colour
        self.opacity = opacity
        self.light = light
        if texture:
            self.texture = pyglet.image.load(os.path.abspath(os.path.join("res","tiles",texture+".png"))).get_texture()
        else:
            self.texture = None
        
class Block(object):
    def __init__(self, material=None):
        self.material = material
        self.base_light = 0
        self.dyn_light = 0

window = MainWindow()
window.push_state(GameState())
pyglet.app.run()