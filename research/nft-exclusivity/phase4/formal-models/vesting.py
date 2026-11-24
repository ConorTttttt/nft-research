"""Small two-ledger recognition model. Evidence delivery is asynchronous."""

from collections import deque
from typing import NamedTuple


class Sale(NamedTuple):
    title_locked: bool = False
    source_reserved: bool = False
    decision: str = ""
    public_proof: bool = False
    exercised: bool = False
    credit: bool = False
    refund: bool = False


def successors(s, weakened):
    if not s.title_locked and not s.decision:
        yield "title authorizes fixed buyer and refund", s._replace(title_locked=True)
    if not s.source_reserved and not s.decision:
        yield "buyer reserves funded unit", s._replace(source_reserved=True)
    if (
        s.source_reserved
        and not s.decision
        and (s.title_locked or weakened == "unprepared")
    ):
        for tag in ("paid", "void"):
            yield "payment authority decides " + tag, s._replace(decision=tag)
    if s.decision and not s.public_proof:
        yield "independent reader obtains certificate", s._replace(public_proof=True)
    if (
        s.decision == "paid"
        and not s.credit
        and (s.public_proof or weakened == "discretionary credit")
    ):
        yield "seller collects", s._replace(credit=True)
    if s.title_locked and s.public_proof and not s.exercised:
        yield "materialize vested title", s._replace(exercised=True)
    if (
        not s.refund
        and s.source_reserved
        and (s.decision == "void" or weakened == "timeout")
    ):
        yield "payer reclaims", s._replace(refund=True)


def explore(profile):
    queue = deque([(Sale(), [])])
    seen = {Sale()}
    edges = 0
    pending_delivery = 0
    while queue:
        s, trace = queue.popleft()
        # Immutable decision vests a claim even before its owner obtains the bytes.
        buyer_title = s.title_locked and s.decision == "paid"
        seller_paid = (
            s.credit if profile == "discretionary credit" else s.decision == "paid"
        )
        if buyer_title != seller_paid or (s.refund and seller_paid):
            return len(seen), edges, pending_delivery, trace
        pending_delivery += int(buyer_title and not s.exercised)
        for label, nxt in successors(s, profile):
            edges += 1
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, trace + [label]))
    return len(seen), edges, pending_delivery, None


if __name__ == "__main__":
    for profile in ("shared vesting", "unprepared", "discretionary credit", "timeout"):
        states, edges, pending, trace = explore(profile)
        assert (trace is None) == (profile == "shared vesting")
        print(
            profile,
            states,
            edges,
            "states with vested unexercised title",
            pending,
            "failure",
            trace,
        )
