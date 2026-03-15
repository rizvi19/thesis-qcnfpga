#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path


def read_values(path: Path) -> list[int]:
    vals: list[int] = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            vals.append(int(row["value_dec"]))
    return vals


def monobit_stats(values: list[int], width: int = 64) -> dict:
    ones = sum(v.bit_count() for v in values)
    total = len(values) * width
    zeros = total - ones
    expected = total / 2.0
    chi2 = ((ones - expected) ** 2) / expected + ((zeros - expected) ** 2) / expected
    z = (ones - expected) / math.sqrt(total * 0.25)
    return {
        "ones": ones,
        "zeros": zeros,
        "one_ratio": ones / total if total else 0.0,
        "chi_square_1bit": chi2,
        "z_score": z,
    }


def bucket_stats(values: list[int], bits: int = 8) -> dict:
    buckets = 1 << bits
    counts = [0] * buckets
    mask = buckets - 1
    for v in values:
        counts[v & mask] += 1
    expected = len(values) / buckets
    chi2 = sum(((c - expected) ** 2) / expected for c in counts) if expected else 0.0
    max_dev = max(abs(c - expected) for c in counts) if counts else 0.0
    return {
        "bucket_bits": bits,
        "bucket_count": buckets,
        "expected_per_bucket": expected,
        "chi_square": chi2,
        "max_abs_bucket_deviation": max_dev,
        "min_bucket_count": min(counts) if counts else 0,
        "max_bucket_count": max(counts) if counts else 0,
    }


def serial_correlation(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    xs = [v / (2**64 - 1) for v in values]
    mean = sum(xs) / len(xs)
    num = sum((xs[i] - mean) * (xs[i + 1] - mean) for i in range(len(xs) - 1))
    den = sum((x - mean) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def evaluate(values: list[int]) -> dict:
    mono = monobit_stats(values)
    buckets = bucket_stats(values, bits=8)
    corr = serial_correlation(values)

    # Simple thesis-friendly sanity gates, not a full test suite.
    pass_monobit = abs(mono["z_score"]) < 4.0
    pass_ratio = abs(mono["one_ratio"] - 0.5) < 0.01
    pass_corr = abs(corr) < 0.05
    overall = pass_monobit and pass_ratio and pass_corr

    return {
        "sample_count": len(values),
        "monobit": mono,
        "low8_bucket": buckets,
        "serial_correlation": corr,
        "sanity_gates": {
            "pass_monobit_z_lt_4": pass_monobit,
            "pass_one_ratio_within_1pct": pass_ratio,
            "pass_serial_corr_lt_0p05": pass_corr,
            "overall_pass": overall,
        },
        "notes": [
            "This is a basic statistical sanity check, not a substitute for a full randomness certification suite.",
            "Use this as the primitive-level verification artifact required by the thesis plan before PMO-GA integration."
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    values = read_values(args.dump)
    report = evaluate(values)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
