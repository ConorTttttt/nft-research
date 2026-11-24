"""Explicit-state search. Two separately granted NFTs compete for one unit.
The one Byzantine member can sign every value. Three honest members retain
one slot each. The bank recognizes a threshold as its debit/void rule.
"""

from collections import deque
from itertools import combinations
from typing import NamedTuple


class State(NamedTuple):
    votes: tuple
    issued: int
    stored: int
    visible: int
    titles: int
    outside: bool


NAMES = ("pay A", "void A", "pay B", "void B")


def transitions(s, fault):
    for i, signed in enumerate(s.votes):
        for v, name in enumerate(NAMES):
            bit = 1 << v
            if signed & bit:
                continue
            if (
                signed
                and not (fault == "rollback" and i == 0)
                and not (fault == "per grant" and not signed & (3 << ((v // 2) * 2)))
            ):
                continue
            votes = list(s.votes)
            votes[i] |= bit
            yield f"w{i} reserves {name}", s._replace(votes=tuple(votes))
    for v, name in enumerate(NAMES):
        bit = 1 << v
        if sum(bool(mask & bit) for mask in s.votes) >= 2 and not s.issued & bit:
            yield "assemble hidden " + name, s._replace(issued=s.issued | bit)
        if s.issued & bit and not s.stored & bit:
            yield "archive complete " + name, s._replace(stored=s.stored | bit)
        if s.stored & bit and not s.visible & bit:
            yield "independent fetch " + name, s._replace(visible=s.visible | bit)
        if s.visible & bit and not s.titles & bit:
            yield "exercise " + name, s._replace(titles=s.titles | bit)
        if fault == "realm replay" and s.visible & bit:
            yield "exercise under other grant", s._replace(
                titles=s.titles | (1 << (v ^ 2))
            )
    if s.visible:
        yield "executor crash; lose local cache", s._replace(visible=0)
    if fault == "unguarded exit" and not s.outside:
        yield "independent native reclaim on other history", s._replace(outside=True)


def invariant(s):
    if s.issued.bit_count() > 1:
        return "source has competing dispositions"
    if s.titles & ~s.issued:
        return "title without corresponding decision"
    if s.outside and s.issued & 5:
        return "seller credit and native reclaim coexist"
    if s.titles & 3 == 3 or s.titles & 12 == 12:
        return "two controllers of one NFT"


def explore(fault):
    initial = State((0, 0, 0), 0, 0, 0, 0, False)
    prev = {initial: None}
    queue = deque([initial])
    edges = 0
    while queue:
        s = queue.popleft()
        if problem := invariant(s):
            path = []
            while prev[s] is not None:
                s, label = prev[s]
                path.append(label)
            return len(prev), edges, problem, list(reversed(path))
        for label, t in transitions(s, fault):
            edges += 1
            if t not in prev:
                prev[t] = (s, label)
                queue.append(t)
    return len(prev), edges, None, []


def retention():
    # q issued fragment holders, f possibly withhold, l other unavailable.
    members = set(range(7))
    for r in range(1, 8):
        survives = all(
            set(copies) - set(bad) - set(lost)
            for copies in combinations(members, r)
            for bad in combinations(members, 2)
            for lost in combinations(members - set(bad), 1)
        )
        assert survives == (r > 3)
    print(
        "full-object archival: r >= 4 survives 2 withholding and 1 independent loss, n=7"
    )


if __name__ == "__main__":
    for fault in ("none", "rollback", "per grant", "unguarded exit", "realm replay"):
        states, edges, problem, trace = explore(fault)
        assert (problem is None) == (fault == "none")
        print(fault, states, edges, problem, trace)
    retention()
