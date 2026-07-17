"""Deterministic train-only P3 Step 5 smoke evidence writer."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from rl.h4_trainer import FULL_TRANSITIONS, SMOKE_SPEC, CandidateResult, train_candidate
from rl.p3_contract import CONFIG_PATH


REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE_TRAINER_SEEDS = (17, 29)


def run_smoke() -> Sequence[CandidateResult]:
    return tuple(train_candidate(seed, SMOKE_SPEC) for seed in SMOKE_TRAINER_SEEDS)


def _write_learning_curves(path: Path, results: Sequence[CandidateResult]) -> None:
    fieldnames = list(asdict(results[0].epochs[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for result in results:
            for epoch in result.epochs:
                row = asdict(epoch)
                for key, value in row.items():
                    if isinstance(value, float):
                        row[key] = f"{value:.12f}"
                writer.writerow(row)


def _candidate_summary(result: CandidateResult) -> Mapping[str, object]:
    return {
        "trainer_seed": result.trainer_seed,
        "epochs": result.spec.epochs,
        "episode_count": result.spec.epochs * len(result.spec.train_seeds),
        "transition_count": result.spec.transitions,
        "visited_state_count": result.visited_state_count,
        "profile_counts": list(result.final_profile_counts),
        "distinct_profiles": sum(count > 0 for count in result.final_profile_counts),
        "q_min": min(value for row in result.q_table for value in row),
        "q_max": max(value for row in result.q_table for value in row),
        "q_table_sha256": result.q_table_sha256,
        "policy_sha256": result.policy_sha256,
        "policy_length": len(result.policy),
    }


def write_smoke_evidence(output_dir: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results = run_smoke()
    curve_path = output_dir / "learning_curves.csv"
    summary_path = output_dir / "smoke_summary.json"
    manifest_path = output_dir / "smoke_manifest.json"
    _write_learning_curves(curve_path, results)
    summaries = [_candidate_summary(result) for result in results]
    summary_path.write_text(
        json.dumps({"schema_version": 1, "candidates": summaries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    trace_hashes = {str(seed): digest for seed, digest in results[0].trace_sha256.items()}
    if any({str(seed): digest for seed, digest in result.trace_sha256.items()} != trace_hashes for result in results[1:]):
        raise RuntimeError("Smoke candidates did not use identical frozen training traces.")
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_5_TRAINING_SMOKE",
        "decision": "PASS",
        "algorithm": "tabular_q_learning",
        "partitions_accessed": ["train"],
        "training_environment_seeds": list(SMOKE_SPEC.train_seeds),
        "trainer_rng_seeds": list(SMOKE_TRAINER_SEEDS),
        "epochs_per_candidate": SMOKE_SPEC.epochs,
        "transitions_per_candidate": SMOKE_SPEC.transitions,
        "full_transitions_per_candidate": FULL_TRANSITIONS,
        "smoke_fraction_of_full_budget": SMOKE_SPEC.transitions / FULL_TRANSITIONS,
        "full_h4_training_performed": False,
        "validation_access_count": 0,
        "test_access_count": 0,
        "test_partition_locked": True,
        "model_selection_performed": False,
        "policy_freeze_performed": False,
        "rom_export_performed": False,
        "rtl_or_board_work_performed": False,
        "training_config_sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
        "trace_sha256": trace_hashes,
        "candidate_q_table_sha256": {
            str(result.trainer_seed): result.q_table_sha256 for result in results
        },
        "candidate_policy_sha256": {
            str(result.trainer_seed): result.policy_sha256 for result in results
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    data_paths = (curve_path, summary_path, manifest_path)
    checksum_entries = (
        ("rl/h4_trainer.py", REPO_ROOT / "rl/h4_trainer.py"),
        ("rl/training_smoke.py", REPO_ROOT / "rl/training_smoke.py"),
        ("sim/rl/test_p3_training_smoke.py", REPO_ROOT / "sim/rl/test_p3_training_smoke.py"),
        ("docs/rl/p3_training_smoke.md", REPO_ROOT / "docs/rl/p3_training_smoke.md"),
        ("docs/rl/p3_step5_status.md", REPO_ROOT / "docs/rl/p3_step5_status.md"),
        *((f"results/rl/p3_training_smoke/{path.name}", path) for path in data_paths),
    )
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {label}" for label, path in checksum_entries]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"manifest": manifest, "candidates": summaries}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3_training_smoke"))
    args = parser.parse_args()
    print(json.dumps(write_smoke_evidence(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
