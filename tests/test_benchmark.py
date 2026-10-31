from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_command import measure


class BenchmarkTests(unittest.TestCase):
    def test_success_statistics_and_unknown_resources(self) -> None:
        result = measure([sys.executable, "-c", "pass"], repeats=2)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["successful_wall_seconds"]["count"], 2)
        self.assertGreater(result["successful_wall_seconds"]["median"], 0)
        self.assertIsNone(result["model_calls"])
        self.assertIsNone(result["peak_memory_bytes"])
        self.assertEqual(result["cache_state"], "not_measured")

    def test_failure_does_not_retry_or_count_as_success(self) -> None:
        result = measure([sys.executable, "-c", "raise SystemExit(7)"], repeats=3)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["completed_runs"], 1)
        self.assertEqual(result["runs"][0]["exit_code"], 7)
        self.assertIsNone(result["successful_wall_seconds"]["median"])

    def test_timeout(self) -> None:
        result = measure([sys.executable, "-c", "import time; time.sleep(2)"], timeout=0.05)
        self.assertEqual(result["runs"][0]["status"], "timeout")
        self.assertEqual(result["status"], "failed")

    def test_missing_executable_and_invalid_options(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = measure([str(Path(directory) / "missing")])
        self.assertEqual(result["runs"][0]["status"], "launch_error")
        for command, repeats, timeout in [([], 1, 1), (["x"], 0, 1), (["x"], 1, 0)]:
            with self.subTest(command=command, repeats=repeats, timeout=timeout):
                with self.assertRaises(ValueError):
                    measure(command, repeats, timeout)

    def test_cli_writes_failure_and_preserves_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "timing.json"
            script = str(ROOT / "scripts/benchmark_command.py")
            args = [sys.executable, script, "--out", str(output), "--", sys.executable,
                    "-c", "raise SystemExit(7)"]
            run = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertEqual(json.loads(output.read_text())["runs"][0]["exit_code"], 7)
            before = output.read_bytes()
            run = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(before, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
