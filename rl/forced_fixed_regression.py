"""Forced-Balanced P2 regression bridge to the frozen canonical H2 result."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple

import reference_model

from rl.h2_profile_adapter import run_h2_action, select_h2_route
from rl.mdp_contract import CONTRACT
from rl.profile_codebook import BALANCED_ACTION_ID, profile_by_action
from rl.ring6_environment import Ring6Environment, StepResult
from rl.trace_generator import Ring6Trace, build_manual_trace, canonical_trace_bytes, generate_trace


FROZEN_H2_SHA256 = "e4a393bc349f064ab7709e75fe6093210cf05f6f842fee33d4cc5b0adbcdaf3f"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def forced_balanced_replay(trace: Ring6Trace) -> Tuple[StepResult, ...]:
    """Replay a complete trace with the action interface clamped to Balanced."""
    environment = Ring6Environment(trace)
    records = []
    while not environment.done:
        result = environment.step(BALANCED_ACTION_ID)
        if result.action_id != BALANCED_ACTION_ID or result.profile_key != "balanced":
            raise RuntimeError("Forced-fixed replay escaped the Balanced action clamp.")
        records.append(result)
    return tuple(records)


def canonical_step_bytes(records: Sequence[StepResult]) -> bytes:
    payload = []
    for record in records:
        item = asdict(record)
        item["selected_path"] = record.selected_path
        item["reward_total"] = record.reward.total
        payload.append(item)
    return canonical_json_bytes(payload)


def h2_regression_summary() -> Mapping[str, object]:
    legacy = reference_model.run_ring6_experiment(verbose=False)
    forced = run_h2_action(BALANCED_ACTION_ID, verbose=False)
    legacy_bytes = canonical_json_bytes(legacy)
    forced_bytes = canonical_json_bytes(forced)
    legacy_hash = hashlib.sha256(legacy_bytes).hexdigest()
    forced_hash = hashlib.sha256(forced_bytes).hexdigest()
    balanced = profile_by_action(BALANCED_ACTION_ID)
    selected = select_h2_route(forced, balanced).selected.objectives.path
    legacy_first = tuple(legacy["pareto_front"][0]["path"])
    summary = {
        "schema_version": 1,
        "regression_boundary": "canonical_h2_computation_and_balanced_action_clamp",
        "legacy_h2_sha256": legacy_hash,
        "forced_balanced_h2_sha256": forced_hash,
        "canonical_json_byte_identical": legacy_bytes == forced_bytes,
        "expected_h2_sha256": FROZEN_H2_SHA256,
        "legacy_first_route": list(legacy_first),
        "balanced_selected_route": list(selected),
        "route_selection_parity": selected == legacy_first,
        "dynamic_trace_equivalence_claimed": False,
    }
    if legacy_hash != FROZEN_H2_SHA256 or forced_hash != FROZEN_H2_SHA256:
        raise RuntimeError("Forced-Balanced H2 hash does not match the frozen anchor.")
    if not summary["canonical_json_byte_identical"] or not summary["route_selection_parity"]:
        raise RuntimeError("Forced-Balanced H2 regression failed.")
    return summary


def _partition_traces() -> Tuple[Tuple[str, int, Ring6Trace], ...]:
    records = []
    for partition, key in (
        ("train", "train_seeds"),
        ("validation", "validation_seeds"),
        ("test", "test_seeds"),
    ):
        for seed in CONTRACT["partitions"][key]:
            value = int(seed)
            records.append(
                (
                    partition,
                    value,
                    generate_trace(value, int(CONTRACT["partitions"]["episode_length"])),
                )
            )
    return tuple(records)


def _write_manual_csv(output_dir: Path) -> Mapping[str, object]:
    trace = build_manual_trace()
    replay = forced_balanced_replay(trace)
    path = output_dir / "forced_balanced_manual.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ("trace_index", "state_id", "action_id", "profile", "success", "selected_path", "reward", "next_state_id", "done")
        )
        for item in replay:
            writer.writerow(
                (
                    item.trace_index,
                    item.state_id,
                    item.action_id,
                    item.profile_key,
                    item.success,
                    "" if item.selected_path is None else "-".join(map(str, item.selected_path)),
                    f"{item.reward.total:.12f}",
                    "" if item.next_state_id is None else item.next_state_id,
                    item.done,
                )
            )
    return {
        "trace_sha256": hashlib.sha256(canonical_trace_bytes(trace)).hexdigest(),
        "step_log_sha256": hashlib.sha256(canonical_step_bytes(replay)).hexdigest(),
        "step_count": len(replay),
        "success_count": sum(item.success for item in replay),
        "all_actions_balanced": all(item.action_id == BALANCED_ACTION_ID for item in replay),
        "final_done": replay[-1].done,
    }


def _write_partition_csv(output_dir: Path) -> Mapping[str, object]:
    path = output_dir / "forced_balanced_trace_summary.csv"
    total_steps = 0
    total_successes = 0
    trace_count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ("partition", "seed", "trace_sha256", "step_log_sha256", "steps", "successes", "blocked", "cumulative_reward", "unique_states", "final_done")
        )
        for partition, seed, trace in _partition_traces():
            replay = forced_balanced_replay(trace)
            successes = sum(item.success for item in replay)
            steps = len(replay)
            writer.writerow(
                (
                    partition,
                    seed,
                    hashlib.sha256(canonical_trace_bytes(trace)).hexdigest(),
                    hashlib.sha256(canonical_step_bytes(replay)).hexdigest(),
                    steps,
                    successes,
                    steps - successes,
                    f"{sum(item.reward.total for item in replay):.12f}",
                    len({item.state_id for item in replay}),
                    replay[-1].done,
                )
            )
            trace_count += 1
            total_steps += steps
            total_successes += successes
    return {
        "trace_count": trace_count,
        "step_count": total_steps,
        "success_count": total_successes,
        "blocked_count": total_steps - total_successes,
        "all_steps_balanced": True,
    }


def write_forced_fixed_evidence(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    h2_path = output_dir / "h2_regression.json"
    h2_path.write_text(json.dumps(h2_regression_summary(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    replay_summary = {
        "schema_version": 1,
        "action_clamp": {"action_id": BALANCED_ACTION_ID, "profile": "balanced"},
        "manual": _write_manual_csv(output_dir),
        "partitions": _write_partition_csv(output_dir),
        "training_performed": False,
    }
    replay_path = output_dir / "replay_summary.json"
    replay_path.write_text(json.dumps(replay_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = (
        h2_path,
        output_dir / "forced_balanced_manual.csv",
        output_dir / "forced_balanced_trace_summary.csv",
        replay_path,
    )
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_forced_fixed"))
    args = parser.parse_args()
    write_forced_fixed_evidence(args.output_dir)
    print((args.output_dir / "h2_regression.json").read_text(encoding="utf-8"), end="")
    print((args.output_dir / "replay_summary.json").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
