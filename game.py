from math import *
import json
import threading
import defs

CO = cos(pi/6)
CORAD = 2*CO/3 
STEPS = ((0, -1), (1, -0.5), (1, 0.5), (0, 1), (-1, 0.5), (-1, -0.5))
DIAGONAL_STEPS = ((1, -1.5), (2, 0), (1, 1.5), (-1, 1.5), (-2, 0), (-1, -1.5))
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

class ActionFailure(Exception):
    pass

class CreatureAction():
    def __init__(self, action, cost, **kwargs):
        self.action = action
        self.cost = cost
        self.__dict__.update (kwargs)
    def __call__(self, target):
        try:
            self.action(target)
        except ActionFailure:
            return 0
        return cost

class GameMap ():
    def __init__ (self):
        self.walls = {}
        self.features = {(0,13):Shop((0,13))}
        self.creatures = {}
        self.map_radius = 15 
    def get (self,xy):
        if abs(xy[0]) > self.map_radius or abs(xy[1]) > self.map_radius:
            return '_'
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
                else:
                    val = self.get(cell)
                column += val
            display.append(column)
        return display


    def load_map (self, path):
        with open(path) as stream:
            jsyms = json.loads(stream.read())
            for k,v in jsyms.items():
                self.walls.update ({(val[0],val[1]):k for val in v})

class MapEntity ():
    def __init__ (self, xy, entname, **kwargs):
        self.xy = xy
        self.entname = entname
        self.infokeys = kwargs.keys()
        self.__dict__.update (kwargs)

    def infos (self, center):
        infos = {"id":id(self),
                "x": self.xy[0]-center[0] + 8,
                "y": int(self.xy[1]-center[1] + CLIENT_COLS[self.xy[0]-center[0]+8]/2)}
        for key in self.infokeys:
            info[key] = getattr(self, key)

class Creature (MapEntity):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, ap=0, status={}, **kwargs)
        self._diagonal_step = self._step #TODO
        self.actions = {'step': CreatureAction(self._step, 4),
                'diagonal_step': CreatureAction(self._diagonal_step, 7),
                'attack': CreatureAction(self._attack, 4)
                }
        #self.last_action = None
        #self.is_pc = False
        #self.max_health = health


    def get_visible_creatures (self, game_map, radius):
        return [ cr for cr in game_map.creatures.values()
            if 0 < dist(self.xy, cr.xy) < radius + 0.4 and self.los(self.xy, cr.xy)]

    def _step (self, step, game_map):
        nextxy = step_add(self.xy, step)
        if game_map.get(nextxy) == '#':
            raise ActionFailure()
        if nextxy in game_map.creatures:
            raise ActionFailure()
        del game_map.creatures[self.xy]
        game_map.creatures[nextxy] = self
        self.xy = nextxy

    def take_damage (self, phys, magic, truedmg):
        self.health -= phys * 1/(1 + self.armor/10)
        self.health -= magic * 1/(1 + self.mr/10)
        self.health -= truedmg

    def _attack (self, targetxy, game_map):
        if dist(targetxy, self.xy) > self.attack_range + 0.01: 
            raise ActionFailure()
        if targetxy not in game_map.creatures:
            raise ActionFailure()
        game_map.creatures[targetxy].take_damage (self.ad, 0, 0)
        if game_map.creatures[targetxy].health <= 0 and game_map.get(targetxy) == ' ':
            game_map.walls[targetxy] = '%' 
        if not target.is_pc:
            target.act(target.try_attack, (self.xy, game_map))
        return True


class Shop ():
    def __init__ (self, xy):
        self.xy = xy
        self.char = "$"
    def try_buy (self, buyer, item):
        if dist(buyer,self.xy) > 2.4:
            return False
        slot = item.definition.slot
        if slot in buyer.slots:
            if buyer.money + 0.8 * buyer.slots[slot].definition.price > item.definition.price :
                self.sell(buyer, buyer.slots[slot])
                buyer.slots[slot] = Item(item.definition)
            return True
        if buyer.money > item.definition.price :
            buyer.slots[slot] = Item(item.definition)
            return True
        return False

    def try_sell (self, seller, item):
        if dist(buyer,self.xy) > 2.4:
            return False
        slot = item.definition.slot
        del seller.slots[slot]
        seller.money += 0.8 * item.definition.price
        return True

class Item ():
    def __init__(self, definition):
        self.count = definition.count 
        self.definition = definition
    def infos (self, center):
        return {
                "id":id(self),
                "count":self.count
                }
    def equip (self, user):
        if not self.definition["slot"] :
            return False
        if self.definition["slot"] in user.slots:
            user.slots[self.definition["slot"]].unequip(user)
        user.slots[self.definition["slot"]] = self
        user.items.remove(self)
        for key, val in self.definition["equip_delta"].items():
            user.__dict__[key] += val
    def unequip (self, user):
        del user.slots[self.definition["slot"]]
        user.items.append(self)
        for key, val in self.definition["equip_delta"].items():
            user.__dict__[key] -= val
       
class Mob (Creature):
    def ai_find_pc (self, game_map):
        creatures = self.get_visible_creatures(game_map, 7)
        for c in creatures :
            if c.is_pc :
                return c.xy

    def closest_step (self, game_map, xy):
        for step in sorted(STEPS, key=lambda a: dist(step_add(self.xy, a), xy)):
            if self.act (self.try_move, (step, game_map)):
                return

    def ai_play (self, game_map):
        pcxy = self.ai_find_pc (game_map)
        if not pcxy:
            self.closest_step (game_map, (0,16))
            return
        if self.act (self.try_attack, (pcxy, game_map)):
            return
        self.closest_step (game_map, pcxy)

class PC (Creature):
    def __init__ (self, xy, client, definition):
        super().__init__(xy, definition) 
        self.is_pc = True
        self.client = client
        self.prev_message = {}
        self.prev_creatures = {}
        self.items = []
        self.slots = {}
        self.pending = None
        #/step
        #if game_map.get(nextxy) == '_' and self.is_pc:
        #    raise ActionFailure()
        
        #/attack
        #target = game_map.creatures[targetxy]
        #if target.is_pc == self.is_pc:
        #    raise ActionFailure()

    def game_over (self):
        message = {"game": "over"}
        self.client.write_message(json.dumps(message)) 
    def send_state(self, game_map, lives):
        message = { "mapentities": { id(cr):cr.infos(self.xy) for cr in self.get_visible_creatures(game_map, 7) },
                    "center": { "x": self.xy[0], "y":self.xy[1] },
                    "lives": lives,
                    "map": [ k for k in game_map.walls.keys() if game_map.walls[k] == '#'],
                    "board": game_map.display(self,7)}
        self.prev_creatures.update(message['mapentities'])
        message["creatures"] = self.prev_creatures
        self.prev_creatures = {idcr:{'reset':True} for idcr in message['mapentities'].keys()}
        deltam = delta_compress(message, self.prev_message)
        if deltam:
            self.client.write_message(json.dumps(deltam)) 
        self.prev_message = message
            
class Room ():
    def __init__ (self, clients):
        self.game = Game()
        self.game_over = False  
        self.players = [PC((0,i),clients[i],defs.robot) for i in range(len(clients))]
        for pc in self.players:
            pc.client.pc = pc
            pc.client.room = self
            self.game.game_map.creatures[pc.xy] = pc
            pc.send_state(self.game.game_map, self.game.lives)
        
    def keypress (self, pc, message):
        m = json.loads(message)
        if 'action' in m and m['action'] in pc.actions:
            addx = int(m['x']) - 8
            addy = int(m['y']) - int(CLIENT_COLS[int(m['x'])]/2)
            if addx % 2:
                 addy += .5
            pc.actions[m['action']](step_add(pc.xy, (addx, addy)))
        max_ap = max((pc.ap for pc in self.players))
        self.game.next_turn(12 - max_ap)
        self.game_over = self.check_game_over()
        for pc in self.players:
            if self.game_over:
                pc.game_over ()
            else:
                pc.send_state (self.game.game_map, self.game.lives)

    def check_game_over (self):
        if self.game.lives <= 0:
            return True

        for player in self.players :
            if player.health > 0:
                return False
        return True

class Game ():
    def __init__ (self):
        self.game_map = GameMap ()
        self.game_map.load_map('mymap.txt')
        self.turn = 0
        self.lives = 10 
    def spawn_mobs(self):
        if self.turn not in defs.waves:
            return
        for xy, mobdef in defs.waves[self.turn].items():
            self.game_map.creatures[xy] = Mob (xy, mobdef)

    def next_turn (self, turns_to_play): 
        for i in range(turns_to_play):
            self.turn += 1
            self.spawn_mobs()
            self.game_map.creatures = { xy:cr for xy,cr in self.game_map.creatures.items() if cr.health > 0 }
            escaped = [ xy for xy in self.game_map.creatures.keys()
                    if xy[1] > 15 and not self.game_map.creatures[xy].is_pc ]
            for e in escaped:
                self.lives -= 1
                del self.game_map.creatures[e]
            for creature in self.game_map.creatures.values():
                creature.ap += 1
                creature.energy = min(creature.energy + 1,100)
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

