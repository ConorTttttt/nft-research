"""One-generation laboratory grant. Clients pin the entire policy out of band."""

from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "phase2/distributed-prototype")
)
from protocol import H, check, context, integer, raw, require, verify_receipt

SCRIPT = bytes.fromhex(
    "d85a559daa87981e6d4dfc2d03655b0c44cb68624ccec83fdae3b67783aac6fb"
)
NETWORK = H(b"phase3/test-payment-network")
PREFIX = b"p3/single-unit-grant/v1"
PRICE = 10


@dataclass(frozen=True)
class Profile:
    issuer: str
    network: bytes = NETWORK

    def anchor(self, config):
        require(len(self.network) == 32, "network width")
        require(
            (len(config["keys"]), config["q"], config["e"]) in ((7, 5, 2), (8, 6, 3)),
            "unsupported roster",
        )
        users = config["users"]
        require(len(users) == 4 and len(set(users)) == 4, "role roster")
        return H(
            PREFIX,
            self.network,
            raw(self.issuer),
            SCRIPT,
            integer(PRICE),
            integer(16384),
            *(raw(k) for k in users)
        ).hex()

    def commitment(self, config, parent, proof):
        require(config["anchor"] == self.anchor(config), "genesis profile")
        require(int.from_bytes(raw(parent)) < 16384, "outside lab genesis")
        require(proof["mode"] == "flat" and proof["n"] == 1, "single-parent grant")
        seller, buyer = config["users"][:2]
        child, to = verify_receipt(config, proof, seller, parent)
        require(to == buyer, "grant recipient")
        return H(PREFIX, b"/sale", context(config), raw(parent), raw(child))

    def exercise(self, config, parent, proof, evidence):
        sale = self.commitment(config, parent, proof)
        outcome, signature = evidence
        require(outcome in ("paid", "void"), "terminal outcome")
        check(self.issuer, signature, terminal_message(sale, outcome))
        index = 1 if outcome == "paid" else 0
        return (
            H(PREFIX, b"/child", sale, outcome.encode()).hex(),
            config["users"][index],
        )


def terminal_message(sale, outcome):
    return PREFIX + b"/terminal/" + sale + outcome.encode()
