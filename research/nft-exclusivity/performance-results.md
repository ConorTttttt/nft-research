# Baseline and measurement

One process, x86-64 Intel Xeon Platinum 8573C, Rust 1.96.1 release build, pinned Cargo.lock. Reproduce with `cd prototype && cargo run --release --locked --example measure`. Each trial uses 64 verified distinct parents, one controller and distinct recipients. The individual baseline uses precisely the same checks, signature implementation and quorum policy with batch width one. Five separate in-memory SQLite stores vote sequentially. The timer includes canonical encoding, owner signing, five witness authorisation checks and reservations, five witness signatures, final certificate verification and child derivation. Setup and key creation are outside the timer. One warm-up is discarded per width, followed by eleven trials; all widths execute in ascending order.

| Moves per certificate | Median time for 64 moves | Min–max | Witness signatures |
|---:|---:|---:|---:|
| 1 | 37.274 ms | 36.356–39.084 ms | 320 |
| 4 | 10.366 ms | 9.870–10.594 ms | 80 |
| 16 | 3.590 ms | 3.404–3.705 ms | 20 |
| 64 | 1.925 ms | 1.889–2.036 ms | 5 |

The 64-wide batch took about 19.4× less local elapsed time per 64 moves in this run. It performs fewer signature operations and fewer SQLite transactions. With five replies the witness signature bytes fall from 20,480 to 320 in total. The 64 input/recipient pairs still occupy 4,096 bytes before framing. Ed25519 signatures add 64 bytes per owner and per witness, with at least one signer index per witness in this format. These counts exclude parent proofs, roster and transport framing. Full proof delivery to each buyer can **increase aggregate outbound bytes**, especially for unrelated recipients. A fair batched object-certificate implementation can obtain the same signature saving.

There are no network RTT, DHT throughput, disk fsync, Wasm verification latency or consensus-view-change measurements in this benchmark. Durability is exercised separately. In a healthy network the signing phase requires a round trip to a reachable quorum once parents and owner signature are available; buyer delivery, acquisition of dependencies and optional publication take additional time. A batch waits for its slowest needed input and may wait to fill. The implementation shares one SQLite writer per witness, so the formal concurrency width cannot be read as a machine-level throughput multiplier.
