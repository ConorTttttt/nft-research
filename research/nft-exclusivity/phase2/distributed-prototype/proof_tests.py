"""Availability, paths, invalid batches and delayed competing votes through real workers."""

from copy import deepcopy
from cryptography.exceptions import InvalidSignature
import json
from lab import Lab, denied, pub, slot
from protocol import context, proposal, receipt, statement, verify_receipt, verify_reset


def reject(fn):
    try:
        fn()
    except (ValueError, InvalidSignature):
        return
    raise AssertionError("unexpected acceptance")


with Lab(7, 5, 2, (0, 1)) as lab:
    p = lab.make(80, 7, mode="tree")
    votes = lab.votes(range(5), p)
    d = statement(context(lab.config), "tree", p["moves"])
    # Collector failed before dissemination. Complete body available from an honest signer.
    assert "error" in lab.rpc(6, dict(op="fetch", digest=d.hex()))[0]
    recovered = lab.rpc(2, dict(op="fetch", digest=d.hex()))[0]["ok"]
    # Re-collect at the original signers, then independently verify all seven paths.
    again = lab.votes(range(5), recovered)
    for i in range(7):
        leaf = receipt(recovered, again, i)
        verify_receipt(lab.config, leaf, pub(lab.owner), slot(80 + i))
        altered = deepcopy(leaf)
        altered["path"][0] = "00" * 32
        reject(
            lambda: verify_receipt(lab.config, altered, pub(lab.owner), slot(80 + i))
        )
    assert len(lab.votes(range(7), lab.make(86, 3, mode="tree"))) < 5
    # Partial overlap must not reserve the non-conflicting tail.
    assert len(lab.votes(range(7), lab.make(87, 2, mode="tree"))) >= 5
    invalid = deepcopy(p)
    invalid["moves"][1] = invalid["moves"][0]
    assert not lab.votes(range(7), invalid)
    fake = proposal(
        lab.config, lab.buyers[0], [(slot(100), pub(lab.buyers[1]))], "tree"
    )
    assert not lab.votes(range(7), fake)
    # Delivery times are finite but unordered. Byzantine voters reply on both sides.
    proposals = [lab.make(101, buyer=i, mode="tree") for i in range(2)]
    scheduled = [(i, j, ((i * 29 + j * 47) % 83)) for i in range(7) for j in range(2)]
    replies = [
        (j, lab.pool.submit(lab.rpc, i, dict(op="vote", p=proposals[j]), delay))
        for i, j, delay in scheduled
    ]
    collected = [[], []]
    for j, f in replies:
        r, _ = f.result()
        if "ok" in r:
            collected[j].append(r["ok"]["vote"])
    assert sum(len(v) >= 5 for v in collected) <= 1
    # Only two reachable signers cannot create finality.
    assert len(lab.votes([0, 4], lab.make(103))) == 2
    # Indistinguishable hidden candidate: no conclusive replacement.
    seal = lab.closes(slot(80))
    denied(lambda: verify_reset(lab.config, slot(80), seal))
    empty = lab.closes(slot(106))
    denied(lambda: verify_reset(lab.config, slot(106), empty[:4]))
    assert verify_reset(lab.config, slot(106), empty[:5]) == verify_reset(
        lab.config, slot(106), empty
    )
    print(
        json.dumps(
            dict(
                tests="retrieval, all seven paths, tamper, overlap, duplicates, wrong owner, partition, reordered votes, insufficient and alternative fences",
                delayed_counts=list(map(len, collected)),
            )
        )
    )
