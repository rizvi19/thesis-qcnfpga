"""Validation and evidence writer for the frozen P3 training contract."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Dict, Mapping, Sequence, Tuple

from rl.mdp_contract import CONTRACT as P2_CONTRACT, decode_state_id


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "rl" / "config" / "training_config.yaml"
SEED_MANIFEST_PATH = REPO_ROOT / "rl" / "config" / "seed_manifest.csv"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path = CONFIG_PATH) -> Dict[str, object]:
    """Load the JSON-compatible YAML contract with the standard library."""
    return json.loads(path.read_text(encoding="utf-8"))


CONTRACT = load_contract()


def h3_action(state_id: int) -> int:
    """Apply the frozen H3 first-match threshold rules."""
    key_bin, fidelity_bin, load_bin, imbalance_bin = decode_state_id(state_id)
    values = {
        "min_key_occupancy_bin": key_bin,
        "bottleneck_fidelity_bin": fidelity_bin,
        "offered_request_load_bin": load_bin,
        "utilization_imbalance_bin": imbalance_bin,
    }
    h3 = CONTRACT["controller_matrix"]["h3"]
    rules = sorted(h3["priority_rules"], key=lambda item: item["priority"])
    for rule in rules:
        if all(values[name] in accepted for name, accepted in rule["all"].items()):
            return int(rule["action_id"])
    return int(h3["default_action_id"])


def _seed_rows() -> Sequence[Mapping[str, str]]:
    with SEED_MANIFEST_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_contract() -> Mapping[str, object]:
    config = CONTRACT
    base = config["base"]
    mdp_path = REPO_ROOT / base["mdp_contract_path"]
    profile_path = REPO_ROOT / base["profile_codebook_path"]
    if _sha256(mdp_path) != base["mdp_contract_sha256"]:
        raise ValueError("P2 MDP contract checksum changed.")
    if _sha256(profile_path) != base["profile_codebook_sha256"]:
        raise ValueError("P2 profile codebook checksum changed.")

    partitions = config["partitions"]
    p2_partitions = P2_CONTRACT["partitions"]
    expected_partitions = {
        "train": tuple(p2_partitions["train_seeds"]),
        "validation": tuple(p2_partitions["validation_seeds"]),
        "test": tuple(p2_partitions["test_seeds"]),
    }
    actual_partitions = {
        "train": tuple(partitions["train_seeds"]),
        "validation": tuple(partitions["validation_seeds"]),
        "test": tuple(partitions["test_seeds"]),
    }
    if actual_partitions != expected_partitions:
        raise ValueError("P3 environment partitions differ from frozen P2.")
    seed_sets = {name: set(values) for name, values in actual_partitions.items()}
    if any(seed_sets[a] & seed_sets[b] for a, b in (("train", "validation"), ("train", "test"), ("validation", "test"))):
        raise ValueError("Environment partitions are not disjoint.")

    training = config["training"]
    if training["learning_rate_alpha"] != 0.1 or training["discount_gamma"] != 0.95:
        raise ValueError("Unexpected Q-learning alpha or gamma.")
    if training["epochs"] != 200 or training["episodes_per_epoch"] != 8:
        raise ValueError("Unexpected fixed training budget.")
    expected_transitions = training["epochs"] * training["episodes_per_epoch"] * partitions["episode_length"]
    if training["transitions_per_trainer"] != expected_transitions:
        raise ValueError("Transitions-per-trainer does not match the fixed budget.")
    if training["early_stopping"]["enabled"] or training["hyperparameter_sweep_allowed"]:
        raise ValueError("Early stopping and hyperparameter sweeps must remain disabled.")
    trainer_seeds = tuple(training["trainer_seeds"])
    if len(trainer_seeds) != 8 or len(set(trainer_seeds)) != 8:
        raise ValueError("Exactly eight unique trainer RNG seeds are required.")

    controller_matrix = config["controller_matrix"]
    if controller_matrix["h2"]["action_id"] != 0:
        raise ValueError("H2 must remain forced Balanced.")
    if controller_matrix["h4"]["state_count"] != 256 or controller_matrix["h4"]["action_count"] != 4:
        raise ValueError("H4 must remain a 256 by 4 tabular controller.")
    if controller_matrix["h4"]["on_chip_learning"]:
        raise ValueError("P3 cannot claim on-chip learning.")
    distribution = {action: 0 for action in range(4)}
    for state_id in range(256):
        action = h3_action(state_id)
        if action not in distribution:
            raise ValueError("H3 produced an invalid action.")
        distribution[action] += 1
    if any(count == 0 for count in distribution.values()):
        raise ValueError("H3 rule table does not exercise every frozen profile.")

    if not config["test_lock"]["locked"] or partitions["test_access"] != "locked_until_policy_freeze":
        raise ValueError("Test partition must remain locked.")
    if config["test_lock"]["access_count_before_freeze"] != 0:
        raise ValueError("Pre-freeze test access count must be zero.")
    firewall = config["scope_firewall"]
    if firewall["dqn_allowed"] or firewall["eight_action_training_allowed_initially"] or firewall["p4_rtl_allowed"]:
        raise ValueError("P3 scope firewall is open.")

    rows = _seed_rows()
    environment_rows = [row for row in rows if row["seed_type"] == "environment"]
    trainer_rows = [row for row in rows if row["seed_type"] == "trainer_rng"]
    statistics_rows = [row for row in rows if row["seed_type"] == "statistics"]
    for partition, seeds in actual_partitions.items():
        recorded = tuple(int(row["seed"]) for row in environment_rows if row["partition"] == partition)
        if recorded != seeds:
            raise ValueError(f"Seed manifest mismatch for {partition}.")
    if tuple(int(row["seed"]) for row in trainer_rows) != trainer_seeds:
        raise ValueError("Trainer seed manifest mismatch.")
    if tuple(int(row["seed"]) for row in statistics_rows) != (config["statistics"]["bootstrap"]["rng_seed"],):
        raise ValueError("Statistical RNG seed manifest mismatch.")
    test_rows = [row for row in environment_rows if row["partition"] == "test"]
    if not all(row["locked_before_policy_freeze"] == "true" for row in test_rows):
        raise ValueError("Every test seed must be explicitly locked.")

    gate = config["utility_gate"]
    if gate["blocking_noninferiority_margin_absolute"] != 0.005:
        raise ValueError("Blocking margin must be 0.005 absolute.")
    if gate["adaptation"]["minimum_distinct_profiles"] != 2:
        raise ValueError("Meaningful adaptation requires at least two profiles.")
    if gate["maximum_switch_rate"] != 0.25:
        raise ValueError("Unexpected switching ceiling.")

    return {
        "action_count": 4,
        "contract_id": config["contract_id"],
        "decision": "PASS",
        "environment_seed_counts": {name: len(values) for name, values in actual_partitions.items()},
        "h3_action_distribution_over_256_states": {str(key): value for key, value in distribution.items()},
        "h4_training_performed": False,
        "p4_authorized": False,
        "p4_rtl_present": False,
        "schema_version": 1,
        "state_count": 256,
        "statistics_seed": config["statistics"]["bootstrap"]["rng_seed"],
        "step": "P3_STEP_2_CONTRACT_FREEZE",
        "test_access_count": 0,
        "test_partition_locked": True,
        "trainer_seed_count": len(trainer_seeds),
        "transitions_per_trainer": expected_transitions,
        "training_config_sha256": _sha256(CONFIG_PATH),
        "seed_manifest_sha256": _sha256(SEED_MANIFEST_PATH),
        "p2_mdp_sha256": _sha256(mdp_path),
        "p2_profile_codebook_sha256": _sha256(profile_path),
    }


def write_validation(output_dir: Path) -> None:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "contract_validation.json"
    summary_path.write_text(json.dumps(validate_contract(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts = (
        REPO_ROOT / "rl/config/training_config.yaml",
        REPO_ROOT / "rl/config/seed_manifest.csv",
        REPO_ROOT / "rl/p3_contract.py",
        REPO_ROOT / "sim/rl/test_p3_contract.py",
        REPO_ROOT / "docs/rl/p3_experiment_contract.md",
        REPO_ROOT / "docs/rl/p3_test_partition_lock.md",
        REPO_ROOT / "docs/rl/p3_step2_status.md",
        summary_path,
    )
    lines = [f"{_sha256(path)}  {path.relative_to(REPO_ROOT)}" for path in artifacts]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "results/rl/p3_contract")
    args = parser.parse_args()
    write_validation(args.output_dir)
    print(json.dumps(validate_contract(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
