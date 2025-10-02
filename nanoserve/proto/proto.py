import socket

class NanoProtocol:
    def __init__(self, proto: str, version: int) -> None:
        self.proto: str = str(proto)
        self.version: int = int(version)

    def protoDict(self, meta: int|dict|list|bytes|bytearray, stream: bytes) -> dict:
        return {"proto": self.proto, "meta": meta, "stream": stream}

    def encode(self, data: dict) -> bytes:
        """ Subclasses should expect a dict formatted like so:
            {"proto": str, "meta": list, "stream": bytes}
            or a call to the `NanoProtocol.protoDict` class method.
        """
        pass

    def decode(self, fileObject: socket.socket) -> dict:
        """ Subclasses should return a dict formatted like so:
            {"proto": str, "meta": list, "stream": bytes}
            or simply return a call to the `NanoProtocol.protoDict` class method.
        """
        pass
    