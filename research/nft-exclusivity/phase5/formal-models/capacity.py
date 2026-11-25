"""Finite unit counts. Independent allocations commute iff every merge is admissible."""

from itertools import combinations, product


def first_bad(capacity, debits):
    indices = range(len(debits))
    return [
        s
        for k in range(1, len(debits) + 1)
        for s in combinations(indices, k)
        if sum(debits[i] for i in s) > capacity
        and all(sum(debits[i] for i in s if j != i) <= capacity for j in s)
    ]


assert first_bad(10, [4, 4, 4]) == [(0, 1, 2)]
print(
    "minimal incompatible sets for capacity 10 and debits 4,4,4:",
    first_bad(10, [4, 4, 4]),
)
n = 0
for cap in range(11):
    for left in range(cap + 1):
        for a, b in product(range(left + 1), range(cap - left + 1)):
            assert (left - a) + (cap - left - b) + a + b == cap
            n += 1
print(n, "escrow-partition merges conserved")
# Confirm two plausible views each admit their individual transition while merged credit falls short.
balance, credit = 0, 10
spent, new_limit = 8, 5
assert spent <= balance + credit and 0 <= new_limit and spent > balance + new_limit
print(
    "credit change requires reservation grandfathering, collateral or a synchronized capacity check"
)
