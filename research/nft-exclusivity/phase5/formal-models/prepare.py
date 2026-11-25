"""Enumerate two independent fenced input versions, two agreements and visibility."""

from collections import deque
from typing import NamedTuple


class State(NamedTuple):
    nft: frozenset = frozenset()
    pay: frozenset = frozenset()
    seen: frozenset = frozenset()
    vested: frozenset = frozenset()


def next_states(s, fault):
    # A choice is (agreement, prepared). Decline consumes the same exact version.
    for side in ("nft", "pay"):
        old = getattr(s, side)
        for g in "AB":
            for yes in (True, False):
                v = (g, yes)
                if not old or (fault == "restored " + side and v not in old):
                    yield f"{side} records {v}", s._replace(**{side: old | {v}})
        for v in old:
            fact = (side, *v)
            if fact not in s.seen:
                yield f"archive/fetch {fact}", s._replace(seen=s.seen | {fact})
    for g in "AB":
        yes = all((side, g, True) in s.seen for side in ("nft", "pay"))
        no = any(g0 != g or not prepared for _, g0, prepared in s.seen)
        candidates = []
        if yes or (fault == "unprepared debit" and ("pay", g, True) in s.seen):
            candidates.append("paid")
        if no or (fault == "timeout" and not yes):
            candidates.append("void")
        for out in candidates:
            if (g, out) not in s.vested:
                yield f"exercise {g} {out}", s._replace(vested=s.vested | {(g, out)})
    if s.seen:
        yield "reader loses cache", s._replace(seen=frozenset())


def violation(s):
    if len(s.pay) > 1 or len(s.nft) > 1:
        return "one source supported incompatible decisions"
    for g, out in s.vested:
        if out == "paid" and not all((g, True) in v for v in (s.nft, s.pay)):
            return "paid without bilateral prepare"
        if out == "void" and all((g, True) in v for v in (s.nft, s.pay)):
            return "refund coexists with irrevocably vested payment"


def run(fault):
    q = deque([(State(), ())])
    seen = {State()}
    edges = 0
    split = False
    while q:
        s, path = q.popleft()
        if violation(s):
            return len(seen), edges, violation(s), path
        split |= ("A", True) in s.nft and ("B", True) in s.pay
        for event, t in next_states(s, fault):
            edges += 1
            if t not in seen:
                seen.add(t)
                q.append((t, (*path, event)))
    assert split
    return len(seen), edges, "safe; split preparation reachable", ()


if __name__ == "__main__":
    for fault in (
        "none",
        "restored nft",
        "restored pay",
        "unprepared debit",
        "timeout",
    ):
        n, e, result, path = run(fault)
        assert bool(path) == (fault != "none")
        print(fault, n, e, result, list(path))
