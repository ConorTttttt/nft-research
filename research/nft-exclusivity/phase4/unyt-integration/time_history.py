"""Measure end-to-end offline signed-history checking, including five Rust processes."""

import json
from pathlib import Path
import resource
import sys
import time

from signed_history import audit_history

capture, binary = sys.argv[1:]
values = {
    row["step"]: row["value"]
    for line in Path(capture).read_text().splitlines()
    if "step" in (row := json.loads(line))
}
grant = values["verified conditional grant"]
for _ in range(25):
    start = time.perf_counter_ns()
    main_start = time.process_time_ns()
    child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    status, message = audit_history(
        values, grant["domain"], grant["conditional_child"], binary
    )
    assert status == "Pending" and message.startswith(
        "signed historical records verified"
    )
    child_end = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (time.process_time_ns() - main_start) / 1000 + 1e6 * (
        child_end.ru_utime
        + child_end.ru_stime
        - child_start.ru_utime
        - child_start.ru_stime
    )
    print(
        json.dumps(
            {
                "cpu_us": round(cpu, 3),
                "wall_us": (time.perf_counter_ns() - start) / 1000,
            }
        )
    )
