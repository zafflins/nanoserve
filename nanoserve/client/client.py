import sys, types
import socket, selectors, threading
from nanoserve.proto import NanoProtocol

class NanoClient:
    def __init__(self, proto: NanoProtocol) -> None:
        self.host: str = None
        self.port: int = None
        self.dataIn: dict = {}
        self.dataOut: dict = {}
        self.proto: NanoProtocol = proto()
        self.address: tuple[str, int] = None

        self.running: bool = True

        self.selector: selectors.DefaultSelector = selectors.DefaultSelector()
        self.fileObject: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host: str, port: int, blocking: bool=False) -> None:
        self.host = str(host)
        self.port = int(port)
        self.address = (self.host, self.port)
        self.fileObject.connect(self.address)
        self.fileObject.setblocking(blocking)
        self.selector.register(self.fileObject, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

    def reconnect(self, host: str, port: int) -> None: pass
    
    def disconnect(self) -> None:
        print("CLIENT DISCCONECT")
        self.fileObject.close()
        self.address = None
        self.host = None
        self.port = None

    def _service(self, key: selectors.SelectorKey, mask: int) -> None:
        fileObj = key.fileobj
        if (mask & selectors.EVENT_READ) == selectors.EVENT_READ:
            self.read()
        if (mask & selectors.EVENT_WRITE) == selectors.EVENT_WRITE:
            self.write()

    def read(self) -> None:
        request = self.proto.decode(self.fileObject)
        print(f"CLIENT READ: {request}")
        if not len(request): self._disconnect()

    def write(self) -> None:
        if not len(self.dataOut): return

        stream = self.proto.encode(self.dataOut)
        sent = 0
        size = len(stream)
        while sent < size:
            sent += self.fileObject.send(stream[sent:])

    def main(self) -> None:
        """ Subclasses should override this method for 'main-loop' functionality. """
        pass

    def run(self) -> None:
        try:
            while self.running:
                self.main()
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self._service(key, mask)
            else: self._shutdown()
        except (KeyboardInterrupt):
            self.disconnect()
