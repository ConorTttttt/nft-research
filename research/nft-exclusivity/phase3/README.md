# Phase 3 — Certified rights and settlement

The working result is a conditional exchange: a certified grant fixes who gets title for each terminal payment outcome. Real hNFT minting, the hNFT Rhai sale template, rave_engine 0.15.0, native CEL witnesses, an independently compiled Rust verifier and Holochain 0.7.1 archival all ran locally. The payment finality authority is a simulated issuer with a dedicated test coupon. Its behavior is the principal unverified production dependency.

* [Architecture decision and answers A–L](architecture-decision.md)
* [Resource model and guard derivation](exclusive-authority-model.md) and [mathematical review](mathematical-architecture-review.md)
* [Settlement protocol](nft-payment-settlement.md) and [portable proof format](shared-proof-interface.md)
* [Source inventory](cross-repository-inventory.md), [Unyt findings](unyt-current-state.md) and [reuse matrix](component-reuse-matrix.md)
* [Reproduction instructions](test-results.md), [formal results](verification-results.md) and [measurements](performance-comparison.md)
* [Security gaps](security-gaps.md), [counterexamples](adversarial-counterexamples.md) and [Phase 4 exit criteria](phase4-roadmap.md)

Everything is scoped to local experiments. Raw evidence is under results/. The parent research directories retain the original Phase 1 and Phase 2 artifacts.
