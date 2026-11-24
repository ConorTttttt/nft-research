# Reproduction and scope

Use the Phase 3 directory in a checkout based on f761cb2. Python 3.12.14 with cryptography 50.0.0, Rust 1.96.1 with wasm32-unknown-unknown and stock hc/holochain 0.7.1 are required. Allow loopback TCP to ephemeral witness ports and ports 43985/43986 for disposable single-conductor fixtures. Fetch public dependencies at build time. All assets and signing keys are test fixtures.

```sh
git clone https://github.com/ConorTttttt/hNFT /tmp/phase3-hnft
rustup target add wasm32-unknown-unknown --toolchain 1.96.1
python3 -m pip install -r ../phase2/distributed-prototype/requirements.txt
integration-prototype/reproduce.sh /tmp/phase3-hnft
```

The script uses temporary files and honors CARGO_TARGET_DIR for caching. It extracts the exact sale script from hNFT's payment branch and the mint zomes from the 0.7.1 compatibility commit. Its hash check guards the native engine against template substitution. See implementation files for complete test inputs. Refreshes print to stdout rather than overwriting the recorded evidence.

## Baseline controls

```sh
for model in recovery temporal authority ambiguous_repair; do python3 "../phase2/formal-models/$model.py"; done
python3 ../formal-models/handoff.py
cargo +1.96.1 test --manifest-path ../prototype/Cargo.toml --release --locked
(cd ../phase2/distributed-prototype && python3 proof_tests.py && python3 membership_test.py && python3 bench.py && python3 failure_bench.py)
(cd ../phase2/distributed-prototype/holochain && cargo +1.96.1 build --locked --release --target wasm32-unknown-unknown)
WASM_DIR="$(realpath ../phase2/distributed-prototype/holochain/target/wasm32-unknown-unknown/release)" python3 ../phase2/distributed-prototype/conductor_test.py
```

Point WASM_DIR at the corresponding external target path if CARGO_TARGET_DIR is set. Baseline conductor uses ports 43785/43786. Reruns passed four Phase 1 Rust integration tests, the Python recovery, temporal, authority and handoff models, receipt/closure proof tests, membership controls, and native process benchmarks. Stock conductor accepted a delayed valid batch receipt and a reset followed by transfer. It rejected edited path, insufficient closure and duplicate reporter. Original Phase 2 results remain in their original directory.

## Integration and independent controls

* hNFT research branch 36b94b60's tools/modelcheck_ownership.py ran separately. Its 3-of-4 durable case visited 3,087 states and its honest split example stalls. See results/hnft-model.txt.
* dex_core at f8593b49 passed 82 native tests in a temporary workspace containing its source modules and serde workspace dependency. To reproduce with repository access, run `cargo test -p dex_core` at that revision. This run excludes the mock ledger conductor, Rust-vs-Rhai parity crate and actual Unyt.
* The sale runner executes the upstream script against rave_engine 0.15.0. Exact payment succeeds; underpayment, overpayment and zero paid against price 10 are refused. The pinned issuer/realm, wrong NFT, edited terminal signature, insufficient funds state, replay, competing void/pay and proof retrieval after a simulated client restart are exercised. A missing executor leaves the reservation pending and retryable. The race uses two threads and distinct SQLite connections. Every terminal result recovered from storage must verify to the same child.
* Paid and void owners each install their child at the five witnesses, make a new transfer and cannot certify a competing onward transfer. Ordinary Phase 2 install from a conditional genesis is refused. Parent vote reservations and receipts still use the original Phase 2 code.
* Native Rust/Python agreement on child and controller was tested for four outcome/roster pairs. All 120 malformed or edited byte cases were rejected. A single-conductor WASM run accepted valid paid evidence, retrieved exactly the published bytes by action hash and rejected altered terminal evidence.
* The hNFT mint fixture uses a test collection and maps its source DNA and actual mint action into the sale realm for slot zero. This is an operator-authorized research import. It does not disable the original hNFT transfer code, establish agreement between the mint identity and the lab seller, or prove globally one-time import.
* The original hNFT main c9fb294 built as WASM with HDK 0.7.0/HDI 0.8.0. Its init failed on stock conductor 0.7.1 with CreateInput deserialization error “missing field constraint” on capability grant creation. The pinned gate/s0-01-holochain-0.7.1 branch addresses the SDK boundary. Direct public Git access to eight private repos required the connected GitHub file API. The sparse crate index and checksum-verified archive supplied rave_engine after the registry metadata endpoint returned HTTP 403.

## Measuring the pieces

Run demo.py without --mint-wasm or --wasm to measure the witness/engine/ledger path alone, with the same --engine and --script arguments as reproduce.sh. Run engine_bench.py with those two paths positionally to time the CLI. checkpoint_bench.py measures CPU with process_time_ns and reports every buyer sample. Baseline bench.py reports every trial. results/ contains raw outputs; performance-comparison.md identifies subsets and aggregation. Tests simulate interruption via separately reopened adapters and missing evidence. Host power-loss, real operator collusion, physical clocks, external network partitions and deployed Unyt state were not experimentally verified.

The complete reproduction script exited successfully after minting on hNFT's 0.7.1 gate branch, binding its mint action to the test realm, performing the sale, recovering and exercising the proof, publishing to the archive DNA, and completing all 24 test slots. See results/full-reproduction.txt for an independent end-to-end rerun.

Two additional component controls passed. At authenticated-state 8a076ad0, run `cargo test -p holochain-snapshot-commitment --lib` (seven tests). The run here used its source and manifest in isolation. At threshold-cryptography 33db0497, run `cargo test --locked -p holochain-mpc-frost-ed25519 --test three_agents three_agent_dkg_two_agent_signing_and_verification` and repeat with filter `activated_group_approved_intent_nonce_wal_and_threshold_signing`. Both passed. These controls demonstrate a working group signature and nonce-management path, without establishing safe CEL integration.
