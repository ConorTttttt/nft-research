"""Two disjoint, healthy groups have the same genesis rights and distinct keys."""

import json
import time
from cryptography.exceptions import InvalidSignature
from lab import Lab, slot, pub, receipt, verify_receipt, verify_reset

with Lab(7, 5, 2) as old, Lab(7, 5, 2, participants=(old.owner, old.buyers)) as new:
    assert old.config["anchor"] == new.config["anchor"]
    assert set(old.config["keys"]).isdisjoint(new.config["keys"])
    proofs = []
    for i, lab in enumerate((old, new)):
        p = lab.make(1, buyer=i, mode="tree")
        proofs.append(receipt(p, lab.votes(range(5), p), 0))
    outcomes = [
        verify_receipt(lab.config, proof, pub(old.owner), slot(1))
        for lab, proof in zip((old, new), proofs)
    ]
    assert outcomes[0] != outcomes[1]
    try:
        verify_receipt(old.config, proofs[1], pub(old.owner), slot(1))
    except InvalidSignature:
        pass
    else:
        raise AssertionError("wrong roster accepted")
    print(
        json.dumps(
            dict(
                test="administrative reassignment of same unresolved input",
                valid_under_own_roster=2,
                valid_under_pinned_old_roster=1,
            )
        )
    )
    for i in range(6):
        parent = slot(i + 20)
        old.votes([0, 1], old.make(i + 20, buyer=0))
        old.votes([2, 3], old.make(i + 20, buyer=1))
        start = time.perf_counter_ns()
        reports = old.closes(parent)
        child = verify_reset(old.config, parent, reports)
        for result, _ in old.fan(
            range(7), dict(op="reset", parent=parent, reports=reports)
        ):
            assert result["ok"] == child
        print(
            json.dumps(
                dict(
                    test="two partial candidates: close + verify + install at seven",
                    trial=i,
                    elapsed_ms=(time.perf_counter_ns() - start) / 1e6,
                )
            )
        )
