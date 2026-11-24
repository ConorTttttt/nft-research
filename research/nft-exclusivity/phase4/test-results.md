# Reproduction and provenance

Local Phase 3 branch and complete Git bundle both resolved to bc97d497877d10d9a9ac5a07dc75b3fb9a2f2bfa. Supplied bundle SHA-256 was 3fbbc96806e74cca5d9918899c52cb3fcbb64f4ce1f50851fec9309a6e6f3d81. Git verified the bundle and object graph. This verifies object identity and ancestry, without a cryptographic author attestation. The remote default was 9fce705. Phase 4 descends directly from the local Phase 3 commit. [Public refs](results/public-heads.txt)

Fresh Phase 3 build and execution used Rust/Cargo 1.96.1, wasm32-unknown-unknown, Holochain and hc 0.7.1, Python 3.12.14, cryptography 50.0.0. Phase 4 additionally used msgpack 1.2.4. OS Linux 6.18.57 x86_64. Rust lockfiles are in each participating crate. The Phase 3 sale engine's locked rave_engine 0.15.0 archive SHA-256 is 7987b4bf8932a86c7da1e85d8803c9de2c96e8c9c5a68d9d9802b19376fb8fde. Native and WASM builds reused the dependency/build cache. Verification used fresh keys, database instances, processes and conductor realms. The tests reproduce the **behavior and measurement boundaries**; timings vary. [Phase 3 build](results/phase3-build.txt) · [Fresh baseline output](results/phase3-run.txt)

## Run the suite

Use a full hNFT checkout with the two research revisions (30da888 for the mint zomes and 8fd2391 for the settlement code). Install the pinned toolchain, hc and conductor on PATH, allow loopback TCP and unused ports 43985/43986 and 43995/43996. The release material is Linux x86_64. From the Phase 4 directory:

```bash
rustup target add wasm32-unknown-unknown --toolchain 1.96.1
python3 -m pip install -r ../phase2/distributed-prototype/requirements.txt msgpack==1.2.4
export HNFT_REPO=/absolute/path/to/hNFT
export RELEASE_DIR=$(mktemp -d)
(
  cd "$RELEASE_DIR"
  for file in alliance.dna unyt.happ unyt_cli; do
    curl -fL -O "https://github.com/unytco/unyt-sandbox/releases/download/v0.117.0/$file"
  done
)
# Verify downloaded binaries before running or unpacking them.
(cd "$RELEASE_DIR" && sha256sum -c <(head -3 "$OLDPWD/unyt-integration/release.sha256"))
chmod +x "$RELEASE_DIR/unyt_cli"
(cd "$RELEASE_DIR" && hc dna unpack alliance.dna && hc app unpack unyt.happ)
./reproduce.sh /absolute/path/to/new-results-directory
```

The driver repeats the Phase 3 models, threshold and recovery enumeration, paid and void flows, Rust/Python differential checks, stock hNFT mint, archive validation and tamper rejection. It runs the Phase 4 explicit-state checks, builds the native verifier, tests both outcomes, witness refusal and onward transfer, shuts down the producer, verifies a surviving full copy and benchmarks the two profiles. Finally it installs the release, provisions disposable credit and checks a separate reject/reclaim control. On failure, see intermediate JSONL in the output directory. Setup and CLI interfaces are release-specific. Run Python without optimization so test assertions are enabled. Code changes to the release hApp are limited to the generated DNA properties and network seed; the driver checks the original manifests and WASM digests. [Full driver](reproduce.sh)

## Inspect existing evidence without a network

```bash
python3 formal-models/economy.py
python3 formal-models/imports.py
python3 formal-models/vesting.py
python3 unyt-integration/check_capture.py results/final-conductor.jsonl
cargo +1.96.1 build --locked --release --manifest-path prototype/verifier/Cargo.toml --bins --example cpu
bin="${CARGO_TARGET_DIR:-prototype/verifier/target}/release"
python3 prototype/differential.py "$bin/payment-evidence-lab" results/public-fixture
f=results/public-fixture
"$bin/examples/cpu" "$f/p3" "$f/root3" "$f/p4" "$f/root" "$f/grant"
```

The standalone audit also takes a capture, externally pinned CEL domain and expected child as arguments. check_capture.py takes its pins from the recorded test, so it is a regression check on a known fixture. An independent relying party must provision its own pins. Initial release setup and failed integration attempts are retained alongside the successful runs, including the template input mismatch and the earlier client tuple decoding error. These are separate realms, so their action hashes cannot be combined. Public fixture files contain proof material and verification roots only.

The archived CPU fixtures also support 146 fresh Rust/Python differential checks in the Phase 4 lab profile. The controls include 144 invalid byte sequences, one missing certificate and one authentic paid certificate. Each of the 24 separately generated sales also exercises either the buyer's or seller's onward transfer. [Differential results](results/differential.txt)

## Offline recovery of five signed native actions

In a further run the buyer cell fetched the seed commitment, its acceptance, the parked-spend link, the RAVE and the seller receipt via hdk_must_get_valid_record. After conductor and executor shutdown the native Rust checker recomputed each action hash, verified its Ed25519 signature over Holochain serialization and recomputed the entry hash for each Create. The Python checker matched authors, amounts, seed references, park, agreement, global definition, grant and collection source. Five altered signatures and an altered entry were refused. Omitting any of the five records left the audit unresolved. No source-chain completeness, DNA-genesis walk, backing or irreversible financial disposition follows from these five signatures. Fixture pins and identity mappings remain externally supplied.

```bash
cargo +1.96.1 build --locked --release --manifest-path unyt-integration/record-check/Cargo.toml
python3 unyt-integration/check_signed_fixture.py results/funded-records.jsonl "${CARGO_TARGET_DIR:-unyt-integration/record-check/target}/release/phase4-historical-record"
```

[Signed capture](results/funded-records.jsonl) · [Offline outcome](results/signed-audit.txt)
