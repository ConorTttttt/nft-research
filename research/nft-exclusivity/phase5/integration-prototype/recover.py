"""Supplied independent pins authenticate one archived laboratory proof."""

import json
import sys
from pathlib import Path
from settlement import verify, verify_onward

root = Path(sys.argv[1])
policy = json.loads((root / "policy.json").read_bytes())
terms = json.loads((root / "terms.json").read_bytes())
proof = (root / "proof").read_bytes()
assert verify(policy, terms, None, unavailable=True) == "UnavailableEvidence"
assert verify(policy, terms, proof) == "FinalPaid"
assert verify(policy, dict(terms, price=11), proof) == "Invalid"
assert verify(policy, terms, proof, profile="native") == "Invalid"
print(
    "Archived proof recovered FinalPaid after producer exit; explicit failed retrieval UnavailableEvidence."
)

transfer = json.loads((root / "onward.json").read_bytes())
assert verify_onward(policy, terms, proof, transfer)
transfer[0] = "00" * 32
assert not verify_onward(policy, terms, proof, transfer)
print("Recovered onward signature and quorum verified; substituted recipient rejected.")
