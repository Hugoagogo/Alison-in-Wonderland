import pyglet, yaml
from pyglet import gl
from pyglet.window import key

def load_materials(material_filename):
    raw_materials = yaml.load(material_filename)
    materials = {}
    for key, mat in materials.items():
        materials[key] = Material(**materials)
    return materials

def construct_room(room_filename,materials):
    room_file = open(room_filename,"rb")
    name = room_file.readline().strip()
    print name
    room = Array2D(60,45)
    for lineno in range(45):
        line = room_file.readline().strip("\n")
        for colno in range(60):
            tile = Block(line[colno])
            room[colno,lineno] = tile

class Block(object):
    def __init__(self, material=None):
        self.material = material
        self.base_light = 0
        self.dyn_light = 0
        
class Material(object):
    def __init__(self,visisble=True,solid=False,colour=None,opacity=255,texture=None,layer=-1):
        self.visible=visible
        self.solid = solid
        self.colour = colour
        self.opacity = opacity
        self.texture = texture
    
class Array2D(object):
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.data = [[None]*x for py in range(y)]
    def __getitem__(self,key):
        x,y = key
        return self.data[y][x]
        
    def __setitem__(self,key,value):
        x,y = key
        self.data[y][x] = value

#materials = load_materials("materials.yaml")
#construct_room("level.lvl",materials)
