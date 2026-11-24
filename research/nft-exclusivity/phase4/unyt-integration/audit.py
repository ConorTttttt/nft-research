"""Offline audit of a captured local run; native finality is unestablished."""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path
from cryptography.exceptions import InvalidSignature

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "phase2/distributed-prototype")
)
from protocol import context, verify_receipt


def action(raw):
    return "u" + base64.urlsafe_b64encode(bytes(raw)).decode().rstrip("=")


def inspect(grant, execution, domain_pin, expected_child):
    if grant is None:
        return "Pending", "missing CEL grant"
    try:
        cfg = grant["config"]
        if context(cfg).hex() != domain_pin:
            return "Invalid", "wrong title domain"
        terms = grant["terms"]
        enc = json.dumps(terms, sort_keys=True, separators=(",", ":")).encode()
        anchor = hashlib.sha256(
            b"phase4/native-candidate/v1"
            + len(enc).to_bytes(4, "big")
            + enc
            + b"".join(bytes.fromhex(k) for k in cfg["users"])
        ).hexdigest()
        if cfg["anchor"] != anchor:
            return "Invalid", "terms changed"
        if (len(cfg["keys"]), cfg["q"], cfg["e"]) != (7, 5, 2):
            return "Invalid", "unadmitted policy"
        child, to = verify_receipt(cfg, grant["proof"], cfg["users"][0], "00" * 32)
        if child != expected_child or to != cfg["users"][1]:
            return "Invalid", "wrong grant"
        if execution is None:
            return "Pending", "missing economic evidence"
        run, _ = execution
        expected = dict(
            receiver=terms["seller"],
            sources=[terms["park"]],
            amounts={terms["unit"]: terms["amount"]},
        )
        if (
            action(run["smart_agreement"]) != terms["agreement"]
            or action(run["global_definition"]) != terms["definition"]
            or action(run["code_template"]) != terms["template"]
            or run["output"]["unyt_allocation"] != [expected]
            or run["output"]["computed_values"]["nft_id"] != terms["asset"]
        ):
            return "Invalid", "execution/terms mismatch"
        return (
            "Pending",
            "matched historical allocation; no independently established native funding exclusion",
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
        AttributeError,
        OverflowError,
        InvalidSignature,
    ):
        return "Invalid", "malformed proof or invalid signature"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture")
    parser.add_argument("domain_pin")
    parser.add_argument("expected_child")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.capture).read_text().splitlines()]
    values = {r["step"]: r["value"] for r in rows if "step" in r}
    g = values.get("verified conditional grant")
    run = values.get("execute_rave")
    verdict = inspect(g, run, args.domain_pin, args.expected_child)
    print(json.dumps(verdict))
    if run and g and verdict[0] == "Pending":
        from copy import deepcopy

        changed = deepcopy(run)
        changed[0]["output"]["unyt_allocation"][0]["amounts"] = {"0": "11"}
        assert inspect(g, changed, args.domain_pin, args.expected_child)[0] == "Invalid"
        assert inspect(g, run, "00" * 32, args.expected_child)[0] == "Invalid"
        assert inspect(g, None, args.domain_pin, args.expected_child)[0] == "Pending"
        print("amount substitution, realm substitution, withheld execution checked")


if __name__ == "__main__":
    main()
