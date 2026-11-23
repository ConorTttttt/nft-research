"""Independent processes, real Ed25519 signatures, isolated SQLite files and TCP streams."""

import concurrent.futures as futures
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import (
    H,
    context,
    integer,
    proposal,
    raw,
    receipt,
    verify_receipt,
    verify_reset,
)

HERE = Path(__file__).resolve().parent


def key():
    return Ed25519PrivateKey.generate()


def pub(k):
    return k.public_key().public_bytes_raw().hex()


def slot(i):
    return integer(i).rjust(32, b"\0").hex()


class Lab:
    def __init__(self, n, q, e, faults=(), anchor_for=None, participants=None):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.owner, self.buyers = participants or (key(), [key() for _ in range(3)])
        keys = [key() for _ in range(n)]
        self.faults = set(faults)
        self.procs = {}
        self.ports = {}
        # Anchor commits the contiguous genesis range, owner and admitted recipient set.
        self.config = dict(
            keys=list(map(pub, keys)),
            q=q,
            e=e,
            users=[pub(self.owner), *map(pub, self.buyers)],
        )
        self.config["anchor"] = H(
            b"lab/genesis", integer(16384), *(raw(k) for k in self.config["users"])
        ).hex()
        if anchor_for:
            self.config["anchor"] = anchor_for(self.config)
        self.pool = futures.ThreadPoolExecutor(max_workers=32)
        for i, k in enumerate(keys):
            path = self.path / str(i)
            path.mkdir()
            (path / "key").write_bytes(k.private_bytes_raw())
            (path / "config.json").write_text(json.dumps(self.config))
            db = sqlite3.connect(path / "journal.db")
            db.executescript(
                "CREATE TABLE locks(id TEXT PRIMARY KEY,prior TEXT,sealed INTEGER NOT NULL);"
                "CREATE TABLE rights(id TEXT PRIMARY KEY,owner TEXT NOT NULL);"
                "CREATE TABLE bodies(digest TEXT PRIMARY KEY,body TEXT NOT NULL);"
            )
            db.execute(
                "CREATE TABLE identity(domain BLOB NOT NULL, signer INTEGER NOT NULL)"
            )
            db.execute("INSERT INTO identity VALUES(?,?)", (context(self.config), i))
            db.executemany(
                "INSERT INTO rights VALUES(?,?)",
                ((slot(j), pub(self.owner)) for j in range(16384)),
            )
            db.commit()
            db.close()
            self.start(i)

    def start(self, i):
        proc = subprocess.Popen(
            [
                sys.executable,
                str(HERE / "witness.py"),
                str(self.path / str(i)),
                "faulty" if i in self.faults else "correct",
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.procs[i] = proc
        self.ports[i] = int(proc.stdout.readline())

    def stop(self, i):
        p = self.procs.pop(i)
        p.kill()
        p.wait()
        p.stdout.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.pool.shutdown()
        for i in list(self.procs):
            self.stop(i)
        self.tmp.cleanup()

    def rpc(self, i, request, delay_ms=0):
        encoded = json.dumps(request, separators=(",", ":")).encode() + b"\n"
        time.sleep(delay_ms / 2000)
        with socket.create_connection(("127.0.0.1", self.ports[i]), timeout=10) as sock:
            sock.sendall(encoded)
            with sock.makefile("rb") as stream:
                reply = stream.readline()
        time.sleep(delay_ms / 2000)
        return json.loads(reply), len(encoded) + len(reply)

    def fan(self, ids, request, delay_ms=0):
        return list(self.pool.map(lambda i: self.rpc(i, request, delay_ms), ids))

    def make(self, start, width=1, buyer=0, mode="flat"):
        return proposal(
            self.config,
            self.owner,
            [(slot(i), pub(self.buyers[buyer])) for i in range(start, start + width)],
            mode,
        )

    def votes(self, ids, p):
        return [
            r["ok"]["vote"] for r, _ in self.fan(ids, dict(op="vote", p=p)) if "ok" in r
        ]

    def closes(self, parent):
        auth = self.owner.sign(b"stop" + context(self.config) + raw(parent)).hex()
        return [
            r["ok"]
            for r, _ in self.fan(self.procs, dict(op="close", parent=parent, auth=auth))
        ]


def denied(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected rejection")


def fault_run(n, q, e):
    with Lab(n, q, e, (0, 1)) as lab:
        a, b = (lab.make(1, buyer=x) for x in range(2))
        path = lab.path / "2" / "journal.db"
        # Copy the entire quiescent database. The same private key survives restoration.
        lab.stop(2)
        shutil.copyfile(path, lab.path / "old.db")
        lab.start(2)
        votes = lab.votes(range(q), a)
        verify_receipt(lab.config, receipt(a, votes, 0), pub(lab.owner), slot(1))
        # Buyer has this certificate. No publish or install request occurs.
        assert len(lab.votes(range(n), b)) < q
        reports = lab.closes(slot(1))
        denied(lambda: verify_reset(lab.config, slot(1), reports))
        lab.stop(2)
        shutil.copyfile(lab.path / "old.db", path)
        lab.start(2)
        after = lab.votes(range(n), b)
        if len(after) >= q:
            verify_receipt(lab.config, receipt(b, after, 0), pub(lab.owner), slot(1))
        assert (len(after) >= q) == (n == 7)
        print(
            json.dumps(
                dict(
                    test="hidden certificate + two equivocators + one restored signer",
                    n=n,
                    q=q,
                    first=len(votes),
                    second=len(after),
                )
            )
        )
        partial = lab.make(7)
        assert len(lab.votes([2, 3], partial)) == 2
        start = time.perf_counter_ns()
        lab.stop(3)
        lab.start(3)
        assert lab.votes([3], lab.make(7, buyer=1)) == []
        assert len(lab.votes([3], partial)) == 1
        print(
            json.dumps(
                dict(
                    test="restart/reject other/retry same",
                    elapsed_ms=(time.perf_counter_ns() - start) / 1e6,
                )
            )
        )
        # Cooperative fences even though two Byzantine voters report empty.
        for i, w in enumerate(([2, 3], [4, 5], [6])):
            assert len(lab.votes(w, lab.make(8, buyer=i))) == len(w)
        reports = lab.closes(slot(8))
        child = verify_reset(lab.config, slot(8), reports)
        for reply, _ in lab.fan(
            range(n), dict(op="reset", parent=slot(8), reports=reports)
        ):
            assert reply["ok"] == child
        next_p = proposal(lab.config, lab.owner, [(child, pub(lab.buyers[1]))], "tree")
        verify_receipt(
            lab.config,
            receipt(next_p, lab.votes(range(n), next_p), 0),
            pub(lab.owner),
            child,
        )
        print(
            json.dumps(
                dict(
                    test="certified fallback installed and spent",
                    n=n,
                    reports=len(reports),
                )
            )
        )
        # Race two concurrent clients, partitioning two different honest subsets.
        with futures.ThreadPoolExecutor(2) as workers:
            fs = [
                workers.submit(lab.votes, ids, lab.make(10, buyer=j))
                for j, ids in enumerate((range(q), [0, 1, *range(n - 3, n)]))
            ]
            counts = [len(f.result()) for f in fs]
        assert sum(c >= q for c in counts) <= 1
        print(
            json.dumps(
                dict(test="concurrent conflicting proposals", n=n, counts=counts)
            )
        )
        proof = receipt(a, votes, 0)
        for _ in range(2):
            assert (
                "ok" in lab.rpc(3, dict(op="install", parent=slot(1), proof=proof))[0]
            )
        assert "error" in lab.rpc(3, dict(op="install", parent=slot(9), proof=proof))[0]
        changed = dict(lab.config, keys=list(reversed(lab.config["keys"])))
        denied_auth = False
        try:
            verify_receipt(changed, proof, pub(lab.owner), slot(1))
        except Exception:
            denied_auth = True
        assert denied_auth
        for i in (0, 1):
            lab.stop(i)
        fresh = lab.make(12)
        assert len(lab.votes(lab.procs, fresh)) >= q
        print(
            json.dumps(dict(test="two silent; wrong predecessor/roster rejected", n=n))
        )


if __name__ == "__main__":
    fault_run(7, 5, 2)
    fault_run(8, 6, 3)
