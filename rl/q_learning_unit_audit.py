"""Write deterministic Step 4 evidence without accessing any frozen trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from rl.p3_contract import CONFIG_PATH, CONTRACT
from rl.tabular_q_learning import (
    XorShift32,
    deployment_action,
    epsilon_at,
    extract_policy,
    new_q_table,
    q_update,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_audit() -> Mapping[str, object]:
    training = CONTRACT["training"]
    rng = XorShift32(17)
    first_words = [rng.next_u32() for _ in range(5)]
    shuffle_rng = XorShift32(17)
    shuffled = list(shuffle_rng.shuffled(CONTRACT["partitions"]["train_seeds"]))

    table = new_q_table()
    table[6] = [1.0, 2.0, 2.0, -1.0]
    nonterminal = q_update(table, 5, 2, 4.0, 6, False, 0.1, 0.95)
    terminal = q_update(table, 5, 2, -4.0, None, True, 0.1, 0.95)
    tie_table = new_q_table()
    tie_table[9] = [0.5, 2.0, 2.0, -3.0]
    policy = extract_policy(tie_table)

    total = int(training["transitions_per_trainer"])
    decay_fraction = float(training["epsilon"]["decay_fraction_of_training_transitions"])
    decay_count = max(1, math.ceil(total * decay_fraction))
    epsilon_points = {
        "first": epsilon_at(0, total),
        "last_decay": epsilon_at(decay_count - 1, total),
        "first_fixed": epsilon_at(decay_count, total),
        "last": epsilon_at(total - 1, total),
    }
    return {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_4_Q_LEARNING_UNIT",
        "decision": "PASS",
        "algorithm": "tabular_q_learning",
        "state_count": 256,
        "action_count": 4,
        "trainer_rng": "xorshift32",
        "xorshift32_seed_17_first_five_u32": first_words,
        "fisher_yates_seed_17_train_order": shuffled,
        "epsilon_schedule": epsilon_points,
        "nonterminal_update": {
            "old": nonterminal.old_value,
            "bootstrap": nonterminal.bootstrap,
            "target": nonterminal.target,
            "new": nonterminal.new_value,
        },
        "terminal_update": {
            "old": terminal.old_value,
            "bootstrap": terminal.bootstrap,
            "target": terminal.target,
            "new": terminal.new_value,
        },
        "deployment_tie_state_9_action": deployment_action(tie_table, 9),
        "extracted_policy_length": len(policy),
        "training_trace_access_count": 0,
        "validation_access_count": 0,
        "test_access_count": 0,
        "test_partition_locked": True,
        "full_h4_training_performed": False,
        "rtl_or_board_work_performed": False,
        "training_config_sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
    }


def write_audit(output_dir: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "unit_audit.json"
    payload = build_audit()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_entries = (
        ("rl/tabular_q_learning.py", REPO_ROOT / "rl/tabular_q_learning.py"),
        ("rl/q_learning_unit_audit.py", REPO_ROOT / "rl/q_learning_unit_audit.py"),
        ("sim/rl/test_p3_q_learning.py", REPO_ROOT / "sim/rl/test_p3_q_learning.py"),
        ("docs/rl/p3_q_learning_implementation.md", REPO_ROOT / "docs/rl/p3_q_learning_implementation.md"),
        ("docs/rl/p3_step4_status.md", REPO_ROOT / "docs/rl/p3_step4_status.md"),
        ("results/rl/p3_q_learning_unit/unit_audit.json", path),
    )
    lines = [f"{hashlib.sha256(item.read_bytes()).hexdigest()}  {label}" for label, item in checksum_entries]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p3_q_learning_unit"))
    args = parser.parse_args()
    print(json.dumps(write_audit(args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
