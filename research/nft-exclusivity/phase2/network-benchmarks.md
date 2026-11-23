# Measurements and comparison boundaries

The original Rust executable ran unchanged at commit 35146dcc, using Rust 1.96.1, release mode and the original lockfile. Its local in-memory medians for 64 moves were 36.695, 10.024, 3.540 and 1.950 ms at widths 1, 4, 16 and 64. The published Phase 1 endpoints were 37.274 and 1.925 ms. Four Rust tests passed. [Reproduction output](results/baseline.txt)

The distributed runs used separate Python 3.12.14 worker processes, one SQLite 3.53.1 database with FULL synchronous transactions per worker, fresh Ed25519 keys through cryptography 50.0.0, TCP loopback and an x86-64 Xeon Platinum 8573C. All workers share a machine, filesystem, scheduler and failure domain. The client is a separate process. For the matched comparison the flat codec implements Phase 1 decision semantics over a common Phase 2 wire protocol. Both batch modes include the extra cost of retaining the body, and verify the same set of outputs at the witnesses. These are networked semantic controls; the original Rust executable is the independent local baseline.

**Matched trials.** Each row processes 64 distinct genesis inputs. One warmup per profile, five measured trials in rotated order, fresh inputs each trial. Send to exactly q willing workers concurrently; wait for all q. Build the owner proposal, request and verify the buyer receipt for index zero in each batch. Timing ends in the collecting client. The buyer bytes column measures the actual compact JSON that a separate buyer would receive. It excludes ancestry and the roster, which are assumed available. The timer includes local proof construction and verification but no second network hop to a buyer. Width 64 therefore verifies one buyer receipt, whereas width one verifies 64. A study of servicing all 64 buyers must measure constructing, delivering and verifying all their receipts.

| n/q | Width, body | Added signing RTT | Median elapsed for 64 (min–max), ms | JSON bytes per buyer receipt | Requests / durable vote transactions |
|---|---|---:|---:|---:|---:|
| 7/5 | 1, flat | 0 | 407.55 (403.98–418.52) | 996 | 320 |
| 7/5 | 64, flat | 0 | 10.89 (9.63–11.58) | 9,565 | 5 |
| 7/5 | 64, tree | 0 | 10.31 (9.64–11.58) | 1,405 | 5 |
| 7/5 | 64, tree | 20 ms | 30.71 (30.49–31.93) | 1,405 | 5 |
| 8/6 | 1, flat | 0 | 455.04 (446.43–469.39) | 1,131 | 384 |
| 8/6 | 64, flat | 0 | 11.33 (9.58–11.75) | 9,700 | 6 |
| 8/6 | 64, tree | 0 | 11.26 (10.99–12.01) | 1,540 | 6 |
| 8/6 | 64, tree | 20 ms | 31.83 (30.54–32.64) | 1,540 | 6 |

At 7/5 the tree cut per-buyer JSON by 85.3%. At 8/6 the reduction was 84.1%. Compact proofs did not reduce signer traffic: at width 64 the 7/5 medians were 45,290 bytes for flat versus 45,291 for tree, and both 8/6 profiles used about 54,349 bytes. These are serialized request plus reply payloads including instrumentation; TCP/IP headers and handshakes are excluded. Median per-receipt verification for 7/5 tree was 661 µs, and the within-trial mean signing time had median 91 µs. For 8/6 tree the corresponding figures were 845 and 72 µs. CPU times include worker-side request handling and some stats overhead. RSS is per-worker process high-water mark. Vote transaction counts are application commits, not physical disk writes. [All trials, CPU, memory and byte counters](results/network.jsonl)

**Contention, delay and failure.** For 16 independent singleton transfers the 7/5 run took 102.65 ms with one client in flight and 102.65 ms with four; 8/6 took 115.04 and 122.41 ms. This single short experiment shows no throughput gain. Each witness serves one request at a time. Artificial RTT sleeps are at the RPC endpoints and approximate delay only. In a separate first-quorum trial fan-out attempted all eight endpoints. Over seven measured singleton trials the median time to six verified votes was 8.16 ms healthy, 7.22 ms with two endpoints delayed by 40 ms, and 7.11 ms with two terminated. Small differences also reflect scheduling and refused loopback connections. These are not evidence that faults improve latency. [Failure trials](results/failure-latency.jsonl)

**Recovery and publication.** For a real 2–2 partial split and seven available reporters, close, verify and install took 16.63 ms median (15.93–19.30, five measured). Process termination, restart, rejection of an alternative and identical retry took 43.30 and 90.46 ms in two individual runs. No storage rollback detector was involved. Publication on stock Holochain was deliberately held 250 ms. The positive CLI call then took 173.71 ms, and a reset-plus-transfer publication took 184.35 ms. These two measurements include client startup and local authoring and exclude remote DHT visibility. [Recovery trials](results/membership.jsonl) · [Conductor test](results/conductor.jsonl)

The results support smaller recipient payloads, a specific safety budget and feasibility of a local end-to-end boundary. They do not estimate WAN throughput, tail service levels, crash-consistent media behaviour under power loss or independently operated committee reliability.
