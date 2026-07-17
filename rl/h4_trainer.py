"""Controlled train-partition orchestration for the P3 H4 tabular learner."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from statistics import fmean
from typing import Dict, List, Mapping, Sequence, Tuple

from rl.p3_contract import CONTRACT
from rl.ring6_environment import Ring6Environment
from rl.tabular_q_learning import TabularQLearner, epsilon_at, extract_policy
from rl.trace_generator import Ring6Trace, canonical_trace_bytes, generate_trace


FROZEN_TRAIN_SEEDS = tuple(int(value) for value in CONTRACT["partitions"]["train_seeds"])
FROZEN_TRAINER_SEEDS = tuple(int(value) for value in CONTRACT["training"]["trainer_seeds"])
EPISODE_LENGTH = int(CONTRACT["partitions"]["episode_length"])
FULL_EPOCHS = int(CONTRACT["training"]["epochs"])
FULL_TRANSITIONS = int(CONTRACT["training"]["transitions_per_trainer"])


@dataclass(frozen=True)
class TrainingSpec:
    epochs: int
    train_seeds: Tuple[int, ...]
    episode_length: int = EPISODE_LENGTH

    def validate(self) -> None:
        if isinstance(self.epochs, bool) or not isinstance(self.epochs, int) or self.epochs <= 0:
            raise ValueError("epochs must be a positive integer.")
        if isinstance(self.episode_length, bool) or not isinstance(self.episode_length, int) or self.episode_length <= 0:
            raise ValueError("episode_length must be a positive integer.")
        if not self.train_seeds or len(set(self.train_seeds)) != len(self.train_seeds):
            raise ValueError("train_seeds must be a nonempty unique sequence.")
        if any(seed not in FROZEN_TRAIN_SEEDS for seed in self.train_seeds):
            raise ValueError("Only frozen train-partition seeds are authorized for P3 training.")

    @property
    def transitions(self) -> int:
        return self.epochs * len(self.train_seeds) * self.episode_length


SMOKE_SPEC = TrainingSpec(epochs=2, train_seeds=FROZEN_TRAIN_SEEDS)
FULL_SPEC = TrainingSpec(epochs=FULL_EPOCHS, train_seeds=FROZEN_TRAIN_SEEDS)


@dataclass(frozen=True)
class EpochMetrics:
    trainer_seed: int
    epoch: int
    transition_count: int
    cumulative_transitions: int
    mean_reward: float
    profile_0_count: int
    profile_1_count: int
    profile_2_count: int
    profile_3_count: int
    distinct_state_count: int
    q_min: float
    q_max: float
    q_table_sha256: str


@dataclass(frozen=True)
class CandidateResult:
    trainer_seed: int
    spec: TrainingSpec
    epochs: Tuple[EpochMetrics, ...]
    q_table: Tuple[Tuple[float, ...], ...]
    policy: Tuple[int, ...]
    q_table_sha256: str
    policy_sha256: str
    trace_sha256: Mapping[int, str]
    final_profile_counts: Tuple[int, int, int, int]
    visited_state_count: int


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _q_table_tuple(q_table: Sequence[Sequence[float]]) -> Tuple[Tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in q_table)


def _validate_trainer_seed(trainer_seed: int) -> int:
    if isinstance(trainer_seed, bool) or not isinstance(trainer_seed, int):
        raise ValueError("trainer_seed must be an integer.")
    if trainer_seed not in FROZEN_TRAINER_SEEDS:
        raise ValueError("trainer_seed is not in the frozen P3 trainer manifest.")
    return trainer_seed


def _training_constants() -> Tuple[float, float, float, float, float, float]:
    training = CONTRACT["training"]
    epsilon = training["epsilon"]
    return (
        float(training["q_initial_value"]),
        float(training["learning_rate_alpha"]),
        float(training["discount_gamma"]),
        float(epsilon["start"]),
        float(epsilon["end"]),
        float(epsilon["decay_fraction_of_training_transitions"]),
    )


def train_candidate(trainer_seed: int, spec: TrainingSpec) -> CandidateResult:
    """Train one deterministic candidate using authorized train seeds only."""
    trainer_seed = _validate_trainer_seed(trainer_seed)
    spec.validate()
    q_initial, alpha, gamma, epsilon_start, epsilon_end, decay_fraction = _training_constants()
    learner = TabularQLearner(trainer_seed, q_initial, alpha, gamma)
    traces: Dict[int, Ring6Trace] = {
        seed: generate_trace(seed, spec.episode_length)
        for seed in spec.train_seeds
    }
    trace_hashes = {
        seed: hashlib.sha256(canonical_trace_bytes(trace)).hexdigest()
        for seed, trace in traces.items()
    }
    transition_index = 0
    all_profile_counts = [0, 0, 0, 0]
    all_visited_states = set()
    epoch_rows: List[EpochMetrics] = []

    for epoch_index in range(spec.epochs):
        order = learner.shuffled_trace_order(spec.train_seeds)
        epoch_rewards: List[float] = []
        epoch_profile_counts = [0, 0, 0, 0]
        epoch_states = set()
        epoch_start = transition_index
        for environment_seed in order:
            environment = Ring6Environment(traces[environment_seed])
            while not environment.done:
                state_id = environment.current_state_id()
                epsilon = epsilon_at(
                    transition_index,
                    spec.transitions,
                    epsilon_start,
                    epsilon_end,
                    decay_fraction,
                )
                action_id = learner.choose_action(state_id, epsilon)
                result = environment.step(action_id)
                learner.update(state_id, action_id, result.reward.total, result.next_state_id, result.done)
                epoch_rewards.append(float(result.reward.total))
                epoch_profile_counts[action_id] += 1
                all_profile_counts[action_id] += 1
                epoch_states.add(state_id)
                all_visited_states.add(state_id)
                transition_index += 1

        if transition_index - epoch_start != len(spec.train_seeds) * spec.episode_length:
            raise RuntimeError("Epoch transition count differs from the declared training specification.")
        q_tuple = _q_table_tuple(learner.q_table)
        q_values = [value for row in q_tuple for value in row]
        epoch_rows.append(
            EpochMetrics(
                trainer_seed=trainer_seed,
                epoch=epoch_index + 1,
                transition_count=transition_index - epoch_start,
                cumulative_transitions=transition_index,
                mean_reward=fmean(epoch_rewards),
                profile_0_count=epoch_profile_counts[0],
                profile_1_count=epoch_profile_counts[1],
                profile_2_count=epoch_profile_counts[2],
                profile_3_count=epoch_profile_counts[3],
                distinct_state_count=len(epoch_states),
                q_min=min(q_values),
                q_max=max(q_values),
                q_table_sha256=_canonical_sha256(q_tuple),
            )
        )

    if transition_index != spec.transitions:
        raise RuntimeError("Candidate transition count differs from the declared training specification.")
    q_tuple = _q_table_tuple(learner.q_table)
    if any(not math.isfinite(value) for row in q_tuple for value in row):
        raise RuntimeError("Candidate Q-table contains a non-finite value.")
    policy = extract_policy(q_tuple)
    return CandidateResult(
        trainer_seed=trainer_seed,
        spec=spec,
        epochs=tuple(epoch_rows),
        q_table=q_tuple,
        policy=policy,
        q_table_sha256=_canonical_sha256(q_tuple),
        policy_sha256=_canonical_sha256(policy),
        trace_sha256=trace_hashes,
        final_profile_counts=tuple(all_profile_counts),
        visited_state_count=len(all_visited_states),
    )
