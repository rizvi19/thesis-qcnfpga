"""Apply a QFlow-RL profile to the existing deterministic H2 model."""

from __future__ import annotations

from typing import Any, Dict

import reference_model

from rl.profile_codebook import Profile, profile_by_action
from rl.route_selector import PathObjectives, RouteSelection, select_route


def run_h2_profile(
    profile: Profile,
    *,
    seed: int = 42,
    sim_duration_s: float = 0.5,
    tick_dt_s: float = 0.001,
    f_min: float = 0.9,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run H2 with only alpha and lambda_TCH selected by the profile."""
    return reference_model.run_ring6_experiment(
        seed=seed,
        sim_duration_s=sim_duration_s,
        tick_dt_s=tick_dt_s,
        f_min=f_min,
        verbose=verbose,
        alphas=profile.alphas,
        obj_weights=profile.lambda_tch,
    )


def run_h2_action(action_id: int, **kwargs: Any) -> Dict[str, Any]:
    return run_h2_profile(profile_by_action(action_id), **kwargs)


def select_h2_route(result: Dict[str, Any], profile: Profile) -> RouteSelection:
    """Select one route from an H2 Pareto front using the profile's lambda_TCH."""
    candidates = tuple(
        PathObjectives(
            path=tuple(record["path"]),
            path_cost=float(record["latency"]),
            bottleneck_fidelity=float(record["bottleneck_fidelity"]),
            utilization_imbalance=float(record["load_balance"]),
        )
        for record in result["pareto_front"]
    )
    return select_route(candidates, profile.lambda_tch)
