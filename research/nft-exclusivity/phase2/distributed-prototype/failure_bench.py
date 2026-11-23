"""First-quorum latency with fanout to all configured endpoints. Drain late replies between trials."""

import concurrent.futures as futures
import json
import time
from lab import Lab, pub, receipt, verify_receipt, slot

with Lab(8, 6, 3) as lab:
    for group, case in enumerate(("healthy", "two_delayed", "two_terminated")):
        if case == "two_terminated":
            lab.stop(0)
            lab.stop(1)
        for trial in range(8):
            parent = group * 100 + trial
            p = lab.make(parent, mode="tree")
            start = time.perf_counter_ns()
            pending = [
                lab.pool.submit(
                    lab.rpc,
                    i,
                    dict(op="vote", p=p),
                    40 if i < 2 and case == "two_delayed" else 0,
                )
                for i in range(8)
            ]
            votes = []
            for future in futures.as_completed(pending):
                try:
                    r, _ = future.result()
                except OSError:
                    continue
                votes.append(r["ok"]["vote"])
                if len(votes) == 6:
                    verify_receipt(
                        lab.config, receipt(p, votes, 0), pub(lab.owner), slot(parent)
                    )
                    break
            assert len(votes) == 6
            elapsed = (time.perf_counter_ns() - start) / 1e6
            futures.wait(pending)
            print(
                json.dumps(
                    dict(
                        case=case,
                        trial=trial,
                        attempted=8,
                        quorum=6,
                        elapsed_ms=elapsed,
                    )
                )
            )
