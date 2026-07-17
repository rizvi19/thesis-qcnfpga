"""Deterministic H2 and H3 controllers for the frozen P3 comparison."""

from __future__ import annotations

from typing import Callable, Dict

from rl.mdp_contract import decode_state_id
from rl.p3_contract import h3_action


H2_ID = "h2_forced_fixed"
H3_ID = "h3_threshold"


def h2_action(state_id: int) -> int:
    """Return the frozen Balanced profile after validating the state ID."""
    decode_state_id(state_id)
    return 0


CONTROLLERS: Dict[str, Callable[[int], int]] = {
    H2_ID: h2_action,
    H3_ID: h3_action,
}


def action_for(controller_id: str, state_id: int) -> int:
    try:
        controller = CONTROLLERS[controller_id]
    except KeyError as exc:
        raise ValueError(f"Unknown controller {controller_id!r}.") from exc
    return controller(state_id)
