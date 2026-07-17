"""Consolidated, reproducible P2 exit-gate validation and evidence manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Mapping, Optional, Tuple

from rl.forced_fixed_regression import FROZEN_H2_SHA256, h2_regression_summary
from rl.mdp_contract import CONTRACT, validate_contract
from rl.profile_codebook import PROFILES


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_MODEL_SHA256 = "82d6935240a05b51ef989c4f55b0de26f630d74dcd52bbc88b352a1860db75e2"
PRIOR_EVIDENCE_DIRS = (
    Path("results/rl/p2_sensitivity"),
    Path("results/rl/p2_contract"),
    Path("results/rl/p2_environment"),
    Path("results/rl/p2_forced_fixed"),
    Path("results/rl/p2_hardware_audit"),
)
FORBIDDEN_P3_PATHS = (
    Path("rl/config/training_config.yaml"),
    Path("results/rl/training_config.yaml"),
    Path("results/rl/learning_curves.csv"),
    Path("results/rl/heldout_results.csv"),
    Path("results/rl/profile_usage.csv"),
    Path("results/rl/policy_rom.mem"),
    Path("results/rl/q_table.mem"),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(relative_path: str) -> Mapping[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def verify_checksum_bundle(relative_dir: Path) -> int:
    directory = REPO_ROOT / relative_dir
    lines = (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Empty checksum bundle: {relative_dir}")
    seen = set()
    for line in lines:
        digest, filename = line.split("  ", 1)
        if filename in seen or "/" in filename or filename == "SHA256SUMS":
            raise ValueError(f"Invalid checksum entry in {relative_dir}: {filename}")
        path = directory / filename
        if not path.is_file() or _sha256(path) != digest:
            raise ValueError(f"Checksum mismatch: {relative_dir / filename}")
        seen.add(filename)
    return len(seen)


def _validate_sources() -> Mapping[str, object]:
    root_hash = _sha256(REPO_ROOT / "reference_model.py")
    tools_hash = _sha256(REPO_ROOT / "tools/reference_model.py")
    if root_hash != REFERENCE_MODEL_SHA256 or tools_hash != REFERENCE_MODEL_SHA256:
        raise ValueError("Reference-model source anchors do not match Step 3.")
    return {
        "root_reference_model_sha256": root_hash,
        "tools_reference_model_sha256": tools_hash,
        "copies_byte_identical": (REPO_ROOT / "reference_model.py").read_bytes()
        == (REPO_ROOT / "tools/reference_model.py").read_bytes(),
    }


def _validate_sensitivity() -> Mapping[str, object]:
    summary = _load_json("results/rl/p2_sensitivity/selection_summary.json")
    selected = summary["selected_profiles"]
    for profile in PROFILES[1:]:
        record = selected[profile.key]
        if (
            int(record["action_id"]) != profile.action_id
            or tuple(record["alphas"]) != profile.alphas
            or tuple(record["lambda_tch"]) != profile.lambda_tch
            or tuple(record["lambda_tch_hw_ratio"]) != profile.lambda_tch_hw_ratio
        ):
            raise ValueError(f"Sensitivity selection does not match codebook profile {profile.key}.")
    return {
        "profile_count": len(PROFILES),
        "adaptive_profiles_selected_by_sensitivity": len(selected),
        "scenario_count": int(summary["protocol"]["scenario_count"]),
    }


def _validate_contract_and_partitions() -> Mapping[str, object]:
    stored = _load_json("results/rl/p2_contract/contract_validation.json")
    current = validate_contract()
    if stored != current:
        raise ValueError("Stored MDP validation no longer matches the current contract.")
    manifest = _load_json("results/rl/p2_environment/trace_manifest.json")
    expected = {
        "train": tuple(int(value) for value in CONTRACT["partitions"]["train_seeds"]),
        "validation": tuple(int(value) for value in CONTRACT["partitions"]["validation_seeds"]),
        "test": tuple(int(value) for value in CONTRACT["partitions"]["test_seeds"]),
    }
    actual = {
        name: tuple(int(item["seed"]) for item in manifest["traces"] if item["partition"] == name)
        for name in expected
    }
    if actual != expected:
        raise ValueError("Trace-manifest seeds do not match the frozen MDP partitions.")
    if len({item["sha256"] for item in manifest["traces"]}) != 16:
        raise ValueError("Frozen partition traces are not hash-unique.")
    manual = manifest["manual_trace"]
    if manual["step_count"] != 8 or manual["success_count"] != 8 or not manual["final_done"]:
        raise ValueError("Manual Ring-6 trace evidence is incomplete.")
    return {
        "state_count": int(stored["state_count"]),
        "action_count": int(stored["action_count"]),
        "episode_length": int(CONTRACT["partitions"]["episode_length"]),
        "partition_seed_counts": stored["partition_seed_counts"],
        "frozen_trace_count": len(manifest["traces"]),
        "manual_trace_steps": int(manual["step_count"]),
        "dqn_allowed_in_p2": bool(stored["dqn_allowed_in_p2"]),
    }


def _validate_forced_fixed() -> Mapping[str, object]:
    stored_h2 = _load_json("results/rl/p2_forced_fixed/h2_regression.json")
    current_h2 = h2_regression_summary()
    if stored_h2 != current_h2:
        raise ValueError("Stored forced-Balanced H2 evidence no longer matches the current model.")
    replay = _load_json("results/rl/p2_forced_fixed/replay_summary.json")
    if (
        not stored_h2["canonical_json_byte_identical"]
        or not stored_h2["route_selection_parity"]
        or stored_h2["forced_balanced_h2_sha256"] != FROZEN_H2_SHA256
        or stored_h2["dynamic_trace_equivalence_claimed"]
    ):
        raise ValueError("Forced-Balanced H2 exit facts failed.")
    if replay["action_clamp"] != {"action_id": 0, "profile": "balanced"}:
        raise ValueError("Forced-fixed replay is not clamped to Balanced.")
    partitions = replay["partitions"]
    if (
        partitions["trace_count"] != 16
        or partitions["step_count"] != 8192
        or not partitions["all_steps_balanced"]
        or replay["training_performed"]
    ):
        raise ValueError("Forced-Balanced replay evidence is incomplete.")
    return {
        "h2_sha256": stored_h2["forced_balanced_h2_sha256"],
        "canonical_json_byte_identical": True,
        "route_selection_parity": True,
        "forced_balanced_trace_count": int(partitions["trace_count"]),
        "forced_balanced_step_count": int(partitions["step_count"]),
        "training_performed": False,
    }


def _validate_hardware() -> Mapping[str, object]:
    summary = _load_json("results/rl/p2_hardware_audit/hardware_audit_summary.json")
    required = {
        "profile_count": 4,
        "profile_rom_payload_bits_each": 18,
        "codebook_rom_payload_bits_total": 72,
        "generic_profile_multiplier_budget": 0,
        "exact_alpha_roundtrip_count": 4,
        "exact_lambda_ratio_count": 4,
        "route_equivalence_checks": 24,
        "route_equivalence_matches": 24,
        "p2_hardware_coefficient_gate_passed": True,
        "rtl_or_synthesis_claimed": False,
    }
    if any(summary.get(key) != value for key, value in required.items()):
        raise ValueError("Hardware coefficient audit does not satisfy the P2 exit gate.")
    return required


def _validate_scope_boundary() -> Mapping[str, object]:
    present = [str(path) for path in FORBIDDEN_P3_PATHS if (REPO_ROOT / path).exists()]
    if present:
        raise ValueError(f"P3 training/deployment artifacts appeared during P2: {present}")
    rtl_root = REPO_ROOT / "rtl/rl"
    rtl_artifacts = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in rtl_root.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    )
    if rtl_artifacts:
        raise ValueError(f"RTL implementation appeared during P2: {rtl_artifacts}")
    return {
        "forbidden_p3_artifacts_present": present,
        "rtl_artifacts_present": rtl_artifacts,
        "training_performed": False,
        "rtl_implemented": False,
        "board_measurement_claimed": False,
    }


def collect_gate_facts() -> Mapping[str, object]:
    checksum_counts = {str(path): verify_checksum_bundle(path) for path in PRIOR_EVIDENCE_DIRS}
    facts = {
        "checksum_bundles": checksum_counts,
        "sources": _validate_sources(),
        "profile_selection": _validate_sensitivity(),
        "mdp_and_partitions": _validate_contract_and_partitions(),
        "forced_fixed": _validate_forced_fixed(),
        "hardware_coefficients": _validate_hardware(),
        "scope_boundary": _validate_scope_boundary(),
    }
    if sum(checksum_counts.values()) != 14:
        raise ValueError("Unexpected number of prior checksummed evidence files.")
    return facts


def _manifest_paths() -> Tuple[Path, ...]:
    paths = {
        Path("reference_model.py"),
        Path("tools/reference_model.py"),
    }
    paths.update(path.relative_to(REPO_ROOT) for path in (REPO_ROOT / "docs/rl").glob("p2_*.md"))
    paths.update(
        path.relative_to(REPO_ROOT)
        for path in (REPO_ROOT / "rl/config").glob("*")
        if path.name != ".gitkeep"
    )
    paths.update(path.relative_to(REPO_ROOT) for path in (REPO_ROOT / "rl").glob("*.py"))
    paths.update(path.relative_to(REPO_ROOT) for path in (REPO_ROOT / "sim/rl").glob("test_p2_*.py"))
    for directory in PRIOR_EVIDENCE_DIRS:
        paths.update(path.relative_to(REPO_ROOT) for path in (REPO_ROOT / directory).glob("*"))
    files = tuple(sorted(path for path in paths if (REPO_ROOT / path).is_file()))
    if any("__pycache__" in path.parts for path in files):
        raise ValueError("Python cache entered the P2 evidence manifest.")
    return files


def evidence_manifest_records() -> Tuple[Mapping[str, object], ...]:
    records = []
    for relative in _manifest_paths():
        path = REPO_ROOT / relative
        if relative.parts[0] == "docs":
            category = "documentation"
        elif relative.parts[0] == "results":
            category = "generated_evidence"
        elif relative.parts[0] == "sim":
            category = "test_source"
        elif relative.parts[0] == "rl" and relative.parts[1] == "config":
            category = "frozen_configuration"
        else:
            category = "implementation_source"
        records.append(
            {
                "category": category,
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return tuple(records)


def write_exit_gate_evidence(
    output_dir: Path,
    *,
    legacy_test_count: int,
    p2_test_count: int,
    tests_passed: bool,
    facts: Optional[Mapping[str, object]] = None,
) -> Mapping[str, object]:
    if legacy_test_count != 26 or p2_test_count != 72 or not tests_passed:
        raise ValueError("P2 exit evidence requires successful 26-test legacy and 72-test P2 runs.")
    if facts is None:
        facts = collect_gate_facts()
    output_dir.mkdir(parents=True, exist_ok=True)
    records = evidence_manifest_records()
    manifest_path = output_dir / "evidence_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("category", "path", "bytes", "sha256"))
        for item in records:
            writer.writerow((item["category"], item["path"], item["bytes"], item["sha256"]))

    criteria = (
        {
            "criterion": "forced_fixed_reproduces_h2",
            "status": "PASS",
            "evidence": "results/rl/p2_forced_fixed/h2_regression.json",
        },
        {
            "criterion": "state_action_reward_and_environment_tests",
            "status": "PASS",
            "evidence": "72 P2 unit tests plus 26 legacy tests",
        },
        {
            "criterion": "partitions_and_seeds_frozen",
            "status": "PASS",
            "evidence": "results/rl/p2_environment/trace_manifest.json",
        },
        {
            "criterion": "profile_multipliers_hardware_implementable",
            "status": "PASS",
            "evidence": "results/rl/p2_hardware_audit/hardware_audit_summary.json",
        },
    )
    summary = {
        "schema_version": 1,
        "phase": "P2",
        "status": "PASS",
        "criteria": criteria,
        "tests": {
            "legacy_test_count": legacy_test_count,
            "p2_test_count": p2_test_count,
            "all_passed": tests_passed,
        },
        "facts": facts,
        "evidence_manifest": {
            "record_count": len(records),
            "sha256": _sha256(manifest_path),
        },
        "checkpoint_commit_pending": True,
        "p3_authorized_before_step10": False,
    }
    summary_path = output_dir / "exit_gate.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = (manifest_path, summary_path)
    lines = [f"{_sha256(path)}  {path.name}" for path in files]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_exit_gate"))
    parser.add_argument("--legacy-test-count", type=int, required=True)
    parser.add_argument("--p2-test-count", type=int, required=True)
    parser.add_argument("--tests-passed", action="store_true")
    args = parser.parse_args()
    summary = write_exit_gate_evidence(
        args.output_dir,
        legacy_test_count=args.legacy_test_count,
        p2_test_count=args.p2_test_count,
        tests_passed=args.tests_passed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
