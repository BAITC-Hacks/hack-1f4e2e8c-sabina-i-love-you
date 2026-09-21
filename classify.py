#!/usr/bin/env python3
"""Print OK or DEFECT for a PNG image based on the amount of red."""

import argparse
import struct
import sys
import zlib
from pathlib import Path


def read_png_rgb(path: Path):
    """Return RGB pixels from a non-interlaced 8-bit RGB/RGBA PNG."""
    data = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        raise ValueError("supported format is PNG")
    width = height = color_type = None
    compressed = bytearray()
    offset = len(signature)
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if (bit_depth, color_type, compression, filtering, interlace) not in {(8, 2, 0, 0, 0), (8, 6, 0, 0, 0)}:
                raise ValueError("PNG must be non-interlaced 8-bit RGB or RGBA")
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
    if width is None:
        raise ValueError("invalid PNG: no IHDR chunk")
    channels = 3 if color_type == 2 else 4
    stride = width * channels
    raw = zlib.decompress(compressed)
    previous = bytearray(stride)
    pixels = []
    position = 0
    for _ in range(height):
        filter_type = raw[position]
        scanline = bytearray(raw[position + 1 : position + 1 + stride])
        position += stride + 1
        for index in range(stride):
            left = scanline[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 255
            elif filter_type == 2:
                scanline[index] = (scanline[index] + above) & 255
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + above) // 2)) & 255
            elif filter_type == 4:
                pa, pb, pc = abs(above - upper_left), abs(left - upper_left), abs(left + above - 2 * upper_left)
                predictor = left if pa <= pb and pa <= pc else above if pb <= pc else upper_left
                scanline[index] = (scanline[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError("unsupported PNG filter")
        pixels.extend(tuple(scanline[i : i + 3]) for i in range(0, stride, channels))
        previous = scanline
    return pixels


def is_red(pixel):
    red, green, blue = pixel
    return red > 180 and red > green * 1.5 and red > blue * 1.5


def main():
    parser = argparse.ArgumentParser(description="Detect a red defect in a PNG image")
    parser.add_argument("image", type=Path, help="path to a PNG file")
    parser.add_argument("--threshold", type=float, default=0.30, help="red pixel share for DEFECT")
    args = parser.parse_args()
    try:
        pixels = read_png_rgb(args.image)
        red_share = sum(is_red(pixel) for pixel in pixels) / len(pixels)
    except (OSError, ValueError, zlib.error) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
    print("DEFECT" if red_share >= args.threshold else "OK")


if __name__ == "__main__":
    main()
