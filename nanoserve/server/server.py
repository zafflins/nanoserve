import sys, types
import socket, selectors

from .router import NanoRouter
from .session import NanoSession
from ..proto.proto import NanoProtocol

class NanoServer:
    def __init__(self, name: str, host: str, port: int, proto: NanoProtocol, router: NanoRouter) -> None:
        self.name: str = str(name)
        self.host: str = str(host)
        self.port: int = int(port)
        self.router: NanoRouter = router
        self.proto: NanoProtocol = proto()
        self.address: tuple[str, int] = (self.host, self.port)

        self.timeout: int = 0
        self.running: bool = True
        
        self.sessions: list[NanoSession] = []
        self.selector: selectors.DefaultSelector = selectors.DefaultSelector()
        self.fileObject: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
    def connect_hook(self, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on connect' functionality """
        pass
    def _connect(self, key: selectors.SelectorKey, mask: int) -> None:
        session = NanoSession(len(self.sessions), *key.fileobj.accept())
        self.selector.register(session.fileObject, selectors.EVENT_READ | selectors.EVENT_WRITE, data=session)
        self.sessions.append(session)
        self.connect_hook(session)

    def _reconnect(self) -> None: pass
    
    def disconnect_hook(self, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on disconnect' functionality """
        pass
    def _disconnect(self, session: NanoSession) -> None:
        self.selector.unregister(session.fileObject)
        self.sessions.remove(session)
        self.disconnect_hook(session)
        session.fileObject.close()

    def read_hook(self, request: dict, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on read' functionality """
        pass
    def _read(self, session: NanoSession) -> None:
        request = self.proto.decode(session.fileObject)
        if len(request["stream"]):
            self.router.dispatch(request, session)
            self.read_hook(request, session)
        else: self._disconnect(session)


    def write_hook(self, stream: bytearray, session: NanoSession) -> None:
        """ Subclasses should override this method for 'on write' functionality """
        pass
    def _write(self, session: NanoSession) -> None:
        if len(session.metaOut) and len(session.streamOut):
            stream = self.proto.encode(self.proto.protoDict(session.metaOut, session.streamOut))
            session.write(stream)
            self.write_hook(stream, session)
            session.streamOut.clear()
            session.metaOut.clear()

    # TODO: server session connection validation before r/w service
    # TODO: heartbeat?
    def _service(self, key: selectors.SelectorKey, mask: int) -> None:
        if (mask & selectors.EVENT_READ) == selectors.EVENT_READ: self._read(key.data)
        if (mask & selectors.EVENT_WRITE) == selectors.EVENT_WRITE: self._write(key.data)

    def startup_hook(self) -> None:
        """ Subclasses should override this method for 'on startup' functionality. """
        pass
    def _startup(self) -> None:
        self.fileObject.bind(self.address)
        self.fileObject.listen()
        self.fileObject.setblocking(False)
        self.selector.register(self.fileObject, selectors.EVENT_READ, data=None)
        self.startup_hook()

    def shutdown_hook(self) -> None:
        """ Subclasses should override this method for 'on shutdown' functionality. """
        pass
    def _shutdown(self) -> None:
        self.fileObject.close()
        self.selector.close()
        self.running = False
        self.shutdown_hook()

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
            self._shutdown()
        except (TimeoutError):
            self._shutdown()
        except (KeyboardInterrupt):
            self._shutdown()
