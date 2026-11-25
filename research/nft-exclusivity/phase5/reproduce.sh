#!/usr/bin/env bash
set -euo pipefail
out=$(realpath -m "${1:?new output directory}")
mkdir "$out"
cd "$(dirname "$0")"
export HNFT_REPO=$(realpath "${HNFT_REPO:?checkout with both pinned hNFT commits}")
export RELEASE_DIR=$(realpath "${RELEASE_DIR:?verified unpacked Sandbox v0.117.0}")
export CARGO_TARGET_DIR=$(realpath -m "${CARGO_TARGET_DIR:-$out/target}")
export PYTHONDONTWRITEBYTECODE=1
../phase4/reproduce.sh "$out/baseline"
python3 formal-models/prepare.py >"$out/prepare.txt"
python3 formal-models/export.py >"$out/export.txt"
python3 formal-models/capacity.py >"$out/capacity.txt"
python3 integration-prototype/trial.py "$out/baseline/final-conductor.jsonl" "$out/public" >"$out/trials.jsonl"
python3 integration-prototype/recover.py "$out/public" >"$out/recovery.txt"
python3 integration-prototype/compare.py "$out/public" >"$out/paired-cpu.jsonl"
cargo +1.96.1 build --locked --release --manifest-path integration-prototype/ancestry/Cargo.toml
export P4_ASSET=$(python3 -c 'import sys,json; x=next(v for l in open(sys.argv[1]) if l.startswith("{") and "mint_action" in (v:=json.loads(l)));print(x["source_dna"]+"/"+x["mint_action"])' "$out/baseline/phase3-run.txt")
python3 -u integration-prototype/capture_ancestry.py "$RELEASE_DIR/unyt.happ" "$RELEASE_DIR/alliance.dna" --setup >"$out/ancestry.jsonl"
python3 integration-prototype/check_ancestry.py "$out/ancestry.jsonl" "$CARGO_TARGET_DIR/release/p5-payer-ancestry" >"$out/ancestry-audit.txt"
python3 ../phase4/unyt-integration/check_signed_fixture.py "$out/ancestry.jsonl" "$CARGO_TARGET_DIR/release/phase4-historical-record" >>"$out/ancestry-audit.txt"
python3 integration-prototype/check_standing.py "$out/ancestry.jsonl" >"$out/standing.txt"
