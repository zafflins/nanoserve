import json, random
import nanoserve as ns

def on_join(request, session, args):
    args.players[session.id] = [random.randint(50, 400), random.randint(50, 400)]
    print(f"Player {session.id} ({request["stream"]}) joined | Players {args.players}")
    args.broadcast()

def on_move(request, session, args):
    if session.id in args.players:
        dx, dy = json.loads(request["stream"]).values()
        args.players[session.id][0] += dx
        args.players[session.id][1] += dy
        args.broadcast()

class GameServer(ns.server.NanoServer):
    def __init__(self) -> None:
        super().__init__("My Server", "127.0.0.1", 5555, ns.proto.NPHS, ns.server.NanoRouter())
        
        self.players = dict()
        self.router.register(0, on_join, self)
        self.router.register(1, on_move, self)

    def disconnect_hook(self, session):
        try:
            self.players.pop(session.id)
        except KeyError: pass

    def broadcast(self):
        for session in self.sessions:
            session.streamOut = bytearray(json.dumps({"players": self.players}).encode())
            session.metaOut = {"mask": 0x01, "length": len(session.streamOut), "method": 1}

GameServer().run()
