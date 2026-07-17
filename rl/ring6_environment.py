"""Deterministic Ring-6 transition engine for the frozen QFlow-RL MDP."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

from rl.mdp_contract import (
    CONTRACT,
    RewardBreakdown,
    RewardInput,
    StateObservation,
    calculate_reward,
    encode_state,
    episode_done,
)
from rl.profile_codebook import Profile, profile_by_action
from rl.route_selector import PathObjectives, select_route
from rl.trace_generator import (
    RING_EDGES,
    Ring6Trace,
    build_manual_trace,
    canonical_trace_bytes,
    generate_trace,
    ring_paths,
    trace_to_dict,
)


EDGE_INDEX = {edge: index for index, edge in enumerate(RING_EDGES)}
KEY_CAPACITY = int(CONTRACT["state"]["normalization_constants"]["key_pool_capacity_per_link"])
REQUEST_CAPACITY = int(CONTRACT["state"]["normalization_constants"]["request_capacity_per_control_window"])
UTILIZATION_WINDOW = int(CONTRACT["state"]["normalization_constants"]["utilization_window_steps"])
FIDELITY_FLOOR = float(CONTRACT["reward"]["fidelity_floor"])


@dataclass
class LinkState:
    key_count: int
    fidelity: float
    key_rate: float
    qber: float


@dataclass(frozen=True)
class StepResult:
    trace_index: int
    state_id: int
    action_id: int
    profile_key: str
    success: bool
    selected_path: Optional[Tuple[int, ...]]
    reward: RewardBreakdown
    next_state_id: Optional[int]
    done: bool


class Ring6Environment:
    def __init__(self, trace: Ring6Trace):
        self._validate_trace(trace)
        self.trace = trace
        self.reset()

    @staticmethod
    def _validate_trace(trace: Ring6Trace) -> None:
        if len(trace.initial_links) != len(RING_EDGES):
            raise ValueError("Trace initial-link count does not match Ring-6 edge order.")
        if not trace.records:
            raise ValueError("Environment trace must contain at least one record.")
        for link in trace.initial_links:
            if isinstance(link.key_count, bool) or not isinstance(link.key_count, int):
                raise ValueError("Initial key counts must be integers.")
            if not 0 <= link.key_count <= KEY_CAPACITY:
                raise ValueError("Initial key count is outside the frozen capacity.")
            if not all(math.isfinite(value) for value in (link.fidelity, link.key_rate, link.qber)):
                raise ValueError("Initial link metrics must be finite.")
            if not 0.0 <= link.fidelity <= 1.0 or link.key_rate < 0.0 or not 0.0 <= link.qber <= 1.0:
                raise ValueError("Initial link metrics are outside their valid ranges.")
        for record in trace.records:
            ring_paths(record.src, record.dst)
            if isinstance(record.offered_requests, bool) or not isinstance(record.offered_requests, int):
                raise ValueError("Offered request count must be an integer.")
            if not 0 <= record.offered_requests <= REQUEST_CAPACITY:
                raise ValueError("Offered request count is outside the frozen capacity.")
            if len(record.updates) != len(RING_EDGES):
                raise ValueError("Trace update count does not match Ring-6 edge order.")
            for update in record.updates:
                if isinstance(update.arrivals, bool) or not isinstance(update.arrivals, int) or update.arrivals < 0:
                    raise ValueError("Key arrivals must be non-negative integers.")
                if not all(math.isfinite(value) for value in (update.fidelity, update.key_rate, update.qber)):
                    raise ValueError("Trace update metrics must be finite.")
                if not 0.0 <= update.fidelity <= 1.0 or update.key_rate < 0.0 or not 0.0 <= update.qber <= 1.0:
                    raise ValueError("Trace update metrics are outside their valid ranges.")

    def reset(self) -> int:
        self.links = {
            edge: LinkState(item.key_count, item.fidelity, item.key_rate, item.qber)
            for edge, item in zip(RING_EDGES, self.trace.initial_links)
        }
        self.consumption_history: Dict[Tuple[int, int], List[int]] = {
            edge: [] for edge in RING_EDGES
        }
        self.trace_index = 0
        self.previous_action_id: Optional[int] = None
        self.done = False
        return self.current_state_id()

    def _candidate_paths(self, src: int, dst: int) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
        return ring_paths(src, dst)

    @staticmethod
    def _path_edges(path: Tuple[int, ...]) -> Tuple[Tuple[int, int], ...]:
        return tuple(zip(path, path[1:]))

    def _window_consumed(self, edge: Tuple[int, int]) -> int:
        return sum(self.consumption_history[edge])

    def _edge_utilization(self, edge: Tuple[int, int]) -> float:
        link = self.links[edge]
        return self._window_consumed(edge) / max(link.key_count, 1)

    def _state_observation(self, record_index: int) -> StateObservation:
        record = self.trace.records[record_index]
        paths = self._candidate_paths(record.src, record.dst)
        candidate_edges = sorted({edge for path in paths for edge in self._path_edges(path)})
        occupancies = [self.links[edge].key_count / KEY_CAPACITY for edge in candidate_edges]
        fidelities = [self.links[edge].fidelity for edge in candidate_edges]
        utilizations = [self._edge_utilization(edge) for edge in candidate_edges]
        return StateObservation(
            min_key_occupancy=min(occupancies),
            bottleneck_fidelity=min(fidelities),
            offered_request_load=record.offered_requests / REQUEST_CAPACITY,
            utilization_imbalance=max(utilizations) - min(utilizations),
        )

    def current_state_id(self) -> int:
        if self.done:
            raise RuntimeError("A terminal environment has no current state.")
        return encode_state(self._state_observation(self.trace_index))

    def _path_objectives(self, path: Tuple[int, ...], profile: Profile) -> Optional[PathObjectives]:
        alpha1, alpha2, alpha3, alpha4 = profile.alphas
        cost = 0.0
        fidelities = []
        utilizations = []
        for edge in self._path_edges(path):
            link = self.links[edge]
            if link.key_count < 1 or link.fidelity < FIDELITY_FLOOR or link.key_rate <= 0.0:
                return None
            cost += (
                alpha1 / link.key_count
                + alpha2 / link.fidelity
                + alpha3 / link.key_rate
                + alpha4 * link.qber
            )
            fidelities.append(link.fidelity)
            utilizations.append((self._window_consumed(edge) + 1.0) / link.key_count)
        return PathObjectives(path, cost, min(fidelities), max(utilizations))

    def _record_consumption(self, selected_edges: Tuple[Tuple[int, int], ...]) -> None:
        selected = set(selected_edges)
        for edge in RING_EDGES:
            history = self.consumption_history[edge]
            history.append(1 if edge in selected else 0)
            if len(history) > UTILIZATION_WINDOW:
                del history[0]

    def _post_decision_imbalance(self) -> float:
        values = [self._edge_utilization(edge) for edge in RING_EDGES]
        return max(values) - min(values)

    def _apply_updates(self, record_index: int) -> None:
        record = self.trace.records[record_index]
        if len(record.updates) != len(RING_EDGES):
            raise ValueError("Trace update count does not match Ring-6 edge order.")
        for edge, update in zip(RING_EDGES, record.updates):
            link = self.links[edge]
            link.key_count = min(KEY_CAPACITY, link.key_count + update.arrivals)
            link.fidelity = update.fidelity
            link.key_rate = update.key_rate
            link.qber = update.qber

    def step(self, action_id: int) -> StepResult:
        if self.done:
            raise RuntimeError("Cannot step a terminal environment; call reset().")
        profile = profile_by_action(action_id)
        state_id = self.current_state_id()
        record_index = self.trace_index
        record = self.trace.records[record_index]
        candidates = []
        for path in self._candidate_paths(record.src, record.dst):
            objectives = self._path_objectives(path, profile)
            if objectives is not None:
                candidates.append(objectives)

        selected_path: Optional[Tuple[int, ...]] = None
        selected_objectives: Optional[PathObjectives] = None
        if candidates:
            selection = select_route(candidates, profile.lambda_tch)
            selected_objectives = selection.selected.objectives
            selected_path = selected_objectives.path
            selected_edges = self._path_edges(selected_path)
            for edge in selected_edges:
                if self.links[edge].key_count < 1:
                    raise RuntimeError("Selected path became infeasible during an atomic decision.")
                self.links[edge].key_count -= 1
            self._record_consumption(selected_edges)
            reward = calculate_reward(
                RewardInput(
                    success=True,
                    action_id=action_id,
                    previous_action_id=self.previous_action_id,
                    bottleneck_fidelity=selected_objectives.bottleneck_fidelity,
                    post_decision_imbalance=self._post_decision_imbalance(),
                    selected_path_hops=len(selected_path) - 1,
                )
            )
        else:
            self._record_consumption(())
            reward = calculate_reward(
                RewardInput(
                    success=False,
                    action_id=action_id,
                    previous_action_id=self.previous_action_id,
                )
            )

        self._apply_updates(record_index)
        self.previous_action_id = action_id
        self.trace_index += 1
        self.done = episode_done(self.trace_index, len(self.trace.records))
        next_state_id = None if self.done else self.current_state_id()

        return StepResult(
            trace_index=record_index,
            state_id=state_id,
            action_id=action_id,
            profile_key=profile.key,
            success=selected_path is not None,
            selected_path=selected_path,
            reward=reward,
            next_state_id=next_state_id,
            done=self.done,
        )


def _write_manual_evidence(output_dir: Path) -> Mapping[str, object]:
    manual = build_manual_trace()
    manual_json = output_dir / "manual_trace.json"
    manual_json.write_text(json.dumps(trace_to_dict(manual), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    actions = (0, 1, 2, 3, 0, 1, 2, 3)
    environment = Ring6Environment(manual)
    rows = []
    step_payload = []
    for action in actions:
        result = environment.step(action)
        reward_dict = asdict(result.reward)
        rows.append(
            (
                result.trace_index,
                result.state_id,
                result.action_id,
                result.profile_key,
                result.success,
                "" if result.selected_path is None else "-".join(map(str, result.selected_path)),
                f"{result.reward.total:.12f}",
                "" if result.next_state_id is None else result.next_state_id,
                result.done,
            )
        )
        step_payload.append(
            {
                "trace_index": result.trace_index,
                "state_id": result.state_id,
                "action_id": result.action_id,
                "profile_key": result.profile_key,
                "success": result.success,
                "selected_path": result.selected_path,
                "reward_components": reward_dict,
                "reward_total": result.reward.total,
                "next_state_id": result.next_state_id,
                "done": result.done,
            }
        )

    csv_path = output_dir / "manual_step_log.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("trace_index", "state_id", "action_id", "profile", "success", "selected_path", "reward", "next_state_id", "done"))
        writer.writerows(rows)

    step_bytes = json.dumps(step_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {
        "trace_sha256": hashlib.sha256(canonical_trace_bytes(manual)).hexdigest(),
        "step_log_sha256": hashlib.sha256(step_bytes).hexdigest(),
        "step_count": len(step_payload),
        "success_count": sum(item["success"] for item in step_payload),
        "final_done": step_payload[-1]["done"],
    }


def write_environment_evidence(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manual_summary = _write_manual_evidence(output_dir)
    partitions = CONTRACT["partitions"]
    manifest_rows = []
    for partition, key in (
        ("train", "train_seeds"),
        ("validation", "validation_seeds"),
        ("test", "test_seeds"),
    ):
        for seed in partitions[key]:
            trace = generate_trace(int(seed), int(partitions["episode_length"]))
            manifest_rows.append(
                {
                    "partition": partition,
                    "seed": seed,
                    "trace_id": trace.trace_id,
                    "record_count": len(trace.records),
                    "sha256": hashlib.sha256(canonical_trace_bytes(trace)).hexdigest(),
                }
            )
    manifest = {
        "schema_version": 1,
        "generator": "xorshift32_ring6_trace_v0",
        "manual_trace": manual_summary,
        "traces": manifest_rows,
    }
    manifest_path = output_dir / "trace_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files = (
        output_dir / "manual_trace.json",
        output_dir / "manual_step_log.csv",
        manifest_path,
    )
    checksum_lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in files]
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("results/rl/p2_environment"))
    args = parser.parse_args()
    write_environment_evidence(args.output_dir)
    manifest = json.loads((args.output_dir / "trace_manifest.json").read_text(encoding="utf-8"))
    print(json.dumps(manifest["manual_trace"], indent=2, sort_keys=True))
    print(f"partitioned_traces={len(manifest['traces'])}")


if __name__ == "__main__":
    main()
