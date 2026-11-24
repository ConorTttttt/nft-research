"""Two realms, one source title. Enumerate gate mappings and migration races."""

from itertools import product, permutations

for canonical, legacy in product((False, True), repeat=2):
    counts = set()
    for order in permutations(("realm-A", "realm-B", "legacy")):
        spent = set()
        issued = []
        for dest in order:
            if dest == "legacy" and not legacy:
                continue
            gate = "source" if canonical and dest != "legacy" else dest
            if gate not in spent:
                spent.add(gate)
                issued.append(dest)
        counts.add(len(issued))
    expected = (1 if canonical else 2) + int(legacy)
    assert counts == {expected}
    print(
        "shared export authority",
        canonical,
        "legacy independently usable",
        legacy,
        "recognized titles",
        expected,
    )

# Prospective transfer of unresolved source. Atomic seal forbids old-version
# decisions after export. A new roster may only start from a certified export.
for require_export in (False, True):
    outcomes = set()
    for order in permutations(("old-pay", "export", "new-void")):
        old = None
        new = None
        for op in order:
            if op == "new-void" and (not require_export or old == "export"):
                new = "void"
            elif op != "new-void" and old is None:
                old = op
        outcomes.add((old, new))
    assert (("old-pay", "void") in outcomes) == (not require_export)
    print(
        "new epoch requires old export",
        require_export,
        "reachable outcomes",
        sorted(map(str, outcomes)),
    )
