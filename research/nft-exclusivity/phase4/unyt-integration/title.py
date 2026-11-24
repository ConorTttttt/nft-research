"""Certify a conditional test title tied to a real local parked-spend action."""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "phase2/distributed-prototype")
)
from lab import Lab, pub, slot
from protocol import receipt, verify_receipt, context


def certify(terms):
    encoded = json.dumps(terms, sort_keys=True, separators=(",", ":")).encode()

    def anchor(cfg):
        return hashlib.sha256(
            b"phase4/native-candidate/v1"
            + len(encoded).to_bytes(4, "big")
            + encoded
            + b"".join(bytes.fromhex(k) for k in cfg["users"])
        ).hexdigest()

    with Lab(7, 5, 2, anchor_for=anchor) as lab:
        proposal = lab.make(0)
        proof = receipt(proposal, lab.votes(range(5), proposal), 0)
        child, to = verify_receipt(lab.config, proof, pub(lab.owner), slot(0))
        return dict(
            terms=terms,
            domain=context(lab.config).hex(),
            config=lab.config,
            proof=proof,
            conditional_child=child,
            recipient=to,
        )
