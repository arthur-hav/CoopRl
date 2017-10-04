from math import *
import json
import threading
import defs
import collections
import itertools

CO = cos(pi/6)
CORAD = 2*CO/3 
STEPS = ((0, -1), (1, -0.5), (1, 0.5), (0, 1), (-1, 0.5), (-1, -0.5))
DIAGONAL_STEPS = ((1, -1.5), (2, 0), (1, 1.5), (-1, 1.5), (-2, 0), (-1, -1.5))
CLIENT_COLS = [5,8,11,12,13,14,15,14,15,14,15,14,13,12,11,8,5]

def dist(xy0, xy1):
    return sqrt((xy1[0]-xy0[0])**2*CO**2 + (xy1[1]-xy0[1])**2)

def step_to (xy0, xy1):
    min_dist = dist(xy0, xy1)
    step = (0,0)
    for s in STEPS:
        d = dist(step_add(xy0, s), xy1)
        if d < min_dist:
            step = s
            min_dist = d
    return step_add(xy0, step)

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
    def __call__(self, *args):
        try:
            self.action(*args)
        except ActionFailure:
            return 0
        return self.cost

class GameMap ():
    def __init__ (self, map_radius=15):
        self.entities = collections.defaultdict(list)
        self.map_radius = map_radius 
        self.turn_callbacks = []

    def next_turn(self):
        for ent in (ent_list for ent_list in self.entities.values()):
            ent.next_turn()

    def is_walkable (self, xy):
        if dist((0,0), xy) > self.map_radius:
            return False
        return all((ent.can_walk_through for ent in self.entities[xy]))

    def los (self, xy0, xy1):
        d0 = dist(xy0, xy1)
        d = d0
        cell = xy0
        dx, dy = (xy1[0] - xy0[0]) * CO, xy1[1] - xy0[1]
        c = - dy * xy0[0] * CO + dx * xy0[1]
        los_steps = [s for s in STEPS if dx / (d0 or 1) * s[0] * CO + dy / (d0 or 1) * s[1] > 0.5001]
        while d > 0 :
            for s in los_steps:
                _cell = step_add(cell, s)
                _cell_dist = abs(_cell[0] * CO * dy - _cell[1] * dx + c) / d0
                if _cell_dist < 0.5001:
                    if not all((ent.can_see_through for ent in self.entities[_cell])):
                        return _cell
            cell = step_to(cell, xy1)
            d = dist(cell, xy1)
        return xy1

    def losmap (self, pc, radius):
        losmap = {}
        for x in range(-int(radius/CO), int(radius/CO)+1):
            for y in range(-radius, radius+1):
                cell = step_add(pc.xy, (x,y)) if x%2==0 else step_add(pc.xy,(x,y+0.5))
                if dist(cell, pc.xy) > radius + 0.4:
                    continue
                losmap[cell] = False
                los_cell = self.los(pc.xy, cell)
                losmap[los_cell] = True
        return losmap

    def load_map (self, path):
        with open(path) as stream:
            jsyms = json.loads(stream.read())
            for k,v in jsyms.items():
                defk = defs.terrain[k]
                for xy in v:
                    self.entities[(xy[0], xy[1])].append(MapEntity(xy, **defk))

class MapEntity ():
    def __init__ (self, xy, can_walk_through=True, can_see_through=True, **kwargs):
        self.xy = xy
        self.can_walk_through = can_walk_through
        self.can_see_through = can_see_through
        self.infokeys = kwargs.keys()
        self.turn_callbacks = []
        self.__dict__.update (kwargs)

    def take_damage (self, dmg, dmg_typpe):
        pass

    def infos (self, center):
        infos = {
                "id":id(self),
                "x": self.xy[0]-center[0] + 8,
                "y": int(self.xy[1]-center[1] + CLIENT_COLS[self.xy[0]-center[0]+8]/2)
        }
        for key in self.infokeys:
            infos[key] = getattr(self, key)
        return infos

class Creature (MapEntity):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, can_walk_through=False, ap=12, status={}, **kwargs)
        self._diagonal_step = self._step #TODO
        self.actions = {'step': CreatureAction(self._step, 4),
                #'diagonal_step': CreatureAction(self._diagonal_step, 7),
                'attack': CreatureAction(self._attack, 4)
                }
        def next_turn (self):
            self.ap = min(self.ap + 1, 12)
            self.energy = min(self.energy + 1, 100)
            self.status = { st:turn for st,turn in self.status.items()
                    if self.status[st] >= self.turn }
        #self.last_action = None
        #self.is_pc = False
        #self.max_health = health

    def get_visible_entities (self, game_map, radius):

        return [ cr for cr in itertools.chain(*game_map.entities.values())
                if dist(self.xy, cr.xy) < radius + 0.4 and game_map.los(self.xy, cr.xy)]

    def _step (self, targetxy, game_map):
        if not game_map.is_walkable(targetxy):
            raise ActionFailure()
        game_map.entities[self.xy].remove(self)
        game_map.entities[targetxy].append(self)
        self.xy = targetxy

    def take_damage (self, dmg, dmg_type):
        self.health -= dmg

    def _attack (self, targetxy, game_map):
        if dist(targetxy, self.xy) > self.attack_range + 0.01: 
            raise ActionFailure()
        if targetxy not in game_map.entities:
            raise ActionFailure()
        for ent in game_map.entities[targetxy]:
            ent.take_damage (self.ad)
        return True
    
    def _dash(self, targetxy, game_map):
        if not game_map.is_walkable(targetxy):
            raise ActionFailure()
        if dist(targetxy, self.xy) > 2:
            raise ActionFailure()
        del game_map.entities[self.xy]
        game_map.entities[targetxy] = self
        self.xy = targetxy
        entities = self.get_visible_entities(game_map, 3)
        game_map.entities[targetxy].take_damage (self.ap)


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
    def _equip (self, user):
        if "slot" not in self.definition:
            raise ActionFailure()
        if self.definition["slot"] in user.slots:
            user.slots[self.definition["slot"]].unequip(user)
        user.slots[self.definition["slot"]] = self
        user.items.remove(self)
        for key, val in self.definition["equip_delta"].items():
            user.__dict__[key] += val
    def _unequip (self, user):
        if "slot" not in self.definition:
            raise ActionFailure()
        if self.definition["slot"] not in user.slots:
            raise ActionFailure()
        del user.slots[self.definition["slot"]]
        user.items.append(self)
        for key, val in self.definition["equip_delta"].items():
            user.__dict__[key] -= val
    def _apply (self, target):
        if "apply" not in self.definition:
            raise ActionFailure()
        self.definition["apply"](self, target) 

class Mob (Creature):
    def ai_find_pc (self, game_map):
        entities = self.get_visible_entities(game_map, 7)
        for c in entities :
            if c.is_pc :
                return c.xy

    def closest_step (self, game_map, xy):
        for step in sorted(STEPS, key=lambda a: dist(step_add(self.xy, a), xy)):
            if self.act (self.try_move, (step, game_map)):
                return

    def ai_play (self, game_map):
        if self.ap < 6:
            return
        pcxy = self.ai_find_pc (game_map)
        if not pcxy:
            return
        if self.act (self.try_attack, (pcxy, game_map)):
            return
        self.closest_step (game_map, pcxy)

class PC (Creature):
    def __init__ (self, client, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self.client = client
        self.prev_message = {}
        self.prev_entities = {}
        self.items = []
        self.slots = {}
        self.pending = None
        self.actions.update({
            "spell1": CreatureAction(self.throw_orb, 4),
            #"spell2": CreatureAction(self.petrify, 4),
        })
    #def _step(self, targetxy, game_map):
    #    if game_map.get(targetxy) == '_':
    #        raise ActionFailure()
    #    return super._step(self, targetxy, game_map)

    def throw_orb(self, targetxy, game_map):
        orb_cell = self.xy
        while orb_cell != targetxy:
            orb_cell = step_to(targetxy)
            for entity in game_map.entities[orb_cell]:
                entity.take_damage(20, 'magical')
        #
        #/attack
        #target = game_map.entities[targetxy]
        #if target.is_pc == self.is_pc:
        #    raise ActionFailure()

    def game_over (self):
        message = {"game": "over"}
        self.client.write_message(json.dumps(message)) 
    def send_state(self, game_map, lives):
        message = { 
                "mapentities": { id(cr):cr.infos(self.xy) for cr in self.get_visible_entities(game_map, 7) },
                "center": { "x": self.xy[0], "y":self.xy[1] },
                "lives": lives,
                #"map": [ k for k in game_map.walls.keys() if game_map.walls[k] == '#'],
                "lit": [],
                "unlit": [] 
        }
        for k, v in game_map.losmap(self, 7).items():
            key = 'lit' if v else 'unlit'
            los_x = k[0] - self.xy[0] + 8
            los_y = int(k[1] - self.xy[1] + CLIENT_COLS[k[0] - self.xy[0]+8]/2)
            message[key].append((los_x, los_y))

        self.prev_entities.update(message['mapentities'])
        message["mapentities"] = self.prev_entities
        self.prev_entities = {idcr:{'reset':True} for idcr in message['mapentities'].keys()}
        deltam = delta_compress(message, self.prev_message)
        if deltam:
            self.client.write_message(json.dumps(deltam)) 
        self.prev_message = message

class Room ():
    def __init__ (self, clients):
        self.game = Game()
        self.game_over = False  
        self.players = [PC(clients[i],xy=(0,1), **defs.robot) for i in range(len(clients))]
        for pc in self.players:
            pc.client.pc = pc
            pc.client.room = self
            self.game.game_map.entities[pc.xy].append(pc)
            pc.send_state(self.game.game_map, self.game.lives)
        
    def keypress (self, pc, message):
        m = json.loads(message)
        if 'action' in m and m['action'] in pc.actions:
            addx = int(m['x']) - 8
            addy = int(m['y']) - int(CLIENT_COLS[int(m['x'])]/2)
            if addx % 2:
                 addy += .5
            pc.actions[m['action']](step_add(pc.xy, (addx, addy)), self.game.game_map)
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
            self.game_map.entities[xy].append(Mob (xy=xy, **mobdef))

    def next_turn (self, turns_to_play): 
        for i in range(turns_to_play):
            self.turn += 1
            self.spawn_mobs()
            escaped = [ xy for xy in self.game_map.entities.keys()
                    if xy[1] > 15 and not self.game_map.entities[xy].is_pc ]
            #for e in escaped:
            #    self.lives -= 1
            #    del self.game_map.entities[e]
                #if creature.pending:
                #    creature.act(*creature.pending)
        #if not self.game_over_state :

