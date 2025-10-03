import sys, types
import socket, selectors, threading

from nanoserve.proto import NanoProtocol

class NanoClient:
    def __init__(self, proto: NanoProtocol) -> None:
        self.host: str = None
        self.port: int = None
        self.dataIn: dict = {}
        self.proto: NanoProtocol = proto()
        self.address: tuple[str, int] = None

        self.metaOut: dict|list|int|str = []
        self.streamOut: bytes|bytearray = bytearray(0)

        self.running: bool = True
        self.connected: bool = False

        self.selector: selectors.DefaultSelector = selectors.DefaultSelector()
        self.fileObject: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host: str, port: int, blocking: bool=False) -> None:
        self.host = str(host)
        self.port = int(port)
        self.address = (self.host, self.port)
        self.fileObject.connect(self.address)
        self.fileObject.setblocking(blocking)
        self.selector.register(self.fileObject, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)
        self.connected = True

    def reconnect(self, host: str, port: int) -> None: pass
    
    def disconnect(self) -> None:
        try:
            self.selector.unregister(self.fileObject)
            self.fileObject.close()
            self.connected = False
            self.address = None
            self.host = None
            self.port = None
        except (ValueError): pass   # unregistering a closed fileObject raises a value error

    def _service(self, mask: int) -> None:
        if (mask & selectors.EVENT_READ) == selectors.EVENT_READ:
            self.read()
        if (mask & selectors.EVENT_WRITE) == selectors.EVENT_WRITE:
            self.write()

    def read_hook(self, request: dict) -> None:
        pass
    def read(self) -> None:
        request = self.proto.decode(self.fileObject)
        if not len(request["stream"]): self.disconnect()
        else: self.read_hook(request)

    def write(self) -> None:
        if not len(self.metaOut) or not len(self.streamOut): return
        stream = self.proto.encode(self.proto.protoDict(self.metaOut, self.streamOut))
        sent = 0
        size = len(stream)
        while sent < size:
            sent += self.fileObject.send(stream[sent:])
        self.streamOut.clear()
        self.metaOut.clear()

    def main(self) -> None:
        """ Subclasses should override this method for 'main-loop' functionality. """
        pass

    def run(self) -> None:
        try:
            while self.running:
                self.main()
                if self.connected:
                    events = self.selector.select(timeout=None)
                    for _, mask in events:
                        self._service(mask)
            else: self.disconnect()
        except (KeyboardInterrupt):
            self.disconnect()
