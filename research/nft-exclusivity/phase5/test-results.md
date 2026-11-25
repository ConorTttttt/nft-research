# Reproduction and evidence ledger

Phase 4 branch and complete-history bundle both resolve to 4fde2d5a12c63fdaee39e652dad5022830fd1f95. Its parent is bc97d497877d10d9a9ac5a07dc75b3fb9a2f2bfa. Git verified the bundle. Phase 5 branched there. The native baseline and the subsequent extended ancestry fixture are separate runs with different agents, signing roots and DNA properties; their actions cannot be combined. [Provenance](results/provenance.txt)

| Level | Result and boundary |
|---|---|
| Mathematically proved | Conditional exclusion from a uniquely decided parent, bilateral conjunction, incompatible-choice exclusion, conserved bounded allowances and unchanged legacy acceptance. All depend on the stated recognition contract. |
| Bounded model checked | Bilateral model 305 states / 876 edges after including foreign-choice exclusion. Four weakened variants generated shortest violating traces. Export model 120 orders × 4 policies. Capacity example 1,001 merges. Phase 4 witness/rollback model and its unsafe variants also reproduced. |
| Executed native | Offline Rust payer ancestry; Phase 4 five-record validation and byte controls; public engine 46 ledger tests and 14 recovery-filter tests; Python lab 24 sales and authenticated onward choices. [Ancestry](results/ancestry-audit.txt) · [RAVE ledger tests](results/engine-network.out) · [Recovery-filter tests](results/recovery-layout.out) |
| Executed conductor / official Unyt release | Genuine local credit and balance, sale agreement execution, seller collection, conventional negative-path control, second-agent reads, independent hNFT mint and Phase 3 archive validation. Holochain 0.7.1, stock v0.117.0 WASMs under local test properties, memory transport. |
| Simulated | All P5J1 input admissions, one-time native export policy, partitioned funds, logical witness separation and exclusive ability to determine entitlement. Phase 4 simulated source ledger retained as baseline. |
| Unverified | Native visibility completeness, all-path financial exclusion, production credit policy, bridge redemption and warrant consequences. No native witness rollback, conflicting native histories, adversarial production or shared testnet run. |
| Blocked | Portable exclusively final native payment, source-enforced hNFT export under existing clients, paid/void native onward transfer and native recovery guarantee. Private runtime's end-to-end acceptance contract is missing. |

## Exact experiments

Use Rust 1.96.1 with wasm32-unknown-unknown, stock hc/holochain 0.7.1, Python 3.12, cryptography 50.0.0 and msgpack 1.2.4. Install and unpack the official release, pin its digests, obtain the required hNFT commits and provide loopback ports according to [Phase 4 setup](../phase4/test-results.md). Use a new output path. The driver reproduces the earlier baseline before running the new models and fixture. It creates only disposable local keys and units.

```sh
export HNFT_REPO=/absolute/path/to/hNFT
export RELEASE_DIR=/absolute/path/to/unpacked-release
./reproduce.sh /absolute/path/to/new-output
```

For the public engine tests use the archive and SHA-256 from Phase 4. The required physical layout below matches the upstream test code's relative template path. An initial offline dependency miss and a test invocation without that sibling are preserved under results/. The corrected run used the unchanged crate, templates and Cargo.lock.

```sh
# layout/crates/rave_engine contains the extracted rave_engine-0.15.0 package.
# layout/smart_agreement_library is at be2d630a3f3861c66b1b2ee341ff1c76b28210b8.
cargo +1.96.1 test --locked --manifest-path layout/crates/rave_engine/Cargo.toml --lib types::ledger
cargo +1.96.1 test --locked --manifest-path layout/crates/rave_engine/Cargo.toml --lib unit_recovery
```

Offline checks against the records in this commit:

```sh
python3 formal-models/prepare.py
python3 formal-models/capacity.py
python3 formal-models/export.py
python3 integration-prototype/recover.py results/public
python3 integration-prototype/compare.py results/public
cargo +1.96.1 build --locked --release --manifest-path integration-prototype/ancestry/Cargo.toml
python3 integration-prototype/check_ancestry.py results/ancestry.jsonl "${CARGO_TARGET_DIR:-integration-prototype/ancestry/target}/release/p5-payer-ancestry"
```

The Python trial and offline checks use assertions as test oracles; run without Python optimization. The cryptographic verifier requires explicit inputs, checks signatures and returns one of five statuses. Historical action verification assumes independently trusted pins; the file-based fixtures extract pins from the known run for regression testing. The ten-action prefix establishes inclusion of this funding acceptance on this payer history. It does not replay every app-specific validation dependency or prove the absence of alternative histories.

The complete Phase 5 driver subsequently passed in a new output directory, including fresh Phase 4 reproduction. The extra read-only standing control records both cells before and after execution/collection. Its independent replay is `python3 integration-prototype/check_standing.py results/standing-run.jsonl`. The original ancestry and standing captures come from different successfully audited runs.
