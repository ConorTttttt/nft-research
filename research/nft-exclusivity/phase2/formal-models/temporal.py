"""BFS over released votes, released fences and live journal state.
One always-Byzantine identity. The first other identity may restore once.
Symmetry quotient sorts the remaining never-rollback honest identities.
"""

from collections import deque
from functools import lru_cache
from itertools import product


@lru_cache(None)
def fences(report_sets, threshold):
    # A Byzantine can report empty. Giving all available truthful reports to a
    # verifier dominates withholding for proving absence. A restored actor can
    # have signed more than one report; the verifier uses at most one per ID.
    choices = [
        [v for v in (0, 1, 2) if mask & (1 << v)] for mask in report_sets if mask
    ]
    for claims in product(*choices):
        if len(claims) + 1 - max(claims.count(1), claims.count(2)) >= threshold:
            return True
    return False


def search(n, q, e, allow_rollback):
    # Each cell stores (current journal, released signature mask, released report mask).
    initial = (False, ((0, 0, 0),) * (n - 1))
    todo = deque([initial])
    prev = {initial: None}
    while todo:
        state = todo.popleft()
        restored, cells = state
        final = [
            str(v)
            for v in (1, 2)
            if 1 + sum(bool(h & 1 << v) for _, h, _ in cells) >= q
        ]
        if fences(tuple(sorted(r for _, _, r in cells)), n - q + e + 1):
            final.append("refund")
        if len(final) > 1:
            trace = []
            cur = state
            while prev[cur]:
                cur, action = prev[cur]
                trace.append(action)
            return len(prev), final, list(reversed(trace))
        for i, (j, h, r) in enumerate(cells):
            ops = []
            if j == 0:
                ops.extend((v, h | 1 << v, r, restored, f"vote {v}") for v in (1, 2))
            if j < 4:
                ops.append((j + 4, h, r | 1 << j, restored, f"close {j}"))
            if i == 0 and allow_rollback and not restored and j:
                ops.append((0, h, r, True, "restore prior empty image"))
            for a, b, c, flag, label in ops:
                nxt = list(cells)
                nxt[i] = (a, b, c)
                key = flag, (nxt[0], *sorted(nxt[1:]))
                if key not in prev:
                    prev[key] = (state, (i, label))
                    todo.append(key)
    return len(prev), [], []


if __name__ == "__main__":
    for args, unsafe in [
        ((4, 3, 1, False), False),
        ((4, 3, 1, True), True),
        ((5, 4, 2, True), False),
    ]:
        count, final, path = search(*args)
        assert bool(final) == unsafe
        print(
            args, "states discovered", count, "conflict", final, "quotient trace", path
        )
