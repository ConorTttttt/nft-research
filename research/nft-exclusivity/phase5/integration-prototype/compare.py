"""Matched Python buyer/seller verification. Report both roles against the same contract."""

import json
import sys
import time
from pathlib import Path
from settlement import verify

base = Path(__file__).resolve().parents[2] / "phase4"
sys.path.insert(0, str(base / "prototype"))
from differential import verify as previous

old = base / "results/public-fixture"
root, grant = [bytes.fromhex((old / f).read_text()) for f in ("root", "grant")]
b3 = (old / "p4").read_bytes()
cur = Path(sys.argv[1])
policy, terms = [
    json.loads((cur / f).read_text()) for f in ("policy.json", "terms.json")
]
proof = (cur / "proof").read_bytes()
for i in range(24):
    costs = {}
    for role in ("buyer", "seller"):
        for ver in (("p4", "p5") if i % 2 else ("p5", "p4")):
            start = time.process_time_ns()
            if ver == "p4":
                assert previous(root, grant, b3) == "Paid"
            else:
                assert verify(policy, terms, proof) == "FinalPaid"
            costs[role + "_" + ver + "_us"] = (time.process_time_ns() - start) / 1000
    print(json.dumps(costs))
