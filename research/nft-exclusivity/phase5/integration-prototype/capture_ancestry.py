"""Extend the cooperative Phase 4 run with a read-only historical audit from seller cell."""

import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import time

base = Path(__file__).resolve().parents[2] / "phase4/unyt-integration"
sys.path.insert(0, str(base))
import transfer

ordinary = transfer.exercise


def observed(root, cli, release, roles, network, record):
    log = io.StringIO()
    parked_id = None

    def observed_cli(*args):
        nonlocal parked_id
        result = cli(*args)
        if len(args) == 10 and args[1] == "zome-call" and result.returncode == 0:
            fn = args[-2]
            if fn == "create_parked_spend":
                parked_id = transfer.h64(json.loads(result.stdout.splitlines()[-1]))
            if parked_id and fn in ("create_parked_spend", "create_receipt_from_rave"):
                for reader in ("p4-buyer", "p4-progenitor"):
                    read = cli(
                        *args[:5],
                        reader,
                        *args[6:8],
                        "get_parked_link_standing",
                        json.dumps(parked_id),
                    )
                    value = (
                        json.loads(read.stdout.splitlines()[-1])
                        if read.returncode == 0
                        else {"read_error": read.stdout[-500:]}
                    )
                    print(
                        json.dumps(
                            dict(
                                step="park standing",
                                after=fn,
                                reader=reader,
                                value=value,
                            )
                        )
                    )
        return result

    with contextlib.redirect_stdout(log):
        ordinary(root, observed_cli, release, roles, network, record)
    print(log.getvalue(), end="")
    rows = {
        r["step"]: r["value"]
        for line in log.getvalue().splitlines()
        if "step" in (r := json.loads(line))
    }
    terms = rows["verified conditional grant"]["terms"]
    cursor = terms["park"]
    path = []
    start = time.perf_counter_ns()
    while cursor and len(path) < 256:
        r = cli(
            "client",
            "zome-call",
            "--piped",
            "--port",
            "43995",
            "p4-progenitor",
            terms["dna"],
            "transactor",
            "hdk_must_get_action",
            json.dumps(cursor),
        )
        if r.returncode:
            raise RuntimeError(r.stdout[-800:])
        action = json.loads(r.stdout.splitlines()[-1])
        path.append(action)
        prev = action["hashed"]["content"]["header"]["prev_action"]
        cursor = transfer.h64(prev) if prev else None
    assert cursor is None
    print(
        json.dumps(
            dict(
                step="payer ancestry",
                value=path,
                wall_us=(time.perf_counter_ns() - start) / 1000,
            )
        )
    )


transfer.exercise = observed
runpy.run_path(str(base / "probe.py"), run_name="__main__")
