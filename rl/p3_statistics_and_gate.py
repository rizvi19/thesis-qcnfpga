"""P3 Step 8 paired statistics, utility gate and defense-level ablations."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import fmean, stdev
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from rl.dwell_controller import MinimumDwellController, validate_policy
from rl.mdp_contract import CONTRACT as MDP_CONTRACT, decode_state_id
from rl.p3_contract import CONTRACT as P3_CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.tabular_q_learning import XorShift32
from rl.trace_generator import generate_trace


REPO_ROOT = Path(__file__).resolve().parents[1]
HELDOUT_ROWS = REPO_ROOT / "results/rl/p3_heldout/heldout_results.csv"
HELDOUT_SUMMARY = REPO_ROOT / "results/rl/p3_heldout/heldout_summary.json"
HELDOUT_USAGE = REPO_ROOT / "results/rl/p3_heldout/profile_usage.csv"
HELDOUT_MANIFEST = REPO_ROOT / "results/rl/p3_heldout/heldout_manifest.json"
FROZEN_POLICY = REPO_ROOT / "results/rl/p3_policy_freeze/selected_policy_seed_229.json"
FREEZE_SUMS = REPO_ROOT / "results/rl/p3_policy_freeze/SHA256SUMS"
TRAINING_CONFIG = REPO_ROOT / "rl/config/training_config.yaml"

H2_ID = "h2_forced_fixed"
H3_ID = "h3_threshold"
H4_ID = "h4_revised_seed_229"
COMPARATORS = (H2_ID, H3_ID)
EXPECTED_INPUT_SHA256 = {
    HELDOUT_ROWS: "bce4be9e1c3534e495d278495ba81ccd97ce8a91a9d19af7a61d8d1c3cb47c49",
    HELDOUT_SUMMARY: "14982823b2af4e93aadbf533010bf22825c507fe2f14cb75aa1cfe150f917abb",
    HELDOUT_USAGE: "512e1bf2afb0e79d2a75a12ae0416cd8700826d65a8f35dbe337a43083c4438b",
    HELDOUT_MANIFEST: "d21f7950aeb03de783d42b631b9b4b65d2533fbec7428b3540a4cec620ec05e6",
    FROZEN_POLICY: "cb1557680472781c01cab7ce961fdc35d672a0c76fbc0993e3c2599274f8d611",
    FREEZE_SUMS: "3b35a3b0488073e3208627d1653f20fe3e092b844f5d618f7eaf909c82e80c51",
    TRAINING_CONFIG: "467a970fe91e4b31388b99642db68442432738b217dc0cae0fcc42b85aeaa7a4",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_frozen_inputs() -> None:
    for path, expected in EXPECTED_INPUT_SHA256.items():
        if _sha256(path) != expected:
            raise RuntimeError(f"Frozen Step 7 input changed: {path.relative_to(REPO_ROOT)}")
    manifest = json.loads(HELDOUT_MANIFEST.read_text(encoding="utf-8"))
    if manifest["test_access_count"] != 4 or manifest["controller_trace_evaluations"] != 12:
        raise RuntimeError("Step 7 held-out access accounting changed.")
    if manifest["policy_revision_after_test"] or manifest["additional_training_after_test"]:
        raise RuntimeError("Step 7 freeze boundary is no longer intact.")


def _quantile_type7(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values or not 0.0 <= probability <= 1.0:
        raise ValueError("Invalid quantile input.")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = (len(sorted_values) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    fraction = position - lower
    return float(sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction)


def paired_bootstrap_ci(
    differences: Sequence[float],
    replicates: int = 10000,
    seed: int = 32452843,
) -> Tuple[float, float]:
    if not differences or replicates < 1:
        raise ValueError("Bootstrap requires differences and positive replicates.")
    rng = XorShift32(seed)
    count = len(differences)
    values = []
    for _ in range(replicates):
        values.append(fmean(differences[rng.randbelow(count)] for _ in range(count)))
    values.sort()
    return _quantile_type7(values, 0.025), _quantile_type7(values, 0.975)


def exact_two_sided_paired_permutation(differences: Sequence[float]) -> float:
    if not differences:
        raise ValueError("Permutation test requires paired differences.")
    observed = abs(fmean(differences))
    tolerance = 1e-15
    extreme = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(differences)):
        statistic = abs(fmean(sign * value for sign, value in zip(signs, differences)))
        total += 1
        if statistic + tolerance >= observed:
            extreme += 1
    return extreme / total


def holm_adjust(p_values: Sequence[float]) -> Tuple[float, ...]:
    if not p_values or any(not 0.0 <= value <= 1.0 for value in p_values):
        raise ValueError("Holm correction requires p-values in [0,1].")
    count = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    adjusted = [0.0] * count
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[index] = running
    return tuple(adjusted)


def paired_cohens_dz(differences: Sequence[float]) -> float | None:
    if len(differences) < 2:
        return None
    spread = stdev(differences)
    return None if spread == 0.0 else fmean(differences) / spread


def _heldout_rows() -> Sequence[Mapping[str, object]]:
    numeric = {
        "environment_seed", "decision_count", "success_count", "blocking_rate",
        "mean_total_reward", "mean_success_bottleneck_fidelity",
        "mean_balance_utility_success", "mean_hops_success", "switch_count",
        "switch_rate", "profile_0_count", "profile_1_count", "profile_2_count",
        "profile_3_count",
    }
    rows = []
    with HELDOUT_ROWS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            converted: Dict[str, object] = dict(row)
            for key in numeric:
                converted[key] = int(row[key]) if key in {
                    "environment_seed", "decision_count", "success_count", "switch_count",
                    "profile_0_count", "profile_1_count", "profile_2_count", "profile_3_count",
                } else float(row[key])
            rows.append(converted)
    if len(rows) != 12:
        raise RuntimeError("Expected exactly 12 frozen held-out rows.")
    return rows


def compute_paired_statistics() -> Tuple[Sequence[Mapping[str, object]], Sequence[Mapping[str, object]]]:
    rows = _heldout_rows()
    by_key = {(str(row["controller"]), int(row["environment_seed"])): row for row in rows}
    seeds = tuple(int(value) for value in P3_CONTRACT["partitions"]["test_seeds"])
    config = json.loads(TRAINING_CONFIG.read_text(encoding="utf-8"))
    bootstrap = config["statistics"]["bootstrap"]
    comparisons = []
    per_seed = []
    raw_p = []
    for comparator in COMPARATORS:
        differences = []
        for seed in seeds:
            h4 = float(by_key[(H4_ID, seed)]["mean_total_reward"])
            baseline = float(by_key[(comparator, seed)]["mean_total_reward"])
            difference = h4 - baseline
            differences.append(difference)
            per_seed.append({
                "comparison": f"{H4_ID}_minus_{comparator}",
                "environment_seed": seed,
                "h4_mean_total_reward": h4,
                "comparator_mean_total_reward": baseline,
                "paired_difference": difference,
            })
        ci_low, ci_high = paired_bootstrap_ci(
            differences,
            int(bootstrap["replicates"]),
            int(bootstrap["rng_seed"]),
        )
        p_value = exact_two_sided_paired_permutation(differences)
        raw_p.append(p_value)
        comparisons.append({
            "comparison": f"{H4_ID}_minus_{comparator}",
            "pair_count": len(differences),
            "h4_wins": sum(value > 0.0 for value in differences),
            "paired_mean_difference": fmean(differences),
            "ci_95_low": ci_low,
            "ci_95_high": ci_high,
            "ci_excludes_zero": ci_low > 0.0 or ci_high < 0.0,
            "raw_permutation_p": p_value,
            "paired_cohens_dz": paired_cohens_dz(differences),
            "minimum_attainable_two_sided_p": 2.0 / (2 ** len(differences)),
        })
    adjusted = holm_adjust(raw_p)
    alpha = float(config["statistics"]["alpha"])
    for item, corrected in zip(comparisons, adjusted):
        item["holm_adjusted_p"] = corrected
        item["statistical_superiority"] = bool(item["ci_excludes_zero"] and corrected < alpha)
        item["interpretation"] = (
            "statistically_superior" if item["statistical_superiority"]
            else "descriptive_improvement_insufficient_power"
        )
    return comparisons, per_seed


def _summary_by_controller() -> Mapping[str, Mapping[str, object]]:
    payload = json.loads(HELDOUT_SUMMARY.read_text(encoding="utf-8"))
    result = {str(item["controller"]): item for item in payload["summaries"]}
    if set(result) != {H2_ID, H3_ID, H4_ID}:
        raise RuntimeError("Unexpected held-out controller summary set.")
    return result


def decide_utility_gate(statistics: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    config = json.loads(TRAINING_CONFIG.read_text(encoding="utf-8"))
    gate = config["utility_gate"]
    summaries = _summary_by_controller()
    h2, h3, h4 = summaries[H2_ID], summaries[H3_ID], summaries[H4_ID]
    checks = {
        "minimum_distinct_profiles": int(h4["distinct_profiles"]) >= int(gate["adaptation"]["minimum_distinct_profiles"]),
        "minimum_secondary_profile_fraction": float(h4["secondary_profile_fraction"]) >= float(gate["adaptation"]["minimum_secondary_profile_fraction"]),
        "blocking_noninferior_to_h2": float(h4["blocking_rate"]) - float(h2["blocking_rate"]) <= float(gate["blocking_noninferiority_margin_absolute"]),
        "reward_exceeds_h2": float(h4["mean_total_reward"]) > float(h2["mean_total_reward"]),
        "reward_exceeds_h3": float(h4["mean_total_reward"]) > float(h3["mean_total_reward"]),
        "fidelity_no_serious_degradation": all(
            float(h4["mean_success_bottleneck_fidelity"]) >= float(item["mean_success_bottleneck_fidelity"]) - float(gate["maximum_fidelity_degradation_absolute"])
            for item in (h2, h3)
        ),
        "balance_no_serious_degradation": all(
            float(h4["mean_balance_utility_success"]) >= float(item["mean_balance_utility_success"]) - float(gate["maximum_balance_utility_degradation_absolute"])
            for item in (h2, h3)
        ),
        "switch_rate_within_ceiling": float(h4["switch_rate"]) <= float(gate["maximum_switch_rate"]),
        "all_four_test_seeds_reward_wins": all(int(item["h4_wins"]) == int(item["pair_count"]) for item in statistics),
    }
    statistical = all(bool(item["statistical_superiority"]) for item in statistics)
    passed = all(checks.values())
    return {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_8_UTILITY_GATE",
        "decision": "PASS_DESCRIPTIVE_INSUFFICIENT_POWER" if passed else "FAIL",
        "checks": checks,
        "all_predeclared_utility_checks_pass": passed,
        "statistical_superiority_claim_allowed": statistical,
        "power_assessment": "insufficient_for_exact_two_sided_p_below_0.05_with_four_pairs",
        "minimum_attainable_two_sided_p": 0.125,
        "claim_boundary": "held_out_descriptive_improvement_and_utility_gate_pass; no_statistical_superiority_claim",
        "p4_authorized_by_p3_utility_gate": passed,
        "selected_controller_for_p4": H4_ID if passed else None,
        "policy_or_training_revision_allowed": False,
        "controller_means": {key: summaries[key] for key in (H2_ID, H3_ID, H4_ID)},
        "adverse_metric_disclosure": {
            "h4_minus_h2_mean_hops": float(h4["mean_hops_success"]) - float(h2["mean_hops_success"]),
            "h4_minus_h3_mean_hops": float(h4["mean_hops_success"]) - float(h3["mean_hops_success"]),
            "h4_minus_h2_switch_rate": float(h4["switch_rate"]) - float(h2["switch_rate"]),
            "h4_minus_h3_switch_rate": float(h4["switch_rate"]) - float(h3["switch_rate"]),
        },
    }


def _encode_bins(bins: Sequence[int]) -> int:
    if len(bins) != 4 or any(not 0 <= value < 4 for value in bins):
        raise ValueError("State bins must be four radix-4 digits.")
    result = 0
    for value in bins:
        result = result * 4 + value
    return result


def feature_marginalized_policy(policy: Sequence[int], feature_index: int) -> Tuple[int, ...]:
    policy = validate_policy(policy)
    if not 0 <= feature_index < 4:
        raise ValueError("Feature index must be in 0..3.")
    result = []
    for state_id in range(256):
        bins = list(decode_state_id(state_id))
        candidates = []
        for value in range(4):
            varied = list(bins)
            varied[feature_index] = value
            candidates.append(policy[_encode_bins(varied)])
        counts = {action: candidates.count(action) for action in range(4)}
        result.append(min(action for action, count in counts.items() if count == max(counts.values())))
    return validate_policy(result)


def _evaluate_validation_policy(policy: Sequence[int], dwell: int) -> Mapping[str, object]:
    seeds = tuple(int(value) for value in P3_CONTRACT["partitions"]["validation_seeds"])
    length = int(P3_CONTRACT["partitions"]["episode_length"])
    trace_rows = []
    component_sums = {name: 0.0 for name in ("success", "blocking", "fidelity_utility", "balance_utility", "hop_cost", "switch_cost")}
    total_decisions = 0
    for seed in seeds:
        environment = Ring6Environment(generate_trace(seed, length))
        controller = MinimumDwellController(policy, dwell)
        rewards: List[float] = []
        actions: List[int] = []
        success = 0
        fidelities: List[float] = []
        balances: List[float] = []
        hops: List[float] = []
        while not environment.done:
            action = controller.choose_action(environment.current_state_id())
            result = environment.step(action)
            actions.append(action)
            rewards.append(float(result.reward.total))
            for key, value in asdict(result.reward).items():
                component_sums[key] += float(value)
            if result.success:
                success += 1
                reward = MDP_CONTRACT["reward"]
                floor = float(reward["fidelity_floor"])
                weight = float(reward["terms"]["fidelity_weight"])
                fidelities.append(floor + (float(result.reward.fidelity_utility) / weight) * (1.0 - floor))
                balances.append(float(result.reward.balance_utility))
                hops.append(float(len(result.selected_path) - 1))
        switches = sum(a != b for a, b in zip(actions, actions[1:]))
        total_decisions += len(actions)
        trace_rows.append({
            "reward": fmean(rewards),
            "blocking": (len(actions) - success) / len(actions),
            "fidelity": fmean(fidelities),
            "balance": fmean(balances),
            "hops": fmean(hops),
            "switches": switches,
            "switch_denominator": max(len(actions) - 1, 1),
            "profile_counts": [actions.count(index) for index in range(4)],
        })
    profile_counts = [sum(row["profile_counts"][index] for row in trace_rows) for index in range(4)]
    return {
        "validation_seed_count": len(seeds),
        "decision_count": total_decisions,
        "mean_total_reward": fmean(row["reward"] for row in trace_rows),
        "blocking_rate": fmean(row["blocking"] for row in trace_rows),
        "mean_success_bottleneck_fidelity": fmean(row["fidelity"] for row in trace_rows),
        "mean_balance_utility_success": fmean(row["balance"] for row in trace_rows),
        "mean_hops_success": fmean(row["hops"] for row in trace_rows),
        "switch_rate": sum(row["switches"] for row in trace_rows) / sum(row["switch_denominator"] for row in trace_rows),
        "profile_counts": profile_counts,
        "distinct_profiles": sum(value > 0 for value in profile_counts),
        "component_means_per_decision": {key: value / total_decisions for key, value in component_sums.items()},
    }


def compute_diagnostic_ablations() -> Mapping[str, Sequence[Mapping[str, object]]]:
    policy = validate_policy(json.loads(FROZEN_POLICY.read_text(encoding="utf-8")))
    full = _evaluate_validation_policy(policy, 3)
    feature_rows = [{"ablation": "none_frozen_h4", "removed_feature": "none", **full}]
    for index, name in enumerate(MDP_CONTRACT["state"]["feature_order"]):
        ablated = _evaluate_validation_policy(feature_marginalized_policy(policy, index), 3)
        feature_rows.append({
            "ablation": f"remove_{name}_by_action_marginalization",
            "removed_feature": name,
            **ablated,
            "reward_delta_from_full": float(ablated["mean_total_reward"]) - float(full["mean_total_reward"]),
        })
    dwell_rows = []
    for dwell in (1, 3):
        values = _evaluate_validation_policy(policy, dwell)
        dwell_rows.append({"minimum_dwell_decisions": dwell, **values})
    component_means = full["component_means_per_decision"]
    full_reward = float(full["mean_total_reward"])
    reward_rows = [{
        "removed_reward_term": "none",
        "trajectory_mean_score": full_reward,
        "score_delta_from_full": 0.0,
        "interpretation": "frozen_action_trajectory_no_retraining",
    }]
    for term, contribution in component_means.items():
        reward_rows.append({
            "removed_reward_term": term,
            "trajectory_mean_score": full_reward - float(contribution),
            "score_delta_from_full": -float(contribution),
            "interpretation": "counterfactual_rescoring_of_frozen_validation_trajectory_no_retraining",
        })
    return {"feature_ablation": feature_rows, "reward_term_ablation": reward_rows, "dwell_ablation": dwell_rows}


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames and key not in {"component_means_per_decision", "profile_counts"}:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            payload = {key: row.get(key, "") for key in fieldnames}
            for key, value in payload.items():
                if isinstance(value, float):
                    payload[key] = f"{value:.12f}"
                elif isinstance(value, bool):
                    payload[key] = str(value).lower()
            writer.writerow(payload)


def write_step8_evidence(output_dir: Path) -> Mapping[str, object]:
    validate_frozen_inputs()
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    statistics, per_seed = compute_paired_statistics()
    gate = decide_utility_gate(statistics)
    ablations = compute_diagnostic_ablations()
    _write_csv(output_dir / "paired_statistics.csv", statistics)
    _write_csv(output_dir / "per_seed_reward_differences.csv", per_seed)
    _write_csv(output_dir / "feature_ablation.csv", ablations["feature_ablation"])
    _write_csv(output_dir / "reward_term_ablation.csv", ablations["reward_term_ablation"])
    _write_csv(output_dir / "dwell_ablation.csv", ablations["dwell_ablation"])
    (output_dir / "utility_gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "schema_version": 1,
        "statistics": statistics,
        "utility_gate_decision": gate["decision"],
        "statistical_superiority_claim_allowed": gate["statistical_superiority_claim_allowed"],
        "p4_authorized_by_p3_utility_gate": gate["p4_authorized_by_p3_utility_gate"],
        "ablation_scope": "defense_level_diagnostics_on_frozen_validation_controller; no retraining or selection",
    }
    (output_dir / "analysis_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_8_STATISTICS_UTILITY_GATE_ABLATIONS",
        "decision": gate["decision"],
        "test_rows_read_only": True,
        "new_test_trace_generation": 0,
        "test_access_count_carried_forward": 4,
        "policy_revision_after_test": False,
        "additional_training_after_test": False,
        "selected_controller_unchanged": H4_ID,
        "statistics_complete": True,
        "utility_gate_complete": True,
        "defense_ablation_summary_complete": True,
        "journal_retrained_ablation_matrix_deferred_to_j2": True,
        "p4_authorized": gate["p4_authorized_by_p3_utility_gate"],
        "rom_export_performed": False,
        "rtl_or_board_work_performed": False,
    }
    (output_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    source_paths = (
        REPO_ROOT / "rl/p3_statistics_and_gate.py",
        REPO_ROOT / "sim/rl/test_p3_statistics_gate.py",
        REPO_ROOT / "docs/rl/p3_step8_statistics_utility_gate.md",
        REPO_ROOT / "docs/rl/p3_step8_status.md",
    )
    result_paths = tuple(output_dir / name for name in (
        "paired_statistics.csv", "per_seed_reward_differences.csv", "feature_ablation.csv",
        "reward_term_ablation.csv", "dwell_ablation.csv", "utility_gate.json",
        "analysis_summary.json", "analysis_manifest.json",
    ))
    checksum_lines = [
        f"{_sha256(path)}  {path.relative_to(REPO_ROOT)}"
        for path in source_paths
    ]
    checksum_lines.extend(
        f"{_sha256(path)}  results/rl/p3_analysis/{path.name}"
        for path in result_paths
    )
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return {"statistics": statistics, "utility_gate": gate, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3_analysis"))
    args = parser.parse_args()
    print(json.dumps(write_step8_evidence(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
