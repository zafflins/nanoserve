import socket

class NanoProtocol:
    def __init__(self, version: str) -> None:
        self.version: str = str(version)

    def encode(self, data: dict) -> bytes: pass
    def decode(self, fileObject: socket.socket) -> dict: pass
    