import time, threading
import random
from math import sqrt
import pubsub

LINES = 28 
COLUMNS = 80
HUD_W = 18
COLORS = ("#ff0000","#00ff00","#0000ff","#ffff00")
game_over ="""


  ________                        ________                     
 /  _____/_____    _____   ____   \_____  \___  __ ___________ 
/   \  ___\__  \  /     \_/ __ \   /   |   \  \/ // __ \_  _  \\
\    \_\  \/ __ \|  Y Y  \  ___/  /    |    \   /\  ___/|  | \/
 \______  (____  /__|_|  /\___  > \_______  /\_/  \___  >__|   
        \/     \/      \/     \/          \/          \/       



Refresh page to try again !
"""
class IoHandler ():
    def __init__ (self, cli, game):
        self.ready = False
        self.client = cli
        self.game = game
        self.disp_map = ['&nbsp'*COLUMNS for i in range(LINES)]
        self.hud_map = ['&nbsp' * HUD_W for i in range(LINES)]

    def _paint (self):
        pass

    def key_press (self, message):
        print message, "recieved"

    def display (self):
        self._paint ()
        text = ''
        for line_screen, line_hud in zip(self.disp_map, self.hud_map):
            text += line_screen.replace('  ',' &nbsp') + '|' + line_hud.replace ('  ',' &nbsp') + '|<br>'
        self.client.write_message (text)
        self.disp_map = ['&nbsp'*COLUMNS for i in range(LINES)]
        self.hud_map = ['&nbsp' * HUD_W for i in range(LINES)]

class Shop (IoHandler):
    lines = [3, 4, 5, 6, 7, 20]
    offers = [
        '        Attack + 1  :<span style="color:#ffff00">{0:4d}</span> gold',
        '        HP     + 10%:<span style="color:#ffff00">{0:4d}</span> gold',
        '        MP     + 10%:<span style="color:#ffff00">{0:4d}</span> gold',
        '        Armor  + 1  :<span style="color:#ffff00">{0:4d}</span> gold',
        '        MR.    + 1  :<span style="color:#ffff00">{0:4d}</span> gold',
        '               &ltDone&gt         '
        ]
    def __init__ (self, cli, game):
        IoHandler.__init__(self,cli,game)
        self.selected_line = 0 

    def cursor_move (self, direction):
        self.selected_line += direction
        self.selected_line = min (max (self.selected_line, 0), len(Shop.lines) - 1)
        self.display ()

    def key_press (self, message):
        if message == 98:
            self.cursor_move (1)
        if message == 101:
            self.cursor_select ()
        if message == 104:
            self.cursor_move (-1)

    def _paint (self):
        for i,j,k in zip (Shop.offers, Shop.lines, (
                (int(20 + 4 * self.client.pc.ad_bonus)),
                (int(20 + 4 * self.client.pc.health_bonus/10)),
                (int(15 + 3 * self.client.pc.mana_bonus/10)),
                (int(15 + 3 * self.client.pc.armor_bonus)),
                (int(15 + 3 * self.client.pc.mr_bonus)),
                ())):
            offer_str = i.format (k)
            offer_str += (COLUMNS - 29) * ' ' 
            if j == Shop.lines[self.selected_line] :
                offer_str = '<span style="background:#666666">' + offer_str + '</span>'
            self.disp_map[j] = offer_str 


        #Right GUI display
        hp_str = "{0:3.0f}".format (100 + self.client.pc.health_bonus)
        self.hud_map [1] = '    HP  &nbsp<span style="color:#ff0000">'+hp_str+' %</span>    '
        mana_str = "{0:3.0f}".format (100 + self.client.pc.mana_bonus)
        self.hud_map [2] = '   Mana &nbsp<span style="color:#0000ff">'+mana_str+' %</span>    '

        ad_str = "   Attack   {0:2.0f}    ".format (self.client.pc.ad + self.client.pc.ad_bonus)
        self.hud_map [9] = ad_str
        res_str = "  Arm {0:2.0f}  MR. {1:2.0f}  ".format (self.client.pc.armor + self.client.pc.armor_bonus,self.client.pc.mr + self.client.pc.mr_bonus)
        self.hud_map [10] = res_str
        gold_str = '    Gold   <span style="color:yellow">{0:4d}</span>    '.format (self.client.pc.gold)
        self.hud_map [25] = gold_str

    def cursor_select (self):
        if self.selected_line == 0:
            if self.client.pc.gold < 20 + 4 * self.client.pc.ad_bonus:
                return
            self.client.pc.gold -= 20 + 4 * self.client.pc.ad_bonus
            self.client.pc.ad_bonus += 1

        if self.selected_line == 1:
            if self.client.pc.gold < 20 + 4 * self.client.pc.health_bonus / 10:
                return
            self.client.pc.gold -= 20 + 4 * self.client.pc.health_bonus / 10
            self.client.pc.health_bonus += 10

        if self.selected_line == 2:
            if self.client.pc.gold < 15 + 3 * self.client.pc.mana_bonus / 10:
                return
            self.client.pc.gold -= 15 + 3 * self.client.pc.mana_bonus / 10
            self.client.pc.mana_bonus += 10

        if self.selected_line == 3:
            if self.client.pc.gold < 15 + 3 * self.client.pc.armor_bonus:
                return
            self.client.pc.gold -= 15 + 3 * self.client.pc.armor_bonus
            self.client.pc.armor_bonus += 1

        if self.selected_line == 4:
            if self.client.pc.gold < 15 + 3 * self.client.pc.mr_bonus:
                return
            self.client.pc.gold -= 15 + 3 * self.client.pc.mr_bonus
            self.client.pc.mr_bonus += 1

        if self.selected_line == 5:
            self.client.ready = True
            for player in self.game.clients:
                if not player.ready:
                    return
            for player in self.game.clients: #FIXME
                player.io_handler = ArenaIo (self.client, self.game)
                player.pc.health = 100
                player.pc.mana = 100
                player.pc.is_dead = False
            self.game.next_turn ()
            return
        self.display ()

class Game ():
    def __init__ (self, clients):

        self.creature_map = [[None]*COLUMNS for i in range(LINES)]
        self.sfx = {}
        #self.creature_map_next_turn = [[None]*COLUMNS for i in range(LINES)]
        self.game_map = [['.']*COLUMNS for i in range(LINES)]
        for i in range (LINES*COLUMNS/15):
            rx = random.randrange (COLUMNS)
            ry = random.randrange (LINES)
            self.game_map[ry][rx] = '#'

        self.mobs = []
        self.turn = 0
        self.clients = clients
        self.timer = None
        self.paused = False
        self.wavenum = 0
        self.game_over_state = False
        position = 0
        for client in self.clients:
            #(game, x, y, health, armor, mr, ad, color)
            client.pc = Paladin (self, COLUMNS/2+position-2,LINES/2,100,4,4,10,COLORS[position])
            position += 1
            client.game = self
        self.spawn_shop ()

    def spawn_shop (self):
        for client in self.clients:
            client.io_handler = Shop (client, self)
            client.io_handler.display ()

    def spawn_monster (self, mobclass):
        while True:
            rand = random.randrange (0,2*LINES+2*COLUMNS-4)
            #Up 
            x = rand
            y = 0
            if rand >= COLUMNS and rand < COLUMNS+2*LINES-2: #Sides
                x = (LINES % 2) * (COLUMNS -1)
                y = (rand - COLUMNS)/2
            #Bottom
            elif rand >= COLUMNS+2*LINES-2:
                x = rand - (COLUMNS+2*LINES-2)
                y = LINES-1
            if not self.creature_map[y][x] and not self.game_map[y][x] == '#':
                mob = mobclass (self, x, y)
                self.mobs += [mob] 
                break

    def spawn_wave (self):
        for i in range (5+(self.wavenum * len(self.clients))):
            mob = Skeleton
            if i > 6 and i % 3 == 1:
                mob = Zombie
            if i > 12 and i % 4 == 2:
                mob = Necromancer
            self.spawn_monster (mob)

    def check_paused (self):
        afk_count = 0
        for client in self.clients:
            if client.pc.afk or client.pc.AP >= 20:
                afk_count += 1
        self.paused = (afk_count == len(self.clients))

    def check_accel (self):
        return 1
        #for client in self.clients:
        #    if not client.pc.afk and client.pc.AP >= 12 :
        #        return 1
        #return 4

    def los (self, x0, y0, x1, y1, los_range):
        dx = x1-x0
        dy = y1-y0
        dist = sqrt(dx * dx + dy * dy)

        if dist > los_range:
            return False

        sx = -1
        if x0 < x1:
            sx = 1
        sy = -1
        if y0 < y1:
            sy = 1
        xnext = x0
        ynext = y0

        while xnext != x1 or ynext != y1:
            if abs(dy * (xnext - x0 + sx) - dx * (ynext - y0)) / dist < 0.5 :
                xnext += sx;

            elif abs(dy * (xnext - x0) - dx * (ynext - y0 + sy)) / dist < 0.5:
                ynext += sy
            else:
                xnext += sx
                ynext += sy

            if xnext > COLUMNS - 1 or xnext < 0 or ynext > LINES - 1 or ynext < 0:
                return 

            if self.game_map[ynext][xnext] in ('#','+'):
                break

        x0 = xnext
        y0 = ynext
        return x0 == x1 and y0 == y1;

    def game_over (self):
        self.game_over_state = True
        html_go = game_over.replace(' ','&nbsp')
        html_go = html_go.replace('>','&gt')
        html_go = html_go.replace('<','&lt')
        html_go = html_go.replace('\n','<br>')
        for client in self.clients :
            client.write_message (html_go)
            client.close ()

    def next_turn (self): 
        if self.timer :
            self.timer.cancel()
        if not self.mobs:
            self.wavenum += 1
            if self.wavenum % 5 == 0:
                for client in self.clients:
                    client.pc.gold += 30 + 4 * self.wavenum
                    client.io_handler = Shop (self, client)
                return
            self.spawn_wave ()
        self.check_paused ()
        if self.paused:
            return

        bonus_ap = self.check_accel ()
        self.turn += bonus_ap

        for client in self.clients:
            client.pc.AP += bonus_ap
            client.pc.mana += bonus_ap / 2.0
            if client.pc.mana > 100:
                client.pc.mana = 100.0
            for st in client.pc.status.copy():
                client.pc.status[st] -= bonus_ap
                if client.pc.status[st] < 0:
                    del client.pc.status[st]
            if client.pc.pending and client.pc.pending[0] <= client.pc.AP:
                client.pc.pending[1](*client.pc.pending[2])
                client.pc.pending = None
            if client.pc.AP > 20:
                client.pc.AP = 20
                client.pc.afk = True


        for mob in self.mobs:
            mob.AP += bonus_ap
            mob.ai_play()
            if mob.AP > 20:
                mob.AP = 20

        if not self.game_over_state :
            for client in self.clients:
                client.io_handler.display ()
        self.sfx = {}

        self.check_paused ()
        if self.clients and not self.paused: #Ensures the loop is killed if nobody plays
            self.timer = threading.Timer (.05, self.next_turn).start()

class ArenaIo ( IoHandler ):
    def __init__ (self, cli, game):
        IoHandler.__init__ (self, cli, game)

    def key_press (self, message):
        self.client.pc.pending = None
        if self.client.pc.ability :
            if message >= 97 and message <= 105:
                if self.client.pc.targeting != None :
                    self.client.pc.targeting (message-97)
                else:
                    if message == 101:
                        self.client.pc.ability = False
                        if self.game.paused:
                            self.display ()
                    else:
                        self.client.pc.cast (message-97)
            return

        if int(message) == 97: #Numpad key codes
            self.client.pc.move (-1,1)
        if int(message) == 98:
            self.client.pc.move (0,1)
        if int(message) == 99:
            self.client.pc.move (1,1)
        if int(message) == 100:
            self.client.pc.move (-1,0)
        if int(message) == 101:
            self.client.pc.ability_on ()
        if int(message) == 102:
            self.client.pc.move (1,0)
        if int(message) == 103:
            self.client.pc.move (-1,-1)
        if int(message) == 104:
            self.client.pc.move (0,-1)
        if int(message) == 105:
            self.client.pc.move (1,-1)

    def _paint (self):
        #Main board
        for j in range (LINES):
            line = ''
            for i in range (COLUMNS):
                line += self._char_at (i, j)
            self.disp_map [j] = line

        #Hud
        hp_str = "{0:3.0f}".format (self.client.pc.health + self.client.pc.health_bonus)
        self.hud_map [1] = '    HP  &nbsp<span style="color:#ff0000">'+hp_str+' %</span>    '
        mana_str = "{0:3.0f}".format (self.client.pc.mana + self.client.pc.mana_bonus)
        self.hud_map [2] = '   Mana &nbsp<span style="color:#0000ff">'+mana_str+' %</span>    '
        ap_str = '<span style="color:#00ff00">'+ '=' * (self.client.pc.AP/4) + '.'* (5 - self.client.pc.AP/4) + '</span>' 
        self.hud_map [3] = '    AP  ['+ap_str+']   '

        line = 5
        for ally in self.game.clients:
            if ally == self.client:
                continue
            hp_str = "{0:3.0f}".format (ally.pc.health + ally.pc.health_bonus)
            self.hud_map [line] = '    ' + ally.pc.char + \
                    '  &nbsp<span style="color:#ff0000">'+hp_str+' %</span>     '
            line += 1
        
        ad_str = "   Attack   {0:2.0f}    ".format (self.client.pc.ad + self.client.pc.ad_bonus)
        self.hud_map [9] = ad_str
        res_str = "  Arm {0:2.0f}  MR. {1:2.0f}  ".format (self.client.pc.armor + self.client.pc.armor_bonus, 
                self.client.pc.mr + self.client.pc.mr_bonus)
        self.hud_map [10] = res_str
        if 'swiftness' in self.client.pc.status:
            self.hud_map [12] = '    Swiftness     '
            self.hud_map [13] = '    [<span style="color:blue">'+\
                    '='* (self.client.pc.status['swiftness']/10) + \
                    '.'* (8 - (self.client.pc.status['swiftness']/10)) +'</span>]    '
        gold_str = '    Gold   <span style="color:yellow">{0:3.0f}</span>    '.format (self.client.pc.gold)
        self.hud_map [25] = gold_str
        if self.client.pc.ability and not self.client.pc.targeting:
            self.hud_map [17] = '    1: Cleave     '
            self.hud_map [18] = '    2: Smite      '
            self.hud_map [19] = '    3: Swiftness  '

        #bottom_line
        if self.client.pc.targeting:
            self.disp_map[-1] = "&ltTARGETTING&gt" + self.disp_map[-1][60:]
        elif self.client.pc.ability:
            self.disp_map[-1] = "&ltABILITY&gt " + self.disp_map[-1][50:]

    def _char_at (self, char_ind, line):
        c = self.game.creature_map[line][char_ind]
        if not self.game.los (self.client.pc.x, self.client.pc.y, char_ind, line, 7.25):
            return '&nbsp'
        if self.client.pc.targets:
            for point in self.client.pc.targets: 
                if (char_ind, line) == (point.x, point.y):
                    index = self.client.pc.targets.index(point) + 1
                    if index > 9:
                        return '0'
                    else:
                        return str(index)
        if (char_ind, line) in self.game.sfx:
            return self.game.sfx[(char_ind,line)]
        elif c: 
            return self.game.creature_map[line][char_ind].char
        else:
            if self.game.game_map[line][char_ind] == ' ':
                return '&nbsp'
            elif self.game.game_map[line][char_ind] == '%':
                return '<span style="color:red">%</span>'
            else:
                return self.game.game_map[line][char_ind]

class Point ():
    def __init__ (self, x, y):
        self.x = x
        self.y = y

class Creature (Point):
    def __init__ (self, game, x, y, health, armor, mr, ad, char):
        Point.__init__ (self, x, y)
        self.game = game
        self.is_pc = False
        self.health = health
        self.armor = armor
        self.mr = mr
        self.ad = ad
        self.health_bonus = 0
        self.mana_bonus = 0
        self.armor_bonus = 0
        self.mr_bonus = 0
        self.ad_bonus = 0
        self.status = {}
        self.char = char
        self.game.creature_map[self.y][self.x] = self
        self.AP = random.randrange (0,15)

    def melee_target (self, x, y):
        nextx = self.x + x
        nexty = self.y + y 
        if nextx > COLUMNS - 1 or nextx < 0 or nexty > LINES - 1 or nexty < 0:
            return None
        return self.game.creature_map[nexty][nextx]

    def ability_on (self):
        if self.AP < 4:
            self.pending = (4, PC.ability_on, (self,))
            return 
        self.ability = True
        self.afk = False
        self.AP -= 4
        if self.game.paused:
            self.game.next_turn ()

    def move (self, x, y):
        if self.melee_target (x, y):
            return 
        nextx = self.x + x
        nexty = self.y + y 
        if nextx > COLUMNS - 1 or nextx < 0 or nexty > LINES - 1 or nexty < 0:
            return False
        if self.game.game_map[nexty][nextx] == '#':
            return False
        required_ap = 12
        if x == 0 or y == 0:
            required_ap = 8
        if 'swiftness' in self.status:
            required_ap *= 2
            required_ap /= 3
        if self.AP < required_ap:
            self.pending = (required_ap, Creature.move, (self, x, y))
            return False
        self.game.creature_map[self.y][self.x] = None
        self.x += x
        self.y += y
        self.game.creature_map[self.y][self.x] = self
        self.AP -= required_ap
        return True

    def take_damage (self, phys, magic, true):
        self.health -= phys * 10.0/(10 + self.armor + self.armor_bonus)
        self.health -= magic * 10.0/(10 + self.mr_bonus + self.mr)
        self.health -= true 
        if self.health + self.health_bonus <= 0:
            self.game.creature_map[self.y][self.x] = None
            self.game.game_map[self.y][self.x] = '%'
            if not self.is_pc :
                self.game.mobs.remove (self)
            else:
                self.is_dead = True
                for client in self.game.clients :
                    if not client.pc.is_dead:
                        return
                self.game.game_over ()

    def attack (self, x, y):
        if self.AP < 12:
            self.pending = (12, PC.attack, (self, x, y))
            return False
        target = self.melee_target (x, y)
        if not target:
            return False
        if target.is_pc == self.is_pc: 
            return False
        target.take_damage (self.ad + self.ad_bonus, 0, 0)
        self.game.sfx [(target.x, target.y)] = '<span style="color:#ff0000">*</span>'
        self.AP -= 12
        return True

    def ai_find_pc (self):
        dist = 100 
        pc_target = None
        for cli in self.game.clients :
            dist_cli = sqrt ((self.x - cli.pc.x)**2 + (self.y - cli.pc.y)**2)
            if not cli.pc.is_dead and dist_cli < dist :
                pc_target = cli.pc
                dist = dist_cli
            if dist_cli <= dist + .01 and dist_cli >= dist - .01:
                flip = random.randrange (2)
                if flip == 1:
                    pc_target = cli.pc
                    dist = dist_cli
        return pc_target

    def ai_play (self):
        if self.AP < 12:
            return
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                if i == j == 0:
                    continue
                self.attack (i,j)
        pc = self.ai_find_pc ()
        if not pc:
            return
        x = random.randrange (-1, 2) 
        y = random.randrange (-1, 2) 
        if pc.x < self.x :
            x = random.randrange (-1, 1) 
        elif pc.x > self.x :
            x = random.randrange (2) 
        if pc.y < self.y :
            y = random.randrange (-1, 1) 
        elif pc.y > self.y :
            y = random.randrange (2) 
        self.move (x,y)

class Skeleton (Creature):
    def __init__ (self, game,x,y):
        Creature.__init__ (self, game, x, y, 20+random.randrange(5), 2, 3, 4, 's')
 
class Zombie (Creature):
    def __init__ (self, game,x,y):
        Creature.__init__ (self, game, x, y, 35+random.randrange(8), 3, 3, 6, 'z')
        self.char = '<span style="color:#995555">z</span>'

class Necromancer (Creature):
    def __init__ (self, game,x,y):
        Creature.__init__ (self, game, x, y, 40+random.randrange(12), 2, 4, 6, 
                '<span style="color:#aa00ff">N</span>')
    def ai_play (self):
        if self.AP < 12:
            return
        for j in range (-3,4):
            for i in range (-3, 4):
                if i == j == 0:
                    continue
                x = self.x+i
                y = self.y+j
                if not self.game.los(self.x, self.y, x, y, 3.25):
                    continue
                if self.game.game_map[y][x] == '%':
                    self.game.game_map [y][x] = '.'
                    self.game.creature_map [y][x] = Skeleton (self.game, x, y)
                    self.AP -= 12
        pc = self.ai_find_pc ()
        if not pc:
            return
        if (self.x - pc.x)**2 + (self.y - pc.y)**2 > 10:
            return Creature.ai_play(self)
        pc.take_damage (0, 6.0, 0)
        self.game.sfx [(pc.x, pc.y)] = '<span style="color:#8888ff">*</span>'
        self.AP -= 12

class PC (Creature):
    def __init__ (self, game, x, y, health, armor, mr, ad, color):
        self.targets = []
        self.color = color
        self.mana = 100.0
        char = '<span style="color:' + self.color + '">@</span>'
        Creature.__init__ (self, game, x, y, health, armor, mr, ad, char)
        self.gold = 100
        self.is_pc = True
        self.is_dead = False
        self.afk = False
        self.cooldowns = [0 for i in range(9)]
        self.abilities = [None for i in range(9)]
        self.ability = False
        self.targeting = None
        self.pending = None
        self.AP = 0

    def move (self, x, y):
        if self.is_dead :
            return 
        self.afk = False
        if self.attack (x, y):
            return True
        if self.x + x < 1 or self.x + x > COLUMNS - 2 or self.y + y < 1 or self.y + y > LINES - 2:
            return False
        ret = Creature.move (self, x, y)
        if self.AP < 20 and self.game.paused :
            self.game.next_turn ()
        return ret

    def cast (self, num, *args):
        if self.abilities[num]:
            self.abilities[num] (self, *args)

class Abilities ():
    def __init__ ():
        pass
    def target ():
        pass
    def cast ():
        pass

class Paladin (PC):
    def __init__ (self, *args, **kwargs):
        PC.__init__ (self, *args, **kwargs)
        self.abilities [0] = Paladin.cleave
        self.abilities [1] = Paladin.smite_target
        self.abilities [2] = Paladin.swiftness
        self.abilities [3] = Paladin.jump_target
        self.abilities [5] = Paladin.fireball_target


    def cleave (self):
        if self.AP < 8 or self.mana < 20:
            return
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                if i == j == 0:
                    continue
                target = self.melee_target (i, j)
                if not target or target.is_pc:
                    continue
                target.take_damage (self.ad *0.8, 0, 0)
                self.game.sfx [(target.x, target.y)] = '<span style="color:#ff0000">*</span>'
        self.ability = False
        self.AP -= 8 
        self.mana -= 20
        self.afk = False
        if self.game.paused:
            self.game.next_turn ()

    def smite_target (self):
        if self.AP < 8 :
            return
        if self.mana < 35:
            return
        self.targeting = None
        self.targets = []
        for i in range(-8,9):
            for j in range(-8,9):
                if i == j == 0:
                    continue
                if not self.game.los(self.x, self.y, self.x+i,self.y+j,7.25):
                    continue
                target = self.melee_target (i, j)
                if target and not target.is_pc:
                    self.targets += [target]
        if not self.targets :
            return
        self.targeting = self.smite_cast 
        for cli in self.game.clients :
            cli.io_handler.display() 


    def fireball_target (self):
        self.smite_target ()
        if self.targeting:
            self.targeting = self.fireball_cast

    def fireball_cast (self, target_num):
        if not self.targets or target_num >= len(self.targets): 
            return
        c = self.targets[target_num]
        if c: 
            c.take_damage (0.0,12.0,0)
            self.game.sfx [(c.x, c.y)] = '<span style="color:#ff8800">*</span>'
        for j in range (-2, 3):
            for i in range (-2, 3):
                if i == j == 0:
                    continue
                if not self.game.los (c.x, c.y, c.x + i, c.y + j, 2.25):
                    continue
                self.game.sfx [(c.x + i, c.y + j)] = '<span style="color:#ff8800">*</span>'
                c2 = self.game.creature_map[c.y + j][c.x + i]
                if c2 and not c2.is_pc:
                    c2.take_damage (0.0,9.0,0)
        self.ability = None
        self.targeting = None
        self.targets = []
        self.AP -= 8
        self.afk = False
        self.mana -= 30
        if self.game.paused:
            self.game.next_turn ()

    def smite_cast (self, target_num):
        if not self.targets or target_num >= len(self.targets): 
            return
        c = self.targets[target_num]
        if c: 
            c.take_damage (0.0,0.0,12.0)
            self.game.sfx [(c.x, c.y)] = '<span style="color:#ffff00">*</span>'
        self.ability = None
        self.targeting = None
        self.targets = []
        self.AP -= 8
        self.afk = False
        self.mana -= 35
        if self.game.paused:
            self.game.next_turn ()

    def swiftness (self):
        if self.AP < 8:
            return
        if self.mana < 15:
            return
        self.AP -= 8
        self.mana -= 15
        self.afk = False
        self.status ['swiftness'] = 80
        self.ability = None
        self.afk = False
        if self.game.paused:
            self.game.next_turn ()

# jump is unusable, forget it for now
    def jump_target (self):
        if self.AP < 8 :
            return
        if self.mana < 15:
            return
        self.afk = False
        jumps = [(2, 1), (2, -1), (1, 2), (1, -2), 
                (-1, 2), (-1, -2), (-2, 1), (-2,-1)]
        for j in jumps :
            self.targets += [Point(self.x + j[0], self.y + j[1])]
        self.targeting = self.jump_cast 
        for cli in self.game.clients :
            cli.io_handler.display ()
        if self.game.paused:
            self.game.next_turn ()

    def jump_cast (self, target_num):
        if target_num > 7:
            return
        x = self.targets[target_num].x
        y = self.targets[target_num].y
        
        if x > COLUMNS - 1 or x < 0 or y > LINES - 1 or y < 0:
            return 
        if self.game.game_map[y][x] == '#':
            return
        self.game.creature_map[self.y][self.x] = None
        self.x = x
        self.y = y
        self.game.creature_map[y][x] = self

        self.ability = None
        self.targeting = None
        self.targets = []
        self.AP -= 8
        self.mana -= 15
        self.afk = False
        if self.game.paused:
            self.game.next_turn ()




        

