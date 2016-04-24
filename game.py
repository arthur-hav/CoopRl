from math import *
import json
import threading

CO = cos(pi/6)
CORAD = 2*CO/3 
STEPS = ((0, -1), (1, -0.5), (1, 0.5), (0, 1), (-1, 0.5), (-1, -0.5))
CLIENT_COLS = [5,8,11,12,13,14,15,14,15,14,15,14,13,12,11,8,5]

def dist(xy0, xy1):
    return sqrt((xy1[0]-xy0[0])**2*CO**2 + (xy1[1]-xy0[1])**2)

def get_closest (xy):
    steps = []
    x = round(xy[0])
    y = round(xy[1]) if x % 2 == 0 else round(xy[1]) + 0.5
    cell = (x,y)
    for s in STEPS:
        if dist(step_add(cell, s), xy) < CORAD + 0.01:
            steps.append(step_add(cell, s))
    if dist(cell, xy) < CORAD + 0.01:
        steps.append(cell)
    return steps

def step_add (xy, step):
    return (xy[0] + step[0], xy[1] + step[1])

def delta_compress (state, prev_state):
    if state == prev_state:
        return None
    try:
        acc = {}
        for k in state.keys():
            d = delta_compress(state[k], prev_state[k]) if k in prev_state else state[k]
            if d != None:
                acc[k] = d
        return acc
    except AttributeError:
        return state 

class GameMap ():
    def __init__ (self, map_radius):
        self.walls = {}
        self.creatures = {}
        self.items = {}
        self.map_radius = map_radius
    def get (self,xy):
        if dist((0,0), xy) > self.map_radius + 0.4:
            return '#'
        if xy in self.walls:
            return self.walls[xy]
        return ' '

    def los (self, xy0, xy1):
        d = dist(xy0, xy1)
        if d == 0 :
            return True
        direction = ((xy1[0]-xy0[0])/d*CO,(xy1[1]-xy0[1])/d*CO) 
        path_found = True
        paths = []
        while path_found :
            xy0 = step_add (xy0, direction)
            path_found = False
            paths.append(get_closest(xy0))
            for cell in get_closest (xy0):
                if cell == xy1:
                    return True
                if self.get(cell) != '#':
                    path_found = True
                    break
        return False

    def display (self, pc, radius):
        display = [] 
        for x in range(-int(radius/CO), int(radius/CO)+1):
            column = ""
            for y in range(-radius, radius+1):
                cell = step_add(pc.xy, (x,y)) if x%2==0 else step_add(pc.xy,(x,y+0.5))
                if dist(cell, pc.xy) > radius + 0.4:
                    continue
                if not self.los(pc.xy, cell):
                    val = '_'    
                elif cell in self.items:
                    val = self.items[cell][0]
                else:
                    val = self.get(cell)
                column += val
            display.append(column)
        return display

    def get_visible_creatures (self, center, radius):
        visible_creatures = []
        for x in range(-int(radius/CO), int(radius/CO)+1):
            for y in range(-radius, radius+1):
                cell = step_add(center, (x,y+.5 if x%2 else y))
                if dist(center, cell) < radius + 0.4 and cell in self.creatures and self.los(center, cell): 
                    visible_creatures.append(self.creatures[cell])
        return visible_creatures


    def load_map (self, path):
        with open(path) as stream:
            jsyms = json.loads(stream.read())
            for k,v in jsyms.items():
                self.walls.update ({(val[0],val[1]):k for val in v})
    def push_item (self, xy, item):
        if xy in self.items:
            self.items[xy].append(item)
        else:
            self.items[xy] = [item]

class Creature ():
    def __init__ (self, creature_id, xy, health, armor, mr, ad):
        self.creature_id = creature_id
        self.xy = xy
        self.max_health = health
        self.health = health
        self.mana = 100
        self.armor = armor
        self.mr = mr
        self.ad = ad
        self.short_steps = []
        self.ap = 0
        self.status = {}
        self.pending = None
        self.last_action = None
        self.attack_range = 1
        self.is_pc = False

    def act (self, action, args):
        """Humans and AI must use this function to submit their orders 
        to the creature they control"""
        if self.health <= 0:
            return False
        ap_cost = self.get_cost(action, args)
        if self.ap < ap_cost:
            self.pending = (action, args)
        elif action (*args):
            self.ap -= ap_cost
            self.pending = None
            self.last_action = (action, args)
            return True
        return False

    def get_cost (self, action, args):
        if action == self.try_move:
            if STEPS.index(args[0]) in self.short_steps:
                return 3
        return 4

    def try_move (self, step, game_map):
        nextxy = step_add(self.xy, step)
        if game_map.get(nextxy) == '#':
            return False
        if nextxy in game_map.creatures:
            return False
        del game_map.creatures[self.xy]
        game_map.creatures[nextxy] = self
        self.xy = nextxy
        i = STEPS.index(step)
        if i in self.short_steps:
            self.short_steps = []
        else:
            self.short_steps = [ (i+1)%6, (i-1)%6 ]
        return True

    def take_damage (self, phys, magic, truedmg):
        self.health -= phys * 1/(1 + self.armor/10)
        self.health -= magic * 1/(1 + self.mr/10)
        self.health -= truedmg

    def try_attack (self, targetxy, game_map):
        if dist(targetxy, self.xy) > self.attack_range + 0.01: 
            return False
        if targetxy not in game_map.creatures:
            return False
        target = game_map.creatures[targetxy]
        if target.is_pc == self.is_pc:
            return False
        game_map.creatures[targetxy].take_damage (self.ad, 0, 0)
        if not target.is_pc:
            target.act(target.try_attack, (self.xy, game_map))
        return True
    def infos (self, center):
        return {"id":self.creature_id,
                "is_pc":self.is_pc,
                "x": self.xy[0]-center[0] + 8,
                "y": int(self.xy[1]-center[1] + CLIENT_COLS[self.xy[0]-center[0]+8]/2),
                "max_health":self.max_health,
                "health": self.health,
                "mana":self.mana,
                "armor":self.armor,
                "mr":self.mr,
                "ad":self.ad,
                "short_steps":self.short_steps,
                "ap":self.ap,
                "chr":self.__str__(),
                "status":self.status
                }

class Mob (Creature):
    def ai_find_pc (self, game_map):
        creatures = game_map.get_visible_creatures(self.xy, 7)
        for c in creatures :
            if c.is_pc :
                return c.xy

    def __str__ (self):
        return "z"
    def ai_play (self, game_map):
        pcxy = self.ai_find_pc (game_map)
        if not pcxy:
            return
        if self.act (self.try_attack, (pcxy, game_map)):
            return
        for step in sorted(STEPS, key=lambda a: dist(step_add(self.xy, a), pcxy)):
            if self.act (self.try_move, (step, game_map)):
                return

class PC (Creature):
    def __init__ (self, player_id, client, player_class = None):
        super().__init__(player_id, (0, player_id), 100, 0, 0, 20)
        self.is_pc = True
        self.client = client
        self.creatures_infos = {} 
        self.prev_message = {}
    def send_state(self, game_map):
        message = { "creatures": { cr.creature_id:cr.infos(self.xy) for cr in game_map.get_visible_creatures(self.xy, 7) },
                    "board": game_map.display(self,7)}
        deltam = delta_compress(message, self.prev_message)
        if deltam:
            self.client.write_message(json.dumps(deltam)) 
        self.prev_message = message
    def __str__ (self):
        return "@"
            
class Room ():
    def __init__ (self, clients):
        self.game = Game()
        self.players = [PC(i,clients[i]) for i in range(len(clients))]
        for pc in self.players:
            pc.client.on_message = lambda m: self.keypress(pc, m)
            self.game.game_map.creatures[(0,pc.creature_id)] = pc
            pc.send_state(self.game.game_map)
        self.timer = threading.Timer (0, self.srv_tick)
        self.timer.start()
        
    def keypress (self, pc, message):
        try:
            m = json.loads(message)
            if "step" in m:
                step = STEPS[int(m["step"])]
                if not pc.act (pc.try_attack, (step_add(pc.xy, step), self.game.game_map)):
                    pc.act (pc.try_move, (step, self.game.game_map))
                pc.send_state (self.game.game_map )
            if "attack" in m:
                addx = int(m["attack"]["x"]) - 8
                addy = int(m["attack"]["y"]) - int(CLIENT_COLS[int(m["attack"]["x"])]/2)
                if addx % 2:
                    addy += .5
                pc.act (pc.try_attack, (step_add(pc.xy, (addx, addy)), self.game.game_map))
        except Exception as e:
            pass
    def srv_tick (self):
        if self.timer:
            self.timer.cancel()
        if self.players:
            self.timer = threading.Timer (.25, self.srv_tick)
            self.timer.start()
        self.game.next_turn()
        for pc in self.players:
            pc.send_state (self.game.game_map)

class Game ():
    def __init__ (self):
        self.game_map = GameMap (6)
        self.game_map.load_map('mymap.txt')
        self.turn = 0
        self.game_map.creatures[(0,4)] = Mob (1, (0,4), 100, 0, 0, 2)

    def next_turn (self): 
        self.turn += 1
        for xy,cr in self.game_map.creatures.items():
            if cr.health <= 0:
                self.game_map.push_item(xy,'%') 
        self.game_map.creatures = { xy:cr for xy,cr in self.game_map.creatures.items() if cr.health > 0 }
        for creature in self.game_map.creatures.values():
            creature.ap += 1
            creature.mana = min(creature.mana + 1,100)
            creature.status = { st:turn for st,turn in creature.status.items()
                if creature.status[st] >= self.turn }
            if creature.pending:
                creature.act(*creature.pending)
            if creature.ap > 12:
                try :
                    creature.ai_play(self.game_map)
                except AttributeError as e:
                    pass
                creature.ap = min(creature.ap, 12)
        #if not self.game_over_state :

