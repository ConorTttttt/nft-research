"""Abstract validator state shared by every recognizing client in the guarded profile."""

from itertools import permutations


def run(order, *, common=True, legacy_guard=True, epoch_guard=True):
    decisions = {}
    imports = set()
    legacy = set()
    for event in order:
        is_legacy = event == "legacy"
        epoch = 1 if event == "rotated B" else 0
        dest = "B" if event in ("rotated B", "export B") else "A"
        fence = ("mint", "version0")
        if not common and not is_legacy:
            fence += ("realm", dest)
        if is_legacy and not legacy_guard:
            fence += ("legacy",)
        if epoch and not epoch_guard:
            fence += ("epoch", epoch)
        value = ("legacy",) if is_legacy else ("export", dest)
        if decisions.setdefault(fence, value) != value:
            continue
        if is_legacy:
            legacy.add("successor")
        else:
            imports.add(dest)
    return imports, legacy


events = ("export A", "export B", "legacy", "rotated B", "replay A")
for name, profile in [
    ("guarded", {}),
    ("independent rosters", dict(common=False)),
    ("legacy independent", dict(legacy_guard=False)),
    ("epoch reset", dict(epoch_guard=False)),
]:
    trace = None
    bad = 0
    for order in permutations(events):
        a, b = run(order, **profile)
        if len(a) + len(b) > 1:
            bad += 1
            if trace is None:
                trace = order
    assert (bad == 0) == (name == "guarded")
    print(name, "orders", 120, "violations", bad, "first", trace)
