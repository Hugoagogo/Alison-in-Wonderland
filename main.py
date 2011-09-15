import pyglet, yaml, util, math
from pyglet import gl
import os

#import profile

from key_bindings import *

SCREEN_X = 960
SCREEN_Y = 720

ROOM_X = 60
ROOM_Y = 45

X_FRICTION = .7
ACCEL = 3
JUMP = 10
GRAVITY = 3
X_MAX_SPEED = 8
Y_MAX_SPEED = 15
JUMP_TIME = 8

range = xrange

EDGES = []
EDGES.extend([(x,0) for x in range(0,ROOM_X)])
EDGES.extend([(x,ROOM_Y-1) for x in range(0,ROOM_X)])
EDGES.extend([(0,y) for y in range(0,ROOM_Y)])
EDGES.extend([(ROOM_X-1,y) for y in range(0,ROOM_Y)])

def load_materials(material_filename):
    f = open(material_filename)
    raw_materials = yaml.load(f.read())
    f.close()
    materials = {}
    for key, mat in raw_materials.items():
        materials[key] = Material(**mat)
        print "Loaded Material:",key
    return materials

def update_lightmap(room):
    for x in range(ROOM_X):
        for y in range(ROOM_Y):
            room[x,y].base_light = 0
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
            
def update_lightmap2(room):
    squares = []
    squares.extend([(x,0) for x in range(0,room.x)])
    squares.extend([(x,room.y-1) for x in range(0,room.x)])
    squares.extend([(0,y) for y in range(0,room.y)])
    squares.extend([(room.x-1,y) for y in range(0,room.y)])
    for bx in range(room.x):
        for by in range(room.y):
            block = room[bx,by]
            if block.material != None and block.material.light:
                l = block.material.light
                block.base_light+=l
                temp = set()
                for x, y in squares:
                    if not (bx == x and by == y):
                        temp |= check_ray2(bx,by,x,y,room)

                for x, y in temp:
                    room[x,y].base_light += int(round((l/(((bx-x)**2+(by-y)**2)**block.material.light_dropoff))))
                        
          
    for bx in range(room.x):
        for by in range(room.y):
            room[bx,by].base_light = util.clip_to_range(room[bx,by].base_light,0,255)
                
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

def check_ray2(x1,y1,x2,y2,room):
    iy = y1
    lit = set()
    dx = x2-x1
    dy = y2-y1
    if x1 == x2:
        y_step_dir = int(math.copysign(1,dy))
        while y1 != y2:
            y1 += y_step_dir
            lit.add((x1,y1))
            if room[x1,y1].material != None and room[x1,y1].material.transparent == 0 and y1 != y2:
                return lit
    else:
        m = abs((dy)/float(dx))
        x_step_dir = int(math.copysign(1,dx))
        y_step_dir = int(math.copysign(1,dy))
        count = m
        while y1 != y2 or x1 != x2:
            if count > 1:
                count -= 1
                y1 += y_step_dir
            else:
                count += m
                x1 += x_step_dir
            lit.add((x1,y1))
            if room[x1,y1].material != None and room[x1,y1].material.transparent == 0 and (y1 != y2 or iy == y1) and x1 != x2:
                return lit
                
    return lit

class Room(util.Array2D):
    def __init__(self, room_filename, materials):
        super(Room, self).__init__(ROOM_X, ROOM_Y)
        room_file = open(room_filename,"rb")
        self.name = room_file.readline().strip()
        self.specials = []
        print "LOADED ROOM: ",self.name
        for lineno in range(ROOM_Y):
            line = room_file.readline().strip("\n")
            for colno in range(ROOM_X):
                mat = line[colno]
                if mat in materials:
                    mat = materials[mat]
                else: mat = None
                if mat and mat.special:
                    tile = SpecialBlock(mat,**mat.special)
                    self.specials.append((tile,colno,ROOM_Y-lineno-1))
                else:
                    tile = Block(mat)
                self[colno,lineno] = tile
        self.data.reverse()

class MainWindow(pyglet.window.Window):
    def __init__(self,*args, **kwargs):
        kwargs['width'] = SCREEN_X
        kwargs['height'] = SCREEN_Y
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
    def __init__(self,parent,x=0,y=0):
        frames = []
        path = os.path.join("res","alison","walk")
        for file in sorted(os.listdir(path)):
            file = os.path.join(path,file)
            if os.path.isfile(file):
                frames.append(pyglet.image.AnimationFrame(pyglet.image.load(os.path.abspath(file)),0.1))
                frames[-1].image.anchor_x = frames[-1].image.width/2
        
        self.eye_right = pyglet.image.load(os.path.abspath(os.path.join("res","alison","eye.png")))
        self.eye_left = pyglet.image.load(os.path.abspath(os.path.join("res","alison","eye2.png")))
        self.eye_right.anchor_x = self.eye_right.width/2
        self.eye_left.anchor_x = self.eye_left.width/2
        self.eye = pyglet.sprite.Sprite(self.eye_left)
        
        self.image_right = pyglet.image.Animation(frames)
        self.image_left = self.image_right.get_transform(flip_x=True)
        self.sprite = pyglet.sprite.Sprite(self.image_left,x,y)
        self.sprite.set_position(x,y)
        
        self.parent = parent
        
        self.vx = self.vy = self.cooldown_jump = self.glow = self.jumping = 0
        self.dir = 1
    
    def _up(self):
        return self.sprite.y + self.sprite.height
    up = property(_up)
    def _down(self):
        return self.sprite.y
    down = property(_down)
    def _left(self):
        return self.sprite.x - self.sprite.width/2
    left = property(_left)
    def _right(self):
        return self.sprite.x + self.sprite.width/2
    right = property(_right)
    
    def glow_on(self):
        self.parent.lights[id(self)] = DynLight(100,0.45)
        self.glow = True
    def glow_off(self):
        del self.parent.lights[id(self)]
        self.glow = False
    #
    #def block_below(self):
    #    left, right = int(self.left/16), int(self.right/16)
    #    for y in range(math.floor(self.down/16),0,-1):
    #        if (self.parent.room[left,y].material and self.parent.room[left,y].material.solid) or (self.parent.room[right,y].material and self.parent.room[right,y].material.solid):
    #            return y+2
    #    return None
    
    def update(self,dt):
        if not self.cooldown_jump and self.parent.keys[PLAYER_JUMP]:
            self.cooldown_jump = 1
            self.jumping = JUMP_TIME
        
        if self.jumping:
            if self.parent.keys[PLAYER_JUMP]:
                self.vy += ACCEL*2
                self.jumping -= 1
            else:
                self.jumping = 0
                
            
        #    self.vy += ACCEL
        #elif self.parent.keys[PLAYER_DOWN]:
        #    self.vy -= ACCEL
        #else:
        self.vy -= GRAVITY
        if self.parent.keys[PLAYER_LEFT]:
            if self.dir != 1:
                self.dir = 1
                self.sprite.image = self.image_left
                self.eye.image = self.eye_left
            self.vx -= ACCEL
        elif self.parent.keys[PLAYER_RIGHT]:
            if self.dir != 0:
                self.dir = 0
                self.sprite.image = self.image_right
                self.eye.image = self.eye_right
            self.vx += ACCEL
        else:
            self.vx *= X_FRICTION
        
        self.vx = util.clip_to_range(self.vx,-X_MAX_SPEED,X_MAX_SPEED)
        self.vy = util.clip_to_range(self.vy,-Y_MAX_SPEED,Y_MAX_SPEED)
        
        self.sprite.x += self.vx
        self.sprite.y += self.vy
        
        ## Check Collisions Here
        for x in range(self.parent.room.x):
            ax = x * 16
            for y in range(self.parent.room.y):
                ay = y * 16
                block = self.parent.room[x,y]
                if block.material and block.material.solid:
                    if self.vy < 0 and ay <= self.down < ay + 16 and (ax <= self.left < ax + 12 or ax+4 <= self.right < ax + 16):
                        self.sprite.y = y*16 + 16
                        self.vy = 0
                        self.cooldown_jump = 0
                        #print "hity DO", self.vx
                    elif self.vy > 0 - 2 and ay <= self.up < ay + 16 and (ax <= self.left < ax + 12 or ax+4 <= self.right < ax + 16):
                        self.sprite.y = y*16 - self.sprite.height -2
                        self.vy = 0
                        self.jumping = 0
                        #print "hity UP"
                    if self.vx < 0 and ax <= self.left < ax + 16 and (ay <= self.down < ay + 13 or ay<= self.up < ay + 16):
                        self.sprite.x = x*16 + 15 + self.sprite.width/2
                        self.vx = 0
                        #print "hitx"
                    elif self.vx > 0 and ax <= self.right < ax + 16 and (ay <= self.down < ay + 13 or ay<= self.up < ay + 16):
                        self.sprite.x = x*16 - self.sprite.width/2 -1
                        self.vx = 0
                        #print "hitx"
        
        self.eye.set_position(self.sprite.x, self.sprite.y)
        
        if self.glow:
            self.parent.lights[id(self)].x = int(self.sprite.x/16)
            self.parent.lights[id(self)].y = int(self.sprite.y/16)
        refresh = False
        for item, x, y in self.parent.room.specials:
            dx = x*16
            dy = y*16
            if (dx < self.left < dx+item.material.texture.width or dx < self.right < dx+item.material.texture.width) and (dy <= self.down <= dy+item.material.texture.height or dy < self.up < dy+item.material.texture.height):
                remove = item.destruct
                if not item.needs_activation or self.parent.keys[PLAYER_ACTIVATE]:
                    if item.type == "vial":
                        if item.type_detail == "glow":
                            self.glow_on()
                    print "Activated: ", item.material.name
                    if remove:
                        refresh = True
                        self.parent.room[x,y] = Block(None)
                        self.parent.room.specials.remove((item, x, y))
                        print x,y
                    
        if refresh:
            update_lightmap(self.parent.room)
            self.parent.update_tilebuffer(True)
            self.parent.update_lightbatch()
                    
                
            
        
        #print ay
    
    def draw(self):
        self.sprite.draw()
        
    def draw_eye(self):
        self.eye.draw()
        

class State(object):
    def activate(self):
        pass
    def deactivate(self):
        pass
            
class GameState(State):
    def __init__(self):
        materials = load_materials("materials.yaml")
        self.room = Room("level.lvl",materials)
        self.bg = pyglet.image.load(os.path.abspath(os.path.join("res","backgrounds","above1.png"))).get_texture()
        update_lightmap(self.room)
        self.lights = {}
        
        self.keys = key.KeyStateHandler()
        
        self.player = Alison(self,250,600)
        
        self.update_tilebuffer()
        self.update_lightbatch()
        
    def activate(self):
        self.parent.push_handlers(self.keys)
        pyglet.clock.schedule_interval(self.do_lights, 1/60.0)
        ##pyglet.clock.schedule_interval(lambda _:exit(), 20)
    def deactivate(self):
        self.parent.pop_handlers()
        
        
    def update(self,dt):
        self.player.update(dt)
    
    def do_lights(self,dt):
        if pyglet.clock.get_fps() > 45:
            self.dynamic_light(self.lights.values())
            self.update_lightbatch()
        
        
    def on_draw(self):
        self.parent.set_caption(str(pyglet.clock.get_fps()))
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glColor4ub(*[255,255,255,255])
        self.bg.blit(0,0)

        self.tilebuffer.blit(0,0)
        
        gl.glColor4ub(*[255,255,255,255])
        self.player.draw()
        self.lightbatch.draw()
        self.player.draw_eye()
        
        #gl.glBegin(gl.GL_LINES)
        #gl.glVertex2i(int(self.player.left),720)
        #gl.glVertex2i(int(self.player.left),0)
        #gl.glVertex2i(int(self.player.right),720)
        #gl.glVertex2i(int(self.player.right),0)
        #gl.glVertex2i(960,int(self.player.up))
        #gl.glVertex2i(0,int(self.player.up))
        #gl.glVertex2i(960,int(self.player.down))
        #gl.glVertex2i(0,int(self.player.down))
        #gl.glEnd()
        
    
    def update_tilebuffer(self,odd=False):
        self.tilebuffer = pyglet.image.Texture.create(SCREEN_X,SCREEN_Y)
        for x in range(ROOM_X):
            for y in range(ROOM_Y):
                square = self.room[x,y]
                if square.material and square.material.visible and square.material.texture != None:
                    #gl.glColor3ub(*square.material.colour)
                    if odd and type(square) != Block:
                        print square
                        print x, y
                    self.tilebuffer.blit_into(square.material.texture,x*16,y*16,0)
                    
    def dynamic_light(self,lights):
        if lights:
            for x in range(ROOM_X):
                for y in range(ROOM_Y):
                    self.room[x,y].dyn_light = 0
            
            for light in lights:
                block = self.room[light.x,light.y]
                block.dyn_light+=light.light
                temp = set()
                for x, y in EDGES:
                    if not (light.x == x and light.y == y):
                        temp |= check_ray2(light.x,light.y,x,y,self.room)
                for x, y in temp:
                    self.room[x,y].dyn_light += int(round((light.light/(((light.x-x)**2+(light.y-y)**2)**light.dropoff))))
                        
            for x in range(ROOM_X):
                for y in range(ROOM_Y):
                    self.room[x,y].dyn_light = util.clip_to_range(self.room[x,y].dyn_light+self.room[x,y].base_light,0,255)-self.room[x,y].base_light
                    
    def update_lightbatch(self):
        self.lightbatch = pyglet.graphics.Batch()
        colours = []
        vertexes = []
        for x in range(ROOM_X):
            for y in range(ROOM_Y):
                colours.extend([0,0,0,255-self.room[x,y].dyn_light-self.room[x,y].base_light]*4)
                vertexes.extend([x*16,y*16,  x*16+16,y*16,  x*16+16,y*16+16,  x*16,y*16+16])
                
                #gl.glColor4ub(*[0,0,0,255-self.room[x,y].base_light])
                #gl.glRecti(x*16,y*16,x*16+16,y*16+16)
        self.lightbatch.add(4*ROOM_X*ROOM_Y, gl.GL_QUADS, None,
                                                              ('c4B',tuple(colours)),
                                                              ('v2f',tuple(vertexes)))
        

class Material(object):
    def __init__(self,name,visible=True,solid=False,colour=None,texture=None,transparent=False,special=None,light_ambient=0,light=0,light_dropoff=0.5,layer=-1):
        self.name = name
        self.visible=visible
        self.solid = solid
        self.colour = colour
        self.light = light
        self.light_dropoff = light_dropoff
        self.light_ambient = light_ambient
        self.transparent = transparent
        self.special = special
        if texture:
            self.texture = pyglet.image.load(os.path.abspath(os.path.join("res","tiles",texture+".png")))
        else:
            self.texture = None
        
class Block(object):
    def __init__(self, material=None):
        self.material = material
        self.base_light = 0
        if self.material != None:
            self.base_light += material.light_ambient
        self.dyn_light = 0
        
class SpecialBlock(Block):
    def __init__(self, material, type = "", description = "", type_detail = "", destruct = 0,needs_activation=False ):
        super(SpecialBlock,self).__init__(material)
        self.type= type
        self.type_detail = type_detail
        self.description = description
        self.destruct = destruct
        self.needs_activation = needs_activation
    
class DynLight(object):
    def __init__(self,light,dropoff):
        self.light = light
        self.dropoff = dropoff
        self.x = 0
        self.y = 0
        self.cooldown = 0
        

window = MainWindow()
window.push_state(GameState())
pyglet.app.run()