"""Deterministic P2 profile sensitivity sweep on controlled Ring-6 stress cases."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
from itertools import product
import json
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from rl.profile_codebook import CONFIG_PATH, Profile
from rl.route_selector import PathObjectives, RouteSelection, select_route


BALANCED_ALPHAS = (1.0, 1.5, 0.5, 2.0)
MIN_REQUIRED_MARGIN = 0.19
UPPER_PATH = (0, 1, 2, 3)
LOWER_PATH = (0, 5, 4, 3)
SHORT_PATH = (0, 1, 2)
LONG_PATH = (0, 5, 4, 3, 2)


@dataclass(frozen=True)
class EdgeState:
    key_count: float
    fidelity: float
    key_rate: float
    qber: float
    consumed: float = 0.0


@dataclass(frozen=True)
class PathCase:
    path: Tuple[int, ...]
    edges: Tuple[EdgeState, ...]


@dataclass(frozen=True)
class Scenario:
    name: str
    purpose: str
    paths: Tuple[PathCase, ...]
    expected_by_intent: Mapping[str, Tuple[int, ...]]


@dataclass(frozen=True)
class CandidateResult:
    intent: str
    profile: Profile
    correct_count: int
    scenario_count: int
    minimum_margin: float
    mean_margin: float
    alpha_distance: float
    ratio_complexity: int
    eligible: bool


def _uniform_path(path: Tuple[int, ...], edge: EdgeState) -> PathCase:
    return PathCase(path=path, edges=tuple(edge for _ in range(len(path) - 1)))


SCENARIOS = (
    Scenario(
        name="resource_fidelity_tradeoff_moderate",
        purpose="Moderate key scarcity versus fidelity tradeoff on equal-hop Ring-6 paths.",
        paths=(
            _uniform_path(UPPER_PATH, EdgeState(3, 0.99, 3, 0.01)),
            _uniform_path(LOWER_PATH, EdgeState(10, 0.91, 8, 0.08)),
        ),
        expected_by_intent={
            "scarcity_protection": LOWER_PATH,
            "fidelity_protection": UPPER_PATH,
            "low_latency": LOWER_PATH,
        },
    ),
    Scenario(
        name="resource_fidelity_tradeoff_severe",
        purpose="Severe near-depletion route versus lower-fidelity replenishing route.",
        paths=(
            _uniform_path(UPPER_PATH, EdgeState(2, 0.98, 2, 0.02)),
            _uniform_path(LOWER_PATH, EdgeState(12, 0.92, 10, 0.07)),
        ),
        expected_by_intent={
            "scarcity_protection": LOWER_PATH,
            "fidelity_protection": UPPER_PATH,
            "low_latency": LOWER_PATH,
        },
    ),
    Scenario(
        name="slow_replenishment_tradeoff",
        purpose="Slow replenishment and moderate occupancy versus noisier healthy pools.",
        paths=(
            _uniform_path(UPPER_PATH, EdgeState(4, 0.985, 2, 0.015)),
            _uniform_path(LOWER_PATH, EdgeState(16, 0.93, 8, 0.06)),
        ),
        expected_by_intent={
            "scarcity_protection": LOWER_PATH,
            "fidelity_protection": UPPER_PATH,
            "low_latency": LOWER_PATH,
        },
    ),
    Scenario(
        name="short_path_quality_tradeoff_moderate",
        purpose="Two-hop stressed path versus four-hop high-quality Ring-6 detour.",
        paths=(
            _uniform_path(SHORT_PATH, EdgeState(3, 0.94, 3, 0.05)),
            _uniform_path(LONG_PATH, EdgeState(12, 0.985, 10, 0.015)),
        ),
        expected_by_intent={
            "scarcity_protection": LONG_PATH,
            "fidelity_protection": LONG_PATH,
            "low_latency": SHORT_PATH,
        },
    ),
    Scenario(
        name="short_path_quality_tradeoff_severe",
        purpose="Two-hop heavily stressed path versus four-hop robust detour.",
        paths=(
            _uniform_path(SHORT_PATH, EdgeState(2, 0.93, 2, 0.06)),
            _uniform_path(LONG_PATH, EdgeState(16, 0.99, 12, 0.01)),
        ),
        expected_by_intent={
            "scarcity_protection": LONG_PATH,
            "fidelity_protection": LONG_PATH,
            "low_latency": SHORT_PATH,
        },
    ),
)


def _normalized_ratio(ratio: Tuple[int, int, int]) -> Tuple[float, float, float]:
    total = sum(ratio)
    return tuple(value / total for value in ratio)


def _profile(
    action_id: int,
    key: str,
    name: str,
    intent: str,
    alphas: Tuple[float, float, float, float],
    ratio: Tuple[int, int, int],
) -> Profile:
    return Profile(
        action_id=action_id,
        key=key,
        name=name,
        status="candidate_pending_sensitivity",
        intent=intent,
        alphas=alphas,
        lambda_tch=_normalized_ratio(ratio),
        lambda_tch_hw_ratio=ratio,
    )


def candidate_profiles() -> Mapping[str, Tuple[Profile, ...]]:
    scarcity = tuple(
        _profile(
            1,
            "scarcity_protection",
            "Scarcity protection",
            "Increase scarcity/replenishment penalties and favor utilization balance.",
            (alpha1, 1.5, alpha3, 2.0),
            ratio,
        )
        for alpha1, alpha3, ratio in product(
            (1.5, 2.0, 3.0, 4.0),
            (1.0, 1.5, 2.0),
            ((1, 1, 2), (1, 1, 3), (1, 1, 4), (1, 2, 3), (2, 1, 3)),
        )
    )
    fidelity = tuple(
        _profile(
            2,
            "fidelity_protection",
            "Fidelity protection",
            "Increase fidelity/QBER penalties and favor bottleneck fidelity.",
            (1.0, alpha2, 0.5, alpha4),
            ratio,
        )
        for alpha2, alpha4, ratio in product(
            (2.0, 3.0, 4.0),
            (3.0, 4.0),
            ((1, 2, 1), (1, 3, 1), (1, 4, 1), (2, 3, 1)),
        )
    )
    low_latency = tuple(
        _profile(
            3,
            "low_latency",
            "Low-latency",
            "Reduce nonessential penalties and favor path cost/hops.",
            (alpha1, alpha2, alpha3, alpha4),
            ratio,
        )
        for alpha1, alpha2, alpha3, alpha4, ratio in product(
            (0.5,),
            (0.5, 1.0),
            (0.25, 0.5),
            (1.0,),
            ((2, 1, 1), (3, 1, 1), (4, 1, 1), (3, 2, 1)),
        )
    )
    return {
        "scarcity_protection": scarcity,
        "fidelity_protection": fidelity,
        "low_latency": low_latency,
    }


def evaluate_path(profile: Profile, path_case: PathCase) -> PathObjectives:
    if len(path_case.edges) != len(path_case.path) - 1:
        raise ValueError(f"Edge count does not match path {path_case.path}.")
    alpha1, alpha2, alpha3, alpha4 = profile.alphas
    path_cost = 0.0
    fidelities = []
    utilizations = []
    for edge in path_case.edges:
        if edge.key_count < 1 or edge.key_rate <= 0 or not 0.0 < edge.fidelity <= 1.0:
            raise ValueError("Sensitivity fixtures must contain feasible finite links.")
        path_cost += (
            alpha1 / edge.key_count
            + alpha2 / edge.fidelity
            + alpha3 / edge.key_rate
            + alpha4 * edge.qber
        )
        fidelities.append(edge.fidelity)
        utilizations.append((edge.consumed + 1.0) / edge.key_count)
    return PathObjectives(
        path=path_case.path,
        path_cost=path_cost,
        bottleneck_fidelity=min(fidelities),
        utilization_imbalance=max(utilizations),
    )


def evaluate_scenario(profile: Profile, scenario: Scenario) -> RouteSelection:
    objectives = tuple(evaluate_path(profile, path_case) for path_case in scenario.paths)
    return select_route(objectives, profile.lambda_tch)


def evaluate_candidate(intent: str, profile: Profile) -> CandidateResult:
    margins = []
    correct_count = 0
    for scenario in SCENARIOS:
        selection = evaluate_scenario(profile, scenario)
        expected = scenario.expected_by_intent[intent]
        correct_count += int(selection.selected.objectives.path == expected)
        margins.append(selection.score_margin)
    alpha_distance = sum(abs(actual - anchor) for actual, anchor in zip(profile.alphas, BALANCED_ALPHAS))
    ratio_complexity = sum(profile.lambda_tch_hw_ratio)
    minimum_margin = min(margins)
    eligible = correct_count == len(SCENARIOS) and minimum_margin >= MIN_REQUIRED_MARGIN
    return CandidateResult(
        intent=intent,
        profile=profile,
        correct_count=correct_count,
        scenario_count=len(SCENARIOS),
        minimum_margin=minimum_margin,
        mean_margin=sum(margins) / len(margins),
        alpha_distance=alpha_distance,
        ratio_complexity=ratio_complexity,
        eligible=eligible,
    )


def run_sweep() -> Tuple[Mapping[str, Profile], Tuple[CandidateResult, ...]]:
    results = tuple(
        evaluate_candidate(intent, profile)
        for intent, profiles in candidate_profiles().items()
        for profile in profiles
    )
    selected: Dict[str, Profile] = {}
    for intent in candidate_profiles():
        eligible = [result for result in results if result.intent == intent and result.eligible]
        if not eligible:
            raise RuntimeError(f"No eligible profile for {intent}.")
        eligible.sort(
            key=lambda result: (
                result.alpha_distance,
                result.ratio_complexity,
                -result.mean_margin,
                result.profile.alphas,
                result.profile.lambda_tch_hw_ratio,
            )
        )
        selected[intent] = eligible[0].profile
    return selected, results


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_results(output_dir: Path, selected: Mapping[str, Profile], results: Sequence[CandidateResult]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ranking_path = output_dir / "candidate_ranking.csv"
    scenario_path = output_dir / "selected_scenario_matrix.csv"
    summary_path = output_dir / "selection_summary.json"

    ordered = sorted(
        results,
        key=lambda result: (
            result.intent,
            not result.eligible,
            result.alpha_distance,
            result.ratio_complexity,
            -result.mean_margin,
            result.profile.alphas,
            result.profile.lambda_tch_hw_ratio,
        ),
    )
    _write_csv(
        ranking_path,
        (
            "intent",
            "alphas",
            "lambda_tch",
            "lambda_tch_hw_ratio",
            "correct_count",
            "scenario_count",
            "minimum_margin",
            "mean_margin",
            "alpha_distance",
            "ratio_complexity",
            "eligible",
            "selected",
        ),
        (
            (
                result.intent,
                json.dumps(result.profile.alphas),
                json.dumps(result.profile.lambda_tch),
                json.dumps(result.profile.lambda_tch_hw_ratio),
                result.correct_count,
                result.scenario_count,
                f"{result.minimum_margin:.12f}",
                f"{result.mean_margin:.12f}",
                f"{result.alpha_distance:.6f}",
                result.ratio_complexity,
                str(result.eligible).lower(),
                str(result.profile == selected[result.intent]).lower(),
            )
            for result in ordered
        ),
    )

    scenario_rows = []
    for intent, profile in selected.items():
        for scenario in SCENARIOS:
            selection = evaluate_scenario(profile, scenario)
            expected = scenario.expected_by_intent[intent]
            scenario_rows.append(
                (
                    intent,
                    scenario.name,
                    json.dumps(expected),
                    json.dumps(selection.selected.objectives.path),
                    f"{selection.selected.tchebycheff_score:.12f}",
                    f"{selection.score_margin:.12f}",
                    str(selection.selected.objectives.path == expected).lower(),
                )
            )
    _write_csv(
        scenario_path,
        ("intent", "scenario", "expected_path", "selected_path", "selected_score", "score_margin", "correct"),
        scenario_rows,
    )

    eligible_counts = {
        intent: sum(result.eligible for result in results if result.intent == intent)
        for intent in selected
    }
    summary = {
        "schema_version": 1,
        "protocol": {
            "scenario_count": len(SCENARIOS),
            "minimum_required_margin": MIN_REQUIRED_MARGIN,
            "selection_order": [
                "all scenario intents correct",
                "minimum margin at least threshold",
                "minimum L1 alpha distance from Balanced",
                "minimum integer-ratio complexity",
                "maximum mean score margin",
            ],
            "normalization_epsilon": 2.0 ** -16,
        },
        "eligible_candidate_counts": eligible_counts,
        "selected_profiles": {
            intent: {
                "action_id": profile.action_id,
                "alphas": list(profile.alphas),
                "lambda_tch": list(profile.lambda_tch),
                "lambda_tch_hw_ratio": list(profile.lambda_tch_hw_ratio),
            }
            for intent, profile in selected.items()
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_lines = []
    for path in (ranking_path, scenario_path, summary_path):
        checksum_lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def apply_selected_profiles(selected: Mapping[str, Profile], config_path: Path = CONFIG_PATH) -> None:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    data["selection_status"] = "four_profiles_selected_by_p2_sensitivity"
    for record in data["profiles"]:
        key = record["key"]
        if key == "balanced":
            continue
        profile = selected[key]
        record["alphas"] = list(profile.alphas)
        record["lambda_tch"] = list(profile.lambda_tch)
        record["lambda_tch_hw_ratio"] = list(profile.lambda_tch_hw_ratio)
        record["status"] = "selected_p2_sensitivity"
        record["selection_evidence"] = "results/rl/p2_sensitivity/selection_summary.json"
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_sensitivity"))
    parser.add_argument("--apply-codebook", action="store_true")
    args = parser.parse_args()

    selected, results = run_sweep()
    write_results(args.output_dir, selected, results)
    if args.apply_codebook:
        apply_selected_profiles(selected)

    for intent, profile in selected.items():
        eligible_count = sum(result.eligible for result in results if result.intent == intent)
        print(
            f"SELECTED {intent}: alphas={profile.alphas} "
            f"lambda_TCH={profile.lambda_tch} ratio={profile.lambda_tch_hw_ratio} "
            f"eligible_candidates={eligible_count}"
        )


if __name__ == "__main__":
    main()
