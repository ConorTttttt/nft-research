"""Fixed-profile laboratory codec. Keys are locally admitted, canonical generated Ed25519 keys."""

import hashlib
from collections import Counter
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def raw(value, length=32):
    b = bytes.fromhex(value)
    require(len(b) == length and b.hex() == value, "invalid canonical bytes")
    return b


def H(*parts):
    return hashlib.sha256(b"".join(parts)).digest()


def integer(i):
    return i.to_bytes(4, "big")


def check(key, signature, message):
    Ed25519PublicKey.from_public_bytes(raw(key)).verify(raw(signature, 64), message)


def context(config):
    keys = config["keys"]
    n, q, e = len(keys), config["q"], config["e"]
    require(len(set(keys)) == n and 0 <= e < q <= n and 2 * q - n > e, "unsafe roster")
    return H(
        b"phase2/domain",
        raw(config["anchor"]),
        integer(n),
        integer(q),
        integer(e),
        *(raw(k) for k in keys)
    )


def layers(moves):
    leaves = [
        H(b"leaf", integer(i), raw(p), raw(to)) for i, (p, to) in enumerate(moves)
    ]
    size = 1 << (len(leaves) - 1).bit_length()
    leaves.extend(H(b"pad", integer(i)) for i in range(len(leaves), size))
    tree = [leaves]
    while len(tree[-1]) > 1:
        row = tree[-1]
        tree.append([H(b"node", row[i], row[i + 1]) for i in range(0, len(row), 2)])
    return tree


def header(domain, mode, n, commitment):
    require(mode in ("flat", "tree") and 0 < n <= 256, "mode/width")
    return H(b"phase2/statement", domain, mode.encode(), integer(n), commitment)


def statement(domain, mode, moves):
    require(0 < len(moves) <= 256, "batch size")
    parents = [p for p, _ in moves]
    require(parents == sorted(set(parents)), "duplicate or unsorted inputs")
    body = (
        layers(moves)[-1][0]
        if mode == "tree"
        else H(b"flat", *(raw(p) + raw(to) for p, to in moves))
    )
    return header(domain, mode, len(moves), body)


def proposal(config, owner, moves, mode):
    digest = statement(context(config), mode, moves)
    return dict(moves=moves, mode=mode, auth=owner.sign(b"owner" + digest).hex())


def verify_votes(config, digest, votes):
    seen = set()
    require(config["q"] <= len(votes) <= len(config["keys"]), "quorum")
    for i, sig in votes:
        require(
            type(i) is int and 0 <= i < len(config["keys"]) and i not in seen, "index"
        )
        check(config["keys"][i], sig, b"vote" + digest)
        seen.add(i)


def receipt(p, votes, i):
    n = len(p["moves"])
    proof = dict(mode=p["mode"], auth=p["auth"], votes=votes, i=i, n=n)
    if p["mode"] == "flat":
        proof["moves"] = p["moves"]
    else:
        proof["move"] = p["moves"][i]
        proof["path"] = [
            row[(i >> level) ^ 1].hex()
            for level, row in enumerate(layers(p["moves"])[:-1])
        ]
    return proof


def verify_receipt(config, proof, owner, expected_parent):
    i, n = proof["i"], proof["n"]
    require(type(i) is int and type(n) is int and 0 <= i < n <= 256, "leaf index")
    domain = context(config)
    if proof["mode"] == "flat":
        moves = proof["moves"]
        require(len(moves) == n, "width")
        digest = statement(domain, "flat", moves)
        p, to = moves[i]
    else:
        require(
            proof["mode"] == "tree" and len(proof["path"]) == (n - 1).bit_length(),
            "path length",
        )
        p, to = proof["move"]
        value = H(b"leaf", integer(i), raw(p), raw(to))
        for level, encoded in enumerate(proof["path"]):
            sibling = raw(encoded)
            value = (
                H(b"node", sibling, value)
                if (i >> level) & 1
                else H(b"node", value, sibling)
            )
        digest = header(domain, "tree", n, value)
    require(
        p == expected_parent and to in config["users"],
        "wrong entitlement or unadmitted recipient",
    )
    check(owner, proof["auth"], b"owner" + digest)
    verify_votes(config, digest, proof["votes"])
    return H(b"child", digest, raw(p)).hex(), to


def close_message(domain, parent, prior):
    record = b"0" if prior is None else b"1" + raw(prior)
    return b"close" + domain + raw(parent) + record


def verify_reset(config, parent, reports):
    domain = context(config)
    seen = set()
    counts = Counter()
    for i, prior, sig in reports:
        require(
            type(i) is int and 0 <= i < len(config["keys"]) and i not in seen,
            "close index",
        )
        check(config["keys"][i], sig, close_message(domain, parent, prior))
        seen.add(i)
        if prior is not None:
            counts[prior] += 1
    negatives = len(seen) - max(counts.values(), default=0)
    require(
        negatives > len(config["keys"]) - config["q"] + config["e"],
        "inconclusive closure",
    )
    return H(b"fixed-refund", domain, raw(parent)).hex()
