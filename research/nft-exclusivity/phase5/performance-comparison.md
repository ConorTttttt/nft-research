# Costs and comparison

All timings are single-host observations. The matched comparison invokes both Python verifiers on complete paid proofs in the same process, alternates execution order across 24 samples and uses process CPU. Both buyer and seller check the complete contract. The Phase 4 historical reference Rust benchmark (434/786 µs for its two profiles) used a different language and proof boundary.

| Operation | Observed median or count |
|---|---|
| Matched Python buyer CPU | Phase 4 1.349 ms; Phase 5 2.151 ms |
| Matched Python seller CPU | Phase 4 1.343 ms; Phase 5 2.137 ms |
| Certificate bytes | Phase 4 fixed binary 1,559. Phase 5 fixture 3,139, including export and three certificates in JSON. Policy and terms supplied separately. |
| Local actors and rounds | Three disjoint rosters of 7 including the one-time source export; 5 votes per certificate. Sale alone requires 10 votes from 10 distinct authorized identities, two prepare fan-outs that can overlap, zero terminal votes. Reusable export costs five more votes, onward transfer another five. Phase 4's two sale decisions ran consecutively. |
| Prepare and settle | 24 lab sales (8 paid, 8 explicit decline, 8 incompatible same-parent choices). Payment preparation 9.165 ms; launch of both prepares through verified outcome 12.410 ms. Dedicated export 8.245 ms separately. No network consensus latency included. |
| Archive and recovery | Four complete SQLite writes and acknowledgment signatures 6.542 ms. One database read and full verification 2.391 ms. A separate process recovered the persisted public paid fixture after producer exit. No hostile multi-host storage experiment. |
| Onward and duplicate export | Onward 19.829 ms, including each local signer verifying the settlement; first refusing export signer 0.292 ms. Logical per trial: five durable choices per export/prepare/onward certificate, four additional full archive writes. SQLite total across 21 witnesses grew from 430,080 to 823,296 bytes. |
| Native source-chain proof | Seller's ten cooperative read calls took 1.622 s total on the memory-network conductor. One bounded Rust CLI verification including process startup took 3.150 ms. The five payment records were verified separately. These are acquisition/verification costs of historical evidence. |
| Contention and stalls | Visible incompatible locked choices on the same version can prove Void without a new vote. Pre-quorum split, lost last certificate, unreachable signer set or absent required owner can stall indefinitely. No finite recovery latency for those failures. |

The sale interval excludes genesis provisioning, export, onward choice and replication. The prototype uses two local threads; votes within each roster are sequential. Message *design* costs in a network realization would include requests and responses for five votes per decision, proof delivery and archive writes/acks. Actual WAN messages, validation callback CPU, throughput, contested BFT progress, public testnet latency and full irreversible **native** exchange latency were not measured. A verifier speed improvement is not claimed. The improvement is a shallower decision dependency and a certified reason to void some split preparations. [Timing rows](results/trials.jsonl) · [Paired CPU rows](results/paired-cpu.jsonl) · [Independent ancestry audit](results/ancestry-audit.txt)
