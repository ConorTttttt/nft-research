# Comparison and operational cost

The matched verifier test uses one optimized native Rust process on Linux x86_64, Intel Xeon Platinum 8573C, Rust 1.96.1. For each of 25 samples it verifies the Phase 3 fixed paid proof ten times and then the Phase 4 lab paid proof ten times, measuring process CPU with CLOCK_PROCESS_CPUTIME_ID. Fixed ordering and repeated inputs favor warm caches. Median microseconds per verification were **434.0** for Phase 3 and **786.4** for Phase 4. Proofs were 909 and 1,559 bytes. The extra cost buys authenticated source votes under a separate currency contract. [Raw paired CPU totals in µs per ten](results/cpu.csv) · [Benchmark](prototype/verifier/examples/cpu.rs)

| Boundary | Result |
|---|---|
| Phase 3 conditional decision | One title quorum (5 of 7) and a simulated unilateral payment issuer. Ordinary Phase 3 paid slots 3–23 had median 26.879 ms including local agreement execution. |
| Phase 4 lab decision | One title quorum plus one source disposition quorum. In the fixed disjoint profile 10 of 14 witnesses sign in two sequential voting stages. Each stage has five independent signatures plus seller/buyer authorization, respectively. Exercise requires zero additional decisions. Fresh onward spending is a new choice. |
| Phase 4 lab wall time | Across 24 runs (16 paid, 8 void), median 22.003 ms for both vote stages including SQLite and in-process threads. CLI verification 3.339 ms, four complete archival writes/acknowledgments 11.800 ms, independent read plus verifier subprocess 3.561 ms. Archive acknowledgments are four extra signatures; the prototype writes sequentially. These are different operations from Phase 3's end-to-end path. |
| Storage | SQLite main files across 14 lab signers occupied 286,720 bytes after the first run and 524,288 after the last. Includes file/page overhead and multiple accumulated slots. Four copies store at least 6,236 payload bytes per completed archival barrier before indexing. |
| Release conductor | One timed local observation each. Park 335 ms, execute RAVE 345 ms, second-cell transaction lookup 170 ms, collect receipt 313 ms. Separate reject 313 ms and reclaim 264 ms. Includes CLI startup, authorization transport and serialization. No network finality CPU or end-to-end *final* settlement time exists for this path. |
| Phase 3 archive control | One stock-conductor publish 182 ms and retrieval 172 ms via CLI. Phase 4's complete lab blob used SQLite rather than the DHT. |

The measurable improvement is removal of reliance on one simulated signer **within the lab acceptance profile** and recovery by another process after writer loss. The release path separately improves the strength of the funding/execution evidence. Neither change speeds up verified native finality. Retention before external recognition costs another dissemination and acknowledgment stage. Recovery after a permanent stall has no finite upper bound. Replica independence, public testnet/WAN overhead, quorum network latency, cold key recovery, batched performance and production throughput were not measured. [Lab rows](results/lab.jsonl) · [Conductor RPC timings](results/final-conductor.jsonl) · [Phase 3 run](results/phase3-run.txt)

For the real payment history, five signed records occupied 12,892 bytes as compact CLI JSON, excluding the CEL grant and transport. Across 25 fresh audits of the cached records, median CPU was 15.455 ms and median elapsed time was 15.397 ms. This includes the Python grant/binding checks and launching five Rust signature/hash checker processes per sample. It excludes conductor retrieval, file parsing at startup, and verification of an exclusive native disposition, for which no evidence was available. Reproduce with the command below. [Raw audit costs](results/history-cost.jsonl)

```sh
python3 unyt-integration/time_history.py results/funded-records.jsonl "${CARGO_TARGET_DIR:-unyt-integration/record-check/target}/release/phase4-historical-record"
```
