import tornado.ioloop
import tornado.web
from tornado import websocket
from game import Room
import os
import json

GLOBALS={
    'waiting' : [],
    'games' : [],
}
P_MAX = 3

class ClientSocket(websocket.WebSocketHandler):
    def open(self):
        GLOBALS['waiting'].append(self) #Add to pickup list
        if len(GLOBALS['waiting']) == P_MAX:
            GLOBALS['games'].append(Room(GLOBALS['waiting']))
            GLOBALS['waiting'] = []
        else:
            for cl in GLOBALS['waiting']:
                cl.write_message(json.dumps({"game": "queuing", "players":len(GLOBALS['waiting'])}))

    def on_close(self):
        if self in GLOBALS['waiting']: 
            GLOBALS['waiting'].remove(self)
            return
    def on_message (self, message) :
        if "start" in message and GLOBALS['waiting'][0] == self:
            GLOBALS['games'].append(Room(GLOBALS['waiting']))
            GLOBALS['waiting'] = []
        else:
            self.room.keypress (self.pc, message)
        #for room in GLOBALS['games']: #FIXME: players still containing pc
        #    if self in room.clients:
        #        ...

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static")
}
application = tornado.web.Application([
    (r"/socket", ClientSocket),
    ], debug=True, **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
