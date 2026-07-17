"""Normalized Tchebycheff route selection for QFlow-RL profiles."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Tuple


NORMALIZATION_EPSILON = 2.0 ** -16


@dataclass(frozen=True)
class PathObjectives:
    path: Tuple[int, ...]
    path_cost: float
    bottleneck_fidelity: float
    utilization_imbalance: float


@dataclass(frozen=True)
class ScoredPath:
    objectives: PathObjectives
    normalized: Tuple[float, float, float]
    tchebycheff_score: float


@dataclass(frozen=True)
class RouteSelection:
    selected: ScoredPath
    ranked: Tuple[ScoredPath, ...]

    @property
    def score_margin(self) -> float:
        if len(self.ranked) < 2:
            return math.inf
        return self.ranked[1].tchebycheff_score - self.ranked[0].tchebycheff_score


def _validate_lambda(lambda_tch: Tuple[float, float, float]) -> None:
    if len(lambda_tch) != 3:
        raise ValueError("lambda_TCH must contain exactly three values.")
    if any(not math.isfinite(value) or value <= 0.0 for value in lambda_tch):
        raise ValueError("lambda_TCH values must be positive and finite.")
    if not math.isclose(sum(lambda_tch), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("lambda_TCH values must sum to one.")


def select_route(
    candidates: Iterable[PathObjectives],
    lambda_tch: Tuple[float, float, float],
) -> RouteSelection:
    """Select one route using normalized minimization-oriented objectives."""
    _validate_lambda(lambda_tch)
    records = tuple(candidates)
    if not records:
        raise ValueError("At least one candidate route is required.")

    for record in records:
        if len(record.path) < 2 or len(set(record.path)) != len(record.path):
            raise ValueError(f"Invalid simple path: {record.path}")
        if not math.isfinite(record.path_cost) or record.path_cost < 0.0:
            raise ValueError("Path cost must be finite and non-negative.")
        if not 0.0 < record.bottleneck_fidelity <= 1.0:
            raise ValueError("Bottleneck fidelity must be in (0, 1].")
        if not math.isfinite(record.utilization_imbalance) or record.utilization_imbalance < 0.0:
            raise ValueError("Utilization imbalance must be finite and non-negative.")

    minimization_vectors = tuple(
        (
            record.path_cost,
            1.0 - record.bottleneck_fidelity,
            record.utilization_imbalance,
        )
        for record in records
    )
    minima = tuple(min(vector[index] for vector in minimization_vectors) for index in range(3))
    maxima = tuple(max(vector[index] for vector in minimization_vectors) for index in range(3))

    scored = []
    for record, vector in zip(records, minimization_vectors):
        normalized = tuple(
            0.0
            if math.isclose(maxima[index], minima[index], rel_tol=0.0, abs_tol=1e-15)
            else (vector[index] - minima[index])
            / (maxima[index] - minima[index] + NORMALIZATION_EPSILON)
            for index in range(3)
        )
        score = max(lambda_tch[index] * normalized[index] for index in range(3))
        scored.append(ScoredPath(record, normalized, score))

    ranked = tuple(
        sorted(
            scored,
            key=lambda item: (
                item.tchebycheff_score,
                item.objectives.path_cost,
                len(item.objectives.path) - 1,
                item.objectives.path,
            ),
        )
    )
    return RouteSelection(selected=ranked[0], ranked=ranked)
