# Local measurements

Linux 6.18.57 x86_64, Xeon Platinum 8573C, cgroup CPU quota two cores. Python 3.12.14, cryptography 50.0.0, SQLite 3.53.1, Rust 1.96.1, stock Holochain and hc 0.7.1. Engine CLI built in dev profile without debug information; WASM and native standalone verifier in release. No public network timing. Do not extrapolate WAN throughput from loopback or simulated delay.

| Path | Work measured | Result |
|---|---|---|
| Phase 2, 7/5/2 direct | Six repeated trials each of 64 separate transfers, five witness TCP requests per transfer | Median 478.16 ms for 64; buyer JSON 996 B; 870.7 µs mean verification per trial at the median. |
| Phase 2, 8/6/3 direct | Same, six TCP requests per transfer | 510.35 ms for 64; 1,131 B per receipt. |
| 7/5/2 atomic batch | One 64-parent decision with five signatures. Flat vs tree, one buyer proof verified | 11.22 vs 11.04 ms; 9,565 vs 1,405 B per buyer. A 20 ms injected round-trip delay moved tree median to 30.54 ms. |
| Concurrent independent transfers | 16 transfers with 1 or 4 submitting clients | 7/5 took 112.03 or 110.63 ms; 8/6 took 127.54 or 108.01 ms. One trial per condition. |
| 8/6 first quorum | Fanout to eight, median of eight runs per condition | Healthy 10.62 ms, two delayed 8.30 ms, two terminated 8.47 ms. Differences this small are scheduling noise. |
| CEL closure | Close, verify and install after partial votes | Median 20.28 ms, six local trials. Inconclusive closure has no finite latency guarantee. |
| Phase 3 fixed grant | Isolated 21 ordinary paid slots (3–23), 7/5 roster with five actual witness responses | Median commitment 7.80 ms, reserve 2.93 ms, paid transition including real engine 15.03 ms, Python exercise 1.00 ms, recovered proof and reverified child 2.25 ms. Measured end-to-end median 28.46 ms excluding a deliberate rejected test call and authorization preparation. |
| Engine in isolation | 21 new native processes including startup, exact-sale execution and parsed-output check | Median 12.14 ms. This is wall time for the CLI, not interpreter-only CPU. |
| Persistent payment data | One test database, 24 funded coupons and full grant evidence | 61,440 bytes at completion, excluding signer journals and filesystem overhead. |
| Holochain publication | One paid envelope in disposable single-conductor archive, CLI call, then exact validated retrieval | 188.31 ms publish; 199.41 ms retrieval. Baseline fixture published a different delayed batch receipt in 374.98 ms. Different payloads/fixtures preclude a speedup claim. |

The commit has one parallel witness request/response round, five witness signatures and one owner signature. Reserve adds the buyer signature to the payment domain. Pay adds an issuer signature. There are zero additional NFT witness signatures to exercise; the first onward transfer has the normal five. A withheld proof can make the end-to-end time infinite. The Phase 2 direct transfer settles no payment. Comparing its latency to the paid path as if both accomplished the same task would be misleading.

## Measured improvements and costs

* **Portable evidence.** At 7/5 the Phase 3 binary contains the policy, full grant and terminal outcome in 909 B. The same logical envelope in compact JSON was 2,253 B, a 59.7% reduction. At 8/6 it was 1,006 vs 2,455 B. Even the Phase 2 *receipt alone* was 996 or 1,131 B in its original JSON. These are wire-format improvements on restricted evidence types. They make no change to the number of coordinating participants.
* **Historical checkpoints.** Sixteen independent slots, twelve certified transfers per slot. Five test signers each replayed all 192 transfers before signing one common root. At the same external trust root and JSON codec, a buyer replayed 11,965 B or verified a 1,134 B quorum checkpoint and four siblings (90.5% smaller). Median buyer process CPU across 15 repetitions fell from 9.33 ms to 0.61 ms. Signer replay and checkpoint construction took 0.76 s serially. Raw samples are in results/checkpoint.jsonl. This moves work and adds a correct historical-attestation duty. It proves one labelled historical state and does not permit a restored witness to resume signing.
* **Coordination placement.** Predetermination removes one potential discretionary vote round for release relative to a pay-then-transfer workflow. Phase 2 already predicts zero extra decisions for a fixed grant. The implemented improvement is making this executable against a real agreement engine and testing safe onward use. There is no measured speedup over a Phase 2 predetermined-grant settlement implementation because that control did not exist.

There is no comparable measured result for a deployed Unyt payment, cross-host issuer failover, FROST, a joint-ledger alternative or a broad generalized rights workload. Delayed loopback TCP and a single process CPU benchmark are reported separately.
