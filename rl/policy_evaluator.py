"""Deterministic H2/H3 evaluation without access to the locked P3 test set."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from statistics import fmean
from typing import Dict, Iterable, List, Mapping, Sequence

from rl.baseline_controllers import CONTROLLERS, H2_ID, H3_ID, action_for
from rl.mdp_contract import CONTRACT as MDP_CONTRACT
from rl.p3_contract import CONFIG_PATH as TRAINING_CONFIG_PATH, CONTRACT as P3_CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.trace_generator import Ring6Trace, canonical_trace_bytes, generate_trace


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_COUNT = 4
ALLOWED_PARTITIONS = ("train", "validation")


@dataclass(frozen=True)
class TraceMetrics:
    controller: str
    partition: str
    seed: int
    trace_id: str
    trace_sha256: str
    decision_count: int
    success_count: int
    blocking_rate: float
    mean_total_reward: float
    mean_success_bottleneck_fidelity: float
    mean_balance_utility_success: float
    mean_hops_success: float
    switch_count: int
    switch_rate: float
    profile_0_count: int
    profile_1_count: int
    profile_2_count: int
    profile_3_count: int


def _mean(values: Sequence[float]) -> float:
    return fmean(values) if values else 0.0


def _reconstruct_fidelity(fidelity_utility: float) -> float:
    reward = MDP_CONTRACT["reward"]
    floor = float(reward["fidelity_floor"])
    weight = float(reward["terms"]["fidelity_weight"])
    return floor + (float(fidelity_utility) / weight) * (1.0 - floor)


def evaluate_trace(controller_id: str, partition: str, trace: Ring6Trace) -> TraceMetrics:
    if partition not in ALLOWED_PARTITIONS:
        raise ValueError("P3 baseline evaluation permits train/validation only; test is locked.")
    if controller_id not in CONTROLLERS:
        raise ValueError(f"Unknown controller {controller_id!r}.")

    environment = Ring6Environment(trace)
    actions: List[int] = []
    rewards: List[float] = []
    fidelities: List[float] = []
    balances: List[float] = []
    hops: List[float] = []
    success_count = 0
    profile_counts = [0] * PROFILE_COUNT

    while not environment.done:
        state_id = environment.current_state_id()
        action_id = action_for(controller_id, state_id)
        result = environment.step(action_id)
        actions.append(action_id)
        profile_counts[action_id] += 1
        rewards.append(result.reward.total)
        if result.success:
            success_count += 1
            fidelities.append(_reconstruct_fidelity(result.reward.fidelity_utility))
            balances.append(result.reward.balance_utility)
            hops.append(float(len(result.selected_path) - 1))

    decision_count = len(actions)
    switch_count = sum(first != second for first, second in zip(actions, actions[1:]))
    switch_denominator = max(decision_count - 1, 1)
    return TraceMetrics(
        controller=controller_id,
        partition=partition,
        seed=trace.seed,
        trace_id=trace.trace_id,
        trace_sha256=hashlib.sha256(canonical_trace_bytes(trace)).hexdigest(),
        decision_count=decision_count,
        success_count=success_count,
        blocking_rate=(decision_count - success_count) / decision_count,
        mean_total_reward=_mean(rewards),
        mean_success_bottleneck_fidelity=_mean(fidelities),
        mean_balance_utility_success=_mean(balances),
        mean_hops_success=_mean(hops),
        switch_count=switch_count,
        switch_rate=switch_count / switch_denominator,
        profile_0_count=profile_counts[0],
        profile_1_count=profile_counts[1],
        profile_2_count=profile_counts[2],
        profile_3_count=profile_counts[3],
    )


def _partition_seeds(partition: str) -> Sequence[int]:
    if partition not in ALLOWED_PARTITIONS:
        raise ValueError("Locked test partition cannot be requested.")
    return tuple(int(value) for value in P3_CONTRACT["partitions"][f"{partition}_seeds"])


def evaluate_baselines() -> Sequence[TraceMetrics]:
    length = int(P3_CONTRACT["partitions"]["episode_length"])
    rows: List[TraceMetrics] = []
    for partition in ALLOWED_PARTITIONS:
        for seed in _partition_seeds(partition):
            trace = generate_trace(seed, length)
            for controller_id in (H2_ID, H3_ID):
                rows.append(evaluate_trace(controller_id, partition, trace))
    return rows


def _summary(rows: Iterable[TraceMetrics]) -> Sequence[Mapping[str, object]]:
    rows = list(rows)
    summaries = []
    metric_names = (
        "blocking_rate",
        "mean_total_reward",
        "mean_success_bottleneck_fidelity",
        "mean_balance_utility_success",
        "mean_hops_success",
        "switch_rate",
    )
    for partition in ALLOWED_PARTITIONS:
        for controller_id in (H2_ID, H3_ID):
            selected = [row for row in rows if row.partition == partition and row.controller == controller_id]
            item: Dict[str, object] = {
                "controller": controller_id,
                "partition": partition,
                "seed_count": len(selected),
                "decision_count": sum(row.decision_count for row in selected),
                "success_count": sum(row.success_count for row in selected),
            }
            for name in metric_names:
                item[name] = _mean([float(getattr(row, name)) for row in selected])
            summaries.append(item)
    return summaries


def _write_per_seed(path: Path, rows: Sequence[TraceMetrics]) -> None:
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            payload = asdict(row)
            for key, value in payload.items():
                if isinstance(value, float):
                    payload[key] = f"{value:.12f}"
            writer.writerow(payload)


def _write_profile_usage(path: Path, rows: Sequence[TraceMetrics]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("controller", "partition", "profile_id", "decision_count", "fraction"))
        for partition in ALLOWED_PARTITIONS:
            for controller_id in (H2_ID, H3_ID):
                selected = [row for row in rows if row.partition == partition and row.controller == controller_id]
                total = sum(row.decision_count for row in selected)
                for profile_id in range(PROFILE_COUNT):
                    count = sum(getattr(row, f"profile_{profile_id}_count") for row in selected)
                    writer.writerow((controller_id, partition, profile_id, count, f"{count / total:.12f}"))


def write_baseline_evidence(output_dir: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(evaluate_baselines())
    per_seed_path = output_dir / "baseline_per_seed.csv"
    summary_path = output_dir / "baseline_summary.json"
    usage_path = output_dir / "profile_usage.csv"
    manifest_path = output_dir / "evaluation_manifest.json"
    _write_per_seed(per_seed_path, rows)
    summaries = list(_summary(rows))
    summary_path.write_text(json.dumps({"schema_version": 1, "summaries": summaries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_profile_usage(usage_path, rows)
    h3_validation = next(
        item for item in summaries
        if item["controller"] == H3_ID and item["partition"] == "validation"
    )
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "baseline_evaluation",
        "controllers": [H2_ID, H3_ID],
        "partitions_evaluated": list(ALLOWED_PARTITIONS),
        "environment_seed_count": len({(row.partition, row.seed) for row in rows}),
        "controller_trace_run_count": len(rows),
        "test_partition_locked": True,
        "test_access_count": 0,
        "h4_training_performed": False,
        "observations": {
            "h3_validation_switch_rate": h3_validation["switch_rate"],
            "h3_exceeds_h4_switch_ceiling": h3_validation["switch_rate"] > float(P3_CONTRACT["utility_gate"]["maximum_switch_rate"]),
            "response": "retain_the_predeclared_h3_baseline_without_post_result_tuning",
        },
        "training_config_sha256": hashlib.sha256(TRAINING_CONFIG_PATH.read_bytes()).hexdigest(),
        "input_trace_sha256": {
            f"{row.partition}:{row.seed}": row.trace_sha256
            for row in rows if row.controller == H2_ID
        },
        "data_sha256": {
            "baseline_per_seed.csv": hashlib.sha256(per_seed_path.read_bytes()).hexdigest(),
            "baseline_summary.json": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            "profile_usage.csv": hashlib.sha256(usage_path.read_bytes()).hexdigest(),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = (per_seed_path, summary_path, usage_path, manifest_path)
    checksum_lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return {"summaries": summaries, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3_baselines"))
    args = parser.parse_args()
    evidence = write_baseline_evidence(args.output_dir)
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
