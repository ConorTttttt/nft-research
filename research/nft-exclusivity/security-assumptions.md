# Security and availability contract

| Assumption | What fails if it is false |
|---|---|
| All parties pin the same DNA/genesis, unique right definitions, roster and verification code. | A seller can show two unrelated roots or two policies. Both proofs can verify in their respective worlds. |
| At most two of the seven identities can ever equivocate for a given historical domain, including compromised or cloned keys and rollback. | Three compromised witnesses can form the entire intersection of two quorums. Corruption is cumulative for reusable signing keys. |
| Honest witnesses process all requests for each input through one persistent, serialisable reservation store; storage and fsync semantics are trustworthy. | A copied key on two independent machines behaves like two signers with one identity. Power loss, restored snapshots, journal truncation and storage lies can enable equivocation. |
| Canonical encoding, collision resistance of SHA-256 and strict Ed25519 authentication hold. Roster operators control distinct admitted keys. | Conflicting meanings may share a digest or signatures may be forged. Seven keys are insufficient evidence of seven independent operators. |
| Authorisation follows from verified parents. Every invariant with conflicting write or read dependencies is represented. | A forged parent map tricks a caller of the low-level core. An omitted revocation or lease guard yields legally incompatible but syntactically valid claims. |
| Uncontended liveness requires a correct owner, complete dependencies, eventually reachable willing quorum, durable retrievable data and fair processing. | Censorship, lost keys, withheld messages or split votes may freeze the right. Safety has no timing bound. |

An adversary can own arbitrary assets, fork its source chain, delay, duplicate, replay or suppress messages, and control two witnesses. The proof covers a hidden certificate even if no honest buyer has seen it. A stolen owner key can transfer title without consent but cannot violate unique succession under the witness bound. Historic ownership differs from rightful authorisation in an external legal system.

Admission is permissioned in this experiment. Hashing a token ID to DHT neighbours gives no deterministic bound on Byzantine membership. If n operators were sampled uniformly without replacement from N containing B corrupt operators, the probability of exceeding f is the upper hypergeometric tail. Grinding multiple roots, correlated hosting and adaptive corruption invalidate a naïve single-draw estimate. Additional independent committees expand aggregate capture exposure. Fixed membership concentrates censorship risk. No slashable deposit substitutes for the invariant. No benchmark measures independence.

Cryptographic evidence can persist indefinitely. Witness identity recovery from an empty journal, witness rotation, proof pruning, and retrospective attacks require separate assurance. The SQLite path and signer must be provisioned as one operational identity. The research fixture keys are public and exclusively for tests.
