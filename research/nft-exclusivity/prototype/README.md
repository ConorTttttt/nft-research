# Running the laboratory

Use Rust 1.96.1, Python 3 and the checked-in lockfiles. The core uses Ed25519-dalek, SHA-256 and SQLite. All code in the witness path is native Rust. Compiling the core without the default journal feature leaves a deterministic verifier for the integrity zome.

```sh
cargo test --release --locked
cargo run --release --locked --example measure
python3 ../formal-models/explore.py
python3 ../formal-models/failures.py
```

The protocol library takes verified parent maps. Populate these only from genesis or recursively verified history for the same domain. Keys in the tests and packaging fixture are intentionally public. A real signer needs its own durable journal and outbox. Provision once, reopen on restart, and stop on database loss. The simulation constructor is for tests and measurements. The signer API is in-process. An authenticated network service, distributed membership and rotation remain future work.

## Build the two Holochain zomes

```sh
rustup target add wasm32-unknown-unknown
cd holochain
cargo build --release --locked --target wasm32-unknown-unknown
```

The target-specific Cargo config imports conductor host symbols using the flag from the upstream test Wasm build. To run the smoke test, put the Holochain 0.7.1 release binaries `hc` and `holochain` on PATH, and install Python's `cryptography` package (tested with 50.0.0). From `holochain/` run the following in a disposable directory. Use the same temporary path and passphrase in both terminals.

```sh
fixture_script="$PWD/fixture/make.py"
lab_dir=$(mktemp -d)
python3 "$fixture_script" --out "$lab_dir"
hc dna pack "$lab_dir/dna"
hc app pack "$lab_dir"
hc dna hash "$lab_dir/dna/rights_lab.dna"
cd "$lab_dir"
printf 'local-test-only' | hc sandbox --piped -f=43781 generate --in-process-lair -r=43782 "$lab_dir/rights_lab.happ" network -b http://127.0.0.1:1 mem
```

In a second terminal, set `lab_dir` to that directory, `fixture_script` to the absolute script path, and `dna_hash` to the printed DNA hash.

```sh
cd "$lab_dir"
printf 'local-test-only' | hc client zome-call-auth --piped --port 43781 test-app
payload=$(python3 "$fixture_script" --dna-hash "$dna_hash")
printf 'local-test-only' | hc client zome-call --piped --port 43781 test-app "$dna_hash" rights_coordinator publish "$payload"
edited=$(python3 -c 'import json,sys; s=json.loads(sys.argv[1]); s[0]["votes"][0][1][0]^=1; print(json.dumps(s))' "$payload")
printf 'local-test-only' | hc client zome-call --piped --port 43781 test-app "$dna_hash" rights_coordinator publish "$edited"
```

The valid call returns an action hash. The final command should fail with `invalid witness signature`. Stop the sandbox in the first terminal after the test. The Python fixture independently encodes the signed messages and creates all votes locally. This checks interoperability and conductor validation of a positive and negative example. Witness transport, peer-to-peer publication latency and producer rollback remain separate experiments.
