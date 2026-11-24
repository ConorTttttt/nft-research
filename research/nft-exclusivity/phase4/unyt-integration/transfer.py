"""Cooperative local payment experiment. Every key here is generated in the sandbox."""

import base64
import json
import os
import re
import subprocess
from pathlib import Path
import time

import msgpack


def raw(h):
    return list(base64.urlsafe_b64decode(h[1:] + "==="))


def h64(o):
    if isinstance(o, str):
        return o
    if isinstance(o, dict):
        for k in ("id", "hash", "action_hash"):
            if k in o:
                return h64(o[k])
        raise ValueError("no id in " + str(o)[:300])
    return "u" + base64.urlsafe_b64encode(bytes(o)).decode().rstrip("=")


def exercise(root, cli, release, roles, network, record):
    def admin(*args):
        return cli("client", "call", "--port", "43995", *args)

    def log(label, obj):
        print(
            json.dumps({"step": label, "value": obj}, separators=(",", ":")), flush=True
        )

    founder, buyer = roles[:2]
    app = "p4-progenitor"
    buyer_app = "p4-buyer"
    if not record(
        "install buyer",
        admin(
            "install-app",
            "--app-id",
            buyer_app,
            "--agent-key",
            buyer,
            str(network / "unyt.happ"),
        ),
    ):
        return
    if not record("enable buyer", admin("enable-app", buyer_app)):
        return
    dna = cli("dna", "hash", str(network / "alliance.dna")).stdout.splitlines()[-1]
    for ident in (app, buyer_app):
        if not record(
            "authorize " + ident,
            cli("client", "zome-call-auth", "--piped", "--port", "43995", ident),
        ):
            return

    def call(ident, fn, body, optional=False):
        started = time.perf_counter_ns()
        r = cli(
            "client",
            "zome-call",
            "--piped",
            "--port",
            "43995",
            ident,
            dna,
            "transactor",
            fn,
            json.dumps(body),
        )
        if r.returncode:
            log(fn, {"error": r.stdout[-1100:]})
            if optional:
                return None
            raise RuntimeError(fn + " refused")
        log("wall_us", {"fn": fn, "us": (time.perf_counter_ns() - started) / 1000})
        obj = json.loads(r.stdout.splitlines()[-1])
        log(fn, obj)
        return obj

    log("roles", dict(dna=dna, seller=founder, buyer=buyer))

    def checked():
        limit = call(app, "get_my_current_applied_credit_limit", None, True)
        gd = call(app, "get_current_global_definition", None)
        # Use the official release CLI for the current prospective credit calculation.
        cmd = [
            str(release / "unyt_cli"),
            "--admin-port",
            "43995",
            "--app-port",
            "43996",
            "--app-id",
            app,
            "--conductor-config",
            str(root / "no-external-lair"),
            "--lair-passphrase-file",
            str(root / "no-pass"),
            "--allow-cap-grant-signing",
            "zome_call",
            "credit_limit",
        ]
        cr = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=45)
        log("computed credit", cr.stdout[-1500:] + cr.stderr[-300:])
        call(app, "get_ledger", None)
        c = call(
            app,
            "create_commitment",
            dict(counterparty=buyer, amount={"0": "-10"}, note="P4 local seed"),
        )
        aid = h64(c)
        accepted = call(
            buyer_app, "create_accept", dict(commitment=aid, note="P4 seed")
        )
        call(buyer_app, "get_ledger", None)
        # The seed recipient has the credited balance on the accepted history.
        return gd, aid, h64(accepted)

    try:
        gd, seed, accepted_seed = checked()
    except (RuntimeError, ValueError) as e:
        log("funding gate", str(e))
        return

    def source(name):
        repo = os.environ["HNFT_REPO"]
        return subprocess.check_output(
            [
                "git",
                "-C",
                repo,
                "show",
                "8fd2391e2f9f584c19dcb329bb21bc034f1bf19e:unyt/nft_sale_settlement/"
                + name,
            ],
            text=True,
        ).replace("buyer_spends", "buyer_spender_allocations")

    def fixture(name):
        return json.loads(source(name + ".json"))

    try:
        code = dict(
            title="p4_local_sale_v1",
            execution_code=list(msgpack.packb(source("execution_code.rhai"))),
            **fixture("other_options")
        )
        for field in (
            "agreement_definition_input",
            "runtime_input_signature",
            "output_signature",
        ):
            code[field] = fixture(field)
        ct = h64(call(app, "create_code_template", code))
        rules = fixture("agreements/example_agreement_rules")
        asset = os.environ["P4_ASSET"]
        rules["code_template_id"] = raw(ct)
        for name, value in (("seller", founder), ("nft_id", asset)):
            next(i for i in rules["input_rules"] if i["name"] == name)[
                "instruction"
            ] = {"Fixed": value}
        rules["roles"][0]["qualification"] = {"Authorized": [buyer]}
        agreement = h64(call(app, "create_smart_agreement", rules))
        park = call(
            buyer_app,
            "create_parked_spend",
            dict(
                ea_id=raw(agreement),
                executor=raw(founder),
                ct_role_id="buyer_spender",
                amount={"0": "10"},
                spender_payload={},
            ),
        )
        from title import certify
        import hashlib

        reservation = certify(
            dict(
                asset=asset,
                dna=dna,
                buyer=buyer,
                seller=founder,
                amount="10",
                unit="0",
                definition=h64(gd),
                park=h64(park),
                agreement=agreement,
                template=ct,
                script_sha256=hashlib.sha256(
                    source("execution_code.rhai").encode()
                ).hexdigest(),
                release="exclusive irrevocable seller credit",
                refund="exclusive exclusion of seller credit",
            )
        )
        log("verified conditional grant", reservation)
        run = call(
            app,
            "execute_rave",
            dict(
                ea_id=raw(agreement), global_definition=raw(h64(gd)), executor_inputs={}
            ),
        )
        rave, action = run
        rid = h64(action)
        allocation = rave["output"]["unyt_allocation"]
        assert allocation == [
            dict(amounts={"0": "10"}, receiver=founder, sources=[h64(park)])
        ]
        assert (
            h64(rave["smart_agreement"]) == agreement
            and h64(rave["code_template"]) == ct
        )
        before = call(app, "get_ledger", None)
        tx = call(buyer_app, "get_transaction", rid, True)
        if tx is None:
            tx = call(buyer_app, "get_transaction", raw(rid), True)
        receipt = call(
            app, "create_receipt_from_rave", dict(hash=rid, note="P4 local sale"), True
        )
        if receipt is None and tx:
            call(app, "create_collect_from_rave", tx, True)
        after = call(app, "get_ledger", None)
        from decimal import Decimal

        assert Decimal(after["balance"]["0"]) - Decimal(before["balance"]["0"]) == 10
        assert tx and tx["details"]["RAVE"]["output"]["unyt_allocation"] == allocation
        log(
            "independent acceptance",
            {"run": rid, "status": "Pending", "reason": "no native exclusion proof"},
        )
        for label, record_id in (
            ("funding", seed),
            ("accept", accepted_seed),
            ("park", h64(park)),
            ("execution", rid),
            ("receipt", h64(receipt)),
        ):
            found = call(buyer_app, "hdk_must_get_valid_record", record_id)
            log("historical record " + label, {"id": record_id, "record": found})
        # Independent negative-path control on a NEW conventional commitment.
        extra = call(
            app,
            "create_commitment",
            dict(
                counterparty=buyer,
                amount={"0": "-1"},
                note="separate rejection control",
            ),
        )
        rejected = call(
            buyer_app,
            "create_reject_proposal",
            dict(proposal=h64(extra), note="declined"),
            True,
        )
        if rejected:
            call(
                app,
                "create_reclaim_balance",
                dict(rejection=h64(rejected), note="return distinct input"),
                True,
            )
    except (RuntimeError, ValueError) as e:
        log("execution gate", str(e))
        raise
