"""Summarise within-profile trials, excluding iteration zero."""

import json
import sys
from collections import defaultdict
from statistics import median

groups = defaultdict(list)
for line in open(sys.argv[1]):
    row = json.loads(line)
    if row.get("iteration", 0) > 0:
        groups[row["n"], row["width"], row["mode"], row["delay_ms"]].append(row)
for k, rows in sorted(groups.items()):
    t = [r["elapsed_ms"] for r in rows]
    print(
        k,
        "median [min,max]",
        *[round(v, 2) for v in (median(t), min(t), max(t))],
        "buyer B",
        rows[0]["one_buyer_bytes"],
        "worker wire B",
        round(median(r["tcp_payload_bytes"] for r in rows)),
        "verify us",
        round(median(r["verify_us"] for r in rows)),
        "sign us",
        round(median(r["sign_us"] for r in rows))
    )
