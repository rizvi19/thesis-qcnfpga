"""Cross-version deterministic Ring-6 traces for the QFlow-RL environment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Dict, Mapping, Tuple


RING_NODES = 6
RING_EDGES = (
    (0, 1), (1, 0),
    (1, 2), (2, 1),
    (2, 3), (3, 2),
    (3, 4), (4, 3),
    (4, 5), (5, 4),
    (5, 0), (0, 5),
)
UPPER_EDGES = frozenset({(0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2)})
LOWER_EDGES = frozenset(set(RING_EDGES) - set(UPPER_EDGES))


@dataclass(frozen=True)
class LinkInitialState:
    key_count: int
    fidelity: float
    key_rate: float
    qber: float


@dataclass(frozen=True)
class LinkUpdate:
    arrivals: int
    fidelity: float
    key_rate: float
    qber: float


@dataclass(frozen=True)
class TraceRecord:
    src: int
    dst: int
    offered_requests: int
    updates: Tuple[LinkUpdate, ...]
    phase: str


@dataclass(frozen=True)
class Ring6Trace:
    trace_id: str
    seed: int
    initial_links: Tuple[LinkInitialState, ...]
    records: Tuple[TraceRecord, ...]


class XorShift32:
    """Small explicit PRNG whose bitstream is independent of Python libraries."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFF_FFFF
        if self.state == 0:
            self.state = 0x6D2B_79F5

    def next_u32(self) -> int:
        value = self.state
        value ^= (value << 13) & 0xFFFF_FFFF
        value ^= value >> 17
        value ^= (value << 5) & 0xFFFF_FFFF
        self.state = value & 0xFFFF_FFFF
        return self.state

    def randbelow(self, upper: int) -> int:
        if upper <= 0:
            raise ValueError("upper must be positive")
        return self.next_u32() % upper


def ring_paths(src: int, dst: int) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    if (
        isinstance(src, bool)
        or isinstance(dst, bool)
        or not isinstance(src, int)
        or not isinstance(dst, int)
        or not 0 <= src < RING_NODES
        or not 0 <= dst < RING_NODES
        or src == dst
    ):
        raise ValueError("Ring-6 endpoints must be distinct node IDs in 0..5.")
    clockwise = [src]
    node = src
    while node != dst:
        node = (node + 1) % RING_NODES
        clockwise.append(node)
    counterclockwise = [src]
    node = src
    while node != dst:
        node = (node - 1) % RING_NODES
        counterclockwise.append(node)
    return tuple(clockwise), tuple(counterclockwise)


def _base_initial() -> Tuple[LinkInitialState, ...]:
    return tuple(LinkInitialState(8, 0.97, 4.0, 0.03) for _ in RING_EDGES)


def _phase_update(edge: Tuple[int, int], phase: str, jitter: int = 0) -> LinkUpdate:
    if phase == "scarcity":
        if edge in UPPER_EDGES:
            return LinkUpdate(0, 0.99, 2.0, 0.01)
        return LinkUpdate(2, 0.92, 10.0, 0.07)
    if phase == "fidelity":
        if edge in UPPER_EDGES:
            return LinkUpdate(1, 0.99, 3.0, 0.01)
        return LinkUpdate(2, 0.905, 10.0, 0.09)
    if phase == "low_latency":
        if edge in UPPER_EDGES:
            return LinkUpdate(1, 0.94, 3.0, 0.05)
        return LinkUpdate(2, 0.985, 10.0, 0.015)
    if phase == "mixed":
        if edge in UPPER_EDGES:
            return LinkUpdate(jitter % 2, 0.93 + (jitter % 3) * 0.01, 2.0 + (jitter % 3), 0.05)
        return LinkUpdate(1 + jitter % 2, 0.94 + (jitter % 4) * 0.01, 6.0 + (jitter % 4), 0.04)
    return LinkUpdate(1 + jitter % 2, 0.96 + (jitter % 4) * 0.005, 4.0 + (jitter % 5), 0.02 + (jitter % 3) * 0.01)


def build_manual_trace() -> Ring6Trace:
    phases = (
        "scarcity",
        "scarcity",
        "fidelity",
        "fidelity",
        "low_latency",
        "low_latency",
        "mixed",
        "nominal",
    )
    records = []
    for index, phase in enumerate(phases):
        src, dst = (0, 2) if phase == "low_latency" else (0, 3)
        offered = (1, 3, 2, 4, 4, 2, 3, 1)[index]
        updates = tuple(_phase_update(edge, phase, index) for edge in RING_EDGES)
        records.append(TraceRecord(src, dst, offered, updates, phase))
    return Ring6Trace("manual_ring6_v0", 0, _base_initial(), tuple(records))


def generate_trace(seed: int, length: int = 512) -> Ring6Trace:
    if length < 1:
        raise ValueError("Trace length must be positive.")
    rng = XorShift32(seed)
    initial = tuple(
        LinkInitialState(
            key_count=6 + rng.randbelow(7),
            fidelity=(9400 + rng.randbelow(501)) / 10000.0,
            key_rate=float(3 + rng.randbelow(7)),
            qber=(150 + rng.randbelow(401)) / 10000.0,
        )
        for _ in RING_EDGES
    )
    phase_names = ("nominal", "scarcity", "fidelity", "high_load", "low_latency", "mixed")
    records = []
    for index in range(length):
        phase = phase_names[(index // 32) % len(phase_names)]
        update_phase = "nominal" if phase == "high_load" else phase
        src, dst = (0, 2) if phase == "low_latency" else (0, 3)
        offered = 4 if phase == "high_load" else rng.randbelow(5)
        updates = tuple(
            _phase_update(edge, update_phase, rng.randbelow(16))
            for edge in RING_EDGES
        )
        records.append(TraceRecord(src, dst, offered, updates, phase))
    return Ring6Trace(f"ring6_seed{seed:04d}_len{length}", seed, initial, tuple(records))


def trace_to_dict(trace: Ring6Trace) -> Dict[str, object]:
    return {
        "trace_id": trace.trace_id,
        "seed": trace.seed,
        "edge_order": [list(edge) for edge in RING_EDGES],
        "initial_links": [asdict(item) for item in trace.initial_links],
        "records": [
            {
                "src": record.src,
                "dst": record.dst,
                "offered_requests": record.offered_requests,
                "phase": record.phase,
                "updates": [asdict(item) for item in record.updates],
            }
            for record in trace.records
        ],
    }


def canonical_trace_bytes(trace: Ring6Trace) -> bytes:
    return json.dumps(
        trace_to_dict(trace),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
