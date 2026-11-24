"""Read function names from the WebAssembly export section."""

import sys
from pathlib import Path
from io import BytesIO

stream = BytesIO(Path(sys.argv[1]).read_bytes())
assert stream.read(8) == b"\0asm\x01\0\0\0"


def varint(f):
    val = 0
    for i in range(5):
        b = f.read(1)[0]
        val |= (b & 127) << (7 * i)
        if b < 128:
            return val
    raise ValueError("malformed varint")


while kind := stream.read(1):
    data = BytesIO(stream.read(varint(stream)))
    if kind != b"\x07":
        continue
    for _ in range(varint(data)):
        name = data.read(varint(data)).decode()
        function = data.read(1) == b"\x00"
        varint(data)
        if function:
            print(name)
