"""Verify signed historical observations against an independently selected grant."""

import argparse
import copy
import json
import subprocess
from pathlib import Path

import msgpack

from audit import action, inspect


class InvalidRecord(ValueError):
    pass


def require(condition, why):
    if not condition:
        raise InvalidRecord(why)


def audit_history(values, domain_pin, child, checker):
    grant = values.get("verified conditional grant")
    status, reason = inspect(grant, None, domain_pin, child)
    if status == "Invalid" or grant is None:
        return status, reason
    terms = grant["terms"]
    roles = {
        "funding": "seller",
        "accept": "buyer",
        "park": "buyer",
        "execution": "seller",
        "receipt": "seller",
    }
    decoded = {}
    items = {}
    try:
        for name, role in roles.items():
            wrapper = values.get("historical record " + name)
            if wrapper is None:
                return "Pending", "missing historical record " + name
            items[name] = wrapper
            record = wrapper["record"]
            proc = subprocess.run(
                [checker, wrapper["id"], terms[role]],
                input=json.dumps(record),
                text=True,
                capture_output=True,
                check=False,
            )
            require(
                proc.returncode == 0,
                name + " failed action, author, signature or entry verification",
            )
            data = record["signed_action"]["hashed"]["content"]["data"]
            require(
                data["type"] == ("CreateLink" if name == "park" else "Create"),
                "wrong action variant",
            )
            decoded[name] = msgpack.unpackb(bytes.fromhex(proc.stdout.strip()))
        require(items["park"]["id"] == terms["park"], "different parked source")
        park_data = items["park"]["record"]["signed_action"]["hashed"]["content"][
            "data"
        ]
        require(
            action(park_data["base_address"]) == terms["agreement"],
            "different park agreement",
        )
        amount = {terms["unit"]: terms["amount"]}
        funding, accept = decoded["funding"], decoded["accept"]
        require(
            funding["committed_amount"] == {terms["unit"]: "-" + terms["amount"]},
            "different seed amount",
        )
        require(
            action(funding["counterparty"]) == terms["buyer"], "different funded buyer"
        )
        require(
            action(accept["commitment"]) == items["funding"]["id"],
            "different seed commitment",
        )
        require(
            accept["accepted_amount"] == amount
            and action(accept["counterparty"]) == terms["seller"],
            "different seed credit",
        )
        require(
            accept["ledger"]["balance"] == amount, "different historical funded balance"
        )
        for row in (funding, accept):
            require(
                action(row["global_definition"]) == terms["definition"],
                "different funding rules",
            )
        require(
            action(decoded["park"][4]) == terms["definition"], "different parking rules"
        )
        require(
            decoded["park"][:2] == ["buyer_spender", amount],
            "different parked role or amount",
        )
        verdict, explanation = inspect(
            grant, [decoded["execution"], None], domain_pin, child
        )
        if verdict == "Invalid":
            return verdict, explanation
        receipt = decoded["receipt"]
        require(
            receipt["source"] == {"ExecutionInstance": items["execution"]["id"]},
            "different collection source",
        )
        require(receipt["receipt_amount"] == amount, "different collected amount")
        require(
            [action(k) for k in receipt["counterparty"]] == [terms["buyer"]],
            "different counterparty",
        )
        return (
            "Pending",
            "signed historical records verified; exclusive native funding remains unestablished",
        )
    except (KeyError, TypeError, ValueError, IndexError, OverflowError) as err:
        return "Invalid", str(err)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("checker")
    ap.add_argument("domain")
    ap.add_argument("child")
    args = ap.parse_args()
    rows = [json.loads(s) for s in Path(args.capture).read_text().splitlines()]
    values = {r["step"]: r["value"] for r in rows if "step" in r}

    def run(v):
        return audit_history(v, args.domain, args.child, args.checker)

    result = run(values)
    print(json.dumps(result))
    if result != (
        "Pending",
        "signed historical records verified; exclusive native funding remains unestablished",
    ):
        raise SystemExit(1)
    for name in ("funding", "accept", "park", "execution", "receipt"):
        field = "historical record " + name
        edited = copy.deepcopy(values)
        edited[field]["record"]["signed_action"]["signature"][0] ^= 1
        assert run(edited)[0] == "Invalid"
        omitted = dict(values)
        del omitted[field]
        assert run(omitted)[0] == "Pending"
    edited = copy.deepcopy(values)
    edited["historical record receipt"]["record"]["entry"]["Present"]["entry"][0] ^= 1
    assert run(edited)[0] == "Invalid"
    print(
        "Five altered signatures and an altered receipt body rejected; five withheld records unresolved."
    )


if __name__ == "__main__":
    main()
