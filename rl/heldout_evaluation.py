"""Freeze the revised H4 controller, then evaluate the untouched P3 test set."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from statistics import fmean
from typing import Dict, List, Mapping, Sequence, Tuple

from rl.baseline_controllers import H2_ID, H3_ID, action_for
from rl.dwell_controller import MinimumDwellController, validate_policy
from rl.mdp_contract import CONTRACT as MDP_CONTRACT
from rl.p3_contract import CONTRACT as V0_CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.trace_generator import Ring6Trace, canonical_trace_bytes, generate_trace


REPO_ROOT = Path(__file__).resolve().parents[1]
SELECTED_SEED = 229
MINIMUM_DWELL = 3
BALANCE_TRAINING_WEIGHT = 4.0
TEST_SEEDS = tuple(int(value) for value in V0_CONTRACT["partitions"]["test_seeds"])
EPISODE_LENGTH = int(V0_CONTRACT["partitions"]["episode_length"])
CONTROLLERS = (H2_ID, H3_ID, "h4_revised_seed_229")
SOURCE_Q = REPO_ROOT / "results/rl/p3_revision/candidates/q_table_seed_229.json"
SOURCE_POLICY = REPO_ROOT / "results/rl/p3_revision/candidates/policy_seed_229.json"
SOURCE_CONFIG = REPO_ROOT / "rl/config/training_config_v1.yaml"
SOURCE_SELECTION = REPO_ROOT / "results/rl/p3_revision/selection_record.json"
SOURCE_MANIFEST = REPO_ROOT / "results/rl/p3_revision/revision_manifest.json"
EXPECTED_Q_FILE_SHA256 = "a95a0431b565f01dc012211a22bf57eddb87ed21d4e8dd34671c55ace16b411a"
EXPECTED_POLICY_FILE_SHA256 = "cb1557680472781c01cab7ce961fdc35d672a0c76fbc0993e3c2599274f8d611"
EXPECTED_Q_SEMANTIC_SHA256 = "c515a2fef2ec0b658d26600e2939db15dc1dcac984af9ef33f9dde1518026b87"
EXPECTED_POLICY_SEMANTIC_SHA256 = "a133e3c7edfd7f592d56b18e46157f70215dd238cd4c23ece2ca018dfca5a5b4"
EXPECTED_CONFIG_SHA256 = "c75b68b25e42f348aa2156ba17479676618d738776e7ebf3e3b1feca7f46da0f"
EXPECTED_SELECTION_SHA256 = "18c2406ffd3fb0d0b3e23a347e41826d95b5bb8e44ff5f1a7d37633aeda10250"
EXPECTED_REVISION_MANIFEST_SHA256 = "cde2ffb62da0fed510811d8e50862a96d76d206afe546ba4c57bc1556b4d8ccb"


@dataclass(frozen=True)
class HeldoutRow:
    controller: str
    partition: str
    environment_seed: int
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _mean(values: Sequence[float]) -> float:
    return fmean(values) if values else 0.0


def _reconstruct_fidelity(fidelity_utility: float) -> float:
    floor = float(MDP_CONTRACT["reward"]["fidelity_floor"])
    weight = float(MDP_CONTRACT["reward"]["terms"]["fidelity_weight"])
    return floor + (float(fidelity_utility) / weight) * (1.0 - floor)


def validate_selected_inputs() -> Tuple[Tuple[Tuple[float, ...], ...], Tuple[int, ...]]:
    expected_files = {
        SOURCE_Q: EXPECTED_Q_FILE_SHA256,
        SOURCE_POLICY: EXPECTED_POLICY_FILE_SHA256,
        SOURCE_CONFIG: EXPECTED_CONFIG_SHA256,
        SOURCE_SELECTION: EXPECTED_SELECTION_SHA256,
        SOURCE_MANIFEST: EXPECTED_REVISION_MANIFEST_SHA256,
    }
    for path, expected in expected_files.items():
        if _sha256(path) != expected:
            raise RuntimeError(f"Frozen Step 6R input changed: {path.relative_to(REPO_ROOT)}")
    selection = json.loads(SOURCE_SELECTION.read_text(encoding="utf-8"))
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    if selection["selected_trainer_seed"] != SELECTED_SEED or manifest["selected_trainer_seed"] != SELECTED_SEED:
        raise RuntimeError("Step 6R no longer selects trainer seed 229.")
    if selection["validation_revision_gate"]["decision"] != "PASS":
        raise RuntimeError("Step 6R validation gate is not green.")
    if selection["additional_revision_allowed"] or manifest["additional_revision_allowed"]:
        raise RuntimeError("Step 6R revision lock is not final.")
    if selection["test_access_count"] != 0 or not selection["test_partition_locked"]:
        raise RuntimeError("Step 6R did not preserve the pre-freeze test lock.")
    if manifest["policy_freeze_performed"]:
        raise RuntimeError("Step 6R unexpectedly claims a prior policy freeze.")
    q_table = tuple(tuple(float(value) for value in row) for row in json.loads(SOURCE_Q.read_text(encoding="utf-8")))
    policy = validate_policy(json.loads(SOURCE_POLICY.read_text(encoding="utf-8")))
    if len(q_table) != 256 or any(len(row) != 4 for row in q_table):
        raise RuntimeError("Selected revised Q-table has the wrong shape.")
    if _canonical_sha256(q_table) != EXPECTED_Q_SEMANTIC_SHA256:
        raise RuntimeError("Selected revised Q-table semantic hash changed.")
    if _canonical_sha256(policy) != EXPECTED_POLICY_SEMANTIC_SHA256:
        raise RuntimeError("Selected revised policy semantic hash changed.")
    return q_table, policy


def write_policy_freeze(output_dir: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    q_table, policy = validate_selected_inputs()
    frozen_q = output_dir / "selected_q_table_seed_229.json"
    frozen_policy = output_dir / "selected_policy_seed_229.json"
    frozen_config = output_dir / "training_config_v1.yaml"
    frozen_q.write_bytes(SOURCE_Q.read_bytes())
    frozen_policy.write_bytes(SOURCE_POLICY.read_bytes())
    frozen_config.write_bytes(SOURCE_CONFIG.read_bytes())
    freeze_record = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_7_POLICY_FREEZE",
        "sequence": 1,
        "selected_trainer_seed": SELECTED_SEED,
        "balance_training_weight": BALANCE_TRAINING_WEIGHT,
        "minimum_dwell_decisions": MINIMUM_DWELL,
        "q_table_file_sha256": _sha256(frozen_q),
        "policy_file_sha256": _sha256(frozen_policy),
        "training_config_sha256": _sha256(frozen_config),
        "q_table_semantic_sha256": _canonical_sha256(q_table),
        "policy_semantic_sha256": _canonical_sha256(policy),
        "selection_record_sha256": _sha256(SOURCE_SELECTION),
        "revision_manifest_sha256": _sha256(SOURCE_MANIFEST),
        "policy_frozen": True,
        "controller_frozen": True,
        "additional_revision_allowed": False,
        "test_access_count_before_freeze": 0,
        "test_evaluation_performed": False,
    }
    freeze_path = output_dir / "freeze_record.json"
    freeze_path.write_text(json.dumps(freeze_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unlock = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_7_TEST_UNLOCK",
        "sequence": 2,
        "freeze_record_sha256": _sha256(freeze_path),
        "authorized_test_seeds": list(TEST_SEEDS),
        "authorized_controllers": list(CONTROLLERS),
        "unique_test_trace_limit": len(TEST_SEEDS),
        "controller_trace_evaluation_limit": len(TEST_SEEDS) * len(CONTROLLERS),
        "test_access_count_at_unlock": 0,
        "unlock_conditions": {
            "all_training_runs_complete": True,
            "candidate_selected_using_validation_only": True,
            "training_config_checksum_frozen": True,
            "selected_q_table_checksum_frozen": True,
            "selected_policy_checksum_frozen": True,
            "selection_record_written_before_test": True,
            "no_additional_revision_allowed": True,
        },
        "test_partition_unlocked": True,
        "post_unlock_revision_allowed": False,
    }
    unlock_path = output_dir / "test_unlock.json"
    unlock_path.write_text(json.dumps(unlock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths = (frozen_q, frozen_policy, frozen_config, freeze_path, unlock_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256(path)}  {path.name}" for path in paths) + "\n",
        encoding="utf-8",
    )
    return {"freeze": freeze_record, "unlock": unlock}


def verify_test_unlock(freeze_dir: Path) -> Tuple[int, ...]:
    if not freeze_dir.is_absolute():
        freeze_dir = REPO_ROOT / freeze_dir
    q_table, policy = validate_selected_inputs()
    del q_table
    sums = freeze_dir / "SHA256SUMS"
    if not sums.is_file():
        raise RuntimeError("Policy-freeze checksum manifest is missing.")
    for line in sums.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(None, 1)
        path = freeze_dir / relative.strip()
        if _sha256(path) != expected:
            raise RuntimeError(f"Policy-freeze checksum mismatch: {relative.strip()}")
    freeze = json.loads((freeze_dir / "freeze_record.json").read_text(encoding="utf-8"))
    unlock = json.loads((freeze_dir / "test_unlock.json").read_text(encoding="utf-8"))
    if freeze["sequence"] != 1 or unlock["sequence"] != 2:
        raise RuntimeError("Freeze/unlock ordering is invalid.")
    if unlock["freeze_record_sha256"] != _sha256(freeze_dir / "freeze_record.json"):
        raise RuntimeError("Test unlock does not bind the freeze record.")
    if not freeze["policy_frozen"] or not freeze["controller_frozen"]:
        raise RuntimeError("Policy/controller freeze is incomplete.")
    if unlock["post_unlock_revision_allowed"] or not unlock["test_partition_unlocked"]:
        raise RuntimeError("Test unlock is invalid.")
    if not all(unlock["unlock_conditions"].values()):
        raise RuntimeError("One or more test-unlock conditions failed.")
    if tuple(unlock["authorized_test_seeds"]) != TEST_SEEDS:
        raise RuntimeError("Test unlock seed set changed.")
    frozen_policy = validate_policy(json.loads((freeze_dir / "selected_policy_seed_229.json").read_text(encoding="utf-8")))
    if frozen_policy != policy:
        raise RuntimeError("Frozen policy bytes do not match the selected policy.")
    return frozen_policy


def _evaluate_trace(
    controller_id: str,
    trace: Ring6Trace,
    policy: Sequence[int],
) -> Tuple[HeldoutRow, Sequence[Mapping[str, object]]]:
    if trace.seed not in TEST_SEEDS:
        raise ValueError("Step 7 held-out evaluation accepts frozen test seeds only.")
    environment = Ring6Environment(trace)
    dwell = MinimumDwellController(policy, MINIMUM_DWELL) if controller_id == "h4_revised_seed_229" else None
    actions: List[int] = []
    rewards: List[float] = []
    fidelities: List[float] = []
    balances: List[float] = []
    hops: List[float] = []
    profiles = [0, 0, 0, 0]
    success_count = 0
    timeline = []
    while not environment.done:
        state_id = environment.current_state_id()
        if controller_id in (H2_ID, H3_ID):
            proposed = action_for(controller_id, state_id)
            action_id = proposed
        else:
            proposed = policy[state_id]
            action_id = dwell.choose_action(state_id)
        result = environment.step(action_id)
        actions.append(action_id)
        profiles[action_id] += 1
        rewards.append(float(result.reward.total))
        if result.success:
            success_count += 1
            fidelities.append(_reconstruct_fidelity(result.reward.fidelity_utility))
            balances.append(float(result.reward.balance_utility))
            hops.append(float(len(result.selected_path) - 1))
        if controller_id == "h4_revised_seed_229":
            timeline.append({
                "environment_seed": trace.seed,
                "trace_index": result.trace_index,
                "state_id": state_id,
                "proposed_action_id": proposed,
                "deployed_action_id": action_id,
                "success": result.success,
                "reward": float(result.reward.total),
            })
    decisions = len(actions)
    switches = sum(first != second for first, second in zip(actions, actions[1:]))
    row = HeldoutRow(
        controller=controller_id,
        partition="test",
        environment_seed=trace.seed,
        trace_sha256=hashlib.sha256(canonical_trace_bytes(trace)).hexdigest(),
        decision_count=decisions,
        success_count=success_count,
        blocking_rate=(decisions - success_count) / decisions,
        mean_total_reward=_mean(rewards),
        mean_success_bottleneck_fidelity=_mean(fidelities),
        mean_balance_utility_success=_mean(balances),
        mean_hops_success=_mean(hops),
        switch_count=switches,
        switch_rate=switches / max(decisions - 1, 1),
        profile_0_count=profiles[0],
        profile_1_count=profiles[1],
        profile_2_count=profiles[2],
        profile_3_count=profiles[3],
    )
    return row, timeline


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        for item in rows:
            payload = dict(item)
            for key, value in payload.items():
                if isinstance(value, float):
                    payload[key] = f"{value:.12f}"
            writer.writerow(payload)


def _summaries(rows: Sequence[HeldoutRow]) -> Sequence[Mapping[str, object]]:
    summaries = []
    for controller in CONTROLLERS:
        selected = [row for row in rows if row.controller == controller]
        profiles = [sum(getattr(row, f"profile_{action}_count") for row in selected) for action in range(4)]
        decisions = sum(row.decision_count for row in selected)
        switches = sum(row.switch_count for row in selected)
        fractions = [count / decisions for count in profiles]
        summaries.append({
            "controller": controller,
            "partition": "test",
            "environment_seed_count": len(selected),
            "decision_count": decisions,
            "success_count": sum(row.success_count for row in selected),
            "blocking_rate": _mean([row.blocking_rate for row in selected]),
            "mean_total_reward": _mean([row.mean_total_reward for row in selected]),
            "mean_success_bottleneck_fidelity": _mean([row.mean_success_bottleneck_fidelity for row in selected]),
            "mean_balance_utility_success": _mean([row.mean_balance_utility_success for row in selected]),
            "mean_hops_success": _mean([row.mean_hops_success for row in selected]),
            "switch_count": switches,
            "switch_rate": switches / sum(max(row.decision_count - 1, 1) for row in selected),
            "profile_counts": profiles,
            "profile_fractions": fractions,
            "distinct_profiles": sum(count > 0 for count in profiles),
            "secondary_profile_fraction": sorted(fractions, reverse=True)[1],
        })
    return summaries


def run_heldout_once(freeze_dir: Path, output_dir: Path) -> Mapping[str, object]:
    if not freeze_dir.is_absolute():
        freeze_dir = REPO_ROOT / freeze_dir
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    policy = verify_test_unlock(freeze_dir)

    # This is the first and only test-trace generation point. The verified
    # freeze and unlock above must complete before these four calls occur.
    traces = {seed: generate_trace(seed, EPISODE_LENGTH) for seed in TEST_SEEDS}
    rows: List[HeldoutRow] = []
    timeline: List[Mapping[str, object]] = []
    for seed in TEST_SEEDS:
        for controller in CONTROLLERS:
            row, controller_timeline = _evaluate_trace(controller, traces[seed], policy)
            rows.append(row)
            timeline.extend(controller_timeline)
    if len(traces) != 4 or len(rows) != 12 or len(timeline) != 2048:
        raise RuntimeError("Held-out access count differs from the frozen Step 7 protocol.")

    results_path = output_dir / "heldout_results.csv"
    summary_path = output_dir / "heldout_summary.json"
    usage_path = output_dir / "profile_usage.csv"
    timeline_path = output_dir / "h4_action_timeline.csv"
    trace_path = output_dir / "test_trace_manifest.json"
    manifest_path = output_dir / "heldout_manifest.json"
    _write_csv(results_path, [asdict(row) for row in rows])
    summaries = _summaries(rows)
    summary_path.write_text(json.dumps({"schema_version": 1, "summaries": summaries}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    usage_rows = []
    for item in summaries:
        for profile_id, (count, fraction) in enumerate(zip(item["profile_counts"], item["profile_fractions"])):
            usage_rows.append({"controller": item["controller"], "partition": "test", "profile_id": profile_id, "decision_count": count, "fraction": fraction})
    _write_csv(usage_path, usage_rows)
    _write_csv(timeline_path, timeline)
    trace_manifest = {
        "schema_version": 1,
        "partition": "test",
        "generated_after_verified_unlock": True,
        "unique_trace_count": len(traces),
        "episode_length": EPISODE_LENGTH,
        "traces": [
            {"seed": seed, "trace_sha256": hashlib.sha256(canonical_trace_bytes(traces[seed])).hexdigest()}
            for seed in TEST_SEEDS
        ],
    }
    trace_path.write_text(json.dumps(trace_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_7_FROZEN_HELDOUT_EVALUATION",
        "decision": "COMPLETE_PENDING_STEP_8_STATISTICS",
        "selected_trainer_seed": SELECTED_SEED,
        "minimum_dwell_decisions": MINIMUM_DWELL,
        "policy_semantic_sha256": EXPECTED_POLICY_SEMANTIC_SHA256,
        "q_table_semantic_sha256": EXPECTED_Q_SEMANTIC_SHA256,
        "freeze_record_sha256": _sha256(freeze_dir / "freeze_record.json"),
        "test_unlock_sha256": _sha256(freeze_dir / "test_unlock.json"),
        "test_access_definition": "unique frozen test traces generated after verified policy freeze",
        "test_access_count": len(traces),
        "unique_test_trace_count": len(traces),
        "controller_trace_evaluations": len(rows),
        "h4_timeline_rows": len(timeline),
        "test_partition_unlocked": True,
        "policy_revision_after_test": False,
        "additional_training_after_test": False,
        "statistics_performed": False,
        "utility_gate_decided": False,
        "rom_export_performed": False,
        "rtl_or_board_work_performed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_paths = (
        REPO_ROOT / "rl/heldout_evaluation.py",
        REPO_ROOT / "sim/rl/test_p3_policy_freeze.py",
        REPO_ROOT / "docs/rl/p3_policy_freeze_and_heldout.md",
        REPO_ROOT / "docs/rl/p3_step7_status.md",
    )
    evidence_paths = (results_path, summary_path, usage_path, timeline_path, trace_path, manifest_path)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256(path)}  {path.relative_to(REPO_ROOT)}" for path in (*source_paths, *evidence_paths)) + "\n",
        encoding="utf-8",
    )
    return {"manifest": manifest, "summaries": summaries}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-dir", type=Path, default=Path("results/rl/p3_policy_freeze"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3_heldout"))
    args = parser.parse_args()
    freeze = write_policy_freeze(args.freeze_dir)
    heldout = run_heldout_once(args.freeze_dir, args.output_dir)
    print(json.dumps({"freeze": freeze, "heldout": heldout}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
