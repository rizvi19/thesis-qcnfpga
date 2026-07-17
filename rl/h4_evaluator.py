"""Validation-only evaluation and frozen model selection for P3 H4."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Dict, List, Mapping, Sequence, Tuple

from rl.h4_trainer import CandidateResult
from rl.mdp_contract import CONTRACT as MDP_CONTRACT
from rl.p3_contract import CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.trace_generator import Ring6Trace, generate_trace


VALIDATION_SEEDS = tuple(int(value) for value in CONTRACT["partitions"]["validation_seeds"])
PROFILE_COUNT = int(CONTRACT["controller_matrix"]["h4"]["action_count"])


@dataclass(frozen=True)
class ValidationTraceMetrics:
    trainer_seed: int
    partition: str
    environment_seed: int
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


def _validate_policy(policy: Sequence[int]) -> Tuple[int, ...]:
    if len(policy) != int(CONTRACT["controller_matrix"]["h4"]["state_count"]):
        raise ValueError("H4 policy must contain exactly 256 action indices.")
    result = tuple(policy)
    if any(isinstance(action, bool) or not isinstance(action, int) or not 0 <= action < PROFILE_COUNT for action in result):
        raise ValueError("H4 policy contains an invalid action index.")
    return result


def evaluate_validation_trace(
    trainer_seed: int,
    trace: Ring6Trace,
    policy: Sequence[int],
) -> ValidationTraceMetrics:
    """Evaluate a frozen policy on one authorized validation trace."""
    if trace.seed not in VALIDATION_SEEDS:
        raise ValueError("P3 Step 6 evaluation accepts frozen validation seeds only.")
    policy = _validate_policy(policy)
    environment = Ring6Environment(trace)
    actions: List[int] = []
    rewards: List[float] = []
    fidelities: List[float] = []
    balances: List[float] = []
    hops: List[float] = []
    profile_counts = [0, 0, 0, 0]
    success_count = 0
    while not environment.done:
        action_id = policy[environment.current_state_id()]
        result = environment.step(action_id)
        actions.append(action_id)
        profile_counts[action_id] += 1
        rewards.append(float(result.reward.total))
        if result.success:
            success_count += 1
            fidelities.append(_reconstruct_fidelity(result.reward.fidelity_utility))
            balances.append(float(result.reward.balance_utility))
            hops.append(float(len(result.selected_path) - 1))
    decision_count = len(actions)
    switch_count = sum(first != second for first, second in zip(actions, actions[1:]))
    return ValidationTraceMetrics(
        trainer_seed=trainer_seed,
        partition="validation",
        environment_seed=trace.seed,
        decision_count=decision_count,
        success_count=success_count,
        blocking_rate=(decision_count - success_count) / decision_count,
        mean_total_reward=_mean(rewards),
        mean_success_bottleneck_fidelity=_mean(fidelities),
        mean_balance_utility_success=_mean(balances),
        mean_hops_success=_mean(hops),
        switch_count=switch_count,
        switch_rate=switch_count / max(decision_count - 1, 1),
        profile_0_count=profile_counts[0],
        profile_1_count=profile_counts[1],
        profile_2_count=profile_counts[2],
        profile_3_count=profile_counts[3],
    )


def evaluate_candidate_validation(candidate: CandidateResult) -> Tuple[ValidationTraceMetrics, ...]:
    length = int(CONTRACT["partitions"]["episode_length"])
    return tuple(
        evaluate_validation_trace(candidate.trainer_seed, generate_trace(seed, length), candidate.policy)
        for seed in VALIDATION_SEEDS
    )


def summarize_validation(rows: Sequence[ValidationTraceMetrics]) -> Mapping[str, object]:
    if not rows or len({row.trainer_seed for row in rows}) != 1:
        raise ValueError("Validation summary requires one nonempty candidate group.")
    trainer_seed = rows[0].trainer_seed
    if tuple(row.environment_seed for row in rows) != VALIDATION_SEEDS:
        raise ValueError("Validation rows do not match the frozen validation seed order.")
    profile_counts = [sum(getattr(row, f"profile_{action}_count") for row in rows) for action in range(PROFILE_COUNT)]
    decision_count = sum(row.decision_count for row in rows)
    success_count = sum(row.success_count for row in rows)
    switch_count = sum(row.switch_count for row in rows)
    switch_denominator = sum(max(row.decision_count - 1, 1) for row in rows)
    fractions = [count / decision_count for count in profile_counts]
    return {
        "trainer_seed": trainer_seed,
        "environment_seed_count": len(rows),
        "decision_count": decision_count,
        "success_count": success_count,
        "blocking_rate": (decision_count - success_count) / decision_count,
        "mean_total_reward": _mean([row.mean_total_reward for row in rows]),
        "mean_success_bottleneck_fidelity": _mean([row.mean_success_bottleneck_fidelity for row in rows]),
        "mean_balance_utility_success": _mean([row.mean_balance_utility_success for row in rows]),
        "mean_hops_success": _mean([row.mean_hops_success for row in rows]),
        "switch_count": switch_count,
        "switch_rate": switch_count / switch_denominator,
        "profile_counts": profile_counts,
        "profile_fractions": fractions,
        "distinct_profiles": sum(count > 0 for count in profile_counts),
        "secondary_profile_fraction": sorted(fractions, reverse=True)[1],
    }


def select_validation_candidate(
    summaries: Sequence[Mapping[str, object]],
    baseline_validation: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    """Apply the frozen eligibility gates and lexicographic ranking."""
    if len(summaries) != 8 or len({int(item["trainer_seed"]) for item in summaries}) != 8:
        raise ValueError("Selection requires exactly eight unique trainer candidates.")
    comparators = {
        str(item["controller"]): item
        for item in baseline_validation
        if item["partition"] == "validation"
    }
    if set(comparators) != {"h2_forced_fixed", "h3_threshold"}:
        raise ValueError("Selection requires frozen H2 and H3 validation summaries.")
    eligibility = CONTRACT["model_selection"]["eligibility"]
    blocking_ceiling = min(float(item["blocking_rate"]) for item in comparators.values()) + float(
        eligibility["blocking_noninferiority_margin_absolute"]
    )
    evaluated = []
    for summary in summaries:
        reasons = []
        if float(summary["blocking_rate"]) > blocking_ceiling:
            reasons.append("blocking_noninferiority")
        if int(summary["distinct_profiles"]) < int(eligibility["minimum_distinct_profiles"]):
            reasons.append("minimum_distinct_profiles")
        if float(summary["secondary_profile_fraction"]) < float(eligibility["minimum_secondary_profile_fraction"]):
            reasons.append("minimum_secondary_profile_fraction")
        if float(summary["switch_rate"]) > float(eligibility["switch_rate_ceiling"]):
            reasons.append("switch_rate_ceiling")
        evaluated.append({**summary, "eligible": not reasons, "ineligibility_reasons": reasons})

    eligible = [item for item in evaluated if item["eligible"]]
    rank_key = lambda item: (
        -float(item["mean_total_reward"]),
        float(item["blocking_rate"]),
        -float(item["mean_success_bottleneck_fidelity"]),
        float(item["switch_rate"]),
        int(item["trainer_seed"]),
    )
    safety_key = lambda item: (
        float(item["blocking_rate"]),
        -float(item["mean_success_bottleneck_fidelity"]),
        float(item["switch_rate"]),
        -float(item["mean_total_reward"]),
        int(item["trainer_seed"]),
    )
    selected = min(eligible, key=rank_key) if eligible else None
    provisional = min(evaluated, key=safety_key)
    return {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_6_VALIDATION_SELECTION",
        "decision": "PASS" if selected is not None else "REVISION_REQUIRED",
        "selected_trainer_seed": None if selected is None else int(selected["trainer_seed"]),
        "eligible_candidate_count": len(eligible),
        "provisional_safety_first_trainer_seed": int(provisional["trainer_seed"]),
        "revision_invoked": selected is None,
        "revision_trigger": None if selected is not None else "validation_only_safety_gate_failure",
        "blocking_ceiling": blocking_ceiling,
        "switch_rate_ceiling": float(eligibility["switch_rate_ceiling"]),
        "candidate_evaluations": evaluated,
        "ranking": list(CONTRACT["model_selection"]["ranking"]),
        "test_access_count": 0,
        "test_partition_locked": True,
        "policy_freeze_performed": False,
    }


def rows_to_dicts(rows: Sequence[ValidationTraceMetrics]) -> Sequence[Mapping[str, object]]:
    return [asdict(row) for row in rows]
