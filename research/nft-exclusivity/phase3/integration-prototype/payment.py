"""Test ledger. Each provisioned coin is dedicated to one NFT genesis slot."""

import json
import sqlite3
import subprocess
from contextlib import closing

from grant import PRICE, PREFIX, check, require, terminal_message


class Ledger:
    def __init__(self, path, profile, config, key, engine, script):
        require(
            key.public_key().public_bytes_raw().hex() == profile.issuer,
            "issuer key mismatch",
        )
        self.path, self.profile, self.config = path, profile, config
        self.key, self.engine, self.script = key, engine, script

    def fund(self, parents):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "CREATE TABLE coins(parent TEXT PRIMARY KEY, state TEXT NOT NULL, sale BLOB, proof TEXT, allocation TEXT)"
            )
            db.executemany(
                "INSERT INTO coins(parent,state) VALUES(?,'free')",
                ((p,) for p in parents),
            )

    def apply(self, parent, proof, command, authorization=None):
        sale = self.profile.commitment(self.config, parent, proof)
        require(command in ("reserve", "paid", "void"), "command")
        if command == "reserve":
            check(self.config["users"][1], authorization, PREFIX + b"/reserve" + sale)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state,sale FROM coins WHERE parent=?", (parent,)
            ).fetchone()
            require(row is not None and row[1] in (None, sale), "dedicated coin")
            state = row[0]
            if state in ("paid", "void"):
                require(state == command, "already final")
            elif command == "paid":
                require(state == "reserve", "unfunded sale")
                run = subprocess.run(
                    [
                        self.engine,
                        self.script,
                        self.config["users"][0],
                        parent,
                        sale.hex(),
                        str(PRICE),
                        str(PRICE),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                db.execute(
                    "UPDATE coins SET allocation=? WHERE parent=?", (run.stdout, parent)
                )
            db.execute(
                "UPDATE coins SET state=?,sale=?,proof=? WHERE parent=?",
                (command, sale, json.dumps(proof), parent),
            )
        if command != "reserve":
            return command, self.key.sign(terminal_message(sale, command)).hex()

    def recover(self, parent):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute(
                "SELECT state,proof FROM coins WHERE parent=?", (parent,)
            ).fetchone()
        if row and row[0] in ("paid", "void"):
            proof = json.loads(row[1])
            return proof, self.apply(parent, proof, row[0])
        return None
