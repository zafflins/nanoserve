import socket

class NanoSession:
    def __init__(self, sessionID: int, fileObject: socket.socket, address: tuple[str, int], blocking: bool=False) -> None:
        self.metaOut: dict|list|int|str = []
        self.streamOut: bytes|bytearray = bytearray(0)

        self.fileObject: socket.socket = fileObject
        self.fileObject.setblocking(blocking)
        self.address: tuple[str, int] = address
        self.id: int = sessionID

    def write(self, stream: bytearray) -> None:
        sent = 0
        size = len(stream)
        while sent < size:
            sent += self.fileObject.send(stream[sent:])
