# Which failure model does an operator actually have?

| Event | Consequence | Permitted response |
|---|---|---|
| Process killed after SQLite transaction commit, before reply | Reservation and full statement survive on honest storage. | Authenticate the identical proposal and reissue its vote. |
| Crash before commit | Honest signer has emitted no vote for the unfinished transaction. | Reopen the same durable database; normal processing may continue. |
| Disk and historical signing key restored together | Restored actor may sign a second digest or a false negative closure report. | Count the identity in e for each affected historical version, or fence it out using independently protected evidence. |
| Losing a disk detected before signing | Halting costs availability. Reconstructing a subset of locks can hide prior votes. | Fail closed until state completeness and exclusive signing-instance control are established. |
| Entire quorum or successive generations roll back beyond the bound | Verifier cannot distinguish authentic conflicting histories. | The stated safety theorem no longer applies. |
| Secret-key compromise without database compromise | Attacker can ignore software locks. | Count the identity as Byzantine. Restoring a clean host cannot withdraw earlier signatures. |

An fsynced write-ahead log protects ordered persistence under its storage contract. The laboratory uses SQLite's default rollback journal and FULL synchronous commits; both remember votes across ordinary process death. Neither supplies a monotonic counter across volume restores. Forward-secure signing helps if old keys have actually been erased everywhere and the verifier can authenticate the period bound. Restoring an old secret reverses that assumption. Key evolution also needs a safe mechanism to choose one transition per period. Threshold signing distributes power, while two reconstructed threshold signatures can still authenticate conflicting statements if enough share holders forget or collude.

A hardware device must bind the parent, digest, signing key and counter advancement atomically, survive cloning/replacement and support an auditable retirement procedure. A fencing token supplied by a cluster only helps if every signing path enforces the token, and old offline verifiers still reject incompatible signatures under their acceptance rule. An independent replicated monotonic signer can replace local persistence, shifting the fault and availability budgets to that service. Replicating immutable positive records without a guaranteed pre-sign write and exhaustive recovery is insufficient.

The prototype's budget covers a **bounded number of forgetting identities**, not a guarantee of detecting stale images. For an operational deployment count lost keys, copied keys, mistaken disk restores and correlated administrators in the same budget. Public fixtures cannot establish independence. A hidden certificate can block reset forever even when every accessible witness honestly reports its own history.
