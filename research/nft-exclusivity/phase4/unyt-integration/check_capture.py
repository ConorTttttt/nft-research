"""Regression checks on a local capture. Fixture pins come from the same run."""

import json
import sys
from decimal import Decimal
from pathlib import Path
from audit import inspect

rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
values = {r["step"]: r["value"] for r in rows if "step" in r}
grant = values["verified conditional grant"]
args = grant["domain"], grant["conditional_child"]
run = values["execute_rave"]
assert inspect(grant, run, *args)[0] == "Pending"
assert inspect(grant, run, "00" * 32, args[1])[0] == "Invalid"
assert inspect(grant, None, *args)[0] == "Pending"
assert values["independent acceptance"]["status"] == "Pending"
assert isinstance(values["create_receipt_from_rave"], str)
assert isinstance(values["create_reclaim_balance"], str)
ledgers = [r["value"] for r in rows if r.get("step") == "get_ledger"]
assert Decimal(ledgers[-1]["balance"]["0"]) - Decimal(ledgers[-2]["balance"]["0"]) == 10
assert values["get_transaction"]["details"]["RAVE"]["output"] == run[0]["output"]
run[0]["output"]["unyt_allocation"][0]["amounts"] = {"0": "11"}
assert inspect(grant, run, *args)[0] == "Invalid"
print(
    "Collected ten units, fetched matching RAVE in buyer cell, separate rejection/reclaim succeeded. Native finality Pending."
)
