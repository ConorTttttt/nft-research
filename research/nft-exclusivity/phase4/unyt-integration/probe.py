"""Run the stock release in an isolated memory network. No external app calls."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

happ, dna = map(Path, sys.argv[1:3])
with tempfile.TemporaryDirectory() as d:
    root = Path(d)

    def cli(*args):
        return subprocess.run(
            ["hc", *args],
            cwd=root,
            input="local-only",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=40,
        )

    dna_id = cli("dna", "hash", str(dna.resolve())).stdout.splitlines()[-1]
    with (root / "log").open("w") as log:
        p = subprocess.Popen(
            [
                "hc",
                "sandbox",
                "--piped",
                "-f=43995",
                "generate",
                "--root",
                d,
                "--in-process-lair",
                "-r=43996",
                str(happ.resolve()),
                "network",
                "-b",
                "http://127.0.0.1:1",
                "mem",
            ],
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        try:
            p.stdin.write(b"local-only")
            p.stdin.close()
            for _ in range(150):
                if (
                    "Conductor launched" in (root / "log").read_text()
                    or p.poll() is not None
                ):
                    break
                time.sleep(0.4)
            if p.poll() is not None:
                raise RuntimeError((root / "log").read_text()[-2000:])
            auth = cli(
                "client", "zome-call-auth", "--piped", "--port", "43995", "test-app"
            )
            print(
                json.dumps(
                    dict(stage="auth", status=auth.returncode, tail=auth.stdout[-600:])
                )
            )
            if not auth.returncode:
                for fn in ("whoami", "get_current_global_definition", "get_ledger"):
                    r = cli(
                        "client",
                        "zome-call",
                        "--piped",
                        "--port",
                        "43995",
                        "test-app",
                        dna_id,
                        "transactor",
                        fn,
                        "null",
                    )
                    print(
                        json.dumps(
                            dict(fn=fn, status=r.returncode, tail=r.stdout[-1100:])
                        )
                    )
            if "--setup" in sys.argv:
                from local_setup import attempt

                attempt(root, cli, happ.resolve().parent)
        finally:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=20)
