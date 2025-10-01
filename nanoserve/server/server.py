import sys, types
import socket, selectors
from nanoserve.proto.proto import NanoProtocol

NANO_SERVER_METHOD_MAX: int = 255

class NanoSession:
    def __init__(self, fileObject: socket.socket, address: tuple[str, int], blocking: bool=False) -> None:
        self.dataIn: dict = {}
        self.dataOut: dict = {}
        self.fileObject: socket.socket = fileObject
        self.fileObject.setblocking(blocking)
        self.address: tuple[str, int] = address

    def write(self, stream: bytes|bytearray) -> None:
        sent = 0
        size = len(stream)
        while sent < size:
            sent += self.fileObject.send(stream[sent:])

def NanoServerMethod(methodID: int) -> callable:
    def wrapper(method: callable):
        setattr(method, "methodID", methodID)
        return method
    return wrapper

class NanoServer:
    def __init__(self, name: str, host: str, port: int, proto: NanoProtocol) -> None:
        self.name: str = str(name)
        self.host: str = str(host)
        self.port: int = int(port)
        self.proto: NanoProtocol = proto()
        self.address: tuple[str, int] = (self.host, self.port)

        self.timeout: int = 0
        self.running: bool = True
        
        self.serverObjects: list[NanoSession] = []
        self.serverMethods: list[callable] = [None] * NANO_SERVER_METHOD_MAX
        self.selector: selectors.DefaultSelector = selectors.DefaultSelector()
        self.fileObject: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def _register_methods(self) -> bool:
        for _name, _attr in self.__class__.__dict__.items():
            if callable(_attr) and hasattr(_attr, "methodID"):
                methodID = _attr.methodID
                if 0 <= methodID < NANO_SERVER_METHOD_MAX:
                    if self.serverMethods[methodID] is not None: continue
                    self.serverMethods[methodID] = _attr
                    print(f"[WaveServer] registered server method: {_attr.__name__} {methodID}")
                else:
                    print(f"[WaveServer] failed to register server method: {_attr.__name__} {methodID}")
                    return False
        return True


    def connect_hook(self, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on connect' functionality """
        pass
    def _connect(self, key: selectors.SelectorKey, mask: int) -> None:
        session = NanoSession(*key.fileobj.accept())
        self.selector.register(session.fileObject, selectors.EVENT_READ | selectors.EVENT_WRITE, data=session)
        self.serverObjects.append(session)
        print(f"SERVER CONNECTION: {session.address}")
        self.connect_hook(session)

    def _reconnect(self) -> None: pass
    
    def disconnect_hook(self, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on disconnect' functionality """
        pass
    def _disconnect(self, session: NanoSession) -> None:
        self.selector.unregister(session.fileObject)
        self.serverObjects.remove(session)
        self.disconnect_hook(session)
        session.fileObject.close()
        print(f"SERVER SESSION DISCONNECTED: {session.address}")

    def read_hook(self, request: dict, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on read' functionality """
        pass
    def _read(self, session: NanoSession) -> None:
        request = self.proto.decode(session.fileObject)
        if len(request):
            print(f"SERVER READ: {request}")
            kind, method, size, stream = request.values()
            serverMethod = self.serverMethods[method]
            if callable(serverMethod): serverMethod(self, request, session)
            self.read_hook(request, session)
        else: self._disconnect(session)


    def write_hook(self, stream: bytes|bytearray, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on write' functionality """
        pass
    def _write(self, session: NanoSession) -> None:
        if len(session.dataOut):
            stream = self.proto.encode(session.dataOut)
            session.write(stream)
            print(f"SERVER WRITE: {stream}")
            self.write_hook(stream, session)
            session.dataOut = {}

    # TODO: server session connection validation before r/w service
    # TODO: heartbeat?
    def _service(self, key: selectors.SelectorKey, mask: int) -> None:
        session = key.data
        fileObj = key.fileobj
        if (mask & selectors.EVENT_READ) == selectors.EVENT_READ:
            self._read(session)
        if (mask & selectors.EVENT_WRITE) == selectors.EVENT_WRITE:
            self._write(session)

    def startup_hook(self) -> None:
        """ Subclasses should override this method for 'on startup' functionality. """
        pass
    def _startup(self) -> None:
        if self._register_methods():
            self.fileObject.bind(self.address)
            self.fileObject.listen()
            self.fileObject.setblocking(False)
            self.selector.register(self.fileObject, selectors.EVENT_READ, data=None)
            self.startup_hook()
            print(f"SERVER STARTED: {self.name} {self.address}")

    def shutdown_hook(self) -> None:
        """ Subclasses should override this method for 'on shutdown' functionality. """
        pass
    def _shutdown(self) -> None:
        self.fileObject.close()
        self.selector.close()
        self.running = False
        self.shutdown_hook()
        print(f"SERVER SHUT DOWN: {self.name} {self.address}")

    def main(self) -> None:
        """ Subclasses should override this method for 'main-loop' functionality. """
        pass
    def run(self) -> None:
        self._startup()
        try:
            while self.running:
                self.main()
                events = self.selector.select(timeout=self.timeout)
                for key, mask in events:
                    if key.data == None:
                        self._connect(key, mask)
                    else:
                        self._service(key, mask)
            else: self._shutdown()
        except (OSError):
            print("SERVER OS ERROR")
            self._shutdown()
        except (TimeoutError):
            print("SERVER TIMEOUT ERROR")
            self._shutdown()
        except (KeyboardInterrupt):
            self._shutdown()
