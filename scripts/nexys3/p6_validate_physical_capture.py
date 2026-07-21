#!/usr/bin/env python3
"""Strictly parse and compare a physical QF6R capture against frozen golden CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

FIELDS = [
    "test_id",
    "policy_id",
    "state_id",
    "profile_id",
    "selected_path",
    "score",
    "bottleneck_fidelity",
    "cycles",
    "status",
]

LINE_RE = re.compile(
    rb"^QF6R,1,"
    rb"(?P<test_id>\d{4}),"
    rb"(?P<policy_id>\d),"
    rb"(?P<state_id>\d{3}),"
    rb"(?P<profile_id>\d),"
    rb"(?P<selected_path>\d{3}),"
    rb"(?P<score>\d{6}),"
    rb"(?P<bottleneck_fidelity>\d{5}),"
    rb"(?P<cycles>\d{3}),"
    rb"(?P<status>\d)\r\n$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--mode", type=int, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = args.raw.read_bytes()
    lines = raw.splitlines(keepends=True)

    if len(raw) != 3696:
        raise SystemExit(f"expected 3696 bytes, got {len(raw)}")
    if len(lines) != 84:
        raise SystemExit(f"expected 84 records, got {len(lines)}")

    board_rows: list[dict[str, int]] = []
    for index, line in enumerate(lines):
        if len(line) != 44:
            raise SystemExit(f"record {index} is {len(line)} bytes, expected 44")
        match = LINE_RE.fullmatch(line)
        if match is None:
            raise SystemExit(f"invalid QF6R record at index {index}: {line!r}")
        row = {field: int(match.group(field)) for field in FIELDS}
        if row["policy_id"] != args.mode:
            raise SystemExit(
                f"record {index} policy {row['policy_id']} != requested mode {args.mode}"
            )
        board_rows.append(row)

    with args.golden.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit("golden CSV has no header")
        missing = [field for field in FIELDS if field not in reader.fieldnames]
        if missing:
            raise SystemExit(f"golden CSV missing fields: {missing}")
        golden_rows = [
            {field: int(row[field]) for field in FIELDS}
            for row in reader
            if int(row["policy_id"]) == args.mode
        ]

    if len(golden_rows) != 84:
        raise SystemExit(f"expected 84 golden rows for mode {args.mode}, got {len(golden_rows)}")

    if len({row["test_id"] for row in board_rows}) != 84:
        raise SystemExit("physical test IDs are not unique")

    args.outdir.mkdir(parents=True, exist_ok=True)

    board_csv = args.outdir / "board_results.csv"
    with board_csv.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(board_rows)

    compare_csv = args.outdir / "exact_compare.csv"
    mismatches = 0
    field_matches = 0
    total_fields = len(FIELDS) * len(board_rows)

    with compare_csv.open("w", encoding="utf-8", newline="\n") as handle:
        fieldnames = ["row_index", "test_id", "field", "golden", "physical", "match"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for index, (golden, physical) in enumerate(zip(golden_rows, board_rows)):
            for field in FIELDS:
                match = golden[field] == physical[field]
                field_matches += int(match)
                mismatches += int(not match)
                writer.writerow(
                    {
                        "row_index": index,
                        "test_id": physical["test_id"],
                        "field": field,
                        "golden": golden[field],
                        "physical": physical[field],
                        "match": "PASS" if match else "FAIL",
                    }
                )

    status_counts: dict[str, int] = {}
    for row in board_rows:
        key = str(row["status"])
        status_counts[key] = status_counts.get(key, 0) + 1

    summary = {
        "mode": f"H{args.mode}",
        "capture_source": "physical_nexys3_uart",
        "uart": "115200_8N1_raw",
        "raw_bytes": len(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "records": len(board_rows),
        "unique_test_ids": len({row["test_id"] for row in board_rows}),
        "golden_rows": len(golden_rows),
        "row_matches": sum(g == p for g, p in zip(golden_rows, board_rows)),
        "field_matches": field_matches,
        "total_fields": total_fields,
        "mismatches": mismatches,
        "status_counts": status_counts,
        "first_test_id": board_rows[0]["test_id"],
        "last_test_id": board_rows[-1]["test_id"],
        "golden_csv": str(args.golden),
        "golden_sha256": hashlib.sha256(args.golden.read_bytes()).hexdigest(),
    }

    (args.outdir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"P6_PHYSICAL_ROWS={summary['records']}_OF_84")
    print(f"P6_GOLDEN_ROWS={summary['golden_rows']}_OF_84")
    print(f"P6_EXACT_ROW_MATCHES={summary['row_matches']}_OF_84")
    print(f"P6_EXACT_FIELD_MATCHES={field_matches}_OF_{total_fields}")
    print(f"P6_MISMATCHES={mismatches}")

    if summary["row_matches"] != 84 or mismatches != 0:
        raise SystemExit("physical H0 output differs from frozen golden output")

    print("P6_PHYSICAL_TO_GOLDEN_EXACT_COMPARE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
