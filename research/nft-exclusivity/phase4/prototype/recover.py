"""Offline buyer recovery after the writer processes and all their keys are gone."""

from pathlib import Path
from contextlib import closing
import sqlite3
import subprocess
import sys
import tempfile

path = Path(sys.argv[1])
pin = (path / "root").read_text()
grant = (path / "grant").read_text()
with closing(
    sqlite3.connect(f"file:{path}/survivor.sqlite?mode=ro", uri=True)
) as replica:
    record = replica.execute(
        "select body from archive where id=?", (bytes.fromhex(grant),)
    ).fetchone()
with tempfile.TemporaryDirectory() as tmp:
    body = Path(tmp) / "proof"

    def outcome():
        return subprocess.check_output(
            [sys.argv[2], "lab", pin, grant, body], text=True
        ).strip()

    assert outcome() == "Pending"
    if record:
        body.write_bytes(record[0])
        assert outcome() == "Paid"
        print(
            "Recovered Paid from one surviving replica, no signing keys; bytes",
            len(record[0]),
        )
        if len(sys.argv) > 3:
            Path(sys.argv[3]).write_bytes(record[0])
