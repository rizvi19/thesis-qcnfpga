"""Deterministic minimum-dwell guard for a frozen H4 policy-index ROM."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from rl.tabular_q_learning import ACTION_COUNT, STATE_COUNT


def validate_policy(policy: Sequence[int]) -> Tuple[int, ...]:
    if len(policy) != STATE_COUNT:
        raise ValueError(f"Policy must contain exactly {STATE_COUNT} action indices.")
    result = tuple(policy)
    if any(
        isinstance(action, bool)
        or not isinstance(action, int)
        or not 0 <= action < ACTION_COUNT
        for action in result
    ):
        raise ValueError("Policy contains an invalid action index.")
    return result


class MinimumDwellController:
    """Hold each accepted profile for a minimum number of decisions.

    The guard does not alter the policy ROM. It only delays a proposed profile
    change until the currently accepted profile has satisfied the frozen dwell.
    State is reset at the beginning of every independent trace.
    """

    def __init__(self, policy: Sequence[int], minimum_dwell_decisions: int):
        if (
            isinstance(minimum_dwell_decisions, bool)
            or not isinstance(minimum_dwell_decisions, int)
            or minimum_dwell_decisions < 1
        ):
            raise ValueError("minimum_dwell_decisions must be a positive integer.")
        self.policy = validate_policy(policy)
        self.minimum_dwell_decisions = minimum_dwell_decisions
        self.current_action: Optional[int] = None
        self.dwell_count = 0

    def reset(self) -> None:
        self.current_action = None
        self.dwell_count = 0

    def choose_action(self, state_id: int) -> int:
        if isinstance(state_id, bool) or not isinstance(state_id, int) or not 0 <= state_id < STATE_COUNT:
            raise ValueError(f"state_id must be in [0, {STATE_COUNT - 1}].")
        proposed = self.policy[state_id]
        if self.current_action is None:
            self.current_action = proposed
            self.dwell_count = 1
        elif proposed != self.current_action and self.dwell_count >= self.minimum_dwell_decisions:
            self.current_action = proposed
            self.dwell_count = 1
        else:
            self.dwell_count += 1
        return self.current_action
