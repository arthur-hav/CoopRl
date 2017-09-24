import random

from game import dist

MAP = []

for i in range(52):
    MAP.append([])
    for j in range(52):
        MAP[i].append('#')

def carve(i, j, c=' '):
    MAP[i][j] = c

def gen_map(room_diameter_x=7, room_diameter_y=7, map_diameter=50, room_density=0.99):
    resmap = {}
    center = (0, 0)
    all_connectors = set()
    #overlapping_connectors = set()
    for i in range (-map_diameter/2, map_diameter/2, room_diameter_x + 1):
        for j in range (-map_diameter/2, map_diameter/2, room_diameter_y + 1):
            connectors = []
            if random.random() < room_density:
                connectors = gen_room(i, j)
            #else:
            #    connectors = gen_corridors(i, j)
            for c in connectors:
                carve(*c, c='+')
                if c in all_connectors:
                    carve(*c, c='+')
                else:
                    all_connectors.add(c)


def gen_room(x, y, diameter=7):
    res = []
    for i in range(x - diameter/2, x + (diameter+1)/2):
        for j in range(y - diameter/2 , y + (diameter+1)/2):
            if i == x + (diameter-1)/2 or i == x - diameter/2 or j == y-diameter/2 or j == y + (diameter-1)/2:
                res.append((i, j))
            else:
                carve(i, j)
    carve(x, y, 'o')
    return res

def gen_corridors(x, y, diameter=5):
    return gen_room(x, y, diameter)


gen_map()
for l in MAP:
    print ''.join(l)

#1 - Place rooms. This can be done using map presets.

#2 - Carve a maze with remaining walls. A maze is basically a DFS but with random son ordering. -> a bias can be ordered to favor straight halls.

#3 - Iterate through rooms and open 1 to 2 doors for each to the generated maze.



