"""Exhaustive finite transition system. No dependencies. Run with python3."""
from collections import deque
from itertools import combinations

def explore(inputs, honest=3, bad=1, q=3):
    # Each mask is every signature ever released by an honest witness.
    # Byzantine witnesses sign every proposal. This dominates withholding for safety.
    start = (0,) * honest
    queue, visited = deque([start]), {start}
    conflict = [sum(1 << j for j, other in enumerate(inputs)
                    if i != j and keys & other) for i, keys in enumerate(inputs)]
    final_sets = set()
    while queue:
        state = queue.popleft()
        final = sum(1 << i for i in range(len(inputs))
                    if bad + sum(bool(mask & 1 << i) for mask in state) >= q)
        final_sets.add(final)
        for i, overlap in enumerate(conflict):
            if final & (1 << i) and final & overlap:
                return len(visited), final_sets, state
            for w, mask in enumerate(state):
                if mask & ((1 << i) | overlap):
                    continue
                nxt = state[:w] + (mask | 1 << i,) + state[w+1:]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
    return len(visited), final_sets, None

def intersections(n,q,f):
    sets = list(map(set, combinations(range(n), q)))
    small = min(len(a & b) for a in sets for b in sets)
    assert (small > f) == (2*q-n > f)
    return small

def option(open_choice):
    # Two isolated copies of a previously certified irrevocable grant.
    allowed = ('B','C') if open_choice else ('B',)
    return {(a,b) for a in allowed for b in allowed if a != b}

if __name__ == '__main__':
    for label, inputs in [('whole', [{0},{0},{0}]),
                          ('rights', [{0},{1},{0,1}])]:
        count, finals, witness = explore(inputs)
        assert witness is None and ((3 in finals) == (label == 'rights'))
        print(label, count, 'reachable states, final masks', sorted(finals))
    count, _, witness = explore([{0},{0}], honest=5,bad=2,q=5)
    assert witness is None
    print('7/5/2 two-way fork:',count,'states')
    _, _, witness = explore([{0},{0}], honest=5,bad=2,q=4)
    assert witness is not None
    print('7/4/2 unsafe honest vote masks:',witness)
    for n in range(1,9):
        for q in range(1,n+1):
            for f in range(n):
                intersections(n,q,f)
    assert not option(False) and option(True)
    print('fixed recipient release safe; late recipient choice forks:', sorted(option(True)))
