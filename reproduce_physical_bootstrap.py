#!/usr/bin/env python3
"""Recompute QFlow physical paired-row bootstrap confidence intervals."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
from pathlib import Path
import random
import statistics
import subprocess


DEFAULT_EVIDENCE_COMMIT = "290b4ad75eef2af2b9da2f1f281a2b89416cfd24"
DEFAULT_REPETITIONS = 10_000
DEFAULT_SEED = 20_260_731
H4_PATH = "results/nexys3/p6_step8_h4_physical/board_results.csv"
BASELINES = {
    "H4-H2": "results/nexys3/p6_step6_h2_physical/board_results.csv",
    "H4-H3": "results/nexys3/p6_step7_h3_physical/board_results.csv",
}


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"])


def read_rows(commit: str, path: str) -> tuple[dict[int, dict[str, str]], str]:
    payload = git_blob(commit, path)
    text = payload.decode("utf-8-sig")
    rows = {int(row["test_id"]): row for row in csv.DictReader(io.StringIO(text))}
    return rows, hashlib.sha256(payload).hexdigest()


def linear_quantile(sorted_values: list[float], probability: float) -> float:
    """R-7/NumPy-linear quantile: interpolate at p*(n-1)."""
    position = probability * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] + fraction * (
        sorted_values[upper] - sorted_values[lower]
    )


def bootstrap_interval(
    differences: list[int], repetitions: int, seed: int
) -> tuple[float, float]:
    rng = random.Random(seed)
    count = len(differences)
    means = sorted(
        sum(differences[rng.randrange(count)] for _ in range(count)) / count
        for _ in range(repetitions)
    )
    return linear_quantile(means, 0.025), linear_quantile(means, 0.975)


def exact_sign_p(higher: int, lower: int) -> float:
    trials = higher + lower
    tail = min(higher, lower)
    if trials == 0:
        return 1.0
    probability = 2.0 * sum(math.comb(trials, k) for k in range(tail + 1)) / (2**trials)
    return min(1.0, probability)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-commit", default=DEFAULT_EVIDENCE_COMMIT)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("data/physical_bootstrap_recomputed.csv"),
    )
    parser.add_argument(
        "--differences-output",
        type=Path,
        default=Path("data/physical_paired_differences.csv"),
    )
    args = parser.parse_args()
    if args.repetitions < 1:
        raise ValueError("Bootstrap repetitions must be positive.")

    h4_rows, h4_hash = read_rows(args.evidence_commit, H4_PATH)
    difference_rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for comparison, baseline_path in BASELINES.items():
        baseline_rows, baseline_hash = read_rows(args.evidence_commit, baseline_path)
        paired: list[int] = []
        path_changes = 0
        for test_id in range(1000, 1064):
            h4 = h4_rows[test_id]
            baseline = baseline_rows[test_id]
            if h4["status"] != "0" or baseline["status"] != "0":
                continue
            difference = int(h4["bottleneck_fidelity"]) - int(
                baseline["bottleneck_fidelity"]
            )
            changed = h4["selected_path"] != baseline["selected_path"]
            paired.append(difference)
            path_changes += int(changed)
            difference_rows.append(
                {
                    "comparison": comparison,
                    "test_id": test_id,
                    "baseline_quality_unorm16": baseline["bottleneck_fidelity"],
                    "h4_quality_unorm16": h4["bottleneck_fidelity"],
                    "difference_h4_minus_baseline": difference,
                    "baseline_selected_path": baseline["selected_path"],
                    "h4_selected_path": h4["selected_path"],
                    "path_changed": changed,
                }
            )

        if len(paired) != 58:
            raise AssertionError(f"{comparison}: expected 58 jointly successful rows, got {len(paired)}")
        mean_difference = statistics.fmean(paired)
        ci_low, ci_high = bootstrap_interval(paired, args.repetitions, args.seed)
        higher = sum(value > 0 for value in paired)
        lower = sum(value < 0 for value in paired)
        ties = sum(value == 0 for value in paired)
        effect_dz = mean_difference / statistics.stdev(paired)
        summaries.append(
            {
                "comparison": comparison,
                "evidence_commit": args.evidence_commit,
                "h4_source_path": H4_PATH,
                "h4_source_sha256": h4_hash,
                "baseline_source_path": baseline_path,
                "baseline_source_sha256": baseline_hash,
                "paired_rows": len(paired),
                "sampling_unit": "jointly_successful_heldout_replay_row",
                "bootstrap_repetitions": args.repetitions,
                "rng": "Python_random_Random_MT19937",
                "rng_seed": args.seed,
                "interval_method": "paired_nonparametric_percentile_R7_linear_quantiles",
                "mean_difference_unorm16": f"{mean_difference:.12f}",
                "ci_95_low_unorm16": f"{ci_low:.12f}",
                "ci_95_high_unorm16": f"{ci_high:.12f}",
                "higher": higher,
                "lower": lower,
                "ties": ties,
                "exact_two_sided_sign_p": f"{exact_sign_p(higher, lower):.12f}",
                "paired_effect_dz": f"{effect_dz:.12f}",
                "path_changes": path_changes,
            }
        )

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    with args.summary_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    with args.differences_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(difference_rows[0]))
        writer.writeheader()
        writer.writerows(difference_rows)

    for row in summaries:
        print(
            f"{row['comparison']}: mean={row['mean_difference_unorm16']}, "
            f"95% CI=[{row['ci_95_low_unorm16']}, {row['ci_95_high_unorm16']}], "
            f"sign p={row['exact_two_sided_sign_p']}, dz={row['paired_effect_dz']}"
        )


if __name__ == "__main__":
    main()
