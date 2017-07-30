from game import *

m = GameMap (4)
m.load_map('mymap.txt')
print (delta_compress( {"A":2, "B":3, "C":6}, {"A":0, "C":6} ))
