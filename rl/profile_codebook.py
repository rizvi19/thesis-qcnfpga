"""Validated access to the four-action QFlow-RL profile codebook."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Tuple


CONFIG_PATH = Path(__file__).resolve().parent / "config" / "profile_codebook_v0.json"
BALANCED_ACTION_ID = 0


@dataclass(frozen=True)
class Profile:
    action_id: int
    key: str
    name: str
    status: str
    intent: str
    alphas: Tuple[float, float, float, float]
    lambda_tch: Tuple[float, float, float]
    lambda_tch_hw_ratio: Tuple[int, int, int]


def _positive_finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) and value > 0.0 for value in values)


def _load_profiles() -> Tuple[Profile, ...]:
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    records = raw["profiles"]
    profiles = tuple(
        Profile(
            action_id=int(record["action_id"]),
            key=str(record["key"]),
            name=str(record["name"]),
            status=str(record["status"]),
            intent=str(record["intent"]),
            alphas=tuple(float(value) for value in record["alphas"]),
            lambda_tch=tuple(float(value) for value in record["lambda_tch"]),
            lambda_tch_hw_ratio=tuple(int(value) for value in record["lambda_tch_hw_ratio"]),
        )
        for record in records
    )

    if len(profiles) != 4:
        raise ValueError("P2 starts with exactly four actions.")
    if tuple(profile.action_id for profile in profiles) != (0, 1, 2, 3):
        raise ValueError("Profile action IDs must be contiguous 0..3.")
    if len({profile.key for profile in profiles}) != 4:
        raise ValueError("Profile keys must be unique.")

    for profile in profiles:
        if len(profile.alphas) != 4 or not _positive_finite(profile.alphas):
            raise ValueError(f"Invalid alpha vector for {profile.key}.")
        if len(profile.lambda_tch) != 3 or not _positive_finite(profile.lambda_tch):
            raise ValueError(f"Invalid lambda_TCH vector for {profile.key}.")
        if not math.isclose(sum(profile.lambda_tch), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"lambda_TCH must sum to one for {profile.key}.")
        if len(profile.lambda_tch_hw_ratio) != 3 or any(value <= 0 for value in profile.lambda_tch_hw_ratio):
            raise ValueError(f"Invalid hardware ratio for {profile.key}.")

    balanced = profiles[BALANCED_ACTION_ID]
    if balanced.alphas != (1.0, 1.5, 0.5, 2.0):
        raise ValueError("Balanced alpha vector must remain the H2 anchor.")
    if balanced.lambda_tch != (0.4, 0.4, 0.2):
        raise ValueError("Balanced lambda_TCH vector must remain the H2 anchor.")

    return profiles


PROFILES = _load_profiles()


def profile_by_action(action_id: int) -> Profile:
    if isinstance(action_id, bool) or not isinstance(action_id, int):
        raise ValueError("Action ID must be an integer in 0..3.")
    if not 0 <= action_id < len(PROFILES):
        raise ValueError(f"Action {action_id} is outside 0..{len(PROFILES) - 1}.")
    return PROFILES[action_id]
