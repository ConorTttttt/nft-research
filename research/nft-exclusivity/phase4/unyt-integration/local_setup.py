"""Attempt release CLI setup in a fresh isolated realm using generated role keys."""

import json
import re
import subprocess
import shutil
from pathlib import Path


def attempt(root, cli, release):
    def admin(*args):
        return cli("client", "call", "--port", "43995", *args)

    def record(stage, result):
        print(
            json.dumps(
                dict(stage=stage, status=result.returncode, tail=result.stdout[-2200:])
            ),
            flush=True,
        )
        return result.returncode == 0

    def agent():
        output = admin("new-agent").stdout
        return re.search(r"uhCAk[A-Za-z0-9_-]{48}", output).group()

    roles = [agent() for _ in range(11)]
    founder = roles[0]
    network = root / "local"
    network.mkdir()
    shutil.copytree(release / "alliance", network / "alliance")
    manifest = network / "alliance/dna.yaml"
    manifest.write_text(
        manifest.read_text()
        .replace(
            "properties: null", "properties:\n    progenitor_agent_pubkey: " + founder
        )
        .replace("00000000-0000-0000-0000-000000000000", "p4-local-" + founder)
    )
    if not record("pack isolated DNA", cli("dna", "pack", str(manifest.parent))):
        return
    shutil.copy(network / "alliance/alliance.dna", network / "alliance.dna")
    shutil.copy(release / "unyt/happ.yaml", network / "happ.yaml")
    if not record("pack local hApp", cli("app", "pack", str(network))):
        return
    if not record(
        "install local progenitor",
        admin(
            "install-app",
            "--app-id",
            "p4-progenitor",
            "--agent-key",
            founder,
            str(network / "unyt.happ"),
        ),
    ):
        return
    if not record("enable local progenitor", admin("enable-app", "p4-progenitor")):
        return
    args = [
        str(release / "unyt_cli"),
        "--admin-port",
        "43995",
        "--app-port",
        "43996",
        "--app-id",
        "p4-progenitor",
        "--conductor-config",
        str(root / "no-external-lair"),
        "--lair-passphrase-file",
        str(root / "no-pass"),
        "--allow-cap-grant-signing",
        "progenitor",
        "holofuel",
        "setup",
    ]
    for name, key in zip(
        [
            "hot-reserver",
            "hot-bridging-agent",
            "windtunnel-admin",
            "pricing-oracle",
            "fee-collector",
            "oracle",
            "global-infra-account",
            "holo-hosting-infra-account",
            "windtunnel-infra-account",
        ],
        roles[1:],
    ):
        args += ["--" + name, key]
    args += [
        "--special-agent",
        founder + "=100",
        "--no-hot-bridging-agreement",
        "--hot-bridge-url",
        "http://127.0.0.1:1",
    ]
    result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=120)
    result.stdout += result.stderr
    record("official local setup", result)
    if result.returncode == 0:
        from transfer import exercise

        exercise(root, cli, release, roles, network, record)
