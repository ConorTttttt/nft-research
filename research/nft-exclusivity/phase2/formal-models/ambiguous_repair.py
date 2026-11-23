"""Can two honest collectors each see exactly one possible old certificate?"""

from collections import Counter


def possible(reports, n=7, q=5, e=2):
    counts = Counter(reports)
    return {
        x
        for x in ("A", "B", "unmentioned")
        if n - len(reports) + counts[x] + e >= q
    }


if __name__ == "__main__":
    # All reports truthful, all seven permanently fenced. Each subset omits one
    # different nonempty vote. Neither observer can rule out Byzantine reports.
    reports = ["A", "A", "B", "B", None, None, None]
    left = reports[:2] + reports[3:]
    right = reports[1:]
    assert possible(left) == {"A"}
    assert possible(right) == {"B"}
    assert possible(reports) == set()
    print("six-report projections uniquely permit A and B respectively; all seven exclude both")
