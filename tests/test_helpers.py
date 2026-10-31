from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from metric_math import contributions, decimal, growth, pooled_rate, ratio
from profile_table import fingerprint, profile


class MetricTests(unittest.TestCase):
    def test_growth_with_known_answer(self) -> None:
        self.assertEqual(growth("80", "100"), Decimal("-0.2"))

    def test_zero_and_negative_baseline(self) -> None:
        self.assertIsNone(growth(10, 0))
        self.assertIsNone(growth(10, -10))
        self.assertIsNone(ratio(5, 0))

    def test_pooled_rate_is_not_mean_of_rates(self) -> None:
        self.assertEqual(pooled_rate([1, 9], [2, 90]), Decimal(10) / Decimal(92))
        with self.assertRaises(ValueError):
            pooled_rate([1], [2, 3])
        with self.assertRaises(ValueError):
            pooled_rate([1], [-2])

    def test_offsetting_changes(self) -> None:
        result = contributions({"A": 80, "B": 120}, {"A": 100, "B": 100})
        self.assertEqual(result["deltas"], {"A": Decimal(-20), "B": Decimal(20)})
        self.assertEqual(result["contributions"], {"A": None, "B": None})

    def test_contributions_can_exceed_one(self) -> None:
        result = contributions({"A": 80, "B": 110}, {"A": 100, "B": 100})
        self.assertEqual(result["contributions"], {"A": Decimal(2), "B": Decimal(-1)})

    def test_near_zero_and_category_change(self) -> None:
        result = contributions({"A": "10.001"}, {"A": "10"}, near_zero="0.01")
        self.assertIsNone(result["contributions"]["A"])
        with self.assertRaises(ValueError):
            contributions({"A": 1}, {"B": 1})

    def test_preserve_decimal_precision_and_reject_ambiguous(self) -> None:
        self.assertEqual(decimal("0.1") + decimal("0.2"), Decimal("0.3"))
        for value in [0.1, None, True, "NaN", "Infinity", "12%", "1,000"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decimal(value)


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_csv_keeps_ids_duplicate_headers_and_multiline(self) -> None:
        path = self.root / "data.csv"
        path.write_text('id,id,note\n001,002,"first\nsecond"\n003,004,last\n', encoding="utf-8")
        result = profile(path, scan_rows=None)
        sheet = result["sheets"][0]
        self.assertEqual(sheet["physical_rows_observed"], 3)
        self.assertEqual([c["value"] for c in sheet["samples"][0]["cells"]], ["id", "id", "note"])
        self.assertEqual(sheet["samples"][1]["cells"][0]["value"], "001")
        self.assertTrue(sheet["all_rows_scanned"])

    def test_bounded_scan_does_not_claim_complete(self) -> None:
        path = self.root / "data.csv"
        path.write_text("a,b,c\n1,2,3\n4,5,6\n", encoding="utf-8")
        sheet = profile(path, scan_rows=2, max_columns=2, sample_rows=0)["sheets"][0]
        self.assertFalse(sheet["all_rows_scanned"])
        self.assertTrue(sheet["columns_truncated"])
        self.assertEqual(sheet["samples"], [])
        self.assertEqual(sheet["physical_rows_observed"], 2)

    def test_empty_csv_and_exact_scan_boundary(self) -> None:
        path = self.root / "data.csv"
        path.write_text("", encoding="utf-8")
        sheet = profile(path)["sheets"][0]
        self.assertEqual(sheet["physical_rows_observed"], 0)
        self.assertTrue(sheet["all_rows_scanned"])
        path.write_text("a\n1\n", encoding="utf-8")
        self.assertTrue(profile(path, scan_rows=2)["sheets"][0]["all_rows_scanned"])

    def test_workbook_formula_error_hidden_and_raw_unchanged(self) -> None:
        from openpyxl import Workbook
        path = self.root / "data.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.append(["id", "id", "amount"])
        ws.append(["001", "002", "=1+2"])
        ws.append([None, None, "#DIV/0!"])
        wb.create_sheet("Hidden").sheet_state = "hidden"
        wb.save(path)
        wb.close()
        before = fingerprint(path)
        result = profile(path, scan_rows=None)
        self.assertEqual(fingerprint(path), before)
        sheet = result["sheets"][0]
        self.assertEqual(sheet["formula_cells_observed"], 1)
        self.assertEqual(sheet["missing_formula_cache_observed"], 1)
        self.assertEqual(sheet["error_cells_observed"], 1)
        self.assertEqual(result["sheets"][1]["visibility"], "hidden")
        self.assertEqual(sheet["formula_cache_freshness"], "unverified")

    def test_bad_dimensions_do_not_truncate_real_rows(self) -> None:
        from openpyxl import Workbook
        from zipfile import ZipFile
        import re
        original = self.root / "original.xlsx"
        path = self.root / "bad-dimension.xlsx"
        wb = Workbook()
        wb.active.append(["a", "b"])
        wb.active.append([1, 2])
        wb.save(original)
        wb.close()
        with ZipFile(original) as source, ZipFile(path, "w") as target:
            for name in source.namelist():
                content = source.read(name)
                if name == "xl/worksheets/sheet1.xml":
                    content = re.sub(rb'<dimension ref="[^"]+"', b'<dimension ref="A1:A1"', content)
                target.writestr(name, content)
        sheet = profile(path, scan_rows=None)["sheets"][0]
        self.assertEqual(sheet["physical_rows_observed"], 2)
        self.assertEqual(sheet["max_columns_observed"], 2)

    def test_cli_json_and_overwrite_rejection(self) -> None:
        path = self.root / "input.csv"
        output = self.root / "profile.json"
        path.write_text("id\n001\n", encoding="utf-8")
        script = str(ROOT / "scripts" / "profile_table.py")
        result = subprocess.run([sys.executable, script, str(path), "--out", str(output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())["sha256"], fingerprint(path))
        before = path.read_bytes()
        result = subprocess.run([sys.executable, script, str(path), "--out", str(path)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_bytes(), before)

    def test_invalid_options_and_legacy_xls(self) -> None:
        path = self.root / "input.csv"
        path.write_text("a", encoding="utf-8")
        for kwargs in [{"scan_rows": 0}, {"max_columns": 0}, {"sample_rows": -1}, {"delimiter": "||"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                profile(path, **kwargs)
        legacy = self.root / "input.xls"
        legacy.write_text("not a supported file", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "legacy"):
            profile(legacy)


if __name__ == "__main__":
    unittest.main()
