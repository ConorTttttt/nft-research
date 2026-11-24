"""Local historical checkpoints. Signers replay claims before signing one root."""

import json
import statistics
import time
from grant import H, context, integer, raw, verify_receipt
from lab import key, pub, slot
from protocol import check, proposal, receipt, statement

WIDTH, DEPTH = 16, 12
DOMAIN = b"phase3/historical-frontier/v1"


def replay(cfg, users, index, history):
    parent, owner = slot(index), pub(users[0])
    for proof in history:
        parent, owner = verify_receipt(cfg, proof, owner, parent)
    return raw(parent) + raw(owner)


def root_paths(values):
    rows = [[H(DOMAIN, b"/leaf", integer(i), v) for i, v in enumerate(values)]]
    while len(rows[-1]) > 1:
        row = rows[-1]
        rows.append(
            [H(DOMAIN, b"/node", row[j], row[j + 1]) for j in range(0, len(row), 2)]
        )
    return rows


def run():
    users = [key(), key()]
    keys = [key() for _ in range(7)]
    cfg = dict(
        keys=list(map(pub, keys)),
        q=5,
        e=2,
        users=list(map(pub, users)),
        anchor=H(DOMAIN, b"/genesis").hex(),
    )
    domain = context(cfg)
    histories = []
    for i in range(WIDTH):
        history = []
        parent = slot(i)
        for step in range(DEPTH):
            owner = users[step % 2]
            target = pub(users[1 - step % 2])
            p = proposal(cfg, owner, [(parent, target)], "flat")
            digest = statement(domain, "flat", p["moves"])
            votes = [[w, keys[w].sign(b"vote" + digest).hex()] for w in range(5)]
            proof = receipt(p, votes, 0)
            parent, _ = verify_receipt(cfg, proof, pub(owner), parent)
            history.append(proof)
        histories.append(history)

    def checkpoint():
        values = [replay(cfg, users, i, h) for i, h in enumerate(histories)]
        return values, root_paths(values)

    start = time.perf_counter()
    votes = []
    for w in range(5):
        values, rows = checkpoint()
        anchor = H(DOMAIN, domain, integer(WIDTH), integer(DEPTH), rows[-1][0])
        votes.append((w, keys[w].sign(anchor).hex()))
    signing = time.perf_counter() - start
    i = 5
    path = [row[(i >> j) ^ 1] for j, row in enumerate(rows[:-1])]

    def member():
        r = H(DOMAIN, b"/leaf", integer(i), values[i])
        for j, sibling in enumerate(path):
            pair = (sibling, r) if (i >> j) & 1 else (r, sibling)
            r = H(DOMAIN, b"/node", *pair)
        anchor = H(DOMAIN, domain, integer(WIDTH), integer(DEPTH), r)
        assert len({w for w, _ in votes}) == 5
        for w, sig in votes:
            check(cfg["keys"][w], sig, anchor)
        return values[i]

    full_times = []
    member_times = []
    for _ in range(15):
        tick = time.process_time_ns()
        result = replay(cfg, users, i, histories[i])
        full_times.append((time.process_time_ns() - tick) / 1000)
        tick = time.process_time_ns()
        assert member() == result
        member_times.append((time.process_time_ns() - tick) / 1000)
    # Same JSON transport and external trust root on both sides.
    codec = lambda x: len(json.dumps(x, separators=(",", ":")).encode())
    print(
        json.dumps(
            dict(
                width=WIDTH,
                depth=DEPTH,
                full_bytes=codec(histories[i]),
                checkpoint_bytes=codec(
                    dict(
                        index=i,
                        width=WIDTH,
                        depth=DEPTH,
                        value=values[i].hex(),
                        path=[p.hex() for p in path],
                        votes=votes,
                    )
                ),
                signer_replay_wall_s=signing,
                full_verify_cpu_us=full_times,
                checkpoint_verify_cpu_us=member_times,
            )
        )
    )


if __name__ == "__main__":
    run()
