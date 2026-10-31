#!/usr/bin/env python3
"""Measure an existing command; does not clear caches or measure model usage.

Example: python benchmark_command.py --out timing.json -- python report.py --help
Repeated commands must be idempotent or create isolated output directories.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def measure(command: list[str], repeats: int = 1, timeout: float = 300) -> dict[str, Any]:
    if not command or repeats < 1 or timeout <= 0:
        raise ValueError("Provide a command, positive repeat count and positive timeout")
    runs = []
    for index in range(repeats):
        start = time.perf_counter()
        error = None
        try:
            # Inherit output rather than holding potentially large reports in memory.
            completed = subprocess.run(command, timeout=timeout, check=False)
            status = "passed" if completed.returncode == 0 else "failed"
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            status, exit_code, error = "timeout", None, "Command exceeded timeout"
        except OSError as exc:
            status, exit_code, error = "launch_error", None, str(exc)
        runs.append({"index": index + 1, "wall_seconds": time.perf_counter() - start,
                     "status": status, "exit_code": exit_code, "error": error})
        if status != "passed":
            break
    times = [run["wall_seconds"] for run in runs if run["status"] == "passed"]
    return {
        "schema_version": 1, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "requested_repeats": repeats, "completed_runs": len(runs),
        "status": "passed" if len(times) == repeats else "failed",
        "runs": runs,
        "successful_wall_seconds": {"count": len(times),
                                    "median": statistics.median(times) if times else None,
                                    "min": min(times) if times else None,
                                    "max": max(times) if times else None},
        "cache_state": "not_measured", "model_calls": None, "input_tokens": None,
        "output_tokens": None, "peak_memory_bytes": None,
        "limitations": ["Measures whole command wall time, not internal stages",
                        "Does not clear or verify caches; successful exit is not report QA",
                        "Stops after first failure; no automatic retry",
                        "Timeout controls direct process; command owns descendant cleanup",
                        "Command argv omitted from saved record to avoid persisting secrets"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.repeat < 1 or args.timeout <= 0:
        parser.error("Provide a command after -- and positive repeat/timeout values")
    output = args.out.expanduser()
    # Reserve a new result path before executing potentially costly work.
    # Do not overwrite any prior artifact, including inputs.
    try:
        with output.open("x", encoding="utf-8") as handle:
            json.dump({"status": "running"}, handle)
            handle.flush()
            result = measure(command, args.repeat, args.timeout)
            handle.seek(0)
            json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.truncate()
            handle.write("\n")
    except OSError as exc:
        parser.exit(2, f"Cannot write benchmark result: {exc}\n")
    print(f"Benchmark {result['status']}: {output}")
    raise SystemExit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
