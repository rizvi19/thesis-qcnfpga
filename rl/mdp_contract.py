"""Validated P2 MDP contract, state encoder and decomposed reward functions."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Mapping, Optional, Tuple

from rl.profile_codebook import CONFIG_PATH as PROFILE_CONFIG_PATH, PROFILES


CONTRACT_PATH = Path(__file__).resolve().parent / "config" / "mdp_v0.yaml"


@dataclass(frozen=True)
class StateObservation:
    min_key_occupancy: float
    bottleneck_fidelity: float
    offered_request_load: float
    utilization_imbalance: float


@dataclass(frozen=True)
class RewardInput:
    success: bool
    action_id: int
    previous_action_id: Optional[int] = None
    bottleneck_fidelity: Optional[float] = None
    post_decision_imbalance: Optional[float] = None
    selected_path_hops: int = 0


@dataclass(frozen=True)
class RewardBreakdown:
    success: float
    blocking: float
    fidelity_utility: float
    balance_utility: float
    hop_cost: float
    switch_cost: float

    @property
    def total(self) -> float:
        return sum(asdict(self).values())


def load_contract(path: Path = CONTRACT_PATH) -> Dict[str, object]:
    """Load the JSON-compatible YAML contract using only the Python standard library."""
    return json.loads(path.read_text(encoding="utf-8"))


CONTRACT = load_contract()


def _clip(value: float, lower: float, upper: float) -> float:
    if not math.isfinite(value):
        raise ValueError("State and reward inputs must be finite.")
    return min(max(value, lower), upper)


def feature_bin(feature_name: str, value: float) -> int:
    state = CONTRACT["state"]
    feature = state["features"][feature_name]
    lower, upper = feature["clip"]
    clipped = _clip(value, float(lower), float(upper))
    return bisect_right(tuple(float(item) for item in feature["thresholds"]), clipped)


def encode_state(observation: StateObservation) -> int:
    values = asdict(observation)
    state_id = 0
    for feature_name in CONTRACT["state"]["feature_order"]:
        state_id = state_id * 4 + feature_bin(feature_name, values[feature_name])
    return state_id


def decode_state_id(state_id: int) -> Tuple[int, int, int, int]:
    if isinstance(state_id, bool) or not isinstance(state_id, int) or not 0 <= state_id < 256:
        raise ValueError("State ID must be an integer in 0..255.")
    bins = [0, 0, 0, 0]
    remainder = state_id
    for index in range(3, -1, -1):
        bins[index] = remainder % 4
        remainder //= 4
    return tuple(bins)


def calculate_reward(inputs: RewardInput) -> RewardBreakdown:
    action_ids = {profile.action_id for profile in PROFILES}
    if isinstance(inputs.action_id, bool) or not isinstance(inputs.action_id, int) or inputs.action_id not in action_ids:
        raise ValueError(f"Invalid action ID {inputs.action_id}.")
    if inputs.previous_action_id is not None and (
        isinstance(inputs.previous_action_id, bool)
        or not isinstance(inputs.previous_action_id, int)
        or inputs.previous_action_id not in action_ids
    ):
        raise ValueError(f"Invalid previous action ID {inputs.previous_action_id}.")

    reward = CONTRACT["reward"]
    terms = reward["terms"]
    switched = inputs.previous_action_id is not None and inputs.previous_action_id != inputs.action_id
    switch_cost = float(terms["profile_switch"]) if switched else 0.0

    if not inputs.success:
        if inputs.selected_path_hops != 0:
            raise ValueError("A blocked step cannot contain selected path hops.")
        return RewardBreakdown(
            success=0.0,
            blocking=float(terms["blocking"]),
            fidelity_utility=0.0,
            balance_utility=0.0,
            hop_cost=0.0,
            switch_cost=switch_cost,
        )

    if inputs.bottleneck_fidelity is None or inputs.post_decision_imbalance is None:
        raise ValueError("A successful step requires fidelity and imbalance values.")
    if inputs.selected_path_hops < 1:
        raise ValueError("A successful step requires at least one selected edge.")

    fidelity_floor = float(reward["fidelity_floor"])
    fidelity = _clip(float(inputs.bottleneck_fidelity), 0.0, 1.0)
    fidelity_normalized = _clip(
        (fidelity - fidelity_floor) / (1.0 - fidelity_floor),
        0.0,
        1.0,
    )
    imbalance = _clip(float(inputs.post_decision_imbalance), 0.0, 1.0)

    return RewardBreakdown(
        success=float(terms["success"]),
        blocking=0.0,
        fidelity_utility=float(terms["fidelity_weight"]) * fidelity_normalized,
        balance_utility=float(terms["balance_weight"]) * (1.0 - imbalance),
        hop_cost=float(terms["hop_cost_per_edge"]) * inputs.selected_path_hops,
        switch_cost=switch_cost,
    )


def episode_done(next_trace_index: int, trace_length: int) -> bool:
    if trace_length < 1 or not 0 <= next_trace_index <= trace_length:
        raise ValueError("Invalid trace position.")
    return next_trace_index >= trace_length


def validate_contract() -> Mapping[str, object]:
    state = CONTRACT["state"]
    if state["radix"] != 4 or state["state_count"] != 256:
        raise ValueError("P2 contract must define 4^4 = 256 states.")
    if len(state["feature_order"]) != 4 or len(set(state["feature_order"])) != 4:
        raise ValueError("Exactly four unique state features are required.")
    normalization = state["normalization_constants"]
    if normalization != {
        "key_pool_capacity_per_link": 16,
        "request_capacity_per_control_window": 4,
        "utilization_window_steps": 16,
    }:
        raise ValueError("Unexpected P2 state-normalization constants.")
    for name in state["feature_order"]:
        feature = state["features"][name]
        thresholds = tuple(float(value) for value in feature["thresholds"])
        if len(thresholds) != 3 or tuple(sorted(thresholds)) != thresholds:
            raise ValueError(f"Invalid thresholds for {name}.")
        if len(feature["labels"]) != 4:
            raise ValueError(f"Exactly four labels are required for {name}.")

    decoded = {decode_state_id(state_id) for state_id in range(256)}
    if len(decoded) != 256:
        raise ValueError("State decoding is not bijective.")

    contract_actions = tuple((item["id"], item["key"]) for item in CONTRACT["action"]["actions"])
    profile_actions = tuple((profile.action_id, profile.key) for profile in PROFILES)
    if contract_actions != profile_actions:
        raise ValueError("MDP actions do not match the selected profile codebook.")

    partitions = CONTRACT["partitions"]
    seed_sets = {
        "train": set(partitions["train_seeds"]),
        "validation": set(partitions["validation_seeds"]),
        "test": set(partitions["test_seeds"]),
    }
    if seed_sets["train"] & seed_sets["validation"] or seed_sets["train"] & seed_sets["test"] or seed_sets["validation"] & seed_sets["test"]:
        raise ValueError("Train, validation and test seeds must be disjoint.")

    max_reward = calculate_reward(
        RewardInput(
            success=True,
            action_id=0,
            bottleneck_fidelity=1.0,
            post_decision_imbalance=0.0,
            selected_path_hops=1,
        )
    ).total
    min_reward = calculate_reward(
        RewardInput(success=False, action_id=1, previous_action_id=0)
    ).total
    nominal_bounds = tuple(float(value) for value in CONTRACT["reward"]["nominal_bounds"])
    if not math.isclose(min_reward, nominal_bounds[0]) or not math.isclose(max_reward, nominal_bounds[1]):
        raise ValueError("Reward implementation does not match the frozen nominal bounds.")

    return {
        "mdp_id": CONTRACT["mdp_id"],
        "state_count": 256,
        "action_count": len(PROFILES),
        "state_feature_order": list(state["feature_order"]),
        "reward_bounds": [min_reward, max_reward],
        "partition_seed_counts": {name: len(values) for name, values in seed_sets.items()},
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "profile_codebook_sha256": hashlib.sha256(PROFILE_CONFIG_PATH.read_bytes()).hexdigest(),
        "dqn_allowed_in_p2": CONTRACT["deployment"]["dqn_allowed_in_p2"],
    }


def write_validation(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "contract_validation.json"
    summary_path.write_text(
        json.dumps(validate_contract(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checksum = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    (output_dir / "SHA256SUMS").write_text(
        f"{checksum}  {summary_path.name}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_contract"))
    args = parser.parse_args()
    write_validation(args.output_dir)
    summary = validate_contract()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
