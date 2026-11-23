"""Finite resource transitions at arbitrary replicas; the certification invariant serialises overlapping inputs."""

from itertools import combinations, product

U = frozenset("tlu")


# Each current version covers a nonempty subset of rights. A rewrite can partition
# any consumed version; recipient changes are abstracted away. No implicit revocation.
def splits(s):
    yield (s,)
    first = min(s)
    for k in range(1, len(s)):
        for left in combinations(sorted(s), k):
            a = frozenset(left)
            if first in a:
                yield (a, s - a)


def next_states(marking):
    for token in marking:
        for outputs in splits(token):
            yield (marking - {token}) | frozenset(outputs)


def check():
    start = frozenset([U])
    frontier = [start]
    seen = {start}
    while frontier:
        state = frontier.pop()
        assert frozenset.union(*state) == U and sum(map(len, state)) == len(U)
        for nxt in next_states(state):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    assert len(seen) == 5
    # For a unit capacity of two, pairwise-admissible requests can collectively fail.
    assert all(len(p) <= 2 for p in combinations(range(3), 2)) and len(range(3)) > 2
    # A binding bit commitment has just one possible opening per world; a union
    # of independent positive attestations can present both bits.
    for world in [(0,), (1,), (0, 1)]:
        fork = any(a != b for a, b in product(world, repeat=2))
        assert fork == (len(world) > 1)
    print(
        "three atoms: 5 reachable partitions; capacity and ambiguous-oracle counterexamples confirmed"
    )


if __name__ == "__main__":
    check()
