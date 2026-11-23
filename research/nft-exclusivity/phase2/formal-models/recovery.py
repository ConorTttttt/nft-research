"""Finite knowledge model. One report per identity in a candidate reset proof.
0 = no report, 1 = sealed with no prior signature; 2,3,4 = sealed for A,B,C.
An unreported honest witness may already have signed or may sign later.
"""

from itertools import combinations, product
from collections import Counter


def feasible(reports, value, bad):
    # Construct an extension in which every eligible signer releases value,
    # before closure if named, otherwise at any time.
    return sum(i in bad or claim in (0, value) for i, claim in enumerate(reports))


def model(n, q, e):
    bad_sets = list(combinations(range(n), e))
    resets = 0
    ambiguous = 0
    for reports in product(range(5), repeat=n):
        k = n - reports.count(0)
        max_votes = max(Counter(x for x in reports if x >= 2).values(), default=0)
        reset = k - max_votes > n - q + e
        # Value 5 stands for every possible unmentioned digest, including hidden ones.
        possible = set()
        for v in range(2, 6):
            bound = min(n, n - k + reports.count(v) + e)
            observed = max(feasible(reports, v, bad) for bad in bad_sets)
            assert bound == observed
            if observed >= q:
                possible.add(v)
        assert reset == (not possible)
        resets += reset
        ambiguous += len(possible) > 1
    print(
        f"n={n} q={q} e={e}: {5**n} observations, {resets} safe resets, {ambiguous} ambiguous"
    )


def quorum(n, q, e):
    sets = list(map(set, combinations(range(n), q)))
    minimum = min(len(a & b) for a in sets for b in sets)
    assert (minimum > e) == (2 * q - n > e)
    print(
        f"n={n} q={q} e={e}: {len(sets)**2} ordered quorum pairs, min intersection {minimum}"
    )


if __name__ == "__main__":
    model(4, 3, 1)
    model(5, 4, 2)
    for args in [(7, 5, 2), (7, 5, 3), (8, 6, 3), (9, 6, 3), (10, 7, 3)]:
        quorum(*args)
