"""Run the one controlled P3 reward/controller revision without test access."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import fmean
from typing import Dict, List, Mapping, Sequence, Tuple

from rl.dwell_controller import MinimumDwellController
from rl.h4_evaluator import select_validation_candidate
from rl.mdp_contract import CONTRACT as MDP_CONTRACT, RewardInput, calculate_reward
from rl.p3_contract import CONTRACT as V0_CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.tabular_q_learning import TabularQLearner, epsilon_at, extract_policy
from rl.trace_generator import Ring6Trace, generate_trace


REPO_ROOT = Path(__file__).resolve().parents[1]
V0_CONFIG_PATH = REPO_ROOT / "rl/config/training_config.yaml"
V1_CONFIG_PATH = REPO_ROOT / "rl/config/training_config_v1.yaml"
V0_SELECTION_PATH = REPO_ROOT / "results/rl/p3/selection_record.json"
BASELINE_SUMMARY_PATH = REPO_ROOT / "results/rl/p3_baselines/baseline_summary.json"
TRAINER_SEEDS = tuple(int(value) for value in V0_CONTRACT["training"]["trainer_seeds"])
TRAIN_SEEDS = tuple(int(value) for value in V0_CONTRACT["partitions"]["train_seeds"])
VALIDATION_SEEDS = tuple(int(value) for value in V0_CONTRACT["partitions"]["validation_seeds"])
TEST_SEEDS = tuple(int(value) for value in V0_CONTRACT["partitions"]["test_seeds"])
EPISODE_LENGTH = int(V0_CONTRACT["partitions"]["episode_length"])
EPOCHS = int(V0_CONTRACT["training"]["epochs"])
TRANSITIONS_PER_CANDIDATE = EPOCHS * len(TRAIN_SEEDS) * EPISODE_LENGTH
BALANCE_WEIGHT = 4.0
MINIMUM_DWELL = 3
EXPECTED_V0_CONFIG_SHA256 = "467a970fe91e4b31388b99642db68442432738b217dc0cae0fcc42b85aeaa7a4"
EXPECTED_V0_SELECTION_SHA256 = "782baeb0196f2af154fe89bd0364290ed22e4f0ff6deb730b8c02c4ea6760761"


@dataclass(frozen=True)
class RevisedEpoch:
    trainer_seed: int
    epoch: int
    transition_count: int
    cumulative_transitions: int
    mean_original_reward: float
    mean_training_reward: float
    profile_0_count: int
    profile_1_count: int
    profile_2_count: int
    profile_3_count: int
    distinct_state_count: int
    q_min: float
    q_max: float
    q_table_sha256: str


@dataclass(frozen=True)
class RevisedCandidate:
    trainer_seed: int
    epochs: Tuple[RevisedEpoch, ...]
    q_table: Tuple[Tuple[float, ...], ...]
    policy: Tuple[int, ...]
    q_table_sha256: str
    policy_sha256: str
    training_profile_counts: Tuple[int, int, int, int]
    visited_state_count: int


@dataclass(frozen=True)
class ValidationRow:
    trainer_seed: int
    partition: str
    environment_seed: int
    minimum_dwell_decisions: int
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


def load_revision_config() -> Mapping[str, object]:
    if _sha256(V0_CONFIG_PATH) != EXPECTED_V0_CONFIG_SHA256:
        raise RuntimeError("Frozen v0 training config changed.")
    if _sha256(V0_SELECTION_PATH) != EXPECTED_V0_SELECTION_SHA256:
        raise RuntimeError("Reviewed v0 selection record changed.")
    config = json.loads(V1_CONFIG_PATH.read_text(encoding="utf-8"))
    revision = config["controlled_revision"]
    if float(revision["training_reward"]["balance_weight"]) != BALANCE_WEIGHT:
        raise RuntimeError("Reviewed v1 balance weight changed.")
    if int(revision["controller_guard"]["minimum_dwell_decisions"]) != MINIMUM_DWELL:
        raise RuntimeError("Reviewed v1 dwell changed.")
    if tuple(config["effective_contract"]["test_seeds"]) != TEST_SEEDS:
        raise RuntimeError("Locked test seeds changed.")
    if config["revision_policy"]["additional_revision_allowed"]:
        raise RuntimeError("v1 must consume the only permitted revision.")
    return config


def _training_constants() -> Tuple[float, float, float, float, float, float]:
    training = V0_CONTRACT["training"]
    epsilon = training["epsilon"]
    return (
        float(training["q_initial_value"]),
        float(training["learning_rate_alpha"]),
        float(training["discount_gamma"]),
        float(epsilon["start"]),
        float(epsilon["end"]),
        float(epsilon["decay_fraction_of_training_transitions"]),
    )


def train_revised_candidate(trainer_seed: int) -> RevisedCandidate:
    if trainer_seed not in TRAINER_SEEDS:
        raise ValueError("trainer_seed is outside the frozen P3 manifest.")
    q_initial, alpha, gamma, epsilon_start, epsilon_end, decay_fraction = _training_constants()
    learner = TabularQLearner(trainer_seed, q_initial, alpha, gamma)
    traces: Dict[int, Ring6Trace] = {seed: generate_trace(seed, EPISODE_LENGTH) for seed in TRAIN_SEEDS}
    transition_index = 0
    all_profile_counts = [0, 0, 0, 0]
    all_states = set()
    epoch_rows: List[RevisedEpoch] = []
    for epoch_index in range(EPOCHS):
        original_rewards: List[float] = []
        training_rewards: List[float] = []
        epoch_profiles = [0, 0, 0, 0]
        epoch_states = set()
        epoch_start = transition_index
        for environment_seed in learner.shuffled_trace_order(TRAIN_SEEDS):
            environment = Ring6Environment(traces[environment_seed])
            while not environment.done:
                state_id = environment.current_state_id()
                epsilon = epsilon_at(transition_index, TRANSITIONS_PER_CANDIDATE, epsilon_start, epsilon_end, decay_fraction)
                action_id = learner.choose_action(state_id, epsilon)
                result = environment.step(action_id)
                original_reward = float(result.reward.total)
                training_reward = original_reward + (BALANCE_WEIGHT - 1.0) * float(result.reward.balance_utility)
                learner.update(state_id, action_id, training_reward, result.next_state_id, result.done)
                original_rewards.append(original_reward)
                training_rewards.append(training_reward)
                epoch_profiles[action_id] += 1
                all_profile_counts[action_id] += 1
                epoch_states.add(state_id)
                all_states.add(state_id)
                transition_index += 1
        if transition_index - epoch_start != len(TRAIN_SEEDS) * EPISODE_LENGTH:
            raise RuntimeError("Revised epoch transition count changed.")
        q_tuple = tuple(tuple(float(value) for value in row) for row in learner.q_table)
        q_values = [value for row in q_tuple for value in row]
        epoch_rows.append(RevisedEpoch(
            trainer_seed=trainer_seed,
            epoch=epoch_index + 1,
            transition_count=transition_index - epoch_start,
            cumulative_transitions=transition_index,
            mean_original_reward=fmean(original_rewards),
            mean_training_reward=fmean(training_rewards),
            profile_0_count=epoch_profiles[0],
            profile_1_count=epoch_profiles[1],
            profile_2_count=epoch_profiles[2],
            profile_3_count=epoch_profiles[3],
            distinct_state_count=len(epoch_states),
            q_min=min(q_values),
            q_max=max(q_values),
            q_table_sha256=_canonical_sha256(q_tuple),
        ))
    if transition_index != TRANSITIONS_PER_CANDIDATE:
        raise RuntimeError("Revised candidate budget changed.")
    q_table = tuple(tuple(float(value) for value in row) for row in learner.q_table)
    if any(not math.isfinite(value) for row in q_table for value in row):
        raise RuntimeError("Revised Q-table contains non-finite values.")
    policy = extract_policy(q_table)
    return RevisedCandidate(
        trainer_seed=trainer_seed,
        epochs=tuple(epoch_rows),
        q_table=q_table,
        policy=policy,
        q_table_sha256=_canonical_sha256(q_table),
        policy_sha256=_canonical_sha256(policy),
        training_profile_counts=tuple(all_profile_counts),
        visited_state_count=len(all_states),
    )


def run_revised_matrix(max_workers: int) -> Tuple[RevisedCandidate, ...]:
    if isinstance(max_workers, bool) or not isinstance(max_workers, int) or max_workers < 1:
        raise ValueError("max_workers must be positive.")
    completed: Dict[int, RevisedCandidate] = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(max_workers, len(TRAINER_SEEDS))) as executor:
        futures = {executor.submit(train_revised_candidate, seed): seed for seed in TRAINER_SEEDS}
        for future in concurrent.futures.as_completed(futures):
            seed = futures[future]
            completed[seed] = future.result()
            print(f"REVISED TRAINING COMPLETE: trainer_seed={seed}", flush=True)
    return tuple(completed[seed] for seed in TRAINER_SEEDS)


def _reconstruct_fidelity(fidelity_utility: float) -> float:
    floor = float(MDP_CONTRACT["reward"]["fidelity_floor"])
    weight = float(MDP_CONTRACT["reward"]["terms"]["fidelity_weight"])
    return floor + (float(fidelity_utility) / weight) * (1.0 - floor)


def evaluate_candidate(candidate: RevisedCandidate) -> Tuple[ValidationRow, ...]:
    rows = []
    for seed in VALIDATION_SEEDS:
        environment = Ring6Environment(generate_trace(seed, EPISODE_LENGTH))
        controller = MinimumDwellController(candidate.policy, MINIMUM_DWELL)
        actions: List[int] = []
        rewards: List[float] = []
        fidelities: List[float] = []
        balances: List[float] = []
        hops: List[float] = []
        profiles = [0, 0, 0, 0]
        success_count = 0
        while not environment.done:
            action_id = controller.choose_action(environment.current_state_id())
            result = environment.step(action_id)
            actions.append(action_id)
            profiles[action_id] += 1
            rewards.append(float(result.reward.total))
            if result.success:
                success_count += 1
                fidelities.append(_reconstruct_fidelity(result.reward.fidelity_utility))
                balances.append(float(result.reward.balance_utility))
                hops.append(float(len(result.selected_path) - 1))
        decisions = len(actions)
        switches = sum(first != second for first, second in zip(actions, actions[1:]))
        rows.append(ValidationRow(
            trainer_seed=candidate.trainer_seed, partition="validation", environment_seed=seed,
            minimum_dwell_decisions=MINIMUM_DWELL, decision_count=decisions, success_count=success_count,
            blocking_rate=(decisions-success_count)/decisions, mean_total_reward=_mean(rewards),
            mean_success_bottleneck_fidelity=_mean(fidelities), mean_balance_utility_success=_mean(balances),
            mean_hops_success=_mean(hops), switch_count=switches,
            switch_rate=switches/max(decisions-1, 1), profile_0_count=profiles[0], profile_1_count=profiles[1],
            profile_2_count=profiles[2], profile_3_count=profiles[3],
        ))
    return tuple(rows)


def summarize(rows: Sequence[ValidationRow], candidate: RevisedCandidate) -> Mapping[str, object]:
    profiles = [sum(getattr(row, f"profile_{action}_count") for row in rows) for action in range(4)]
    decisions = sum(row.decision_count for row in rows)
    successes = sum(row.success_count for row in rows)
    switches = sum(row.switch_count for row in rows)
    switch_denominator = sum(max(row.decision_count - 1, 1) for row in rows)
    fractions = [count/decisions for count in profiles]
    return {
        "trainer_seed": candidate.trainer_seed, "minimum_dwell_decisions": MINIMUM_DWELL,
        "environment_seed_count": len(rows), "decision_count": decisions, "success_count": successes,
        "blocking_rate": (decisions-successes)/decisions,
        "mean_total_reward": _mean([row.mean_total_reward for row in rows]),
        "mean_success_bottleneck_fidelity": _mean([row.mean_success_bottleneck_fidelity for row in rows]),
        "mean_balance_utility_success": _mean([row.mean_balance_utility_success for row in rows]),
        "mean_hops_success": _mean([row.mean_hops_success for row in rows]),
        "switch_count": switches, "switch_rate": switches/switch_denominator,
        "profile_counts": profiles, "profile_fractions": fractions,
        "distinct_profiles": sum(count>0 for count in profiles),
        "secondary_profile_fraction": sorted(fractions, reverse=True)[1],
        "q_table_sha256": candidate.q_table_sha256, "policy_sha256": candidate.policy_sha256,
    }


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        for item in rows:
            payload = dict(item)
            for key, value in payload.items():
                if isinstance(value, float): payload[key] = f"{value:.12f}"
                elif isinstance(value, (list, tuple)): payload[key] = json.dumps(value, separators=(",", ":"))
            writer.writerow(payload)


def _gate(selected: Mapping[str, object], baselines: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    h2 = next(item for item in baselines if item["controller"] == "h2_forced_fixed")
    h3 = next(item for item in baselines if item["controller"] == "h3_threshold")
    checks = {
        "reward_exceeds_h2": selected["mean_total_reward"] > h2["mean_total_reward"],
        "reward_exceeds_h3": selected["mean_total_reward"] > h3["mean_total_reward"],
        "blocking_noninferior": selected["blocking_rate"] <= h2["blocking_rate"] + 0.005,
        "fidelity_vs_h2": selected["mean_success_bottleneck_fidelity"] >= h2["mean_success_bottleneck_fidelity"] - 0.005,
        "fidelity_vs_h3": selected["mean_success_bottleneck_fidelity"] >= h3["mean_success_bottleneck_fidelity"] - 0.005,
        "balance_vs_h2": selected["mean_balance_utility_success"] >= h2["mean_balance_utility_success"] - 0.05,
        "balance_vs_h3": selected["mean_balance_utility_success"] >= h3["mean_balance_utility_success"] - 0.05,
        "switch_rate": selected["switch_rate"] <= 0.25,
        "meaningful_adaptation": selected["distinct_profiles"] >= 2 and selected["secondary_profile_fraction"] >= 0.01,
    }
    return {"decision": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


def write_revision_evidence(output_dir: Path, max_workers: int) -> Mapping[str, object]:
    if not output_dir.is_absolute(): output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_dir = output_dir / "candidates"; candidate_dir.mkdir(parents=True, exist_ok=True)
    load_revision_config()
    candidates = run_revised_matrix(max_workers)
    learning_path=output_dir/"learning_curves.csv"; validation_path=output_dir/"validation_per_seed.csv"
    summary_path=output_dir/"validation_summary.json"; usage_path=output_dir/"profile_usage.csv"
    selection_path=output_dir/"selection_record.json"; training_path=output_dir/"training_summary.json"
    audit_path=output_dir/"reward_dependency_audit.json"; manifest_path=output_dir/"revision_manifest.json"
    _write_csv(learning_path, [asdict(epoch) for candidate in candidates for epoch in candidate.epochs])
    training_summaries=[]
    for candidate in candidates:
        q_path=candidate_dir/f"q_table_seed_{candidate.trainer_seed}.json"
        p_path=candidate_dir/f"policy_seed_{candidate.trainer_seed}.json"
        q_path.write_text(json.dumps(candidate.q_table, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        p_path.write_text(json.dumps(candidate.policy, indent=2)+"\n", encoding="utf-8")
        training_summaries.append({"trainer_seed":candidate.trainer_seed,"epoch_count":EPOCHS,
            "transition_count":TRANSITIONS_PER_CANDIDATE,"visited_state_count":candidate.visited_state_count,
            "training_profile_counts":list(candidate.training_profile_counts),"q_table_sha256":candidate.q_table_sha256,
            "policy_sha256":candidate.policy_sha256})
    training_path.write_text(json.dumps({"schema_version":1,"candidates":training_summaries},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    all_rows=[]; summaries=[]
    for candidate in candidates:
        rows=evaluate_candidate(candidate); all_rows.extend(asdict(row) for row in rows); summaries.append(summarize(rows,candidate))
    _write_csv(validation_path, all_rows)
    summary_path.write_text(json.dumps({"schema_version":1,"candidates":summaries},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    usage=[]
    for item in summaries:
        for profile_id,(count,fraction) in enumerate(zip(item["profile_counts"],item["profile_fractions"])):
            usage.append({"trainer_seed":item["trainer_seed"],"partition":"validation","minimum_dwell_decisions":MINIMUM_DWELL,
                "profile_id":profile_id,"decision_count":count,"fraction":fraction})
    _write_csv(usage_path,usage)
    baseline_payload=json.loads(BASELINE_SUMMARY_PATH.read_text(encoding="utf-8"))
    baselines=[item for item in baseline_payload["summaries"] if item["partition"]=="validation"]
    selection=dict(select_validation_candidate(summaries,baselines))
    selected=next(item for item in selection["candidate_evaluations"] if item["trainer_seed"]==selection["selected_trainer_seed"])
    validation_gate=_gate(selected,baselines)
    selection.update({"step":"P3_STEP_6R_CONTROLLED_REVISION","revision_invoked":True,
        "revision_trigger":"validation_only_switch_instability_and_balance_degradation",
        "balance_training_weight":BALANCE_WEIGHT,"minimum_dwell_decisions":MINIMUM_DWELL,
        "additional_revision_allowed":False,"validation_revision_gate":validation_gate})
    if selection["selected_trainer_seed"]!=229 or selection["eligible_candidate_count"]!=7 or validation_gate["decision"]!="PASS":
        raise RuntimeError("Reviewed revised selection no longer matches the accepted result.")
    selection_path.write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    common=dict(success=True,action_id=1,bottleneck_fidelity=.96,post_decision_imbalance=.2,selected_path_hops=3)
    same=calculate_reward(RewardInput(previous_action_id=1,**common)); changed=calculate_reward(RewardInput(previous_action_id=0,**common))
    audit={"schema_version":1,"previous_profile_present_in_v0_state":False,"previous_profile_used_by_reward":True,
        "identical_observation_action_reward_difference":changed.total-same.total,"diagnosis":"hidden_switch_history_and_balance_underweighting"}
    audit_path.write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    manifest={"schema_version":1,"phase":"P3","step":"P3_STEP_6R_CONTROLLED_REVISION","decision":"PASS",
        "revision_count":1,"additional_revision_allowed":False,"balance_training_weight":BALANCE_WEIGHT,
        "minimum_dwell_decisions":MINIMUM_DWELL,"candidate_count":8,"eligible_candidate_count":7,"selected_trainer_seed":229,
        "epochs_per_candidate":EPOCHS,"transitions_per_candidate":TRANSITIONS_PER_CANDIDATE,
        "total_revised_training_transitions":TRANSITIONS_PER_CANDIDATE*8,"validation_trace_evaluations":32,
        "test_access_count":0,"test_partition_locked":True,"policy_freeze_performed":False,"rom_export_performed":False,
        "rtl_or_board_work_performed":False,"selected_validation":selected,"validation_revision_gate":validation_gate,
        "base_training_config_sha256":_sha256(V0_CONFIG_PATH),"revision_config_sha256":_sha256(V1_CONFIG_PATH),
        "v0_selection_record_sha256":_sha256(V0_SELECTION_PATH)}
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    sources=(V1_CONFIG_PATH,REPO_ROOT/"rl/dwell_controller.py",REPO_ROOT/"rl/p3_controlled_revision.py",
        REPO_ROOT/"sim/rl/test_p3_controlled_revision.py",REPO_ROOT/"docs/rl/p3_controlled_revision.md",REPO_ROOT/"docs/rl/p3_step6r_status.md")
    evidence=(learning_path,validation_path,summary_path,usage_path,selection_path,training_path,audit_path,manifest_path,
        *(candidate_dir/f"q_table_seed_{seed}.json" for seed in TRAINER_SEEDS),*(candidate_dir/f"policy_seed_{seed}.json" for seed in TRAINER_SEEDS))
    (output_dir/"SHA256SUMS").write_text("\n".join(f"{_sha256(path)}  {path.relative_to(REPO_ROOT)}" for path in (*sources,*evidence))+"\n",encoding="utf-8")
    return {"manifest":manifest,"selection":selection}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-dir",type=Path,default=Path("results/rl/p3_revision"))
    parser.add_argument("--workers",type=int,default=int(os.environ.get("QFLOW_MAX_WORKERS",min(8,os.cpu_count() or 1))))
    args=parser.parse_args(); print(json.dumps(write_revision_evidence(args.output_dir,args.workers),indent=2,sort_keys=True))


if __name__=="__main__": main()
