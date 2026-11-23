"""Three disjoint 4/3/1 committees; one old version and two candidate child domains."""
from collections import deque

# Each committee has one Byzantine signer (assumed willing to sign everything).
# Digits 0,1,2 mean unreserved, first statement or second statement.
def certified(witnesses, value):
    return witnesses.count(value) >= 2

def check():
    initial = ((0,0,0),) * 3
    queue, visited = deque([initial]), {initial}
    while queue:
        state = queue.popleft()
        old, left, right = state
        h1,h2 = certified(old,1),certified(old,2)
        assert not (h1 and h2)
        final = [certified(child,v) for child in (left,right) for v in (1,2)]
        assert sum(final) <= 1
        for committee,enabled in enumerate((True,h1,h2)):
            if not enabled: continue
            for i,record in enumerate(state[committee]):
                if record: continue
                for vote in (1,2):
                    child = list(state[committee])
                    child[i] = vote
                    nxt = list(state)
                    nxt[committee] = tuple(child)
                    nxt = tuple(nxt)
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
    return len(visited)

if __name__ == '__main__':
    print('branch-bound handoff, reachable states:',check())
