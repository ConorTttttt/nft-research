"""Compare Python and native Rust on both fixed rosters and outcome tags."""

import json
import subprocess
import sys
from pathlib import Path
from archive_io import encode
from grant import Profile, context, terminal_message
from lab import Lab, key, pub, slot
from protocol import receipt


def run(executable):
    for n, q, e in ((7, 5, 2), (8, 6, 3)):
        signer = key()
        profile = Profile(pub(signer))
        with Lab(n, q, e, anchor_for=profile.anchor) as lab:
            cfg = lab.config
            pin = lab.path / "pin"
            pin.write_bytes(context(cfg))
            path = lab.path / "proof"

            def native(blob):
                path.write_bytes(blob)
                return subprocess.run(
                    [executable, pin, path], capture_output=True, text=True
                )

            for i, tag in enumerate(("void", "paid")):
                parent = slot(i)
                proposal = lab.make(i)
                proof = receipt(proposal, lab.votes(range(q), proposal), 0)
                sale = profile.commitment(cfg, parent, proof)
                evidence = tag, signer.sign(terminal_message(sale, tag)).hex()
                blob = encode(profile, cfg, parent, proof, evidence)
                result = native(blob)
                assert result.returncode == 0 and tuple(
                    result.stdout.splitlines()
                ) == profile.exercise(cfg, parent, proof, evidence)
                mutants = [blob[:-1], blob + b"x", b"x" * 1537]
                # Edit one byte of each proof field, including every participant.
                offsets = [0, 4, 5, 6, 7, 39, 71, 103, 135, 167]
                offsets += [199 + 32 * j for j in range(n + 1)]
                auth = 199 + 32 * n + 32
                offsets += (
                    [auth]
                    + [auth + 64 + 65 * j for j in range(q)]
                    + [len(blob) - 65, len(blob) - 1]
                )
                for offset in offsets:
                    edited = bytearray(blob)
                    edited[offset] ^= 1
                    mutants.append(edited)
                for invalid in mutants:
                    assert native(invalid).returncode != 0
                reference = dict(
                    profile=dict(network=profile.network.hex(), issuer=profile.issuer),
                    config=cfg,
                    parent=parent,
                    proof=proof,
                    evidence=evidence,
                )
                print(
                    json.dumps(
                        dict(
                            n=n,
                            q=q,
                            tag=tag,
                            binary=len(blob),
                            reference_json=len(
                                json.dumps(reference, separators=(",", ":")).encode()
                            ),
                            baseline_receipt_json=len(
                                json.dumps(proof, separators=(",", ":")).encode()
                            ),
                            rejected=len(mutants),
                        )
                    )
                )


if __name__ == "__main__":
    run(sys.argv[1])
