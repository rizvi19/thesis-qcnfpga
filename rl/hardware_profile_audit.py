"""Exact P2 shift/add audit for the selected four-profile codebook."""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple

from rl.h2_profile_adapter import run_h2_action
from rl.profile_codebook import PROFILES, Profile
from rl.route_selector import NORMALIZATION_EPSILON, PathObjectives, select_route
from rl.sensitivity_sweep import SCENARIOS, evaluate_path


ALPHA_FRACTION_BITS = 1
ALPHA_NUMERATOR_BITS = 3
LAMBDA_RATIO_BITS = 2
PROFILE_ROM_PAYLOAD_BITS = 4 * ALPHA_NUMERATOR_BITS + 3 * LAMBDA_RATIO_BITS
CODEBOOK_ROM_PAYLOAD_BITS = len(PROFILES) * PROFILE_ROM_PAYLOAD_BITS
MAX_ALPHA_SHIFT_ADD_TERMS = 2
MAX_LAMBDA_SHIFT_ADD_TERMS = 1


def shift_positions(unsigned_value: int) -> Tuple[int, ...]:
    if isinstance(unsigned_value, bool) or not isinstance(unsigned_value, int) or unsigned_value <= 0:
        raise ValueError("Shift/add numerator must be a positive integer.")
    return tuple(index for index in range(unsigned_value.bit_length()) if unsigned_value & (1 << index))


def encode_alpha(value: float) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0:
        raise ValueError("Alpha must be positive and finite.")
    scaled = Fraction(str(value)) * (1 << ALPHA_FRACTION_BITS)
    if scaled.denominator != 1:
        raise ValueError(f"Alpha {value} is not exactly representable with one fractional bit.")
    numerator = scaled.numerator
    if numerator >= 1 << ALPHA_NUMERATOR_BITS:
        raise ValueError(f"Alpha {value} exceeds the 3-bit numerator field.")
    return numerator


def decode_alpha(numerator: int) -> Fraction:
    if isinstance(numerator, bool) or not isinstance(numerator, int) or not 0 < numerator < 1 << ALPHA_NUMERATOR_BITS:
        raise ValueError("Alpha numerator is outside the 3-bit unsigned field.")
    return Fraction(numerator, 1 << ALPHA_FRACTION_BITS)


def normalized_ratio(ratio: Tuple[int, int, int]) -> Tuple[Fraction, Fraction, Fraction]:
    if len(ratio) != 3 or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in ratio):
        raise ValueError("lambda_TCH hardware ratio must contain three positive integers.")
    if any(value >= 1 << LAMBDA_RATIO_BITS for value in ratio):
        raise ValueError("lambda_TCH ratio exceeds its 2-bit field.")
    common = math.gcd(math.gcd(ratio[0], ratio[1]), ratio[2])
    if common != 1:
        raise ValueError("lambda_TCH hardware ratio must be primitive.")
    total = sum(ratio)
    return tuple(Fraction(value, total) for value in ratio)


def _profile_encoding(profile: Profile) -> Mapping[str, object]:
    alpha_numerators = tuple(encode_alpha(value) for value in profile.alphas)
    alpha_terms = tuple(shift_positions(value) for value in alpha_numerators)
    ratio = profile.lambda_tch_hw_ratio
    ratio_terms = tuple(shift_positions(value) for value in ratio)
    exact_lambda = tuple(Fraction(str(value)) for value in profile.lambda_tch)
    expected_lambda = normalized_ratio(ratio)
    alpha_exact = all(
        decode_alpha(numerator) == Fraction(str(value))
        for numerator, value in zip(alpha_numerators, profile.alphas)
    )
    lambda_exact = exact_lambda == expected_lambda
    alpha_term_bound = max(len(terms) for terms in alpha_terms) <= MAX_ALPHA_SHIFT_ADD_TERMS
    lambda_term_bound = max(len(terms) for terms in ratio_terms) <= MAX_LAMBDA_SHIFT_ADD_TERMS
    passed = alpha_exact and lambda_exact and alpha_term_bound and lambda_term_bound
    return {
        "action_id": profile.action_id,
        "profile": profile.key,
        "alphas": profile.alphas,
        "alpha_numerators_q1": alpha_numerators,
        "alpha_shift_positions": alpha_terms,
        "lambda_tch": profile.lambda_tch,
        "lambda_ratio": ratio,
        "lambda_shift_positions": ratio_terms,
        "alpha_exact": alpha_exact,
        "lambda_ratio_exact": lambda_exact,
        "max_alpha_add_terms": max(len(terms) for terms in alpha_terms),
        "max_lambda_add_terms": max(len(terms) for terms in ratio_terms),
        "profile_rom_payload_bits": PROFILE_ROM_PAYLOAD_BITS,
        "generic_profile_multipliers": 0,
        "passed": passed,
    }


def integer_ratio_selected_path(
    candidates: Iterable[PathObjectives],
    ratio: Tuple[int, int, int],
) -> Tuple[int, ...]:
    """Select with unnormalized integer weights; a common scale cannot change argmin."""
    records = tuple(candidates)
    normalized_ratio(ratio)
    select_route(records, tuple(float(value) for value in normalized_ratio(ratio)))
    minimization = tuple(
        (
            item.path_cost,
            1.0 - item.bottleneck_fidelity,
            item.utilization_imbalance,
        )
        for item in records
    )
    minima = tuple(min(vector[index] for vector in minimization) for index in range(3))
    maxima = tuple(max(vector[index] for vector in minimization) for index in range(3))
    scored = []
    for item, vector in zip(records, minimization):
        normalized = tuple(
            0.0
            if math.isclose(maxima[index], minima[index], rel_tol=0.0, abs_tol=1e-15)
            else (vector[index] - minima[index])
            / (maxima[index] - minima[index] + NORMALIZATION_EPSILON)
            for index in range(3)
        )
        score = max(ratio[index] * normalized[index] for index in range(3))
        scored.append((score, item.path_cost, len(item.path) - 1, item.path))
    return min(scored)[3]


def _h2_candidates(profile: Profile) -> Tuple[PathObjectives, ...]:
    result = run_h2_action(profile.action_id, verbose=False)
    return tuple(
        PathObjectives(
            path=tuple(record["path"]),
            path_cost=float(record["latency"]),
            bottleneck_fidelity=float(record["bottleneck_fidelity"]),
            utilization_imbalance=float(record["load_balance"]),
        )
        for record in result["pareto_front"]
    )


def route_equivalence_rows() -> Tuple[Mapping[str, object], ...]:
    rows = []
    for profile in PROFILES:
        for scenario in SCENARIOS:
            candidates = tuple(evaluate_path(profile, path_case) for path_case in scenario.paths)
            float_path = select_route(candidates, profile.lambda_tch).selected.objectives.path
            ratio_path = integer_ratio_selected_path(candidates, profile.lambda_tch_hw_ratio)
            rows.append(
                {
                    "source": "controlled_sensitivity",
                    "case": scenario.name,
                    "action_id": profile.action_id,
                    "profile": profile.key,
                    "float_path": float_path,
                    "integer_ratio_path": ratio_path,
                    "match": float_path == ratio_path,
                }
            )
        candidates = _h2_candidates(profile)
        float_path = select_route(candidates, profile.lambda_tch).selected.objectives.path
        ratio_path = integer_ratio_selected_path(candidates, profile.lambda_tch_hw_ratio)
        rows.append(
            {
                "source": "canonical_h2_pareto",
                "case": "ring6_seed42",
                "action_id": profile.action_id,
                "profile": profile.key,
                "float_path": float_path,
                "integer_ratio_path": ratio_path,
                "match": float_path == ratio_path,
            }
        )
    return tuple(rows)


def audit_summary(
    routes: Optional[Tuple[Mapping[str, object], ...]] = None,
) -> Mapping[str, object]:
    encodings = tuple(_profile_encoding(profile) for profile in PROFILES)
    if routes is None:
        routes = route_equivalence_rows()
    passed = all(item["passed"] for item in encodings) and all(item["match"] for item in routes)
    summary = {
        "schema_version": 1,
        "profile_count": len(PROFILES),
        "alpha_format": {
            "unsigned_numerator_bits": ALPHA_NUMERATOR_BITS,
            "implicit_fraction_bits": ALPHA_FRACTION_BITS,
            "maximum_encoded_numerator": max(max(item["alpha_numerators_q1"]) for item in encodings),
            "maximum_shift_add_terms": max(item["max_alpha_add_terms"] for item in encodings),
        },
        "lambda_ratio_format": {
            "unsigned_ratio_bits": LAMBDA_RATIO_BITS,
            "maximum_encoded_ratio": max(max(item["lambda_ratio"]) for item in encodings),
            "maximum_shift_add_terms": max(item["max_lambda_add_terms"] for item in encodings),
            "common_scale_removed_per_profile": True,
        },
        "profile_rom_payload_bits_each": PROFILE_ROM_PAYLOAD_BITS,
        "codebook_rom_payload_bits_total": CODEBOOK_ROM_PAYLOAD_BITS,
        "generic_profile_multiplier_budget": 0,
        "exact_alpha_roundtrip_count": sum(item["alpha_exact"] for item in encodings),
        "exact_lambda_ratio_count": sum(item["lambda_ratio_exact"] for item in encodings),
        "route_equivalence_checks": len(routes),
        "route_equivalence_matches": sum(item["match"] for item in routes),
        "p2_hardware_coefficient_gate_passed": passed,
        "rtl_or_synthesis_claimed": False,
    }
    if not passed:
        raise RuntimeError("P2 hardware coefficient audit failed.")
    return summary


def _json_value(value: object) -> str:
    return json.dumps(value, separators=(",", ":"))


def write_hardware_audit(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    profiles_path = output_dir / "profile_encoding_audit.csv"
    with profiles_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            (
                "action_id", "profile", "alphas", "alpha_numerators_q1", "alpha_shift_positions",
                "lambda_tch", "lambda_ratio", "lambda_shift_positions", "alpha_exact",
                "lambda_ratio_exact", "max_alpha_add_terms", "max_lambda_add_terms",
                "profile_rom_payload_bits", "generic_profile_multipliers", "passed",
            )
        )
        for profile in PROFILES:
            item = _profile_encoding(profile)
            writer.writerow(
                (
                    item["action_id"], item["profile"], _json_value(item["alphas"]),
                    _json_value(item["alpha_numerators_q1"]), _json_value(item["alpha_shift_positions"]),
                    _json_value(item["lambda_tch"]), _json_value(item["lambda_ratio"]),
                    _json_value(item["lambda_shift_positions"]), item["alpha_exact"],
                    item["lambda_ratio_exact"], item["max_alpha_add_terms"], item["max_lambda_add_terms"],
                    item["profile_rom_payload_bits"], item["generic_profile_multipliers"], item["passed"],
                )
            )

    routes = route_equivalence_rows()
    routes_path = output_dir / "route_equivalence.csv"
    with routes_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("source", "case", "action_id", "profile", "float_path", "integer_ratio_path", "match"))
        for item in routes:
            writer.writerow(
                (
                    item["source"], item["case"], item["action_id"], item["profile"],
                    _json_value(item["float_path"]), _json_value(item["integer_ratio_path"]), item["match"],
                )
            )

    summary_path = output_dir / "hardware_audit_summary.json"
    summary_path.write_text(json.dumps(audit_summary(routes), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files = (profiles_path, routes_path, summary_path)
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
    (output_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_hardware_audit"))
    args = parser.parse_args()
    write_hardware_audit(args.output_dir)
    print((args.output_dir / "hardware_audit_summary.json").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
