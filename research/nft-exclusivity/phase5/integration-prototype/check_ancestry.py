"""Conformance checks for historical payer ancestry; five-record audit is a separate dependency."""

import json
import subprocess
import sys
import time
from pathlib import Path

rows = [json.loads(l) for l in Path(sys.argv[1]).read_text().splitlines()]
v = {r["step"]: r["value"] for r in rows if "step" in r}
terms = v["verified conditional grant"]["terms"]
args = [
    terms["park"],
    terms["buyer"],
    terms["dna"],
    v["historical record accept"]["id"],
]


def call(pins, path):
    return subprocess.run(
        [sys.argv[2], *pins], input=json.dumps(path), capture_output=True, text=True
    )


path = v["payer ancestry"]
start = time.perf_counter_ns()
r = call(args, path)
assert r.returncode == 0, r.stderr
print(
    r.stdout.strip(), "wall_us including CLI", (time.perf_counter_ns() - start) / 1000
)
for bad in (path[:-1], path[1:], list(reversed(path))):
    assert call(args, bad).returncode
assert call([*args[:2], "other-DNA", args[3]], path).returncode
assert call([*args[:3], v["historical record receipt"]["id"]], path).returncode
print("Three incomplete or reordered prefixes and two substituted roots rejected.")
print(
    "Seller retrieval wall_us",
    next(r["wall_us"] for r in rows if r.get("step") == "payer ancestry"),
)
