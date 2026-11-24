"""Verify the known run using fixture pins. Applications must supply independent pins."""

from pathlib import Path
import json
import subprocess
import sys

capture, checker = sys.argv[1:]
grant = next(
    row["value"]
    for line in Path(capture).read_text().splitlines()
    if (row := json.loads(line)).get("step") == "verified conditional grant"
)
subprocess.run(
    [
        sys.executable,
        Path(__file__).with_name("signed_history.py"),
        capture,
        checker,
        grant["domain"],
        grant["conditional_child"],
    ],
    check=True,
)
