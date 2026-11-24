# Portable proofs and policy negotiation

A relying party first chooses a trust root and a versioned statement type. The outer application records its own source DNA and validates the mapping to a proof realm before accepting an imported right. The lab archive can be replicated on several DNAs deliberately: its DNA properties pin the same external domain and verification returns the same child. Creating two independently spendable imports from the same evidence would duplicate authority. Both applications must use the original child and its roster, or consume that child once in a certified export to precisely one destination realm.

## Implemented binary profile P3G1

Network byte order. Concatenate below in exact order, without lengths except the roster and threshold specifying fixed counts. Reject trailing bytes, invalid signatures and unknown profiles.

| Field | Encoding |
|---|---|
| Format and policy | Four ASCII bytes P3G1, then unsigned octets n, q, e. Only (7,5,2) or (8,6,3). |
| Realm and roles | 32-byte payment-network identifier, 32-byte issuer Ed25519 public key, four distinct 32-byte public keys in policy order (seller, buyer, two other admitted recipients). Then n distinct 32-byte witness keys in roster order. |
| Grant | 32-byte big-endian genesis slot 0..16383, owner signature (64 bytes), exactly q pairs of 1-byte roster index and 64-byte signature sorted by strictly increasing index. Mode is flat, width one, destination is buyer. |
| Terminal | One octet (0 void, 1 paid), 64-byte issuer signature. |

The fixed prefix P is ASCII p3/single-unit-grant/v1. Hash is SHA-256 of concatenated fields. Integers in hashed context are four bytes big-endian. The template hash, price and genesis capacity are constants in grant.py and verifier/src/lib.rs. The profile anchor hashes P, network, issuer, template SHA-256, price, capacity and the four roles. Compute the unmodified Phase 2 domain over anchor and roster policy, then match the caller's independent 32-byte pin. Reconstruct the Phase 2 flat statement. Check owner and unique roster votes using the original owner and vote tags. Derive Phase 2 child from the statement digest and parent. The sale ID hashes P, /sale, domain, parent and child. The issuer signs P || /terminal/ || sale || ASCII outcome. The exercised child hashes P, /child, sale and ASCII outcome. Its controller follows the outcome. Replays derive the identical child. Extra signatures do not change child identity.

The inner binary verifier rejects inputs above 1,536 bytes before traversing the proof. Valid widths are exactly 909 and 1,006 bytes. It performs at most eight Ed25519 checks. Rust uses strict verification; Python parity was checked on admitted generated keys and edited fixtures, not all noncanonical points. Caller validates key admission and genesis before pinning. The Holochain host deserializes an entry before the inner cap applies. Host allocation/fuel under arbitrary envelope sizes was not benchmarked. The format intentionally supports only a single-generation fixed-price single-unit lab sale. A changed policy needs a new format and explicit activation/import. Existing CEL statements, hNFT ActionHashes and Unyt agreement hashes are unchanged.

## Proof families

| Evidence | Statement, signer and dependency | Replay, verification bounds and status |
|---|---|---|
| Genesis | Out-of-band trusted collection registry or unique mint permit binds facet namespace, initial controller and policy. Lab substitutes 16,384 slots under one pinned profile. | Cache by realm and genesis ID. Historical. No general mint/import proof implemented. |
| Transition / predetermined grant | Owner signature plus parent q votes on complete typed transition. P3G1 reinterprets a Phase 2 statement only within its pinned grant realm. | Verify ancestry to anchor and policy at every step. Prototype caps this grant path at one. A historical state can authorize a proposal, while acceptance of its spend still needs witnesses. |
| Signed closure / refund | Permanently closed reporter signs Phase 2 close_message with domain, parent and prior digest or empty. Aggregate distinct authenticated reporters and apply exclusion inequality. | Bound n reports before heavy verification. Fixed-refund hash derives from domain and parent, independent of subset. Native Phase 2 supports this, P3G1 terminal void has a different authority and tag. |
| Handoff | Old parent quorum covers child policy hash, epoch and new roster. New proof starts from that exact child. | Reject stand-alone new-roster certificates. Hash/policy pin must advance with authenticated ancestry. Model only here. |
| Compact batch | Phase 2 signs a tree header (domain, width, root); buyer proves membership and selected parent/recipient. | At most 256 leaves and eight siblings in the baseline. Relies on voters validating whole batch and serving dependencies. Historical. |
| Checkpoint | Separate historical-frontier domain. Pinned quorum attests that independently replayed labelled histories terminate in leaf values; membership binds slot, owner and child. | Experiment fixes width 16 and depth 12. Verify five distinct roster signatures and four siblings. A production type needs bounded parsing, exact complete-frontier semantics and checkpoint issuance rules. No freshness or safe signer reconstruction. |
| Agreement execution | Pinned engine/rules, complete typed inputs, sources and derived output or validated exact-hash RAVE record in source realm. | Re-execution validates computation. Agree on source DNA, validator and dependency budgets before importing. No standalone cross-DNA execution codec defined. |
| Irrevocable payment | P3G1's issuer signs paid/void after a durably exclusive row decision for this sale. | Fixed size and idempotent. Actual Unyt evidence would require a different type and audited adapter. |
| Current-authority claim | A nonce-bound exclusive reservation or certified self-transition consumes the expected live parent and fences incompatible operations for the transaction. | Indicates authority at that linearization point. A historical signed receipt or challenge response alone cannot prove still-current ownership after subsequent transitions. Proposed only. |

Unimplemented rows are semantics for protocol negotiation, not assigned wire tags. Verifiers must reject unknown kinds and versions. A common Rust verifier runs natively and in the integrity WASM for the implemented type.
