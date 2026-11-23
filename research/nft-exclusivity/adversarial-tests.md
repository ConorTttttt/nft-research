# Adversarial evidence

| Scenario | Evidence and outcome |
|---|---|
| Simultaneous owner equivocation, partition, withheld certificates | Finite-state search counts signatures regardless of publication. The valid parameter sets preserve exclusivity across all explored delivery orders. |
| Two Byzantine voters and intersecting multi-input histories | Rust property test permutes delivery of all candidate requests to seven witnesses over 48 deterministic seeds. The two faulty witnesses discard memory before each vote. All verified batches have disjoint consumed inputs. |
| Forged ownership, stale parent, modified recipient, cross-network replay | Rust rejects edited proposals, wrong-domain certificates, a stale controller signing a child and verification against a map lacking the parent. Authentic old certificates can still verify as history. |
| Insufficient, duplicated or alternative quorum | Rust rejects four signatures and repeated indices. Two different valid signer subsets derive identical child IDs. |
| Restart and partial reservation | File-backed SQLite test closes and reopens a witness, rejects an overlapping batch after its first insert and then certifies another spend of the first input. This exercises transaction rollback and persistent retry. It does not simulate power failure or a lying disk. |
| Compromised keys or unsafe reconfiguration | Executable rollback/epoch traces give double certificates. Compromise of an owner alone allows theft within the single lineage. |
| Multi-object exchange | Same-controller, same-roster transfers are atomic under a shared statement digest. Cross-roster atomicity and fair exchange are outside the implementation. |
| Stalled or censored transfers | Split voting is reproducible. The protocol preserves the reservations indefinitely. |

Run from `prototype/` using `cargo test --release --locked`. Run the two model scripts from the research directory. Test keys are deterministic public fixtures. The property tests use actual Ed25519 signatures. The state search abstracts authentication as ideal. Neither substitutes for an independent implementation review, hardware failure injection or a networked quorum test.

On a stock local 0.7.1 conductor, the coordinator published a one-step history from an independent Python encoder. A one-bit mutation of a witness signature returned an InvalidCommit error with the reason `invalid witness signature`. The test used the real Wasm entry validation callback and a public fixture roster. A separate Rust race test starts two SQLite connections at a barrier and checks that exactly one conflicting request wins, duplicate provisioning fails and reopening a missing database fails closed.
