import random

from game import dist

MAP = []

for i in range(67):
    MAP.append([])
    for j in range(127):
        MAP[i].append('#')

def carve(i, j, c=' '):
    if MAP[i+33][j+63] != '#':
        return
    MAP[i+33][j+63] = c

def gen_map(resmap=None, radius_x=33, radius_y=63, center=(0,0), connections=[], room_density=0.5):
    if not resmap:
        resmap = {}
    if radius_x > radius_y:
        if radius_x > 6:
            #print (center[0], radius_x)
            #print(center, MAP[center[0] + 15][center[1] + 25])
            right = center[0] + (radius_x) / 2, center[1]
            left = center[0] - (radius_x + 1) / 2, center[1]
            
            conns_l = [center]
            conns_r = [center]
            if connections and random.random() < 1:
                conns_l.append(connections[0])
                conns_r.append(connections[0])
            #if random.random() < 0.0:
            #    randx = center[0] + random.randint(-radius_x + 1, radius_x + 1)
            #    randy = center[1] + random.randint(-radius_y + 1, radius_y + 1)
            #    conns.append((randx, randy))
            left = gen_map(resmap, (radius_x)/2, radius_y, left, conns_l, room_density)
            right = gen_map(resmap, (radius_x + 1)/2, radius_y, right, conns_r, room_density)
            center = left[0] + (radius_x) / 2, left[1]

            #center = center[0] x % 2, center[1]

    else:
        if radius_y > 6:
            #print (center[1], radius_y)
            #print(center, MAP[center[0] + 15][center[1] + 25])
            bot = center[0], center[1] + (radius_y + 1) / 2
            top = center[0], center[1] - (radius_y) / 2
            conns_l = [center]
            conns_r = [center]
            if connections and random.random() < 1:
                conns_l.append(connections[0])
                conns_r.append(connections[0])
            bot = gen_map(resmap, radius_x, (radius_y)/2, bot, conns_l, room_density)
            top = gen_map(resmap, radius_x, (radius_y + 1)/2, top, conns_r, room_density)

            center = top[0], top[1] + (radius_y + 1)/2

    carve(*center, c=' ')
    if radius_x <= 6 and radius_y <= 6 and random.random() < room_density:
        gen_room(center, radius_x-1, radius_y-1)
        for connection in connections:
            for i in range(min(center[0], connection[0]), max(center[0], connection[0])):
                carve(i, center[1], ' ')
            for j in range(min(center[1], connection[1]), max(center[1], connection[1])):
                carve(center[0], j, ' ')
    else:
        for connection in connections:
            for i in range(min(center[0], connection[0]), max(center[0], connection[0])):
                carve(i, center[1], ' ')
            for j in range(min(center[1], connection[1]), max(center[1], connection[1])):
                carve(center[0], j, ' ')
    return center
        #carve(center[0] - radius_x + 1,center[1] - radius_y + 1,c='/')
        #carve(center[0] + radius_x - 1, center[1] + radius_y - 1,c='/')

        #carve(center[0] + radius_x - 1,center[1] - radius_y + 1,c='\\')
        #carve(center[0] - radius_x + 1, center[1] + radius_y - 1,c='\\')
                #pass
        #carve(*center,c='o')
        #p = gen_room(center[0], center[1], min(radius_x, radius_y))
        #for c in p:
        #    carve(*c, c='=')

    #for i in range (-map_diameter/2, map_diameter/2, room_diameter_x + 1):
    #    for j in range (-map_diameter/2, map_diameter/2, room_diameter_y + 1):
    #        connectors = []
    #        if random.random() < room_density:
    #            connectors = gen_room(i, j)
            #else:
            #    connectors = gen_corridors(i, j)
    #        for c in connectors:
    #            carve(*c, c='+')
    #            if c in all_connectors:
    #            else:
    #                all_connectors.add(c)


def gen_room(center, radius_x, radius_y):
    for i in range(center[0] - radius_x + 1, center[0] + radius_x):
        for j in range(center[1] - radius_y + 1, center[1] + radius_y):
            carve(i, j, 'r')

def gen_corridors(x, y, diameter=5):
    return gen_room(x, y, diameter)


gen_map()
for l in MAP:
    print ''.join(l)

#1 - Place rooms. This can be done using map presets.

#2 - Carve a maze with remaining walls. A maze is basically a DFS but with random son ordering. -> a bias can be ordered to favor straight halls.

#3 - Iterate through rooms and open 1 to 2 doors for each to the generated maze.



