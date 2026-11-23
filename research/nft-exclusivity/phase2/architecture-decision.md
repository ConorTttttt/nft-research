# Decision and gates

**Choose according to the liveness contract.** For admitted federations that can tolerate stalled disputed assets, use direct per-input certificates, permanent signed fences for provably impossible transfers, one deterministic refund outcome, and prospectively bound membership. Use a compact receipt when an honest quorum can be trusted to validate its siblings. Use six of eight only if two lifetime Byzantine identities plus one other lifetime forgetting identity and at most two silent identities are supportable assumptions. For applications promising resolution of *every* contested transfer under eventual synchrony, select a reviewed BFT service with prepared-state evidence and view change from inception. The direct protocol fails that requirement. Neither choice tolerates arbitrary restoration of all historical keys and evidence. There is no overall winner independent of these contracts.

| Gate | Decision and evidence |
|---|---|
| Formal safety | Pass in the specified static/cumulative identity model. Intersection, exclusion and deterministic refund cover every pair of incompatible successor types. Unbounded arguments are mathematical derivations; temporal search and receipt tests are finite. |
| Recovery | Conditional pass. Reissue an identical reservation, retrieve an available prior certificate or prove a deterministic refund. Preserving an image and key across arbitrary restores is outside the bound. Some contested inputs have no recoverable decision given available evidence. |
| Adversarial tests | Lab pass. Real independent signer processes, stale image, mixed schedules, withholding, two failures, wrong roster, forged/tampered claims and publication tested. Independent operators, WAN partitions, power loss and key custody unverified. |
| Decentralisation | Permissioned, explicit trust. No on-path central batch builder or global order. One operator provisioned every lab node. Permissionless membership, correlated faults and adaptive capture are unresolved. |
| Measurable advantage | Pass for bounded additional rollback tolerance, conclusive negative recovery and smaller per-buyer receipts. Same witness count per quorum for flat and compact formats. No demonstrated CPU parallel speedup or WAN benefit. |
| Holochain compatibility | Lab pass for fixed-domain portable tree/reset history. Compiled and exercised stock 0.7.1 Wasm validation. No claim of latest-state reads, physical scarcity or native DHT exclusivity. |

**Scope of the recommendation.** Pinning seven or eight keys in DNA properties is an experimental admission mechanism. A full service must establish legal right definitions, independent administration, reliable storage and audited cryptographic/serialization boundaries. No production security or deployment approval follows from the gates. The authority algebra, conditional decision programs and prospective handoff are design results; the executable implements a bounded subset.

[Recovery proof](mathematical-theorems.md) · [Network evidence](network-benchmarks.md) · [Remaining work](phase3-roadmap.md)
