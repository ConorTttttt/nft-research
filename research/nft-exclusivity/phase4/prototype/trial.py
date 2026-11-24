"""Separate laboratory currency with a funded genesis pin. No Unyt funds."""

import concurrent.futures
import hashlib
import json
import os
import shutil
from pathlib import Path
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def H(tag, *fields):
    return hashlib.sha256(tag + b"".join(fields)).digest()


def public(key):
    return key.public_key().public_bytes_raw()


class Member:
    def __init__(self, path):
        self.key = Ed25519PrivateKey.generate()
        self.path = path
        with closing(sqlite3.connect(path)) as db:
            db.execute(
                "create table choices(parent blob primary key,digest blob not null)"
            )
            db.execute("create table archive(id blob primary key,body blob not null)")

    def vote(self, parent, digest):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("begin immediate")
            db.execute("insert or ignore into choices values(?,?)", (parent, digest))
            if db.execute(
                "select digest from choices where parent=?", (parent,)
            ).fetchone() != (digest,):
                raise ValueError("parent fenced")
        return self.key.sign(digest)

    def archive(self, id, blob):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("insert or ignore into archive values(?,?)", (id, blob))
            if db.execute("select body from archive where id=?", (id,)).fetchone() != (
                blob,
            ):
                raise ValueError("conflicting archive")
        return self.key.sign(H(b"p4/archive/v1", id, H(b"body", blob)))


def signs(members, msg, record):
    with concurrent.futures.ThreadPoolExecutor(5) as workers:
        sigs = list(workers.map(record, members[:5]))
    for m, s in zip(members, sigs):
        m.key.public_key().verify(s, msg)
    return b"".join(bytes([i]) + s for i, s in enumerate(sigs))


def check_votes(roster, msg, votes):
    assert len(votes) == 325
    seen = set()
    for j in range(0, len(votes), 65):
        idx = votes[j]
        if idx in seen or idx >= 7:
            raise ValueError("roster")
        Ed25519PublicKey.from_public_bytes(roster[idx]).verify(
            votes[j + 1 : j + 65], msg
        )
        seen.add(idx)


def main(binary):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nft = [Member(root / f"n{i}") for i in range(7)]
        pay = [Member(root / f"p{i}") for i in range(7)]
        buyer, seller = [Ed25519PrivateKey.generate() for _ in range(2)]
        nr, pr = [[public(m.key) for m in roster] for roster in (nft, pay)]
        for i in range(24):
            seq = i.to_bytes(4, "big")
            source = H(b"fixture-coin", seq)
            policy = b"".join(
                [
                    H(b"fixture-payment-dna"),
                    source,
                    H(b"unit-zero"),
                    public(buyer),
                    public(seller),
                    (10).to_bytes(8, "big"),
                    *nr,
                    *pr,
                ]
            )
            pin = H(b"p4/lab-funding/v1", policy)
            terms = b"".join(
                [
                    H(b"source-dna"),
                    H(b"mint", seq),
                    H(b"cel-parent", seq),
                    H(b"agreement-instance", seq),
                    H(b"fixed-historical-rule-v1"),
                ]
            )
            g = H(b"p4/grant/v1", pin, terms)

            def verify(data, mode="lab", expected=g):
                path = root / "input"
                path.write_bytes(data)
                return subprocess.check_output(
                    [binary, mode, pin.hex(), expected.hex(), path], text=True
                ).strip()

            start = time.perf_counter_ns()
            title = H(b"p4/title-reserve/v1", g)
            auth = seller.sign(title)

            def reserve(m):
                seller.public_key().verify(auth, title)
                return m.vote(terms[:96], title)

            votes = signs(nft, title, reserve)
            prefix = b"P4L1" + policy + terms + auth + votes
            tag = bytes([int(i % 3 != 0)])
            terminal = H(b"p4/disposition/v1", g, tag)
            debit = buyer.sign(terminal)

            def settle(member):
                # The admitted source, currency, amount and authorized identities
                # are fixed externally by the fixture at genesis.
                buyer.public_key().verify(debit, terminal)
                seller.public_key().verify(auth, title)
                check_votes(nr, title, votes)
                return member.vote(source, terminal)

            final = prefix + tag + debit + signs(pay, terminal, settle)
            decided = time.perf_counter_ns()
            verdict = "Paid" if tag == b"\x01" else "Void"
            assert verify(final) == verdict
            checked = time.perf_counter_ns()
            # Four authenticated replicas store complete dependency-closed bytes.
            for member in pay[:4]:
                ack = member.archive(g, final)
                member.key.public_key().verify(
                    ack, H(b"p4/archive/v1", g, H(b"body", final))
                )
            replicated = time.perf_counter_ns()
            # New reader has only trusted pin, expected grant and one surviving DB.
            del final, prefix
            with closing(
                sqlite3.connect(f"file:{pay[3].path}?mode=ro", uri=True)
            ) as db:
                blob = db.execute(
                    "select body from archive where id=?", (g,)
                ).fetchone()[0]
            assert verify(blob) == verdict
            recovered = time.perf_counter_ns()
            assert verify(blob, "unyt") == "Invalid"
            assert verify(blob, expected=H(b"other-grant")) == "Invalid"
            assert verify(blob[:-1]) == "Invalid"
            assert verify(blob[:-1] + bytes([blob[-1] ^ 1])) == "Invalid"
            other = H(b"p4/disposition/v1", g, bytes([1 - tag[0]]))
            for member in pay[:5]:
                try:
                    member.vote(source, other)
                except ValueError:
                    pass
                else:
                    raise AssertionError("accepted conflicting disposition")
            successor = H(b"p4/successor/v1", g, tag)
            owner = buyer if verdict == "Paid" else seller
            onward = H(
                b"p4/onward/v1",
                successor,
                public(seller if verdict == "Paid" else buyer),
            )
            permit = owner.sign(onward)

            def transfer(member):
                check_votes(pr, terminal, blob[-325:])
                owner.public_key().verify(permit, onward)
                return member.vote(successor, onward)

            check_votes(nr, onward, signs(nft, onward, transfer))
            if i == 1 and (dest := os.environ.get("P4_PUBLIC")):
                dest = Path(dest)
                dest.mkdir(exist_ok=True)
                shutil.copyfile(pay[3].path, dest / "survivor.sqlite")
                (dest / "root").write_text(pin.hex())
                (dest / "grant").write_text(g.hex())
            print(
                json.dumps(
                    dict(
                        i=i,
                        verdict=verdict,
                        bytes=len(blob),
                        decision_us=(decided - start) / 1000,
                        verify_cli_us=(checked - decided) / 1000,
                        replicate_us=(replicated - checked) / 1000,
                        recover_cli_us=(recovered - replicated) / 1000,
                        db_bytes=sum(m.path.stat().st_size for m in nft + pay),
                    )
                ),
                flush=True,
            )


if __name__ == "__main__":
    main(str(Path(sys.argv[1]).resolve()))
