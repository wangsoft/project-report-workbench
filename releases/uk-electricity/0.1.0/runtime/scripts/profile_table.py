#!/usr/bin/env python3
"""Bounded, read-only table inspection. No cleaning or formula recalculation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from datetime import date, datetime
from itertools import islice, zip_longest
from pathlib import Path
from typing import Any


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value[:160] if isinstance(value, str) else value
    return str(value)[:160]


def summarize_rows(rows: Any, scan_rows: int | None, sample_rows: int,
                   max_columns: int) -> dict[str, Any]:
    """Rows are sequences of (raw value, cached value, kind, number format)."""
    result: dict[str, Any] = {
        "physical_rows_observed": 0, "nonempty_rows_in_observed_columns": 0,
        "formula_cells_observed": 0, "missing_formula_cache_observed": 0,
        "error_cells_observed": 0, "max_columns_observed": 0,
        "columns_truncated": False, "samples": [], "issues": [],
    }
    iterator = iter(rows)
    inspected = iterator if scan_rows is None else islice(iterator, scan_rows)
    for row_no, row in enumerate(inspected, 1):
        result["physical_rows_observed"] = row_no
        result["columns_truncated"] |= len(row) > max_columns
        selected = row[:max_columns]
        result["max_columns_observed"] = max(result["max_columns_observed"], len(selected))
        if any(cell[0] not in (None, "") for cell in selected):
            result["nonempty_rows_in_observed_columns"] += 1
        for column_no, (value, cached, kind, _) in enumerate(selected, 1):
            issue = None
            if kind == "f":
                result["formula_cells_observed"] += 1
                if cached is None:
                    result["missing_formula_cache_observed"] += 1
                    issue = "formula_cache_missing"
            if kind == "e" or (kind == "f" and isinstance(cached, str)
                               and cached in {"#REF!", "#DIV/0!", "#VALUE!", "#N/A",
                                              "#NAME?", "#NUM!", "#NULL!"}):
                result["error_cells_observed"] += 1
                issue = "excel_error"
            if issue and len(result["issues"]) < 20:
                result["issues"].append({"row": row_no, "column": column_no, "issue": issue})
        if len(result["samples"]) < sample_rows:
            result["samples"].append({
                "row": row_no,
                "cells": [{"column": index, "value": sample_value(value),
                           "cached": sample_value(cached), "kind": kind,
                           "number_format": fmt}
                          for index, (value, cached, kind, fmt) in enumerate(selected, 1)]})
    # At most one extra physical row is read to distinguish exhaustion from a limit.
    result["all_rows_scanned"] = next(iterator, None) is None
    result["issues_are_bounded_examples"] = True
    return result


def profile_excel(path: Path, scan_rows: int | None, sample_rows: int,
                  max_columns: int) -> list[dict[str, Any]]:
    try:
        import openpyxl
    except ImportError as exc:
        raise ValueError("Excel inspection requires openpyxl; use an environment containing it") from exc
    raw = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        cached = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
        try:
            sheets = []
            for sheet in raw:
                other = cached[sheet.title]
                hints = {"rows": sheet.max_row, "columns": sheet.max_column}
                # Reset unreliable producer dimensions. max_col still bounds cell expansion.
                sheet.reset_dimensions()
                other.reset_dimensions()

                def paired_rows() -> Any:
                    left_rows = sheet.iter_rows(max_col=max_columns + 1)
                    right_rows = other.iter_rows(max_col=max_columns + 1)
                    for left, right in zip_longest(left_rows, right_rows):
                        if left is None or right is None:
                            raise ValueError("Formula/cache row views do not align")
                        # Discard only padding, not duplicates, blank headers or interior blanks.
                        cells = [(a.value, b.value, a.data_type, a.number_format)
                                 for a, b in zip(left, right)]
                        while cells and cells[-1][0] is None and cells[-1][1] is None:
                            cells.pop()
                        yield cells

                stats = summarize_rows(paired_rows(), scan_rows, sample_rows, max_columns)
                stats.update({"name": sheet.title, "visibility": sheet.sheet_state,
                              "dimension_hint_not_record_count": hints,
                              "columns_beyond_limit_may_exist":
                                  hints["columns"] is None or hints["columns"] > max_columns,
                              "formula_cache_freshness": "unverified"})
                sheets.append(stats)
            return sheets
        finally:
            cached.close()
    finally:
        raw.close()


def profile_csv(path: Path, scan_rows: int | None, sample_rows: int,
                max_columns: int, encoding: str, delimiter: str) -> list[dict[str, Any]]:
    with path.open(encoding=encoding, newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        rows = ([(value, value, "text", None) for value in row] for row in reader)
        stats = summarize_rows(rows, scan_rows, sample_rows, max_columns)
    stats.update({"name": path.name, "visibility": "not_applicable",
                  "encoding": encoding, "delimiter": delimiter,
                  "row_definition": "CSV records, including header; quoted newlines stay in one record"})
    return [stats]


def profile(path: Path, *, scan_rows: int | None = 200, sample_rows: int = 5,
            max_columns: int = 128, encoding: str = "utf-8-sig",
            delimiter: str = ",") -> dict[str, Any]:
    path = path.expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError("Input must be a file")
    if scan_rows is not None and scan_rows < 1:
        raise ValueError("scan_rows must be positive or None")
    if sample_rows < 0 or max_columns < 1 or len(delimiter) != 1:
        raise ValueError("Invalid sample limit, column limit or delimiter")
    before = path.stat()
    digest = fingerprint(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        sheets = profile_excel(path, scan_rows, sample_rows, max_columns)
    elif suffix == ".csv":
        sheets = profile_csv(path, scan_rows, sample_rows, max_columns, encoding, delimiter)
    else:
        raise ValueError("Supported: .xlsx, .xlsm, .csv. Convert legacy .xls explicitly on a copy.")
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("Input changed during inspection; rerun on a stable snapshot")
    return {"schema_version": 1, "source": str(path), "sha256": digest,
            "file_bytes": after.st_size,
            "scope": {"scan_rows_per_sheet": scan_rows, "max_columns": max_columns,
                      "sample_rows": sample_rows},
            "limitations": ["No business header or record-grain inference",
                            "Nonempty formula cache does not prove freshness",
                            "Merged ranges, hidden rows, external links and charts not inspected",
                            "Only observed rows/columns checked; dimensions are hints"],
            "sheets": sheets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--scan-rows", type=int, default=200)
    parser.add_argument("--full-scan", action="store_true")
    parser.add_argument("--sample-rows", type=int, default=5)
    parser.add_argument("--max-columns", type=int, default=128)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--delimiter", default=",")
    args = parser.parse_args()
    if args.out and args.out.expanduser().resolve() == args.input.expanduser().resolve():
        parser.error("Output must not overwrite input")
    try:
        result = profile(args.input, scan_rows=None if args.full_scan else args.scan_rows,
                         sample_rows=args.sample_rows, max_columns=args.max_columns,
                         encoding=args.encoding, delimiter=args.delimiter)
        payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            output = args.out.expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                                 delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(payload)
                os.replace(temporary, output)
            finally:
                if temporary:
                    temporary.unlink(missing_ok=True)
            print(f"Profile written: {output}")
        else:
            print(payload, end="")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Inspection failed: {exc}\n")


if __name__ == "__main__":
    main()
