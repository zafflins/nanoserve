# NPHS/impl.py

from .proto import NanoProtocol
from nanoserve.server import NanoSession
import socket

PHS_VERSION = "1.0.0"

# === NPHS REQUEST KINDS ===
PHS_CONNECT: int       = 0x01
PHS_HEARTBEAT: int     = 0x02
PHS_RECONNECT: int     = 0x03
PHS_DISCONNECT: int    = 0x04

# === NPHS MAXIMUMS ===
PHS_BUFFER_MAX: int         = 0xFFF
PHS_METHOD_ID_MAX: int      = 0xFF
PHS_REQUEST_KIND_MAX: int   = 0xFF

class NPHS(NanoProtocol):
    def __init__(self) -> None:
        super().__init__(PHS_VERSION)

    def _buildHeader(self, kind: int, method: int, size: int) -> bytes:
        if not (0 <= kind <= PHS_REQUEST_KIND_MAX):
            print("[NPHS] invalid header kind")
            return None
        if not (0 <= method <= PHS_METHOD_ID_MAX):
            print("[NPHS] invalid header method")
            return None
        if not (0 < size <= PHS_BUFFER_MAX):
            print("[NPHS] invalid header size")
            return None
        header = ((size & 0xFFFF) << 16) | ((method & 0xFF) << 8) | (kind & 0xFF)
        return header.to_bytes(4, byteorder="big")

    def _parseHeader(self, header: bytes) -> tuple[int, int, int] | None:
        if len(header) != 4:
            print("[NPHS] invalid header size")
            return {}
        buffer = int.from_bytes(header, "big")
        kind   = buffer & 0xFF
        method = (buffer >> 8) & 0xFF
        size   = (buffer >> 16) & 0xFFFF
        return kind, method, size

    # validate request kind + method for u8 overflow
    def encode(self, data: dict) -> bytes:
        # data = {"kind": int, "method": int, "size": int "stream": bytearray}
        header = self._buildHeader(data["kind"], data["method"], data["size"])
        if header is None:
            print(f"[NPHS] failed to build header: (header){header}")
            return {}
        if len(data["stream"]) != data["size"]:
            print(f"[NPHS] stream size mismatch in build_request: (size){len(data["stream"])} (expected){data["size"]}")
            return {}
        
        return header + data["stream"]

    def decode(self, fileObject: socket.socket) -> dict:
        if fileObject.fileno() == -1:
            print("[NPHS] attempted to operate on closed socket")
            return (PHS_DISCONNECT, 0, 0, b"\0")
        try:
            header = fileObject.recv(4)
            if len(header) < 4:
                return {}

            parsed = self._parseHeader(header)
            if parsed is None:
                print("[NPHS] invalid header parsed")
                return {}
            kind, method, size = parsed

            body = bytearray()
            while len(body) < size:
                chunk = fileObject.recv(size - len(body))
                if not chunk:
                    print("[NPHS] connection dropped mid-stream")
                    return (PHS_DISCONNECT, 0, 0, b"\0")
                body += chunk

            return {"kind": kind, "method": method, "size": size, "stream": bytes(body)}
        except OSError as e:
            print(f"[NPHS] client connection aborted")
            return {}
        except TimeoutError:
            print(f"[NPHS] client connection timeout")
            return (PHS_DISCONNECT, 0, 0, b"\0")
        except BlockingIOError:
            print(f"[NPHS] client blocking error")
            return (PHS_DISCONNECT, 0, 0, b"\0")
        except (KeyboardInterrupt, Exception) as e:
            print(f"[NPHS] unknown exception: {e}")
            return (PHS_DISCONNECT, 0, 0, b"\0")
        except ConnectionRefusedError as e:
            print(f"[NPHS] client connection refused")
            return {}
        except ConnectionAbortedError as e:
            print(f"[NPHS] client connection aborted")
            return {}
        except ConnectionResetError as e:
            print(f"[NPHS] client connection reset")
            return {}
        except ConnectionError as e:
            print(f"[NPHS] client connection error")
            return {}
