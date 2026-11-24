#!/usr/bin/env bash
# Run from the Phase 3 checkout. Supply a full hNFT clone as the first argument.
set -euo pipefail
hnft=$(realpath "${1:?path to local hNFT repository}")
here=$(cd "$(dirname "$0")" && pwd)
trial=$(mktemp -d)
trap 'rm -rf "$trial"' EXIT
export CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$trial/target}"
export CARGO_PROFILE_DEV_DEBUG=0
export PYTHONDONTWRITEBYTECODE=1
wasm="$CARGO_TARGET_DIR/wasm32-unknown-unknown/release"
git -C "$hnft" show 8fd2391e2f9f584c19dcb329bb21bc034f1bf19e:unyt/nft_sale_settlement/execution_code.rhai >"$trial/sale.rhai"
mkdir "$trial/hnft"
git -C "$hnft" archive 30da888cf5cfdd67561a3dac0d9ff2e32757fc4a | tar -x -C "$trial/hnft"
(cd "$trial/hnft" && RUSTFLAGS='--cfg getrandom_backend="custom" -C link-arg=--import-undefined' cargo +1.96.1 build --locked --release --target wasm32-unknown-unknown -p nft -p nft_integrity)
(cd "$here/archive" && cargo +1.96.1 build --locked --release --target wasm32-unknown-unknown)
cargo +1.96.1 build --manifest-path "$here/engine/Cargo.toml" --locked
cargo +1.96.1 build --manifest-path "$here/verifier/Cargo.toml" --locked --release --example check
python3 "$here/../formal-models/check.py"
python3 "$here/../formal-models/compiler.py"
python3 "$here/differential.py" "$CARGO_TARGET_DIR/release/examples/check"
python3 "$here/checkpoint_bench.py"
python3 "$here/demo.py" --mint-wasm "$wasm" --wasm "$wasm" --engine "$CARGO_TARGET_DIR/debug/phase3-agreement" --script "$trial/sale.rhai"
