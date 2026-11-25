"""Exercise sealed lab resources with Phase 4 SQLite guards and fresh disposable keys."""

import json
import importlib.util
import sys
import tempfile
import sqlite3
from contextlib import closing
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from settlement import (
    verify_onward,
    ballot,
    check,
    digest,
    encode,
    pack,
    parents,
    verify,
    verify_sig,
)

baseline = Path(__file__).resolve().parents[2] / "phase4/prototype/trial.py"
spec = importlib.util.spec_from_file_location("phase4_fixture", baseline)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
Member, public = fixture.Member, fixture.public


def micros(start):
    return (time.perf_counter_ns() - start) / 1000


def simulate(root, capture, directory):
    groups = {
        name: [Member(root / f"{name}{i}") for i in range(7)]
        for name in ("source", "title", "payment")
    }
    buyer, seller = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    owners = {"source": seller, "title": seller, "payment": buyer}
    grant = next(
        r["value"]["terms"]
        for l in capture.read_text().splitlines()
        if (r := json.loads(l)).get("step") == "verified conditional grant"
    )
    for i in range(24):
        policy = {
            "profile": "lab-P5J1",
            "owners": {k: public(v).hex() for k, v in owners.items()},
            "rosters": {k: [public(m.key).hex() for m in v] for k, v in groups.items()},
            "origin": [grant["asset"], "lab-provisioned-version", i],
            "destination": ["test-realm", "epoch-1"],
            "payment": [
                grant["dna"],
                grant["definition"],
                grant["park"],
                "simulated-partition",
                i,
                "0",
                10,
            ],
        }
        terms = {
            "agreement": grant["agreement"],
            "version": 1,
            "rule": "both-prepare",
            "price": 10,
            "unit": "0",
            "buyer": public(buyer).hex(),
            "seller": public(seller).hex(),
        }
        tx = digest("sale", [digest("policy", policy), terms])
        origin, dest, title, pay = parents(policy)

        def decide(parent, choice):
            side = parent[0]
            return ballot(policy, parent, choice, owners[side], groups[side])

        sale_start = time.perf_counter_ns()
        export = decide(origin, ["export", dest])
        assert check(policy, export, origin) == ("export", dest)
        export_us = micros(sale_start)
        start = time.perf_counter_ns()
        try:
            decide(origin, ["export", digest("other", "destination")])
        except ValueError:
            pass
        else:
            raise AssertionError("duplicate export")
        duplicate = micros(start)
        scenario = i % 3
        other = digest(
            "sale",
            [
                digest("policy", policy),
                dict(terms, agreement=digest("other-agreement", i)),
            ],
        )

        def timed(parent, choice):
            begin = time.perf_counter_ns()
            return decide(parent, choice), micros(begin)

        start = time.perf_counter_ns()
        with ThreadPoolExecutor(2) as pool:
            left = pool.submit(timed, title, ["prepare", tx])
            right = pool.submit(
                timed,
                pay,
                [
                    "decline" if scenario == 1 else "prepare",
                    other if scenario == 2 else tx,
                ],
            )
            (nft, _), (funding, prepare_us) = left.result(), right.result()
        proof = pack({"export": export, "title": nft, "payment": funding})
        expected = "FinalPaid" if scenario == 0 else "FinalVoid"
        cpu = time.process_time_ns()
        assert verify(policy, terms, proof) == expected
        cpu_us = (time.process_time_ns() - cpu) / 1000
        elapsed = micros(start)
        # Only return this sale's prepared input. A foreign payment remains committed to its own sale.
        assert (
            verify(policy, terms, pack({"export": export, "title": nft})) == "Pending"
        )
        assert (
            verify(
                policy, terms, pack({"export": export, "title": nft}), unavailable=True
            )
            == "UnavailableEvidence"
        )
        assert verify(policy, terms, proof, profile="native") == "Invalid"
        assert (
            verify(policy, terms, b"observed historical records", profile="native")
            == "Pending"
        )
        corrupt = json.loads(proof[4:])
        corrupt["payment"][2][0][1] = "00" * 64
        assert verify(policy, terms, pack(corrupt)) == "Invalid"
        # Separate idempotent exercise name per prepared title version.
        parent = ["successor", digest("exercise", [title, tx, expected])]
        owner = buyer if expected == "FinalPaid" else seller
        target = public(Ed25519PrivateKey.generate()).hex()
        message = digest("onward", [digest("policy", policy), parent, target])
        sig = owner.sign(bytes.fromhex(message))
        start = time.perf_counter_ns()
        votes = []
        for member in groups["title"][:5]:
            assert verify(policy, terms, proof) == expected
            verify_sig(
                terms["buyer" if expected == "FinalPaid" else "seller"],
                sig.hex(),
                message,
            )
            votes.append(
                member.vote(bytes.fromhex(parent[1]), bytes.fromhex(message)).hex()
            )
        for key, v in zip(policy["rosters"]["title"], votes):
            verify_sig(key, v, message)
        onward = micros(start)
        transfer = [target, sig.hex(), votes]
        assert verify_onward(policy, terms, proof, transfer)
        start = time.perf_counter_ns()
        for replica in groups["payment"][:4]:
            replica.archive(bytes.fromhex(tx), proof)
        archive = micros(start)
        start = time.perf_counter_ns()
        with closing(sqlite3.connect(groups["payment"][3].path)) as db:
            recovered = db.execute(
                "select body from archive where id=?", (bytes.fromhex(tx),)
            ).fetchone()[0]
        assert verify(policy, terms, recovered) == expected
        recover = micros(start)
        store_bytes = sum(
            m.path.stat().st_size for roster in groups.values() for m in roster
        )
        if i == 0:
            directory.mkdir(exist_ok=True)
            (directory / "policy.json").write_bytes(encode(policy))
            (directory / "terms.json").write_bytes(encode(terms))
            (directory / "proof").write_bytes(proof)
            (directory / "onward.json").write_bytes(encode(transfer))
        print(
            json.dumps(
                dict(
                    i=i,
                    outcome=expected,
                    bytes=len(proof),
                    prepare_wall_us=prepare_us,
                    settlement_wall_us=elapsed,
                    verify_cpu_us=cpu_us,
                    export_wall_us=export_us,
                    archive_wall_us=archive,
                    recovery_wall_us=recover,
                    db_bytes=store_bytes,
                    onward_wall_us=onward,
                    duplicate_export_us=duplicate,
                )
            )
        )


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        simulate(Path(tmp), Path(sys.argv[1]), Path(sys.argv[2]))
