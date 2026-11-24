"""Finite relational oracle and explicit-state asynchronous product model."""

from collections import deque
from itertools import combinations, product
from math import comb


def thresholds(n, q, e):
    quorums = list(map(set, combinations(range(n), q)))
    intersection = min(len(a & b) for a in quorums for b in quorums)
    # Reports absent, empty, A, B. Enumerate multisets by number of each
    # kind. For each candidate independently choose every final quorum and
    # count the reporters that would have to lie. An unseen C is admissible.
    count = 0
    for absent in range(n + 1):
        for empty in range(n - absent + 1):
            for a in range(n - absent - empty + 1):
                b = n - absent - empty - a
                reports = [None] * absent + ["empty"] * empty + ["A"] * a + ["B"] * b
                possible = any(
                    sum(reports[i] not in (None, x) for i in Q) <= e
                    for Q in quorums
                    for x in "ABC"
                )
                assert (not possible) == (n - absent - max(a, b) > n - q + e)
                count += 1
    print(
        f"{n=}, {q=}, {e=}, minimum overlap {intersection}, {count} report histograms"
    )
    return intersection > e


def settlement():
    # Durable commitment, payment state, delivered outcome, materialized title.
    initial = (False, "free", "", "")
    seen = {initial}
    queue = deque([initial])
    edges = 0
    while queue:
        committed, pay, evidence, title = queue.popleft()

        def steps():
            yield True, pay, evidence, title
            if committed and pay == "free":
                yield True, "reserved", evidence, title
            if committed and pay in ("free", "reserved"):
                yield True, "void", evidence, title
            if pay == "reserved":
                yield True, "paid", evidence, title
            if pay in ("paid", "void"):
                yield True, pay, pay, title
            yield committed, pay, "", title  # lose a local proof
            if evidence:
                yield committed, pay, evidence, {"void": "Alice", "paid": "Bob"}[
                    evidence
                ]

        for state in steps():
            edges += 1
            c, p, ev, t = state
            assert not ev or ev == p
            assert not t or (c and (p, t) in (("void", "Alice"), ("paid", "Bob")))
            assert p != "paid" or c  # vested claim exists even before delivery
            if state not in seen:
                queue.append(state)
                seen.add(state)
    print(
        f"Settlement {len(seen)} reachable states, {edges} edges including loss and replay"
    )


def guards():
    # Title control and occupancy are separate goods, initially owned by A.
    # Transition = partial map from a coordinate to (required, successor).
    # Vacant sale transfers title AND future occupancy issuance for both days.
    ops = {
        "sale": {0: ("A", "B")},
        "vacant": {i: ("A", "B") for i in range(3)},
        "lease1": {1: ("A", "L")},
        "lease2": {2: ("A", "L")},
        "delegate": {1: ("A", "D")},
        "revoke": {1: ("D", "A")},
    }
    states = list(product("ABLD", repeat=3))

    def apply(op, s):
        if s is None or any(s[i] != old for i, (old, _) in op.items()):
            return None
        return tuple(op[i][1] if i in op else x for i, x in enumerate(s))

    checks = 0
    for left, right in combinations(ops, 2):
        a, b = ops[left], ops[right]
        for s in states:
            if apply(a, s) and apply(b, s):
                ab, ba = apply(b, apply(a, s)), apply(a, apply(b, s))
                if a.keys().isdisjoint(b):
                    assert ab == ba and ab is not None
                else:
                    assert ab is None and ba is None
                checks += 1
    # Every guard of vacant is necessary for the stated precondition.
    for i in ops["vacant"]:
        weakened = {k: v for k, v in ops["vacant"].items() if k != i}
        s = tuple("L" if j == i else "A" for j in range(3))
        assert apply(weakened, s) and apply(ops["vacant"], s) is None
    print(
        f"Guard diamond/exclusion checks {checks}; all three vacant-sale guards necessary"
    )


if __name__ == "__main__":
    assert thresholds(7, 5, 2) and not thresholds(7, 5, 3) and thresholds(8, 6, 3)
    guards()
    settlement()
