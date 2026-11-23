"""Executable counterexamples, votes remain usable even if publication is delayed."""
from itertools import combinations
from explore import explore
def votes(voters, faults, memory, value):
    result = set()
    for w in voters:
        if w in faults or memory.setdefault(w, value) == value:
            result.add(w)
    return result
bad = {0,1}
locks = {}
a = votes(range(5),bad,locks,'A')
assert len(a)==5
assert len(votes(range(7),bad,locks,'B'))==4
del locks[2]  # honest witness restored from stale snapshot
assert len(votes(range(7),bad,locks,'B'))==5
print('rollback: old A and new B both have 5 votes')
locks = {}
assert len(votes(range(5),bad,locks,'A'))==5
assert len(votes(range(7,12),set(),locks,'B'))==5
print('disjoint epoch: locally valid certificates even with old A withheld')
locks = {}
assert len(votes([2,3,4],bad,locks,'A'))==3
assert len(votes([5,6],bad,locks,'B'))==2
assert all(len(votes(range(2,7),bad,locks,v))<5 for v in ['A','B'])
print('split vote: all honest nodes reachable, two Byzantine abstentions, no progress')
# Conflict graph of a whole-title sale and three independent assignments.
# Enumerate exact exclusive guard representations including empty and overlapping cliques.
edges = {(0,i) for i in (1,2,3)}
cliques = []
for k in range(2,5):
    for s in combinations(range(4),k):
        pairs = set(combinations(s,2))
        if pairs <= edges:
            cliques.append(pairs)
minimum = next(k for k in range(1,5) if any(set.union(*family)==edges
               for family in combinations(cliques,k)))
assert minimum==3
print('three independent rights plus bundle: exact exclusive guard minimum',minimum)
