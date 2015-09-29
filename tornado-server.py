import tornado.ioloop
import tornado.web
from tornado import websocket
from engine import *
import pubsub

GLOBALS={
    'waiting' : [],
    'games' : [],
}

tut_text = ["""Play a survival roguelike in cooperation with other online players !<br>
Your goal is to survive as much evil monster waves as possible.<br>
Navigate in tutorial with numpad 4 and 6 (previous and next)<br>""",
"""The game is in text mode only, and each number represents a different feature of the map.<br>
-'@'is a player. You or your coop friends.<br>
-'.' represents floor. You can move freely on it.<br>
-'#' represents a wall. You can't move on it, and it also obstructs your field of view.<br>
-'%' represents a corpse.<br>
- Any other letter represent an enemy.<br>""",
"""The game is played with numpad only.<br><br>
 &nbsp   7 8 9<br>
 &nbsp &nbsp\|/ 
 &nbsp   4-@-6 &nbsp
 &nbsp &nbsp/|\<br>
 &nbsp   1 2 3<br>
 &nbsp These keys are to move around. <br>
 If you move into a monster,it will automatically attack it instead.<br>
 """,
"""If you press 5, you enter in ability mode, and each number activate a different special.<br><br>
Ability 1: Cleave. Damages all enemies in melee range for 80% attack.<br>
Ability 2: Smite. Damages one enemy at distance for 12 true damage.<br>
Ability 3: Swiftness. Increase your movement speed for a short duration.<br>""",
"""That's it! Good luck and have fun!<br>"""]

#class GenericDisplay ():
#    def __init__ (self, client):
#        self.array = ['&nbsp'*COLUMNS for i in range(LINES)]
#        self.client = client
#    def flip (self):
#        for j in range(LINES):
#            for i in range(COLUMNS):
#                text += self.array[j][i]
#        self.client.write_message (text)
#    def blit (self, x, y, string):
#        self.array[y][x] = string

class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['waiting'] += [self] #Add to pickup list
        players = len(GLOBALS['waiting'])
        if players == 4:
            GLOBALS['games'] = Game (GLOBALS['waiting']) #Start a game
            GLOBALS['waiting'] = []
            print "Game launched"
        else:
            for client in GLOBALS['waiting']:
                client.tut_ind = 0
            self.disp_tut ()

    def disp_tut (self):
        for client in GLOBALS['waiting']:
            msg = tut_text[client.tut_ind].split ('<br>')
            for i in range(len(msg)):
                length = len (msg[i]) -1
                left_padding = (COLUMNS + 19 - length)/2
                right_padding = (COLUMNS + 20 - length)/2
                msg [i] = '&nbsp' * left_padding + msg[i] + ('&nbsp' * right_padding)
            top_padding = (LINES - 2 - len(msg))/2
            bottom_padding = (LINES - 1 - len(msg))/2
            msg = ['&nbsp'] * top_padding + msg
            msg += ['&nbsp'] * bottom_padding
            msg = '<br>'.join(msg)
            if client == GLOBALS['waiting'][0]: # Game owner
                client.write_message (msg + '<br><br>%d / 4 players. Start without full party by pressing 5<br>' % len(GLOBALS['waiting']))
            else:
                client.write_message (msg + '<br><br>Curently %d players out of 4.<br>' % len(GLOBALS['waiting']))

    def on_close(self):
        if self in GLOBALS['waiting']: #Not in game
            GLOBALS['waiting'].remove(self)
            return
        self.game.clients.remove(self) #In game
        if not self.game.clients :
            GLOBALS['games'].remove(self.game)

    def on_message (self, message):
        if self in GLOBALS['waiting']:
            if int(message) == 100:
                self.tut_ind = max (0, self.tut_ind -1)
                self.disp_tut ()
            elif int(message) == 102:
                self.tut_ind = min (len(tut_text)-1, self.tut_ind +1)
                self.disp_tut ()
            if self != GLOBALS['waiting'][0] or int(message) != 101:
                return
            #Start a game
            g = Game (GLOBALS['waiting'])
            GLOBALS['games'] += [g] 
            GLOBALS['waiting'] = []
            self.game = g
            print "Game launched"
            return

        self.io_handler.key_press (int(message))


class GameHandler (tornado.web.RequestHandler):
    def get (self, *args, **kwargs):
        f = open ("game.html")
        self.write ( f.read () )

class GameJsHandler (tornado.web.RequestHandler):
    def get (self, *args, **kwargs):
        f = open ("game.js")
        self.write ( f.read () )

application = tornado.web.Application([
    (r"/socket", ClientSocket),
    (r"/game", GameHandler),
    (r"/game.js", GameJsHandler),
], debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
