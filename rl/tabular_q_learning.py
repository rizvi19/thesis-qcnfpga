"""Deterministic tabular Q-learning primitives for frozen P3 H4 training.

This module contains no trace loading and no command-line training entry point.
It is intentionally limited to the learner mechanics required by the P3
contract; controlled trace orchestration begins in the next guarded step.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, List, Optional, Protocol, Sequence, Tuple


STATE_COUNT = 256
ACTION_COUNT = 4
UINT32_MASK = 0xFFFFFFFF
UINT32_RANGE = 1 << 32


def _integer(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    return value


def _state_id(value: int) -> int:
    value = _integer(value, "state_id")
    if not 0 <= value < STATE_COUNT:
        raise ValueError(f"state_id must be in [0, {STATE_COUNT - 1}].")
    return value


def _action_id(value: int) -> int:
    value = _integer(value, "action_id")
    if not 0 <= value < ACTION_COUNT:
        raise ValueError(f"action_id must be in [0, {ACTION_COUNT - 1}].")
    return value


def _finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


class XorShift32:
    """Small explicit PRNG whose bit-level behavior is independent of Python random."""

    def __init__(self, seed: int):
        seed = _integer(seed, "seed")
        if not 1 <= seed <= UINT32_MASK:
            raise ValueError("xorshift32 seed must be in [1, 2^32 - 1].")
        self.state = seed

    def next_u32(self) -> int:
        value = self.state
        value ^= (value << 13) & UINT32_MASK
        value ^= value >> 17
        value ^= (value << 5) & UINT32_MASK
        self.state = value & UINT32_MASK
        return self.state

    def uniform01(self) -> float:
        """Return a value in [0, 1) using one 32-bit draw."""
        return self.next_u32() / UINT32_RANGE

    def randbelow(self, upper: int) -> int:
        """Draw uniformly from range(upper) using rejection sampling."""
        upper = _integer(upper, "upper")
        if not 1 <= upper <= UINT32_RANGE:
            raise ValueError("upper must be in [1, 2^32].")
        rejection_limit = UINT32_RANGE % upper
        while True:
            value = self.next_u32()
            if value >= rejection_limit:
                return value % upper

    def shuffled(self, values: Iterable[int]) -> Tuple[int, ...]:
        """Return a deterministic Fisher-Yates permutation."""
        result = list(values)
        for index in range(len(result) - 1, 0, -1):
            other = self.randbelow(index + 1)
            result[index], result[other] = result[other], result[index]
        return tuple(result)


class EnvironmentStep(Protocol):
    state_id: int
    action_id: int
    next_state_id: Optional[int]
    done: bool

    @property
    def reward(self): ...


class EpisodicEnvironment(Protocol):
    done: bool

    def current_state_id(self) -> int: ...

    def step(self, action_id: int) -> EnvironmentStep: ...


def new_q_table(initial_value: float = 0.0) -> List[List[float]]:
    initial_value = _finite(initial_value, "initial_value")
    return [[initial_value for _ in range(ACTION_COUNT)] for _ in range(STATE_COUNT)]


def validate_q_table(q_table: Sequence[Sequence[float]]) -> None:
    if len(q_table) != STATE_COUNT:
        raise ValueError(f"Q-table must have exactly {STATE_COUNT} rows.")
    for row in q_table:
        if len(row) != ACTION_COUNT:
            raise ValueError(f"Every Q-table row must have exactly {ACTION_COUNT} actions.")
        if any(not math.isfinite(float(value)) for value in row):
            raise ValueError("Q-table values must be finite.")


def _validated_row(q_table: Sequence[Sequence[float]], state_id: int) -> Sequence[float]:
    if len(q_table) != STATE_COUNT:
        raise ValueError(f"Q-table must have exactly {STATE_COUNT} rows.")
    state_id = _state_id(state_id)
    row = q_table[state_id]
    if len(row) != ACTION_COUNT:
        raise ValueError(f"Every Q-table row must have exactly {ACTION_COUNT} actions.")
    if any(not math.isfinite(float(value)) for value in row):
        raise ValueError("Q-table values must be finite.")
    return row


def maximizing_actions(q_table: Sequence[Sequence[float]], state_id: int) -> Tuple[int, ...]:
    row = _validated_row(q_table, state_id)
    maximum = max(row)
    return tuple(action for action, value in enumerate(row) if value == maximum)


def deployment_action(q_table: Sequence[Sequence[float]], state_id: int) -> int:
    """Extract the smallest maximizing action for evaluation/deployment."""
    return maximizing_actions(q_table, state_id)[0]


def extract_policy(q_table: Sequence[Sequence[float]]) -> Tuple[int, ...]:
    validate_q_table(q_table)
    return tuple(
        min(action for action, value in enumerate(row) if value == max(row))
        for row in q_table
    )


def epsilon_at(
    transition_index: int,
    total_transitions: int,
    start: float = 1.0,
    end: float = 0.05,
    decay_fraction: float = 0.8,
) -> float:
    """Frozen linear schedule: endpoints span the first ceil(0.8*T) decisions."""
    transition_index = _integer(transition_index, "transition_index")
    total_transitions = _integer(total_transitions, "total_transitions")
    start = _finite(start, "start")
    end = _finite(end, "end")
    decay_fraction = _finite(decay_fraction, "decay_fraction")
    if total_transitions <= 0:
        raise ValueError("total_transitions must be positive.")
    if not 0 <= transition_index < total_transitions:
        raise ValueError("transition_index must identify a scheduled transition.")
    if not 0.0 <= end <= start <= 1.0:
        raise ValueError("epsilon endpoints must satisfy 0 <= end <= start <= 1.")
    if not 0.0 < decay_fraction <= 1.0:
        raise ValueError("decay_fraction must be in (0, 1].")
    decay_count = max(1, math.ceil(total_transitions * decay_fraction))
    if decay_count == 1 or transition_index >= decay_count - 1:
        return end
    fraction = transition_index / (decay_count - 1)
    return start + (end - start) * fraction


def training_action(
    q_table: Sequence[Sequence[float]],
    state_id: int,
    epsilon: float,
    rng: XorShift32,
) -> int:
    """Epsilon-greedy action with uniform random training tie resolution."""
    state_id = _state_id(state_id)
    epsilon = _finite(epsilon, "epsilon")
    if not 0.0 <= epsilon <= 1.0:
        raise ValueError("epsilon must be in [0, 1].")
    if not isinstance(rng, XorShift32):
        raise ValueError("rng must be an XorShift32 instance.")
    if epsilon == 1.0 or (epsilon > 0.0 and rng.uniform01() < epsilon):
        return rng.randbelow(ACTION_COUNT)
    maxima = maximizing_actions(q_table, state_id)
    return maxima[rng.randbelow(len(maxima))]


@dataclass(frozen=True)
class UpdateRecord:
    state_id: int
    action_id: int
    old_value: float
    reward: float
    bootstrap: float
    target: float
    temporal_difference: float
    new_value: float
    done: bool


def q_update(
    q_table: List[List[float]],
    state_id: int,
    action_id: int,
    reward: float,
    next_state_id: Optional[int],
    done: bool,
    alpha: float = 0.1,
    gamma: float = 0.95,
) -> UpdateRecord:
    """Apply one frozen tabular Q-learning update in place."""
    state_id = _state_id(state_id)
    action_id = _action_id(action_id)
    current_row = _validated_row(q_table, state_id)
    reward = _finite(reward, "reward")
    alpha = _finite(alpha, "alpha")
    gamma = _finite(gamma, "gamma")
    if not isinstance(done, bool):
        raise ValueError("done must be boolean.")
    if not 0.0 < alpha <= 1.0 or not 0.0 <= gamma <= 1.0:
        raise ValueError("alpha must be in (0,1] and gamma in [0,1].")
    if done:
        if next_state_id is not None:
            raise ValueError("Terminal transitions must use next_state_id=None.")
        bootstrap = 0.0
    else:
        if next_state_id is None:
            raise ValueError("Nonterminal transitions require next_state_id.")
        next_state_id = _state_id(next_state_id)
        bootstrap = max(float(value) for value in _validated_row(q_table, next_state_id))
    old_value = float(current_row[action_id])
    target = reward + gamma * bootstrap
    temporal_difference = target - old_value
    new_value = old_value + alpha * temporal_difference
    if not math.isfinite(new_value):
        raise ValueError("Q update produced a non-finite value.")
    q_table[state_id][action_id] = new_value
    return UpdateRecord(
        state_id=state_id,
        action_id=action_id,
        old_value=old_value,
        reward=reward,
        bootstrap=bootstrap,
        target=target,
        temporal_difference=temporal_difference,
        new_value=new_value,
        done=done,
    )


@dataclass(frozen=True)
class EpisodeRecord:
    transition_start: int
    transition_end: int
    transition_count: int
    total_reward: float


class TabularQLearner:
    """Stateful deterministic learner with no partition or trace ownership."""

    def __init__(
        self,
        trainer_seed: int,
        q_initial_value: float = 0.0,
        alpha: float = 0.1,
        gamma: float = 0.95,
    ):
        self.rng = XorShift32(trainer_seed)
        self.q_table = new_q_table(q_initial_value)
        self.alpha = _finite(alpha, "alpha")
        self.gamma = _finite(gamma, "gamma")
        if not 0.0 < self.alpha <= 1.0 or not 0.0 <= self.gamma <= 1.0:
            raise ValueError("alpha must be in (0,1] and gamma in [0,1].")

    def shuffled_trace_order(self, train_seeds: Sequence[int]) -> Tuple[int, ...]:
        seeds = tuple(_integer(seed, "train seed") for seed in train_seeds)
        if not seeds or len(set(seeds)) != len(seeds):
            raise ValueError("train_seeds must be a nonempty unique sequence.")
        return self.rng.shuffled(seeds)

    def choose_action(self, state_id: int, epsilon: float) -> int:
        return training_action(self.q_table, state_id, epsilon, self.rng)

    def update(
        self,
        state_id: int,
        action_id: int,
        reward: float,
        next_state_id: Optional[int],
        done: bool,
    ) -> UpdateRecord:
        return q_update(
            self.q_table,
            state_id,
            action_id,
            reward,
            next_state_id,
            done,
            self.alpha,
            self.gamma,
        )

    def run_episode(
        self,
        environment: EpisodicEnvironment,
        transition_start: int,
        total_transitions: int,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay_fraction: float = 0.8,
    ) -> EpisodeRecord:
        """Train one caller-supplied episode; the caller controls all data access."""
        transition_start = _integer(transition_start, "transition_start")
        if transition_start < 0:
            raise ValueError("transition_start must be nonnegative.")
        if environment.done:
            raise ValueError("environment must be reset and nonterminal.")
        transition_index = transition_start
        total_reward = 0.0
        while not environment.done:
            if transition_index >= total_transitions:
                raise ValueError("episode exceeds the declared training budget.")
            state_id = environment.current_state_id()
            epsilon = epsilon_at(
                transition_index,
                total_transitions,
                epsilon_start,
                epsilon_end,
                epsilon_decay_fraction,
            )
            action_id = self.choose_action(state_id, epsilon)
            result = environment.step(action_id)
            if result.state_id != state_id or result.action_id != action_id:
                raise ValueError("environment step does not match the selected transition.")
            reward_total = _finite(result.reward.total, "reward.total")
            self.update(state_id, action_id, reward_total, result.next_state_id, result.done)
            total_reward += reward_total
            transition_index += 1
        return EpisodeRecord(
            transition_start=transition_start,
            transition_end=transition_index,
            transition_count=transition_index - transition_start,
            total_reward=total_reward,
        )

    def policy(self) -> Tuple[int, ...]:
        return extract_policy(self.q_table)
