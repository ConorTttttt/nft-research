"""Wall time for 21 fresh CLI processes, including startup and output validation."""

import json
import subprocess
import sys
import time

for i in range(21):
    tick = time.perf_counter_ns()
    subprocess.run(
        [*sys.argv[1:], "01" * 32, str(i), "02" * 32, "10", "10"],
        check=True,
        capture_output=True,
    )
    print(
        json.dumps(dict(sample=i, engine_cli_us=(time.perf_counter_ns() - tick) / 1000))
    )
