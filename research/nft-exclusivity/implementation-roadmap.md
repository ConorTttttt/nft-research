# From research core to an operational testnet

1. Agree on a genesis manifest with one non-duplicable namespace, machine-readable right definitions, and a public policy for title, outstanding leases and revocation. Exercise disagreements with an application-level reference interpreter.
2. Operate seven distinct test witnesses with authenticated transport, verified-parent caches, single-instance identity ownership, crash-safe outboxes and observability. Simulate client loss immediately after the fifth vote. Require identical recovered child IDs.
3. Test disk loss, rollback, concurrent requests, partition/heal, corrupted ancestry and withheld batches against a multi-conductor network. Measure durable p50/p95/p99 acceptance and publication delays separately, along with proof sizes and delivery to distinct buyers.
4. Replace full-history replay limits with authenticated checkpoints or explicit verified dependencies, with an analysis of long-range compromise and data availability. Bound verification fuel, proof length, malicious request cost and history storage.
5. If contested progress or changing membership is mandatory, select an audited BFT implementation and specify its interaction with old certificates. Model the cutover with hidden signatures before enabling key retirement or lock release.
6. Independently audit encoding, rights semantics, trust bootstrapping, witness storage and recovery. Put production activation behind the resulting evidence. The research branch is a local laboratory and ships no live keys or service deployment.
