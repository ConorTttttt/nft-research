"""Portable byte projection and a disposable, single-conductor publisher."""

from contextlib import contextmanager
import base64
import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from grant import raw, require


def encode(profile, config, parent, proof, evidence):
    profile.exercise(config, parent, proof, evidence)
    require(proof["n"] == 1 and proof["mode"] == "flat", "portable lab profile")
    q = config["q"]
    votes = sorted(proof["votes"])[:q]
    return b"".join(
        [
            b"P3G1",
            bytes((len(config["keys"]), q, config["e"])),
            profile.network,
            raw(profile.issuer),
            *map(raw, config["users"]),
            *map(raw, config["keys"]),
            raw(parent),
            raw(proof["auth"], 64),
            *(bytes([i]) + raw(s, 64) for i, s in votes),
            bytes([int(evidence[0] == "paid")]),
            raw(evidence[1], 64),
        ]
    )


@contextmanager
def sandbox(wasm, integrity, coordinator, properties):
    from conductor_test import hc

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dna = root / "dna"
        dna.mkdir()
        for name in (integrity, coordinator):
            shutil.copy(Path(wasm) / (name + ".wasm"), dna)
        manifest = dict(
            manifest_version="0",
            name="archive",
            integrity=dict(
                network_seed="phase3-local",
                properties=properties,
                zomes=[dict(name=integrity, path=integrity + ".wasm")],
            ),
            coordinator=dict(
                zomes=[
                    dict(
                        name=coordinator,
                        path=coordinator + ".wasm",
                        dependencies=[dict(name=integrity)],
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
                            name="archive",
                            provisioning=dict(strategy="create", deferred=False),
                            dna=dict(path="dna/archive.dna", clone_limit=0),
                        )
                    ],
                )
            )
        )
        hc("dna", "pack", str(dna), cwd=root)
        hc("app", "pack", str(root), cwd=root)
        dna_id = hc(
            "dna", "hash", str(dna / "archive.dna"), cwd=root
        ).stdout.splitlines()[-1]
        port = "43985"
        log_path = root / "log"
        with log_path.open("w") as log:
            runner = subprocess.Popen(
                [
                    "hc",
                    "sandbox",
                    "--piped",
                    "-f=" + port,
                    "generate",
                    "--root",
                    tmp,
                    "--in-process-lair",
                    "-r=43986",
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
            try:
                runner.stdin.write(b"phase2-fixture")
                runner.stdin.close()
                for _ in range(180):
                    if "Conductor launched" in log_path.read_text():
                        break
                    if runner.poll() is not None:
                        raise RuntimeError(log_path.read_text()[-2000:])
                    time.sleep(0.5)
                auth = hc(
                    "client",
                    "zome-call-auth",
                    "--piped",
                    "--port",
                    port,
                    "test-app",
                    cwd=root,
                    secret=True,
                    check_result=False,
                )
                if auth.returncode:
                    raise RuntimeError(
                        auth.stdout[-1800:] + log_path.read_text()[-3200:]
                    )

                def call(fn, payload):
                    return hc(
                        "client",
                        "zome-call",
                        "--piped",
                        "--port",
                        port,
                        "test-app",
                        dna_id,
                        coordinator,
                        fn,
                        json.dumps(payload),
                        cwd=root,
                        secret=True,
                        check_result=False,
                    )

                yield dna_id, call
            finally:
                if runner.poll() is None:
                    os.killpg(runner.pid, signal.SIGTERM)
                runner.wait(timeout=15)


def roundtrip(pin, blob, wasm):
    with sandbox(
        wasm, "grant_integrity", "grant_coordinator", dict(domain=list(pin))
    ) as (_, call):
        start = time.perf_counter()
        write = call("publish", list(blob))
        assert write.returncode == 0, write.stdout
        addr = json.loads(write.stdout.splitlines()[-1])
        published = time.perf_counter()
        for _ in range(15):
            read = call("retrieve", addr)
            assert read.returncode == 0, read.stdout
            if json.loads(read.stdout.splitlines()[-1]) == list(blob):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("evidence not integrated")
        retrieved = time.perf_counter()
        changed = list(blob)
        changed[-1] ^= 1
        invalid = call("publish", changed)
        assert invalid.returncode and "signature" in invalid.stdout, invalid.stdout
        return dict(
            action=base64.urlsafe_b64encode(bytes(addr)).decode(),
            publish_cli_ms=(published - start) * 1000,
            retrieval_cli_ms=(retrieved - published) * 1000,
            edited_proof="rejected",
        )


def mint_fixture(wasm):
    props = dict(
        name="Phase 3 test collection",
        symbol="TEST",
        max_supply=0,
        minter_pubkey=None,
        royalty_bps=0,
        transfer_window_secs=300,
    )
    with sandbox(wasm, "nft_integrity", "nft", props) as (dna_id, call):
        result = call("mint_nft", dict(metadata_hash=list(range(32))))
        assert result.returncode == 0, result.stdout
        # CLI prints compact JSON. The action is scoped by the actual DNA.
        mint = json.loads(result.stdout.splitlines()[-1])["nft"]
        return dna_id, bytes(mint)
