import json
import nanoserve as ns, pygame as pg

class GameClient(ns.client.NanoClient):
    def __init__(self) -> None:
        
        self.players = {}

        self.clock = pg.time.Clock()
        self.windowSize = [400, 300]
        self.window = pg.display.set_mode(self.windowSize, flags=pg.SRCALPHA)

        super().__init__(ns.proto.NPHS)

    def read_hook(self, request: dict) -> None:
        if request["meta"][3] == 1:
            self.players = json.loads(request["stream"])["players"]

    def main(self) -> None:
        speed = 5
        dx, dy = 0, 0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_F5:
                    self.connect("127.0.0.1", 5555)
                    self.streamOut = bytearray(b"zafflins") # username stream
                    self.metaOut = {"mask": 0x00, "length": len(self.streamOut), "method": 0x00} # join method

        keys = pg.key.get_pressed()
        if keys[pg.K_w]: dy -= speed
        if keys[pg.K_s]: dy += speed
        if keys[pg.K_a]: dx -= speed
        if keys[pg.K_d]: dx += speed

        if dx or dy:
            self.streamOut = bytearray(json.dumps({"dx": dx, "dy": dy}).encode()) # movement stream
            self.metaOut = {"mask": 0x00, "length": len(self.streamOut), "method": 1}   # move method

        self.window.fill([50, 50, 50])
        for _, [x, y] in self.players.items():
            pg.draw.circle(self.window, [255, 255, 0], [x, y],  16)

        pg.display.flip()
        self.clock.tick(60)

GameClient().run()
