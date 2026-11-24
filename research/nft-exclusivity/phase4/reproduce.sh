#!/usr/bin/env bash
# HNFT_REPO must contain both pinned research commits. RELEASE_DIR is prepared
# with the commands in test-results.md. Use an unused output directory.
set -euo pipefail
out=$(realpath -m "${1:?supply new output directory}")
mkdir "$out"
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
export CARGO_TARGET_DIR=$(realpath -m "${CARGO_TARGET_DIR:-$out/target}")
export HNFT_REPO=$(realpath "${HNFT_REPO:?supply hNFT checkout}")
release=$(realpath "${RELEASE_DIR:?supply unpacked official release}")
sha256sum --check --status <(sed "s|  |  $release/|" unyt-integration/release.sha256)
../phase3/integration-prototype/reproduce.sh "$HNFT_REPO" >"$out/phase3-run.txt"
python3 formal-models/economy.py >"$out/model.txt"
python3 formal-models/imports.py >"$out/imports.txt"
python3 formal-models/vesting.py >"$out/vesting.txt"
cargo +1.96.1 build --manifest-path prototype/verifier/Cargo.toml --locked --release --bins --example cpu
cargo +1.96.1 build --manifest-path unyt-integration/record-check/Cargo.toml --locked --release
bin="$CARGO_TARGET_DIR/release/payment-evidence-lab"
export P4_PUBLIC="$out/public"
python3 prototype/trial.py "$bin" >"$out/lab.jsonl"
python3 prototype/recover.py "$P4_PUBLIC" "$bin" "$P4_PUBLIC/p4" >"$out/recovery.txt"
python3 prototype/differential.py "$bin" "$P4_PUBLIC" >"$out/differential.txt"
python3 prototype/p3_fixture.py "$P4_PUBLIC"
"$CARGO_TARGET_DIR/release/examples/cpu" "$P4_PUBLIC/p3" "$P4_PUBLIC/root3" "$P4_PUBLIC/p4" "$P4_PUBLIC/root" "$P4_PUBLIC/grant" >"$out/cpu.csv"
export P4_ASSET=$(python3 -c 'import sys,json; x=next(v for l in open(sys.argv[1]) if l.startswith("{") and "mint_action" in (v:=json.loads(l)));print(x["source_dna"]+"/"+x["mint_action"])' "$out/phase3-run.txt")
python3 -u unyt-integration/probe.py "$release/unyt.happ" "$release/alliance.dna" --setup >"$out/final-conductor.jsonl"
python3 unyt-integration/check_capture.py "$out/final-conductor.jsonl"
python3 unyt-integration/check_signed_fixture.py "$out/final-conductor.jsonl" "$CARGO_TARGET_DIR/release/phase4-historical-record" >"$out/signed-audit.txt"
python3 unyt-integration/time_history.py "$out/final-conductor.jsonl" "$CARGO_TARGET_DIR/release/phase4-historical-record" >"$out/history-cost.jsonl"
