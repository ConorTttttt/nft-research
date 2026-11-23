"""Publish live witness evidence to a disposable stock 0.7.1 conductor."""

import base64
import os
import re
import signal
from copy import deepcopy
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from lab import Lab, pub, slot
from protocol import proposal, receipt, verify_receipt, verify_reset


def hc(*args, cwd, secret=False, check_result=True):
    return subprocess.run(
        ["hc", *args],
        cwd=cwd,
        input="phase2-fixture" if secret else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check_result,
        timeout=60,
    )


def b(value):
    return list(bytes.fromhex(value))


def tree(proof):
    return dict(
        Tree=dict(
            n=proof["n"],
            i=proof["i"],
            to=b(proof["move"][1]),
            path=list(map(b, proof["path"])),
            auth=b(proof["auth"]),
            votes=[[i, b(s)] for i, s in proof["votes"]],
        )
    )


def smoke(root):
    dna = root / "dna"
    dna.mkdir()
    wasm = Path(os.environ["WASM_DIR"])

    def anchor(cfg):
        props = dict(
            keys=list(map(b, cfg["keys"])),
            users=list(map(b, cfg["users"])),
            q=cfg["q"],
            e=cfg["e"],
        )
        for name in ("phase2_integrity", "phase2_coordinator"):
            shutil.copyfile(wasm / (name + ".wasm"), dna / (name + ".wasm"))
        manifest = dict(
            manifest_version="0",
            name="recovery_lab",
            integrity=dict(
                network_seed="phase2-local",
                properties=props,
                zomes=[dict(name="phase2_integrity", path="phase2_integrity.wasm")],
            ),
            coordinator=dict(
                zomes=[
                    dict(
                        name="phase2_coordinator",
                        path="phase2_coordinator.wasm",
                        dependencies=[dict(name="phase2_integrity")],
                    )
                ]
            ),
        )
        (dna / "dna.yaml").write_text(json.dumps(manifest))
        (root / "happ.yaml").write_text(
            json.dumps(
                dict(
                    manifest_version="0",
                    name="lab",
                    roles=[
                        dict(
                            name="rights",
                            provisioning=dict(strategy="create", deferred=False),
                            dna=dict(path="dna/recovery_lab.dna", clone_limit=0),
                        )
                    ],
                )
            )
        )
        hc("dna", "pack", str(dna), cwd=root)
        hc("app", "pack", str(root), cwd=root)
        digest = hc(
            "dna", "hash", str(dna / "recovery_lab.dna"), cwd=root
        ).stdout.splitlines()[-1]
        (root / "hash").write_text(digest)
        return base64.urlsafe_b64decode(digest[1:] + "===")[3:35].hex()

    with Lab(8, 6, 3, (0, 1), anchor_for=anchor) as lab:
        dna_hash = (root / "hash").read_text()
        with (root / "conductor.log").open("w") as log:
            port = "43785"
            runner = subprocess.Popen(
                [
                    "hc",
                    "sandbox",
                    "--piped",
                    "-f=" + port,
                    "generate",
                    "--root",
                    str(root),
                    "--in-process-lair",
                    "-r=43786",
                    str(root / "lab.happ"),
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
            runner.stdin.write(b"phase2-fixture")
            runner.stdin.close()
            try:
                for _ in range(180):
                    if "Conductor launched" in (root / "conductor.log").read_text():
                        break
                    if runner.poll() is not None:
                        raise RuntimeError((root / "conductor.log").read_text()[-1200:])
                    time.sleep(0.5)
                hc(
                    "client",
                    "zome-call-auth",
                    "--piped",
                    "--port",
                    port,
                    "test-app",
                    cwd=root,
                    secret=True,
                )

                def publish(history, valid, reason="invalid signature"):
                    start = time.perf_counter()
                    result = hc(
                        "client",
                        "zome-call",
                        "--piped",
                        "--port",
                        port,
                        "test-app",
                        dna_hash,
                        "phase2_coordinator",
                        "publish",
                        json.dumps(history),
                        cwd=root,
                        secret=True,
                        check_result=False,
                    )
                    if valid:
                        assert result.returncode == 0 and re.search(
                            r"\[132,41,36,", result.stdout
                        ), result.stdout
                    else:
                        assert (
                            result.returncode and reason in result.stdout
                        ), result.stdout
                    return round((time.perf_counter() - start) * 1000, 2)

                p = lab.make(0, 8, mode="tree")
                proof = receipt(p, lab.votes(range(6), p), 4)
                verify_receipt(lab.config, proof, pub(lab.owner), slot(4))
                # Withhold publication while a conflicting spend fails at the witnesses.
                time.sleep(0.25)
                assert len(lab.votes(range(8), lab.make(4, buyer=2, mode="tree"))) < 6
                history = dict(genesis=4, steps=[tree(proof)])
                ms = publish(history, True)
                edited = deepcopy(history)
                edited["steps"][0]["Tree"]["path"][0][0] ^= 1
                publish(edited, False)
                reports = lab.closes(slot(18))
                child = verify_reset(lab.config, slot(18), reports)
                for response, _ in lab.fan(
                    range(8), dict(op="reset", parent=slot(18), reports=reports)
                ):
                    assert response["ok"] == child
                retry = proposal(
                    lab.config, lab.owner, [(child, pub(lab.buyers[0]))], "tree"
                )
                after = receipt(retry, lab.votes(range(6), retry), 0)
                reset = dict(
                    Reset=dict(
                        reports=[
                            [i, None if d is None else b(d), b(s)]
                            for i, d, s in reports
                        ]
                    )
                )
                short = deepcopy(reset)
                short["Reset"]["reports"] = short["Reset"]["reports"][:5]
                publish(dict(genesis=18, steps=[short]), False, "inconclusive closure")
                repeated = deepcopy(reset)
                repeated["Reset"]["reports"][2] = repeated["Reset"]["reports"][1]
                publish(dict(genesis=18, steps=[repeated]), False, "report index")
                reset_ms = publish(dict(genesis=18, steps=[reset, tree(after)]), True)
                print(
                    json.dumps(
                        dict(
                            stock_conductor="0.7.1",
                            witnesses=8,
                            requested_hold_ms=250,
                            delayed_leaf_publish_cli_ms=ms,
                            reset_then_transfer_publish_cli_ms=reset_ms,
                            tampered_path="InvalidCommit",
                            insufficient_fence="InvalidCommit",
                            duplicate_reporter="InvalidCommit",
                        )
                    )
                )
            finally:
                if runner.poll() is None:
                    os.killpg(runner.pid, signal.SIGTERM)
                runner.wait(timeout=15)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        smoke(Path(tmp))
