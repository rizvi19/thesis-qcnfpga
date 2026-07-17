"""Run the frozen P3 full H4 candidate matrix and validation-only selection."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple

from rl.h4_evaluator import evaluate_candidate_validation, rows_to_dicts, select_validation_candidate, summarize_validation
from rl.h4_trainer import CandidateResult, FROZEN_TRAINER_SEEDS, FULL_SPEC, FULL_TRANSITIONS, train_candidate
from rl.p3_contract import CONFIG_PATH, CONTRACT


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_SUMMARY_PATH = REPO_ROOT / "results/rl/p3_baselines/baseline_summary.json"


def _train_worker(seed: int) -> CandidateResult:
    return train_candidate(seed, FULL_SPEC)


def run_full_training(max_workers: int) -> Tuple[CandidateResult, ...]:
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers <= 0:
        raise ValueError("max_workers must be a positive integer.")
    worker_count = min(max_workers, len(FROZEN_TRAINER_SEEDS))
    completed: Dict[int, CandidateResult] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(_train_worker, seed): seed for seed in FROZEN_TRAINER_SEEDS}
        for future in concurrent.futures.as_completed(futures):
            seed = futures[future]
            completed[seed] = future.result()
            print(f"TRAINING COMPLETE: trainer_seed={seed}", flush=True)
    return tuple(completed[seed] for seed in FROZEN_TRAINER_SEEDS)


def _write_learning_curves(path: Path, candidates: Sequence[CandidateResult]) -> None:
    fieldnames = list(asdict(candidates[0].epochs[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for candidate in candidates:
            for epoch in candidate.epochs:
                row = asdict(epoch)
                for key, value in row.items():
                    if isinstance(value, float):
                        row[key] = f"{value:.12f}"
                writer.writerow(row)


def _write_validation_rows(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for item in rows:
            row = dict(item)
            for key, value in row.items():
                if isinstance(value, float):
                    row[key] = f"{value:.12f}"
            writer.writerow(row)


def _write_profile_usage(path: Path, summaries: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("trainer_seed", "partition", "profile_id", "decision_count", "fraction"))
        for summary in summaries:
            for profile_id, (count, fraction) in enumerate(zip(summary["profile_counts"], summary["profile_fractions"])):
                writer.writerow((summary["trainer_seed"], "validation", profile_id, count, f"{fraction:.12f}"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_full_evidence(output_dir: Path, max_workers: int) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = output_dir / "candidates"
    checksum_dir = output_dir / "training_selection"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    checksum_dir.mkdir(parents=True, exist_ok=True)
    candidates = run_full_training(max_workers)
    learning_path = output_dir / "learning_curves.csv"
    validation_rows_path = output_dir / "validation_per_seed.csv"
    validation_summary_path = output_dir / "validation_summary.json"
    training_summary_path = output_dir / "training_summary.json"
    profile_usage_path = output_dir / "profile_usage.csv"
    selection_path = output_dir / "selection_record.json"
    manifest_path = output_dir / "training_manifest.json"
    _write_learning_curves(learning_path, candidates)

    training_summaries = []
    q_paths = []
    policy_paths = []
    for candidate in candidates:
        q_path = candidate_dir / f"q_table_seed_{candidate.trainer_seed}.json"
        policy_path = candidate_dir / f"policy_seed_{candidate.trainer_seed}.json"
        q_path.write_text(json.dumps(candidate.q_table, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        policy_path.write_text(json.dumps(candidate.policy, indent=2) + "\n", encoding="utf-8")
        q_paths.append(q_path)
        policy_paths.append(policy_path)
        training_summaries.append({
            "trainer_seed": candidate.trainer_seed,
            "epoch_count": candidate.spec.epochs,
            "transition_count": candidate.spec.transitions,
            "visited_state_count": candidate.visited_state_count,
            "training_profile_counts": list(candidate.final_profile_counts),
            "q_min": min(value for row in candidate.q_table for value in row),
            "q_max": max(value for row in candidate.q_table for value in row),
            "q_table_sha256": candidate.q_table_sha256,
            "policy_sha256": candidate.policy_sha256,
        })
    training_summary_path.write_text(
        json.dumps({"schema_version": 1, "candidates": training_summaries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    all_validation_rows = []
    validation_summaries = []
    for candidate in candidates:
        rows = evaluate_candidate_validation(candidate)
        all_validation_rows.extend(rows_to_dicts(rows))
        summary = dict(summarize_validation(rows))
        summary["q_table_sha256"] = candidate.q_table_sha256
        summary["policy_sha256"] = candidate.policy_sha256
        validation_summaries.append(summary)
    _write_validation_rows(validation_rows_path, all_validation_rows)
    _write_profile_usage(profile_usage_path, validation_summaries)
    validation_summary_path.write_text(
        json.dumps({"schema_version": 1, "candidates": validation_summaries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    baseline_payload = json.loads(BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    selection = select_validation_candidate(validation_summaries, baseline_payload["summaries"])
    selection_path.write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_6_FULL_TRAINING_SELECTION",
        "decision": selection["decision"],
        "candidate_count": len(candidates),
        "trainer_rng_seeds": list(FROZEN_TRAINER_SEEDS),
        "training_environment_seeds": list(FULL_SPEC.train_seeds),
        "epochs_per_candidate": FULL_SPEC.epochs,
        "transitions_per_candidate": FULL_TRANSITIONS,
        "total_training_transitions": FULL_TRANSITIONS * len(candidates),
        "eligible_checkpoint": "epoch_200_only",
        "full_h4_training_performed": True,
        "validation_model_selection_performed": True,
        "validation_trace_evaluations": len(all_validation_rows),
        "test_access_count": 0,
        "test_partition_locked": True,
        "policy_freeze_performed": False,
        "rom_export_performed": False,
        "rtl_or_board_work_performed": False,
        "selected_trainer_seed": selection["selected_trainer_seed"],
        "revision_required": selection["decision"] == "REVISION_REQUIRED",
        "training_config_sha256": _sha256(CONFIG_PATH),
        "baseline_summary_sha256": _sha256(BASELINE_SUMMARY_PATH),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    output_paths = (
        learning_path,
        validation_rows_path,
        validation_summary_path,
        training_summary_path,
        profile_usage_path,
        selection_path,
        manifest_path,
        *q_paths,
        *policy_paths,
    )
    checksum_entries = (
        ("rl/h4_evaluator.py", REPO_ROOT / "rl/h4_evaluator.py"),
        ("rl/full_training_selection.py", REPO_ROOT / "rl/full_training_selection.py"),
        ("sim/rl/test_p3_full_selection.py", REPO_ROOT / "sim/rl/test_p3_full_selection.py"),
        ("docs/rl/p3_full_training_selection.md", REPO_ROOT / "docs/rl/p3_full_training_selection.md"),
        ("docs/rl/p3_step6_status.md", REPO_ROOT / "docs/rl/p3_step6_status.md"),
        *((str(path.relative_to(REPO_ROOT)), path) for path in output_paths),
    )
    lines = [f"{_sha256(path)}  {label}" for label, path in checksum_entries]
    (checksum_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"manifest": manifest, "selection": selection, "validation_summaries": validation_summaries}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3"))
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("QFLOW_MAX_WORKERS", min(8, os.cpu_count() or 1))),
    )
    args = parser.parse_args()
    print(json.dumps(write_full_evidence(args.output_dir, args.workers), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
