"""Run from any directory with fresh local keys and dedicated test coins."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess
import time
from cryptography.exceptions import InvalidSignature
from grant import Profile, PREFIX, context, H, NETWORK
from payment import Ledger
from archive_io import encode, roundtrip, mint_fixture
from lab import key, pub, slot
from protocol import receipt, proposal, verify_receipt
from grant_witness import GrantLab


def reject(fn):
    try:
        fn()
    except (ValueError, InvalidSignature):
        return
    raise AssertionError("expected rejection")


def run(args):
    issuer = key()
    network = NETWORK
    if args.mint_wasm:
        dna, action = mint_fixture(args.mint_wasm)
        network = H(b"p3/mint-fixture", NETWORK, dna.encode(), action)
        print(
            json.dumps(
                dict(
                    source_dna=dna,
                    mint_action=action.hex(),
                    test_realm=network.hex(),
                    mapped_slot=0,
                )
            ),
            flush=True,
        )
    profile = Profile(pub(issuer), network)
    with GrantLab(profile) as lab:
        cfg = lab.config
        ledger = Ledger(
            lab.path / "payment.db", profile, cfg, issuer, args.engine, args.script
        )
        ledger.fund(slot(i) for i in range(24))
        for i in range(24):
            parent = slot(i)
            start = time.perf_counter_ns()
            listing = lab.make(i)
            proof = receipt(listing, lab.votes(range(5), listing), 0)
            sale = profile.commitment(cfg, parent, proof)
            committed = time.perf_counter_ns()
            reserve = lab.buyers[0].sign(PREFIX + b"/reserve" + sale).hex()
            reject(lambda: ledger.apply(parent, proof, "paid"))
            reserve_start = time.perf_counter_ns()
            if i != 1:
                ledger.apply(parent, proof, "reserve", reserve)
            if i == 0:
                unavailable = Ledger(
                    ledger.path,
                    profile,
                    cfg,
                    issuer,
                    str(lab.path / "absent-engine"),
                    args.script,
                )
                try:
                    unavailable.apply(parent, proof, "paid")
                except FileNotFoundError:
                    assert ledger.recover(parent) is None
                else:
                    raise AssertionError("expected unavailable engine")
            reserved = time.perf_counter_ns()
            if i == 2:

                def compete(cmd):
                    try:
                        return ledger.apply(parent, proof, cmd)
                    except ValueError:
                        return None

                with ThreadPoolExecutor(2) as pool:
                    contenders = list(pool.map(compete, ("paid", "void")))
                assert sum(x is not None for x in contenders) == 1
                evidence = next(x for x in contenders if x)
            else:
                evidence = ledger.apply(parent, proof, "void" if i == 1 else "paid")
            settled = time.perf_counter_ns()
            child, owner = profile.exercise(cfg, parent, proof, evidence)
            verified = time.perf_counter_ns()
            blob = encode(profile, cfg, parent, proof, evidence)
            assert owner == cfg["users"][int(evidence[0] == "paid")]
            restored = Ledger(
                ledger.path, profile, cfg, issuer, args.engine, args.script
            )
            recovery_start = time.perf_counter_ns()
            recovered_proof, recovered_evidence = restored.recover(parent)
            assert profile.exercise(
                cfg, parent, recovered_proof, recovered_evidence
            ) == (child, owner)
            recovery_end = time.perf_counter_ns()
            reject(
                lambda: ledger.apply(
                    parent, proof, "void" if evidence[0] == "paid" else "paid"
                )
            )
            reject(
                lambda: profile.exercise(cfg, parent, proof, (evidence[0], "00" * 64))
            )
            reject(
                lambda: Profile(pub(issuer), b"x" * 32).exercise(
                    cfg, parent, proof, evidence
                )
            )
            reject(lambda: profile.exercise(cfg, slot(i + 1), proof, evidence))
            if i in (0, 1):

                def send(request):
                    return [reply for reply, _ in lab.fan(range(5), request)]

                assert all(
                    "error" in r
                    for r in send(dict(op="install", parent=parent, proof=proof))
                )
                assert all(
                    r.get("ok") == child
                    for r in send(
                        dict(
                            op="install_grant",
                            parent=parent,
                            proof=proof,
                            terminal=evidence,
                        )
                    )
                )
                controller = lab.buyers[0] if evidence[0] == "paid" else lab.owner
                onward = proposal(
                    cfg, controller, [(child, pub(lab.buyers[1]))], "flat"
                )
                votes = lab.votes(range(5), onward)
                successor = verify_receipt(cfg, receipt(onward, votes, 0), owner, child)
                assert successor[1] == pub(lab.buyers[1])
                rival = proposal(cfg, controller, [(child, pub(lab.buyers[2]))], "flat")
                assert len(lab.votes(range(7), rival)) < 5
            if i == 0:
                for price in ("9", "11", "0"):
                    attempt = subprocess.run(
                        [
                            args.engine,
                            args.script,
                            cfg["users"][0],
                            parent,
                            sale.hex(),
                            "10",
                            price,
                        ],
                        capture_output=True,
                    )
                    assert (
                        attempt.returncode
                        and b"exactly the agreed price" in attempt.stderr
                    )
                if args.wasm:
                    print(
                        json.dumps(roundtrip(context(cfg), blob, args.wasm)), flush=True
                    )
            print(
                json.dumps(
                    dict(
                        slot=i,
                        outcome=evidence[0],
                        bytes=len(blob),
                        commit_us=(committed - start) / 1000,
                        reserve_us=(reserved - reserve_start) / 1000,
                        settle_us=(settled - reserved) / 1000,
                        exercise_us=(verified - settled) / 1000,
                        recover_us=(recovery_end - recovery_start) / 1000,
                        db_bytes=ledger.path.stat().st_size,
                        latency_us=(verified - start - (reserve_start - committed))
                        / 1000,
                    )
                ),
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--wasm")
    parser.add_argument("--mint-wasm")
    run(parser.parse_args())
