"""Matched loopback profiles. Each trial uses fresh inputs and five or six provisioned workers."""

import statistics
import concurrent.futures as futures
import json
import time
from lab import Lab, pub, slot
from protocol import receipt, verify_receipt


def stats(lab, ids):
    return [r["ok"] for r, _ in lab.fan(ids, {"op": "stats"})]


def trial(lab, offset, width, mode, delay):
    q = lab.config["q"]
    ids = range(q)
    before = stats(lab, ids)
    sign_ns = []
    traffic = buyer_bytes = verify_ns = 0
    start = time.perf_counter_ns()
    for first in range(offset, offset + 64, width):
        p = lab.make(first, width, mode=mode)
        replies = lab.fan(ids, dict(op="vote", p=p), delay)
        traffic += sum(size for _, size in replies)
        votes = [r["ok"]["vote"] for r, _ in replies]
        sign_ns.extend(r["ok"]["sign_ns"] for r, _ in replies)
        proof = receipt(p, votes, 0)
        buyer_bytes += len(json.dumps(proof, separators=(",", ":")))
        tick = time.perf_counter_ns()
        verify_receipt(lab.config, proof, pub(lab.owner), slot(first))
        verify_ns += time.perf_counter_ns() - tick
    elapsed = (time.perf_counter_ns() - start) / 1e6
    after = stats(lab, ids)
    return dict(
        n=len(lab.procs),
        q=q,
        width=width,
        mode=mode,
        delay_ms=delay,
        elapsed_ms=elapsed,
        verify_us=verify_ns / 1000 / (64 / width),
        sign_us=statistics.mean(sign_ns) / 1000,
        requests=64 // width * q,
        tcp_payload_bytes=traffic,
        one_buyer_bytes=buyer_bytes // (64 // width),
        vote_txns=sum(y[0] - x[0] for x, y in zip(before, after)),
        worker_cpu_ms=sum(y[1] - x[1] for x, y in zip(before, after)) * 1000,
        max_worker_peak_kib=max(y[2] for y in after),
    )


if __name__ == "__main__":
    for n, q, e in [(7, 5, 2), (8, 6, 3)]:
        with Lab(n, q, e) as lab:
            offset = 0
            profiles = [
                (1, "flat", 0),
                (64, "flat", 0),
                (64, "tree", 0),
                (64, "tree", 20),
            ]
            for iteration in range(6):
                for j in range(4):
                    width, mode, delay = profiles[(iteration + j) % 4]
                    row = trial(lab, offset, width, mode, delay)
                    row.update(iteration=iteration)
                    print(json.dumps(row), flush=True)
                    offset += 64
            for simultaneous in [1, 4]:
                ps = [lab.make(offset + i) for i in range(16)]
                start = time.perf_counter()
                with futures.ThreadPoolExecutor(simultaneous) as workers:

                    def finish(p):
                        v = lab.votes(range(q), p)
                        verify_receipt(
                            lab.config,
                            receipt(p, v, 0),
                            pub(lab.owner),
                            p["moves"][0][0],
                        )

                    list(workers.map(finish, ps))
                print(
                    json.dumps(
                        dict(
                            n=n,
                            parallel_clients=simultaneous,
                            transfers=16,
                            elapsed_ms=(time.perf_counter() - start) * 1000,
                        )
                    ),
                    flush=True,
                )
                offset += 16
