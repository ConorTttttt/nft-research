# Reproduce the witness experiments

From this directory, use Python 3.12.14 with cryptography 50.0.0 (`python3 -m pip install -r requirements.txt`). The standard library's SQLite was 3.53.1. Tests require permission to open **loopback TCP** and create temporary files. All workers use newly generated signing keys. Each process opens its own pre-provisioned database in read/write mode, checks its domain and signer identity, commits reservations and the full proposal together, then signs. The full image restore test copies a quiescent database into the original location while the process is stopped.

```sh
python3 lab.py
python3 proof_tests.py
python3 membership_test.py
python3 failure_bench.py
python3 bench.py > /tmp/nft-network.jsonl
python3 summarize.py /tmp/nft-network.jsonl
python3 ../formal-models/recovery.py
python3 ../formal-models/temporal.py
python3 ../formal-models/authority.py
python3 ../formal-models/ambiguous_repair.py
```

The harness creates loopback endpoints dynamically, uses separate subprocesses and temporary directories, and tears them down. Lab users and genesis rights are fixed in the trust anchor; all initial slots are held by one controller. The network codec uses canonical signed binary digests inside JSON messages. The wire interface is a research harness, with no service authentication, TLS or hostile-traffic hardening. Honest worker processes process one request at a time. The initial benchmark control contacts q responsive processes. The separate failure benchmark fans out to all eight and measures the first six replies. A comparison run can vary in scheduling and absolute times.

## Actual conductor

Put stock 0.7.1 `hc` and `holochain` binaries on PATH. Use Rust 1.96.1 with the Wasm target. Build from the nested workspace so its checked-in target configuration takes effect. These commands assume the default Cargo target directory.

```sh
rustup target add wasm32-unknown-unknown --toolchain 1.96.1
(cd holochain && cargo +1.96.1 build --locked --release --target wasm32-unknown-unknown)
WASM_DIR="$PWD/holochain/target/wasm32-unknown-unknown/release" python3 conductor_test.py
```

If using CARGO_TARGET_DIR, point WASM_DIR to its wasm32-unknown-unknown/release subdirectory. The conductor fixture needs free local ports 43785 and 43786. It constructs a fresh DNA with the live witnesses' public keys and genesis policy, binds signatures to the packaged DNA hash, authorises fixture zome calls, submits one valid delayed leaf, one invalid leaf and a reset followed by a transfer. All packaging and conductor state are temporary. No service is deployed. The Phase 1 local Rust benchmark is in ../../prototype, where `cargo +1.96.1 test --release --locked` and `cargo +1.96.1 run --release --locked --example measure` reproduce the controls.
