#!/usr/bin/env python3
"""Create the two small PNG samples required by the exercise."""

import struct
import zlib
from pathlib import Path


def write_solid_png(path: str, color: tuple[int, int, int]):
    width = height = 128
    raw = b"".join(b"\0" + bytes(color) * width for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


write_solid_png("ok.png", (35, 150, 85))
write_solid_png("defect.png", (220, 35, 35))
