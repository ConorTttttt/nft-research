"""Loopback-only experimental signer. Parent harness controls fault injection."""

import json
import resource
import socketserver
import sqlite3
import sys
import time
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from protocol import (
    check,
    close_message,
    context,
    raw,
    require,
    statement,
    verify_receipt,
    verify_reset,
)


class Store:
    def __init__(self, directory, faulty):
        self.config = json.loads((directory / "config.json").read_text())
        self.key = Ed25519PrivateKey.from_private_bytes(
            (directory / "key").read_bytes()
        )
        self.index = self.config["keys"].index(
            self.key.public_key().public_bytes_raw().hex()
        )
        self.domain = context(self.config)
        self.faulty = faulty
        path = directory / "journal.db"
        self.db = sqlite3.connect(f"file:{path}?mode=rw", uri=True)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("SELECT prior,sealed FROM locks LIMIT 0")
        require(
            self.db.execute("SELECT domain,signer FROM identity").fetchall()
            == [(self.domain, self.index)],
            "journal belongs to a different domain or witness",
        )
        self.writes = 0

    def owner(self, p):
        row = self.db.execute("SELECT owner FROM rights WHERE id=?", (p,)).fetchone()
        require(row is not None, "unknown predecessor")
        return row[0]

    def run(self, r):
        op = r["op"]
        if op == "stats":
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return [self.writes, usage.ru_utime + usage.ru_stime, usage.ru_maxrss]
        if op == "fetch":
            row = self.db.execute(
                "SELECT body FROM bodies WHERE digest=?", (r["digest"],)
            ).fetchone()
            require(row is not None, "missing body")
            return json.loads(row[0])
        if op == "vote":
            p = r["p"]
            digest = statement(self.domain, p["mode"], p["moves"])
            require(
                all(to in self.config["users"] for _, to in p["moves"]),
                "unadmitted recipient",
            )
            owners = {self.owner(x) for x, _ in p["moves"]}
            require(len(owners) == 1, "mixed owners")
            check(owners.pop(), p["auth"], b"owner" + digest)
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                for x, _ in p["moves"]:
                    row = self.db.execute(
                        "SELECT prior,sealed FROM locks WHERE id=?", (x,)
                    ).fetchone()
                    if not self.faulty:
                        require(
                            not row or row[0] == digest.hex(), "reservation or closure"
                        )
                    self.db.execute(
                        "INSERT OR IGNORE INTO locks VALUES(?,?,0)", (x, digest.hex())
                    )
                self.db.execute(
                    "INSERT OR IGNORE INTO bodies VALUES(?,?)",
                    (digest.hex(), json.dumps(p)),
                )
            self.writes += 1
            start = time.perf_counter_ns()
            sig = self.key.sign(b"vote" + digest).hex()
            return dict(vote=[self.index, sig], sign_ns=time.perf_counter_ns() - start)
        parent = r["parent"]
        owner = self.owner(parent)
        if op == "close":
            check(owner, r["auth"], b"stop" + self.domain + raw(parent))
            with self.db:
                self.db.execute(
                    "INSERT INTO locks VALUES(?,NULL,1) ON CONFLICT(id) DO UPDATE SET sealed=1",
                    (parent,),
                )
                prior = self.db.execute(
                    "SELECT prior FROM locks WHERE id=?", (parent,)
                ).fetchone()[0]
            self.writes += 1
            if self.faulty:
                prior = None
            return [
                self.index,
                prior,
                self.key.sign(close_message(self.domain, parent, prior)).hex(),
            ]
        if op == "reset":
            child = verify_reset(self.config, parent, r["reports"])
        elif op == "install":
            child, owner = verify_receipt(self.config, r["proof"], owner, parent)
        else:
            raise ValueError("unknown request")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO rights VALUES(?,?)", (child, owner))
        self.writes += 1
        return child


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            r = json.loads(self.rfile.readline(1 << 20))
            response = {"ok": self.server.store.run(r)}
        except Exception as error:
            response = {"error": str(error) or type(error).__name__}
        self.wfile.write(json.dumps(response).encode() + b"\n")


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    store = Store(directory, sys.argv[2] == "faulty")
    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        server.store = store
        print(server.server_address[1], flush=True)
        server.serve_forever()
