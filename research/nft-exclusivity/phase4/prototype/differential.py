"""Independent Python decoding and differential checks on a public P4L1 fixture."""

import hashlib
import itertools
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def digest(prefix, *data):
    return hashlib.sha256(prefix.encode() + b"".join(data)).digest()


def verify(pin, expected, record):
    if record is None:
        return "Pending"
    try:
        magic, policy, terms, owner, title, tag, debit, votes = struct.unpack(
            ">4s616s160s64s325sB64s325s", record
        )
        if magic != b"P4L1" or digest("p4/lab-funding/v1", policy) != pin:
            return "Invalid"
        _, _, _, buyer, seller, amount, *roster = struct.unpack(
            ">32s32s32s32s32sQ" + "32s" * 14, policy
        )
        if not amount or buyer == seller or len(set(roster)) != 14:
            return "Invalid"
        if digest("p4/grant/v1", pin, terms) != expected or tag > 1:
            return "Invalid"
        for msg, key, consent, keys, proof in (
            (digest("p4/title-reserve/v1", expected), seller, owner, roster[:7], title),
            (
                digest("p4/disposition/v1", expected, bytes([tag])),
                buyer,
                debit,
                roster[7:],
                votes,
            ),
        ):
            Ed25519PublicKey.from_public_bytes(key).verify(consent, msg)
            last = -1
            for index, signature in struct.iter_unpack(">B64s", proof):
                if not last < index < len(keys):
                    return "Invalid"
                Ed25519PublicKey.from_public_bytes(keys[index]).verify(signature, msg)
                last = index
        return ("Void", "Paid")[tag]
    except (struct.error, InvalidSignature, ValueError):
        return "Invalid"


def main(binary, fixture):
    pin, grant = (bytes.fromhex((fixture / k).read_text()) for k in ("root", "grant"))
    body = (fixture / "p4").read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "test"
        mutations = (
            body[:i] + bytes([body[i] ^ 0x80]) + body[i + 1 :]
            for i in range(0, len(body), 11)
        )
        for i, sample in enumerate(
            itertools.chain([None, body, body[:-1], body + b"0"], mutations)
        ):
            if sample is not None:
                path.write_bytes(sample)
            rust = subprocess.check_output(
                [binary, "lab", pin.hex(), grant.hex(), path], text=True
            ).strip()
            expected = "Pending" if i == 0 else "Paid" if i == 1 else "Invalid"
            assert verify(pin, grant, sample) == rust == expected
    print(json.dumps(dict(cases=i + 1, rejected=i - 1, valid_paid=1, withheld=1)))


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
