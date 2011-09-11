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
        
def clip_to_range(val,min,max):
    if val < min:
        return min
    elif val > max:
        return max
    return val