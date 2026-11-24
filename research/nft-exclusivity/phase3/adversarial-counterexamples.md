# Failure traces and interpretations

These are protocol-level histories. They make the missing premise explicit.

| Weakened rule | Observable history | Consequence |
|---|---|---|
| Highest locally visible receipt is final | Two views each contain a valid sequence-one receipt from the same predecessor. After healing both see duplicate sequence one. | Earlier buyers cannot both have had irreversible title. Detecting the conflict later cannot choose a previously guaranteed winner. |
| Rollback counts only simultaneous faults | At 7/5 the minimum intersection is three identities. If three can contradict themselves over time both branches can certify. | Fails the stated e=2 premise. baseline-temporal.txt contains the small-model restoring trace and state counts. |
| Promote the sole still-possible transfer after closing | A,A,B,B,empty,empty,empty. One projection omits a B, another omits an A. | The projections support incompatible promotions. Both candidates can be excluded by the complete set. Only the fixed refund is safe under that rule. |
| Reassign an unresolved parent to a new committee | Disjoint policies each approve a child of the same parent. | Each local certificate verifies under its own policy; only one verifies under the authenticated predecessor. See baseline-membership_test.jsonl. |
| Refund on deadline or missing publication | Payment is committed and evidence is withheld. Seller sees the same timeout as in the never-paid execution. | Unconditionally refunding title can give the seller both assets. Preserve pending status until terminal evidence is recovered. |
| Payment issuer may roll back | Issuer signs paid for a committed sale, then its earlier view permits void for the same ID. | The two signatures entail opposite controllers. NFT quorum correctness alone cannot protect this boundary. |
| Derive title from economic simulation | A valid computed allocation is shown before any authoritative debit or before recovery of funds is excluded. | Transferring title can leave seller unpaid. The actual hNFT payment seam explicitly marks this as demo-only. |
| Prove vacant possession by scanning bookings | Scan sees no lease; concurrent issuer grants tomorrow's booking before sale acceptance. | A predicate changed without consuming a common guard. compiler.py and check.py establish the required interval support in the bounded model. |
| Use a signed record as a validated root | Exact action exists but local validation status is rejected, or dependencies are unavailable. | A proof against an untrusted historical root is worthless. Upstream G6.2 documented this behavior. The archive checks local status and verifies the full portable proof. |
| Reuse proof under a second payment realm / free import | Same key bytes or RAVE hash interpreted under different rules, or two apps independently mint on the same receipt. | Role and realm substitution or duplicated title. Wrong realm rejected in demo. Consuming export is required for moving exclusive authority. |
| Treat a once-valid successor as current | Alice→Bob certificate is retained after Bob→Carol certifies. | Both certificates remain valid history. Only the current version can complete a new certified spend. |

Withholding a terminal proof, refusing to execute, and split partial votes can cause permanent locking within the safety model. A wrongly backdated action on a source-chain branch cannot satisfy this prototype's missing issuer-signature check because time is not an input. No live attacks on third-party applications were performed.
