"""Infer exact coordinate dependencies of a finite deterministic transition."""

from itertools import combinations, product


def compile_table(states, transition):
    # The output term is a sparse write map. A total copy of an unrelated
    # field would spuriously introduce a dependency on that field.
    table = {s: transition(s) for s in states}
    reads = set()
    for s, effect in table.items():
        for i in range(len(s)):
            for value in (0, 1):
                alternate = s[:i] + (value,) + s[i + 1 :]
                if table[alternate] != effect:
                    reads.add(i)
    writes = {i for effect in table.values() if effect is not None for i, _ in effect}
    return reads, writes


def verify():
    states = list(product((0, 1), repeat=3))
    # 0 = available for certified assignment, 1 = already assigned.
    for mask in range(1, 8):
        indices = {i for i in range(3) if mask & (1 << i)}

        def restricted(s):
            return (
                tuple((i, 1) for i in sorted(indices))
                if all(s[i] == 0 for i in indices)
                else None
            )

        reads, writes = compile_table(states, restricted)
        assert reads == writes == indices
        # Independent minimum over all coordinate projections.
        sufficient = []
        for k in range(4):
            for projection in combinations(range(3), k):
                lookup = {}
                for s in states:
                    key = tuple(s[i] for i in projection)
                    if key in lookup and lookup[key] != restricted(s):
                        break
                    lookup[key] = restricted(s)
                else:
                    sufficient.append(set(projection))
        assert reads == set.intersection(*sufficient)
    print(
        "7 transition tables x 8 states x 8 projections. Exact least coordinate support in every case."
    )


if __name__ == "__main__":
    verify()
