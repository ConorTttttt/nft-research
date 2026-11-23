# Counterexample traces

| Failed conjecture | Trace and consequence |
|---|---|
| FULL synchronous SQLite prevents equivocation after volume restoration | In 7/5, 0 and 1 are Byzantine. A is signed by 0–4 and retained privately. 5 and 6 vote B. Restore 2's quiescent old database and retain its old private key. B now has 0,1,2,5,6. Both pass signature verification. Process trace in results/adversarial.jsonl. |
| A valid fence read can be reused after enough reporters forget | With n=4,q=3, one Byzantine and one extra restorable signer, three empty reports can establish reset assuming e=1. Restore one truthful empty reporter. Together with the Byzantine and the missing signer it can now certify A. Counting the restorable identity in e invalidates this parameter set. |
| A timeout can always safely release partial votes | Accessible honest reports A,A,A,B,B, two silent. The silent pair may have signed A privately. There is no valid negative proof for A. |
| Fresh epoch keys resolve old disputes | Two disjoint healthy committees both certify from the same input when the registry changes its current roster without an old-policy decision. Both certificates validate independently under their own rosters. |
| Any Merkle inclusion proves global validity | A builder could include the same parent twice at different indices. Both leaves have valid paths. Honest whole-batch validators reject before signing. Omitting that check would violate conservation even with a unique root. |
| Reading absent votes is equivalent to permanent fencing | Collect empty read responses from everyone, then let five vote A. A reset based on the earlier reads conflicts with A. |
| Quorum aggregation removes participant coordination | One threshold signature can encode the participation of five signers. Removing the honest intersection still permits two conflicting aggregate certificates. |
| A pairwise conflict graph captures all restrictions | Three different unit claims against a pool of capacity two. Every pair is feasible and the triple is impossible. |
| Any conditional program can be exercised independently | Program sends title to B on oracle X, C on oracle Y. If both positive facts can coexist, two isolated presentations satisfy distinct branches. |

A failure from an out-of-budget fault is a model boundary. A stalled contested input is a liveness failure allowed by the direct certification protocol. The two are operationally different. All live-process adversarial scenarios use locally generated keys and real signature checks.

The strongest rejected repair was “finish the only remaining plausible transfer”. From the same seven entirely honest permanent reports, two six-report projections each leave exactly one plausible old certificate, for opposite recipients. The constructed trace is reproducible with `python3 formal-models/ambiguous_repair.py`. It demonstrates why the fallback child has to be fixed even when a local view seems decisive.
