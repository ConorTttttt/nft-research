"""P5J1 laboratory recognition contract. Source authority is provisioned externally."""

import hashlib
import json
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def encode(x):
    return json.dumps(
        x, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(domain, x):
    return hashlib.sha256(b"P5J1/" + domain.encode() + b"\0" + encode(x)).hexdigest()


def verify_sig(key, signature, message):
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(key)).verify(
        bytes.fromhex(signature), bytes.fromhex(message)
    )


def ballot(policy, parent, choice, owner, committee):
    body = [digest("policy", policy), parent, choice]
    message = digest("decision", body)
    consent = owner.sign(bytes.fromhex(message)).hex()
    votes = []
    for i, member in enumerate(committee[:5]):
        verify_sig(policy["owners"][parent[0]], consent, message)
        sig = member.vote(
            bytes.fromhex(digest("parent", parent)), bytes.fromhex(message)
        )
        votes.append([i, sig.hex()])
    return [body, consent, votes]


def check(policy, cert, parent):
    body, consent, votes = cert
    policy_id, actual, choice = body
    if policy_id != digest("policy", policy) or actual != parent:
        raise ValueError("wrong policy or parent")
    op, target = choice
    if (
        op not in {"export", "prepare", "decline", "send"}
        or not isinstance(target, str)
        or len(target) != 64
    ):
        raise ValueError("bad choice")
    if bytes.fromhex(target).hex() != target:
        raise ValueError("noncanonical target")
    message = digest("decision", body)
    verify_sig(policy["owners"][parent[0]], consent, message)
    keys = policy["rosters"][parent[0]]
    indices = [i for i, _ in votes]
    if (
        len(keys) != 7
        or len(set(keys)) != 7
        or len(indices) != 5
        or indices != sorted(set(indices))
    ):
        raise ValueError("invalid quorum")
    for i, s in votes:
        if type(i) is not int or not 0 <= i < 7:
            raise ValueError("invalid index")
        verify_sig(keys[i], s, message)
    return op, target


def parents(policy):
    origin = ["source", digest("native-title-version", policy["origin"])]
    dest = digest("destination", policy["destination"])
    imported = ["title", digest("import", [origin, dest])]
    source = ["payment", digest("funded-source-version", policy["payment"])]
    return origin, dest, imported, source


def verify(policy, terms, evidence, *, profile="lab", unavailable=False):
    """policy and terms are externally pinned. evidence is canonical, size-limited bytes."""
    if evidence is None:
        return "UnavailableEvidence" if unavailable else "Pending"
    if len(evidence) > 16384:
        return "Invalid"
    if profile == "native":
        return "Invalid" if evidence.startswith(b"P5J1") else "Pending"
    if profile != "lab" or not evidence.startswith(b"P5J1"):
        return "Invalid"
    try:
        records = json.loads(evidence[4:])
        if (
            encode(records) != evidence[4:]
            or not isinstance(records, dict)
            or set(records) - {"export", "title", "payment"}
        ):
            return "Invalid"
        if policy["profile"] != "lab-P5J1" or set(terms) != {
            "agreement",
            "version",
            "rule",
            "price",
            "unit",
            "buyer",
            "seller",
        }:
            return "Invalid"
        if (
            terms["rule"] != "both-prepare"
            or type(terms["price"]) is not int
            or terms["price"] <= 0
            or terms["version"] != 1
            or [terms["unit"], terms["price"]] != policy["payment"][-2:]
            or terms["buyer"] != policy["owners"]["payment"]
            or terms["seller"] != policy["owners"]["title"]
        ):
            return "Invalid"
        origin, dest, title, payment = parents(policy)
        transaction = digest("sale", [digest("policy", policy), terms])
        if "export" in records and check(policy, records["export"], origin) != (
            "export",
            dest,
        ):
            return "Invalid"
        approvals = 0
        exclusion = False
        for key, parent in [("title", title), ("payment", payment)]:
            if key not in records:
                continue
            op, target = check(policy, records[key], parent)
            if op not in {"prepare", "decline"}:
                return "Invalid"
            if key == "title" and "export" not in records:
                continue
            if op == "prepare" and target == transaction:
                approvals += 1
            else:
                exclusion = True
        if exclusion:
            return "FinalVoid"
        if approvals == 2:
            return "FinalPaid"
        return "UnavailableEvidence" if unavailable else "Pending"
    except (
        InvalidSignature,
        KeyError,
        ValueError,
        OverflowError,
        TypeError,
        IndexError,
        RecursionError,
    ):
        return "Invalid"


def pack(records):
    return b"P5J1" + encode(records)


def verify_onward(policy, terms, proof, transfer):
    """Authorize a spend of the deterministic title child only after its own prepare."""
    outcome = verify(policy, terms, proof)
    if outcome not in ("FinalPaid", "FinalVoid"):
        return False
    try:
        _, _, title, _ = parents(policy)
        tx = digest("sale", [digest("policy", policy), terms])
        records = json.loads(proof[4:])
        if "export" not in records or check(policy, records["title"], title) != (
            "prepare",
            tx,
        ):
            return False
        target, consent, votes = transfer
        key = terms["buyer"] if outcome == "FinalPaid" else terms["seller"]
        parent = ["successor", digest("exercise", [title, tx, outcome])]
        msg = digest("onward", [digest("policy", policy), parent, target])
        if len(bytes.fromhex(target)) != 32 or len(votes) != 5:
            return False
        verify_sig(key, consent, msg)
        for witness, sig in zip(policy["rosters"]["title"][:5], votes):
            verify_sig(witness, sig, msg)
        return True
    except (InvalidSignature, ValueError, KeyError, IndexError, TypeError):
        return False
