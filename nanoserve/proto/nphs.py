# nanoserve/proto/nphs.py
"""
NPHS - OSI Layer 6 Prototcol
- date: 10/2/25
- author(s): @zafflins

Packed Header: 8bit VERSION | 8bit MASK | LENGTH | METHOD
                            | 0th bit specifies how to intepret LENGTH/METHOD
                            | 0: 16bit LENGTH | 32bit METHOD - 64KB OSI Layer 2 frame-size
                            | 1: 16bit METHOD | 32bit LENGTH -  4GB OSI Layer 2 frame-size

Packed Header Fields:
VERSION (8-bit) - NPHS version.
MASK    (8-bit) - Flags for header/packet intepretation/behavior.
LENGTH  (16/32bit) - Stream length in bytes. Can be 16-bit or 32-bit depending on 0th MASK bit.
METHOD  (16/32bit) - Method/command ID. Can be 16-bit or 32-bit depending on 0th MASK bit.

NPHS Packet: VERSION|MASK|LENGTH|METHOD|STREAM
"""

import socket
from .proto import NanoProtocol

NPHS_VERSION = 0b00000001

class NPHS(NanoProtocol):
    def __init__(self) -> None:
        super().__init__("NPHS", NPHS_VERSION)

    def _packHeader(self, mask: int, length: int, method: int) -> bytes:
        if mask & 0x01:
            header = ((length & 0xFFFFFFFF) << 32) | ((method & 0xFFFF) << 16) | ((mask & 0xFF) << 8) | (NPHS_VERSION & 0xFF)
        else:
            header = ((method & 0xFFFFFFFF) << 32) | ((length & 0xFFFF) << 16) | ((mask & 0xFF) << 8) | (NPHS_VERSION & 0xFF)
        return header.to_bytes(8, byteorder="big")

    def _unpackHeader(self, header: bytes) -> list[int] | None:
        if len(header) != 8:
            print("[NPHS] invalid header size")
            return None
        h = int.from_bytes(header, "big")
        version = h & 0xFF
        mask = ((h >> 8) & 0xFF)
        if mask & 0x01:
            method = ((h >> 16) & 0xFFFF)
            length = ((h >> 32) & 0xFFFFFFFF)
        else:
            length = ((h >> 16) & 0xFFFF)
            method = ((h >> 32) & 0xFFFFFFFF)
        return [version, mask, length, method]

    def encode(self, data: dict) -> bytes:
        meta = data["meta"]
        stream = bytes(data["stream"])
        header = self._packHeader(meta["mask"], meta["length"], meta["method"])
        if len(stream) != meta["length"]:
            print(f"[NPHS] stream length mismatch during encode: (length){len(stream)} (expected){meta["length"]}")
            return b""
        return header + stream

    def decode(self, fileObject: socket.socket) -> dict:
        if fileObject.fileno() == -1:
            print("[NPHS] attempted to operate on closed socket")
            return self.protoDict([], bytes(0))
        try:
            header = fileObject.recv(8)
            if len(header) < 8:
                return self.protoDict([], bytes(0))

            h = self._unpackHeader(header)
            if h is None:
                print("[NPHS] invalid header parsed")
                return self.protoDict([], bytes(0))

            version, mask, length, method = h

            stream = b""
            while len(stream) < length:
                chunk = fileObject.recv(length - len(stream))
                if not chunk:
                    print("[NPHS] connection dropped mid-stream")
                    return self.protoDict([], bytes(0))
                stream += chunk

            return self.protoDict(h, stream) 
        except OSError as e:
            print(f"[NPHS] client connection aborted")
            return self.protoDict([], bytes(0))
        except TimeoutError:
            print(f"[NPHS] client connection timeout")
            return self.protoDict([], bytes(0))
        except BlockingIOError:
            print(f"[NPHS] client blocking error")
            return self.protoDict([], bytes(0))
        except (KeyboardInterrupt, Exception) as e:
            print(f"[NPHS] unknown exception: {e}")
            return self.protoDict([], bytes(0))
        except ConnectionRefusedError as e:
            print(f"[NPHS] client connection refused")
            return self.protoDict([], bytes(0))
        except ConnectionAbortedError as e:
            print(f"[NPHS] client connection aborted")
            return self.protoDict([], bytes(0))
        except ConnectionResetError as e:
            print(f"[NPHS] client connection reset")
            return self.protoDict([], bytes(0))
        except ConnectionError as e:
            print(f"[NPHS] client connection error")
            return self.protoDict([], bytes(0))
