#!/usr/bin/env python3
# Strict parser for P6 QF6R version-1 physical or simulated raw logs.

from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path

FIELDS=["test_id","policy_id","state_id","profile_id","selected_path","score",
        "bottleneck_fidelity","cycles","status"]
PATTERN=re.compile(
    rb"QF6R,1,(\d{4}),(\d),(\d{3}),(\d),(\d{3}),"
    rb"(\d{6}),(\d{5}),(\d{3}),(\d)\r\n"
)

def parse_bytes(data:bytes):
    matches=list(PATTERN.finditer(data))
    rows=[]
    for m in matches:
        values=[int(x) for x in m.groups()]
        row=dict(zip(FIELDS,values))
        if not 0<=row["test_id"]<=9999: raise ValueError("test_id")
        if not 0<=row["policy_id"]<=4: raise ValueError("policy_id")
        if not 0<=row["state_id"]<=255: raise ValueError("state_id")
        if not 0<=row["profile_id"]<=3: raise ValueError("profile_id")
        if row["selected_path"] not in (0,1,2,3,255): raise ValueError("selected_path")
        if not 0<=row["score"]<=262143: raise ValueError("score")
        if not 0<=row["bottleneck_fidelity"]<=65535: raise ValueError("fidelity")
        if not 0<=row["cycles"]<=999: raise ValueError("cycles")
        if row["status"] not in (0,1,2): raise ValueError("status")
        if row["status"]!=0 and (
            row["selected_path"]!=255 or
            row["score"]!=0 or
            row["bottleneck_fidelity"]!=0
        ):
            raise ValueError("non-OK sentinel")
        rows.append(row)
    return rows,matches

def write_csv(path:Path,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("raw_log",type=Path)
    ap.add_argument("output_csv",type=Path)
    ap.add_argument("--expected-records",type=int)
    args=ap.parse_args()
    data=args.raw_log.read_bytes()
    rows,matches=parse_bytes(data)
    if args.expected_records is not None and len(rows)!=args.expected_records:
        raise SystemExit(f"record count {len(rows)} != {args.expected_records}")
    raw_only=b"".join(m.group(0) for m in matches)
    if len(raw_only)!=len(rows)*44:
        raise SystemExit("fixed record length failure")
    write_csv(args.output_csv,rows)
    print(f"P6_QF6R_PARSED_RECORDS={len(rows)}")
    print(f"P6_QF6R_PARSED_BYTES={len(raw_only)}")
    print("P6_QF6R_PARSER=PASS")

if __name__=="__main__":
    main()
