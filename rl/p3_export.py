"""P3 Step 9 deterministic ROM export, model card and exit evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Dict, Mapping, Sequence, Tuple

from rl.dwell_controller import validate_policy


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_Q = REPO_ROOT / "results/rl/p3_policy_freeze/selected_q_table_seed_229.json"
SOURCE_POLICY = REPO_ROOT / "results/rl/p3_policy_freeze/selected_policy_seed_229.json"
PROFILE_CODEBOOK = REPO_ROOT / "rl/config/profile_codebook_v0.json"
UTILITY_GATE = REPO_ROOT / "results/rl/p3_analysis/utility_gate.json"
PAIRED_STATISTICS = REPO_ROOT / "results/rl/p3_analysis/paired_statistics.csv"
FREEZE_RECORD = REPO_ROOT / "results/rl/p3_policy_freeze/freeze_record.json"
REVISION_CONFIG = REPO_ROOT / "rl/config/training_config_v1.yaml"
P2_HARDWARE_AUDIT = REPO_ROOT / "results/rl/p2_hardware_audit/hardware_audit_summary.json"
EXPECTED_INPUT_SHA256 = {
    SOURCE_Q: "a95a0431b565f01dc012211a22bf57eddb87ed21d4e8dd34671c55ace16b411a",
    SOURCE_POLICY: "cb1557680472781c01cab7ce961fdc35d672a0c76fbc0993e3c2599274f8d611",
    PROFILE_CODEBOOK: "a6faf2b8fdb760213fa92ad0f43fa8a3ce812b50e9210a75afac6f5150dd3fa1",
    UTILITY_GATE: "eec76961c8e3c5d5b0c3e6c20b723a31eb452fd3da0fb743b2e89d5479ad0cd0",
    PAIRED_STATISTICS: "e637730417a345167ae4e89be0e9ec7c78310ebf423331c5d7f86d5b2b0d235b",
    FREEZE_RECORD: "f460c5896954d9be53ba445c7ec3304f86237ad01730724f8dc35086b883dfd9",
    REVISION_CONFIG: "c75b68b25e42f348aa2156ba17479676618d738776e7ebf3e3b1feca7f46da0f",
    P2_HARDWARE_AUDIT: "25c8b30d1f41fb9f3aced24d1b93c7cfc88cb830bfb2b7495a4660ee1b660f2b",
}
Q_WORD_BITS = 16
Q_FRACTION_BITS = 7
Q_SCALE = 1 << Q_FRACTION_BITS


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_inputs() -> Tuple[Tuple[Tuple[float, ...], ...], Tuple[int, ...], Mapping[str, object]]:
    for path, expected in EXPECTED_INPUT_SHA256.items():
        if _sha256(path) != expected:
            raise RuntimeError(f"Frozen Step 8 input changed: {path.relative_to(REPO_ROOT)}")
    q_table = tuple(tuple(float(value) for value in row) for row in json.loads(SOURCE_Q.read_text(encoding="utf-8")))
    policy = validate_policy(json.loads(SOURCE_POLICY.read_text(encoding="utf-8")))
    codebook = json.loads(PROFILE_CODEBOOK.read_text(encoding="utf-8"))
    gate = json.loads(UTILITY_GATE.read_text(encoding="utf-8"))
    audit = json.loads(P2_HARDWARE_AUDIT.read_text(encoding="utf-8"))
    if len(q_table) != 256 or any(len(row) != 4 for row in q_table):
        raise RuntimeError("Frozen Q-table shape changed.")
    if gate["decision"] != "PASS_DESCRIPTIVE_INSUFFICIENT_POWER" or not gate["p4_authorized_by_p3_utility_gate"]:
        raise RuntimeError("Step 8 did not authorize the frozen H4 controller.")
    if gate["statistical_superiority_claim_allowed"]:
        raise RuntimeError("Step 8 claim boundary unexpectedly changed.")
    if len(codebook["profiles"]) != 4 or not audit["p2_hardware_coefficient_gate_passed"]:
        raise RuntimeError("Frozen profile hardware audit is not green.")
    return q_table, policy, codebook


def quantize_q(value: float) -> int:
    if not math.isfinite(value):
        raise ValueError("Q value must be finite.")
    scaled = value * Q_SCALE
    integer = math.floor(scaled + 0.5) if scaled >= 0.0 else math.ceil(scaled - 0.5)
    lower, upper = -(1 << (Q_WORD_BITS - 1)), (1 << (Q_WORD_BITS - 1)) - 1
    if not lower <= integer <= upper:
        raise OverflowError("Q value does not fit signed Q8.7 storage.")
    return integer


def q_hex_word(value: float) -> str:
    integer = quantize_q(value)
    return f"{integer & 0xFFFF:04X}"


def decode_q_hex(word: str) -> float:
    raw = int(word, 16)
    signed = raw - (1 << Q_WORD_BITS) if raw & (1 << (Q_WORD_BITS - 1)) else raw
    return signed / Q_SCALE


def encode_profile(profile: Mapping[str, object]) -> int:
    alphas = [float(value) for value in profile["alphas"]]
    numerators = [int(round(value * 2.0)) for value in alphas]
    ratios = [int(value) for value in profile["lambda_tch_hw_ratio"]]
    if any(num / 2.0 != alpha or not 0 <= num < 8 for num, alpha in zip(numerators, alphas)):
        raise ValueError("Profile alpha is not exact unsigned U2.1.")
    if any(not 0 <= value < 4 for value in ratios):
        raise ValueError("Profile ratio does not fit two bits.")
    fields = (*numerators, *ratios)
    widths = (3, 3, 3, 3, 2, 2, 2)
    payload = 0
    for value, width in zip(fields, widths):
        payload = (payload << width) | value
    return payload


def decode_profile(payload: int) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    if not 0 <= payload < (1 << 18):
        raise ValueError("Profile payload must be 18 bits.")
    values = []
    remainder = payload
    for width in reversed((3, 3, 3, 3, 2, 2, 2)):
        values.append(remainder & ((1 << width) - 1))
        remainder >>= width
    ordered = tuple(reversed(values))
    return ordered[:4], ordered[4:]


def _model_card(export_manifest: Mapping[str, object]) -> str:
    return f"""# QFlow-RL Frozen Controller Model Card

## Identity and decision

- Model ID: `qflow_rl_tabular_h4_seed229_dwell3_v1`
- Phase: P3, frozen after the single permitted validation-only revision.
- Selected trainer seed: 229.
- Controller: offline tabular Q-learning policy with a three-decision minimum dwell guard.
- Utility decision: `PASS_DESCRIPTIVE_INSUFFICIENT_POWER`.
- P4 status: authorized for the frozen controller; no policy revision is allowed.

## Inputs and outputs

The policy addresses 256 states formed from four radix-4 features in this order:
minimum key occupancy, bottleneck fidelity, offered request load and utilization
imbalance. Each state returns one of four two-bit profile IDs: Balanced, scarcity
protection, fidelity protection or low-latency.

## Training and selection

Training was offline only. Eight train seeds, four validation seeds and eight
trainer seeds were frozen before learning. Each candidate completed 819,200
transitions. The initial run triggered the one permitted validation-only
revision. Revision v1 used balance weight 4.0 for learning targets and dwell 3
for deployment. Final evaluation retained the original frozen reward. Seed 229
was selected mechanically from seven eligible candidates. Test data was not
used for training, revision or selection.

## Held-out evidence and claim boundary

Across four untouched 512-decision test traces, H4 achieved mean reward
4.677079357437266, zero blocking, fidelity 0.96043583984375, balance utility
0.2649934199372676, mean hops 2.9541015625 and switch rate
0.2328767123287671. H4 reward exceeded H2 and H3 on all four paired seeds.

The paired bootstrap intervals excluded zero, but the exact two-sided paired
permutation p-value was 0.125 and Holm-adjusted p-value was 0.25. Four pairs
cannot attain p<0.05. The permitted claim is therefore a held-out descriptive
improvement and complete utility-gate pass, not statistical superiority.

## Deployment representation

- `policy_rom.mem`: 256 state-major one-hex-digit profile IDs (2 useful bits).
- `q_table.mem`: 1,024 state-major/action-minor signed 16-bit Q8.7 hex words.
- `profile_rom.mem`: four 18-bit payloads stored in five hex digits.
- Profile layout: alpha numerators `[17:15],[14:12],[11:9],[8:6]`, followed by
  Tchebycheff integer ratios `[5:4],[3:2],[1:0]`.
- Q quantization maximum absolute error: {export_manifest['q_quantization']['maximum_absolute_error']}.
- Quantized-Q/policy argmax mismatches: {export_manifest['q_quantization']['policy_argmax_mismatch_count']}.

The policy ROM is the deployed decision artifact. The Q-table is retained for
reproducibility and audit; online or on-chip learning is not claimed.

## Intended use and limitations

The controller is intended for the frozen Ring-6 QFlow research architecture
and subsequent same-board H2/H3/H4 FPGA comparison. It is not validated for
arbitrary network topologies, production QKD operation or safety-critical
autonomous deployment. P3 provides Python/reference-model evidence only. RTL,
synthesis, timing, power and physical-board evidence begin in later phases.

Defense-level feature/reward/dwell diagnostics are available. A broader
retrained ablation matrix and more held-out seeds remain journal-expansion work.
"""


def write_export(output_dir: Path, model_card_path: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    if not model_card_path.is_absolute():
        model_card_path = REPO_ROOT / model_card_path
    output_dir.mkdir(parents=True, exist_ok=True)
    model_card_path.parent.mkdir(parents=True, exist_ok=True)
    q_table, policy, codebook = validate_inputs()
    policy_path = output_dir / "policy_rom.mem"
    q_path = output_dir / "q_table.mem"
    profile_path = output_dir / "profile_rom.mem"
    layout_path = output_dir / "rom_layout.json"
    manifest_path = output_dir / "export_manifest.json"
    policy_path.write_text("\n".join(f"{action:X}" for action in policy) + "\n", encoding="ascii")
    q_words = [q_hex_word(value) for row in q_table for value in row]
    q_path.write_text("\n".join(q_words) + "\n", encoding="ascii")
    profile_payloads = [encode_profile(profile) for profile in codebook["profiles"]]
    profile_path.write_text("\n".join(f"{value:05X}" for value in profile_payloads) + "\n", encoding="ascii")
    decoded_q = tuple(tuple(decode_q_hex(q_words[state * 4 + action]) for action in range(4)) for state in range(256))
    quantized_policy = tuple(min(index for index, value in enumerate(row) if value == max(row)) for row in decoded_q)
    max_error = max(abs(original - quantized) for source_row, decoded_row in zip(q_table, decoded_q) for original, quantized in zip(source_row, decoded_row))
    layout = {
        "schema_version": 1,
        "policy_rom": {"depth": 256, "useful_width_bits": 2, "file_hex_digits_per_word": 1, "address_order": "state_id_0_to_255"},
        "q_table": {"depth": 1024, "word_bits": 16, "fraction_bits": 7, "signed_twos_complement": True, "format_name": "Q8.7", "address_order": "state_major_action_minor"},
        "profile_rom": {"depth": 4, "payload_bits": 18, "file_hex_digits_per_word": 5, "field_order_msb_to_lsb": ["alpha1_u2_1", "alpha2_u2_1", "alpha3_u2_1", "alpha4_u2_1", "lambda1_u2", "lambda2_u2", "lambda3_u2"]},
    }
    layout_path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_9_FROZEN_EXPORT",
        "model_id": "qflow_rl_tabular_h4_seed229_dwell3_v1",
        "selected_trainer_seed": 229,
        "minimum_dwell_decisions": 3,
        "policy_entry_count": len(policy),
        "q_word_count": len(q_words),
        "profile_entry_count": len(profile_payloads),
        "profile_payload_bits_total": 72,
        "source_policy_file_sha256": _sha256(SOURCE_POLICY),
        "source_q_file_sha256": _sha256(SOURCE_Q),
        "source_policy_semantic_sha256": _canonical_sha256(policy),
        "source_q_semantic_sha256": _canonical_sha256(q_table),
        "q_quantization": {"word_bits": 16, "fraction_bits": 7, "maximum_absolute_error": max_error, "policy_argmax_mismatch_count": sum(a != b for a, b in zip(policy, quantized_policy))},
        "policy_roundtrip_match": tuple(int(value, 16) for value in policy_path.read_text().splitlines()) == policy,
        "profile_roundtrip_match": all(decode_profile(payload) == (tuple(int(round(float(value) * 2)) for value in profile["alphas"]), tuple(int(value) for value in profile["lambda_tch_hw_ratio"])) for payload, profile in zip(profile_payloads, codebook["profiles"])),
        "utility_gate_decision": "PASS_DESCRIPTIVE_INSUFFICIENT_POWER",
        "statistical_superiority_claim_allowed": False,
        "policy_revision_allowed": False,
        "online_or_onchip_learning_claimed": False,
        "rtl_or_synthesis_claimed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    model_card_path.write_text(_model_card(manifest), encoding="utf-8")
    source_paths = (
        REPO_ROOT / "rl/p3_export.py", REPO_ROOT / "sim/rl/test_p3_export.py",
        REPO_ROOT / "docs/rl/p3_export_contract.md", REPO_ROOT / "docs/rl/p3_step9_status.md",
        model_card_path,
    )
    result_paths = (policy_path, q_path, profile_path, layout_path, manifest_path)
    labels = [
        "rl/p3_export.py",
        "sim/rl/test_p3_export.py",
        "docs/rl/p3_export_contract.md",
        "docs/rl/p3_step9_status.md",
        "docs/rl/rl_model_card.md",
    ]
    labels.extend(f"results/rl/p3_export/{path.name}" for path in result_paths)
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256(path)}  {label}" for path, label in zip((*source_paths, *result_paths), labels)) + "\n",
        encoding="utf-8",
    )
    return manifest


def _category(path: str) -> str:
    if path.startswith("docs/"):
        return "documentation"
    if path.startswith("sim/"):
        return "test_source"
    if path.startswith("results/"):
        return "generated_evidence"
    if path.startswith("rl/config/"):
        return "configuration"
    return "implementation_source"


def write_exit_gate(output_dir: Path) -> Mapping[str, object]:
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    export_dir = REPO_ROOT / "results/rl/p3_export"
    export_manifest = json.loads((export_dir / "export_manifest.json").read_text(encoding="utf-8"))
    if export_manifest["q_quantization"]["policy_argmax_mismatch_count"] != 0 or not export_manifest["policy_roundtrip_match"] or not export_manifest["profile_roundtrip_match"]:
        raise RuntimeError("ROM export verification is not green.")
    raw = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"], cwd=REPO_ROOT)
    records = [item for item in raw.decode().split("\0") if item]
    paths = []
    for record in records:
        if not record.startswith("?? "):
            raise RuntimeError(f"Unexpected tracked modification: {record}")
        path = record[3:]
        if not path.startswith("results/rl/p3_exit_gate/"):
            paths.append(path)
    paths = sorted(paths)
    if len(paths) != 136:
        raise RuntimeError(f"Expected 136 pre-exit P3 evidence files, found {len(paths)}.")
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "evidence_manifest.csv"
    with evidence_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("category", "path", "bytes", "sha256"))
        for relative in paths:
            path = REPO_ROOT / relative
            writer.writerow((_category(relative), relative, path.stat().st_size, _sha256(path)))
    gate = json.loads(UTILITY_GATE.read_text(encoding="utf-8"))
    exit_gate = {
        "schema_version": 1,
        "phase": "P3",
        "step": "P3_STEP_9_EXIT_GATE",
        "decision": "PASS_PENDING_STEP_10_CHECKPOINT",
        "selected_controller": "h4_revised_seed_229",
        "selected_trainer_seed": 229,
        "utility_gate_decision": gate["decision"],
        "all_predeclared_utility_checks_pass": gate["all_predeclared_utility_checks_pass"],
        "statistical_superiority_claim_allowed": False,
        "claim_boundary": gate["claim_boundary"],
        "p4_authorized_after_step10_checkpoint": True,
        "policy_revision_allowed": False,
        "rom_export": {"policy_entries": 256, "q_words": 1024, "profile_entries": 4, "q_argmax_mismatches": 0, "profile_payload_bits_total": 72},
        "verification": {"p3_tests": 67, "legacy_tests": 26, "applicable_p2_tests": 64, "controlled_file_count_after_exit": 139},
        "evidence_record_count": len(paths),
        "evidence_manifest_sha256": _sha256(evidence_path),
        "export_manifest_sha256": _sha256(export_dir / "export_manifest.json"),
        "export_sha256sums_sha256": _sha256(export_dir / "SHA256SUMS"),
        "model_card_sha256": _sha256(REPO_ROOT / "docs/rl/rl_model_card.md"),
        "test_access_count": 4,
        "new_test_trace_generation_in_step9": 0,
        "additional_training_after_test": False,
        "rtl_synthesis_or_board_work_performed": False,
        "commit_or_push_performed": False,
        "next_required_action": "guarded_step10_verification_commit_and_non_force_push",
    }
    exit_path = output_dir / "exit_gate.json"
    exit_path.write_text(json.dumps(exit_gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "SHA256SUMS").write_text(
        f"{_sha256(evidence_path)}  results/rl/p3_exit_gate/evidence_manifest.csv\n"
        f"{_sha256(exit_path)}  results/rl/p3_exit_gate/exit_gate.json\n",
        encoding="utf-8",
    )
    return exit_gate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--export-dir", type=Path, default=Path("results/rl/p3_export"))
    parser.add_argument("--model-card", type=Path, default=Path("docs/rl/rl_model_card.md"))
    parser.add_argument("--exit-dir", type=Path, default=Path("results/rl/p3_exit_gate"))
    args = parser.parse_args()
    if args.export_only == args.finalize:
        parser.error("Choose exactly one of --export-only or --finalize.")
    result = write_export(args.export_dir, args.model_card) if args.export_only else write_exit_gate(args.exit_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
