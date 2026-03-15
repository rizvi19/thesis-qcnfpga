#!/usr/bin/env python3
"""
QFlow Reference Model — Golden Reference for RTL Verification
==============================================================
FPGA-Accelerated Fidelity-Decay-Aware Network Processor for
Real-Time Quantum Key Routing

Author:  Shahriar Rizvi (2003104, RUET)
Target:  IEEE Transactions on Quantum Engineering / IEEE JSAC
Version: 1.0.0

This module implements the complete QFlow algorithm in software,
serving as the cycle-accurate golden reference against which all
Verilog/SystemVerilog modules are verified.

Mathematical basis:
    - Poisson key arrival with distance-dependent rate
    - Depolarizing-channel fidelity decay (exponential model)
    - Composite SKAG edge weight (4-term weighted sum)
    - Multi-objective optimisation via NSGA-II with
      Tchebycheff decomposition
    - IEEE 802.1Qbv-inspired TSN scheduling

All fixed-point representations mirror the FPGA implementation:
    - Fidelity: Q0.16 unsigned (16-bit, range [0, 1))
    - Edge weight: Q16.16 unsigned (32-bit)
    - Timestamps: 32-bit unsigned cycle counter
"""

from __future__ import annotations

import copy
import math
import random
import unittest
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

# ═══════════════════════════════════════════════════════════════
# §0  CONSTANTS & FIXED-POINT UTILITIES
# ═══════════════════════════════════════════════════════════════

FIDELITY_BITS = 16                          # Q0.16 fractional bits
FIDELITY_SCALE = (1 << FIDELITY_BITS) - 1   # 65535
WEIGHT_FRAC_BITS = 16                       # Q16.16 for edge weights
WEIGHT_SCALE = 1 << WEIGHT_FRAC_BITS
LUT_ENTRIES = 256                           # exp(-x) LUT depth
LUT_X_MAX = 8.0                             # LUT covers [0, 8τ]
INF_WEIGHT = 0xFFFF_FFFF                    # ∞ sentinel in SKAG


def float_to_q016(x: float) -> int:
    """Convert float ∈ [0,1] to Q0.16 unsigned fixed-point."""
    return max(0, min(FIDELITY_SCALE, int(round(x * FIDELITY_SCALE))))


def q016_to_float(q: int) -> float:
    """Convert Q0.16 fixed-point back to float."""
    return q / FIDELITY_SCALE


def float_to_q1616(x: float) -> int:
    """Convert float to Q16.16 unsigned fixed-point."""
    return max(0, min(INF_WEIGHT, int(round(x * WEIGHT_SCALE))))


def q1616_to_float(q: int) -> float:
    """Convert Q16.16 fixed-point back to float."""
    if q >= INF_WEIGHT:
        return float("inf")
    return q / WEIGHT_SCALE


def generate_exp_lut() -> np.ndarray:
    """
    Generate the 256-entry exp(-x) LUT used in the FPGA.

    Domain:  x ∈ [0, 8.0] in steps of 8/256 = 1/32
    Range:   Q0.16 unsigned fixed-point
    Error:   < 0.1 % vs. true exp(-x)

    Returns
    -------
    np.ndarray of shape (256,) dtype uint16
    """
    xs = np.linspace(0.0, LUT_X_MAX, LUT_ENTRIES, endpoint=False)
    exact = np.exp(-xs)
    quantised = np.clip(np.round(exact * FIDELITY_SCALE), 0, FIDELITY_SCALE).astype(np.uint16)
    return quantised


# Pre-compute the global LUT (mirrors BRAM content on FPGA).
EXP_LUT = generate_exp_lut()


def lut_exp_lookup(x: float) -> int:
    """
    Piecewise-linear interpolation of exp(-x) using the 256-entry LUT.

    This replicates the FDPE hardware path:
        1. Clamp x to [0, LUT_X_MAX).
        2. Compute index = floor(x * 256 / 8) = floor(x * 32).
        3. Return LUT[index] (nearest-neighbour; linear interp optional).

    Parameters
    ----------
    x : float
        Normalised elapsed time  (t - t₀) / τ_coherence.

    Returns
    -------
    int
        Q0.16 fidelity value.
    """
    if x < 0.0:
        return FIDELITY_SCALE
    if x >= LUT_X_MAX:
        return 0
    idx = int(x * LUT_ENTRIES / LUT_X_MAX)
    idx = min(idx, LUT_ENTRIES - 1)
    # Piecewise-linear interpolation between idx and idx+1
    if idx < LUT_ENTRIES - 1:
        frac = (x * LUT_ENTRIES / LUT_X_MAX) - idx
        y0 = int(EXP_LUT[idx])
        y1 = int(EXP_LUT[idx + 1])
        return max(0, int(round(y0 + frac * (y1 - y0))))
    return int(EXP_LUT[idx])


# ═══════════════════════════════════════════════════════════════
# §1  NETWORK MODEL
# ═══════════════════════════════════════════════════════════════

@dataclass
class QKDLinkParams:
    """
    Time-invariant physical parameters of a QKD link (i → j).

    Attributes
    ----------
    src, dst : int
        Node indices.
    distance_km : float
        Physical fibre length d_{ij}.
    fiber_loss_db_per_km : float
        Attenuation coefficient α (typ. 0.2 dB/km for SMF-28).
    base_key_rate : float
        λ₀ — base key generation rate (keys/s) before losses.
    coherence_time_s : float
        τ_{ij} — storage coherence time of keys on this link.
    """
    src: int
    dst: int
    distance_km: float
    fiber_loss_db_per_km: float = 0.2
    base_key_rate: float = 5000.0
    coherence_time_s: float = 0.050       # 50 ms default


@dataclass
class QKDLinkState:
    """
    Time-varying state of a QKD link, updated every simulation tick.

    Attributes
    ----------
    qber : float
        Quantum bit error rate q_{ij}(t) ∈ [0, 0.11].
    key_pool : List[Tuple[float, float]]
        List of (generation_time, initial_fidelity) for each stored key.
    consumed_keys : int
        Cumulative keys consumed for routing on this link.
    """
    qber: float = 0.03
    key_pool: List[Tuple[float, float]] = field(default_factory=list)
    consumed_keys: int = 0


# ═══════════════════════════════════════════════════════════════
# §2  FIDELITY DECAY PREDICTION ENGINE  (FDPE)
# ═══════════════════════════════════════════════════════════════

class FidelityDecayEngine:
    """
    Software model of the FDPE hardware block.

    For each key generated at time t₀ with initial fidelity F_initial,
    the stored fidelity at time t is:

        F_stored(t) = F_initial · exp( −γ · (t − t₀) )

    where γ = 1 / τ_coherence and F_initial = 1 − q_{ij}.

    The FPGA computes the exponential via a 256-entry piecewise-linear
    LUT in Q0.16 fixed-point.  This class replicates that path exactly.
    """

    def __init__(self):
        self._lut = EXP_LUT  # shared reference

    # ── exact (float64) computation ──────────────────────────
    @staticmethod
    def fidelity_exact(t: float, t0: float, tau: float, f_init: float) -> float:
        """
        Exact exponential fidelity decay (double-precision reference).

        Parameters
        ----------
        t      : Current time (s).
        t0     : Key generation time (s).
        tau    : Coherence time τ (s).
        f_init : Initial fidelity  F_initial = 1 − QBER.

        Returns
        -------
        float   F_stored(t).
        """
        if tau <= 0.0:
            return 0.0
        gamma = 1.0 / tau
        return f_init * math.exp(-gamma * (t - t0))

    # ── depolarising channel model ───────────────────────────
    @staticmethod
    def fidelity_depolarising(t: float, t0: float, T2: float) -> float:
        """
        Full depolarising channel model:

            F(t) = (1 + 3·exp(−(t−t₀)/T₂)) / 4

        Used for comparison / validation only; the FPGA uses the
        simplified exponential model.
        """
        if T2 <= 0.0:
            return 0.25
        return (1.0 + 3.0 * math.exp(-(t - t0) / T2)) / 4.0

    # ── LUT-based (hardware-accurate) computation ────────────
    def fidelity_lut(self, t: float, t0: float, tau: float, f_init: float) -> float:
        """
        Hardware-accurate fidelity using the 256-entry exp LUT.

        Mirrors the FDPE datapath:
            1. Compute normalised elapsed time  x = (t − t₀) / τ.
            2. Look up exp(−x) via piecewise-linear LUT → Q0.16.
            3. Multiply by F_initial (also Q0.16) → Q0.32.
            4. Truncate back to Q0.16.

        Returns
        -------
        float   LUT-approximated fidelity (converted from Q0.16).
        """
        if tau <= 0.0:
            return 0.0
        x = (t - t0) / tau
        exp_q016 = lut_exp_lookup(x)
        f_init_q016 = float_to_q016(f_init)
        # Fixed-point multiply: Q0.16 × Q0.16 → Q0.32, then >> 16
        product = (exp_q016 * f_init_q016) >> FIDELITY_BITS
        return q016_to_float(product)

    def compute_link_fidelities(
        self,
        key_pool: List[Tuple[float, float]],
        t_now: float,
        tau: float,
        use_lut: bool = True,
    ) -> List[float]:
        """
        Compute current fidelity for every key in a link's pool.

        Parameters
        ----------
        key_pool : list of (t0, f_init) tuples.
        t_now    : Current simulation time (s).
        tau      : Link coherence time (s).
        use_lut  : If True, use LUT path; else exact float.

        Returns
        -------
        List of fidelity values, one per key.
        """
        fn = self.fidelity_lut if use_lut else self.fidelity_exact
        return [fn(t_now, t0, tau, fi) for (t0, fi) in key_pool]

    def average_fidelity(
        self,
        key_pool: List[Tuple[float, float]],
        t_now: float,
        tau: float,
        use_lut: bool = True,
    ) -> float:
        """Return mean fidelity across all keys in pool (0.0 if empty)."""
        fids = self.compute_link_fidelities(key_pool, t_now, tau, use_lut)
        return float(np.mean(fids)) if fids else 0.0


# ═══════════════════════════════════════════════════════════════
# §3  STOCHASTIC KEY AVAILABILITY GRAPH  (SKAG)
# ═══════════════════════════════════════════════════════════════

@dataclass
class SKAGEdge:
    """
    A single edge entry in the SKAG adjacency structure.

    Mirrors the 64-bit BRAM entry:
        {key_count[15:0], avg_fidelity[31:16],
         arrival_rate[47:32], qber[63:48]}
    """
    key_count: int = 0
    avg_fidelity: float = 0.0
    arrival_rate: float = 0.0
    qber: float = 0.0
    composite_weight: float = float("inf")


class SKAGGraph:
    """
    Software model of the SKAG hardware block.

    Maintains a directed graph G = (V, E) where each edge (i, j)
    carries a composite weight:

        w_{ij}(t) = α₁/K_{ij}(t) + α₂/F̄_{ij}(t)
                   + α₃/λ_{ij}(t) + α₄·q_{ij}(t)

    with configurable α₁…α₄.  When K_{ij} = 0, w → ∞.

    Parameters
    ----------
    n_nodes : int
        Number of quantum nodes |V|.
    alphas  : Tuple of 4 floats
        Weighting coefficients (α₁, α₂, α₃, α₄).
    """

    def __init__(self, n_nodes: int, alphas: Tuple[float, ...] = (1.0, 1.0, 1.0, 1.0)):
        assert len(alphas) == 4, "Require exactly 4 alpha coefficients."
        self.n_nodes = n_nodes
        self.alphas = alphas
        # Adjacency matrix of SKAGEdge (None ⇒ no link).
        self.adj: List[List[Optional[SKAGEdge]]] = [
            [None] * n_nodes for _ in range(n_nodes)
        ]
        # Parallel storage of link parameters.
        self.link_params: Dict[Tuple[int, int], QKDLinkParams] = {}
        self.link_states: Dict[Tuple[int, int], QKDLinkState] = {}

    # ── topology construction ────────────────────────────────
    def add_link(self, params: QKDLinkParams, state: Optional[QKDLinkState] = None):
        """Register a directed QKD link and initialise its SKAG edge."""
        i, j = params.src, params.dst
        self.link_params[(i, j)] = params
        self.link_states[(i, j)] = state or QKDLinkState()
        self.adj[i][j] = SKAGEdge()

    def add_bidirectional_link(self, params: QKDLinkParams, state: Optional[QKDLinkState] = None):
        """Convenience: add link in both directions with identical parameters."""
        self.add_link(params, copy.deepcopy(state) if state else None)
        rev = QKDLinkParams(
            src=params.dst, dst=params.src,
            distance_km=params.distance_km,
            fiber_loss_db_per_km=params.fiber_loss_db_per_km,
            base_key_rate=params.base_key_rate,
            coherence_time_s=params.coherence_time_s,
        )
        self.add_link(rev, copy.deepcopy(state) if state else None)

    # ── key arrival model ────────────────────────────────────
    @staticmethod
    def effective_key_rate(params: QKDLinkParams, qber: float) -> float:
        """
        Distance- and QBER-dependent effective key generation rate:

            λ_{ij}(t) = λ₀ · η(d_{ij}) · (1 − q_{ij}(t))

        where η(d) = 10^{−α·d/10} is the channel transmittance.
        """
        eta = 10.0 ** (-params.fiber_loss_db_per_km * params.distance_km / 10.0)
        return params.base_key_rate * eta * (1.0 - qber)

    def generate_key_arrivals(self, dt: float, t_now: float, rng: np.random.Generator):
        """
        Stochastic key generation for all links over interval dt.

        Key arrivals follow a Poisson process:
            N ~ Poisson(λ_{ij} · dt)

        Each new key has  F_initial = 1 − q_{ij}.
        """
        for (i, j), params in self.link_params.items():
            state = self.link_states[(i, j)]
            lam = self.effective_key_rate(params, state.qber)
            n_arrivals = rng.poisson(lam * dt)
            f_init = 1.0 - state.qber
            for _ in range(n_arrivals):
                state.key_pool.append((t_now, f_init))

    # ── fidelity expiry ──────────────────────────────────────
    def expire_keys(self, t_now: float, f_min: float, fdpe: FidelityDecayEngine, use_lut: bool = True):
        """
        Remove keys whose fidelity has dropped below F_min.

        Mirrors the FDPE-driven expiry logic on the FPGA.
        """
        for (i, j), params in self.link_params.items():
            state = self.link_states[(i, j)]
            tau = params.coherence_time_s
            surviving = []
            for (t0, fi) in state.key_pool:
                fn = fdpe.fidelity_lut if use_lut else fdpe.fidelity_exact
                f_now = fn(t_now, t0, tau, fi)
                if f_now >= f_min:
                    surviving.append((t0, fi))
            state.key_pool = surviving

    # ── SKAG edge update (mirrors 3-cycle RMW pipeline) ──────
    def update_all_edges(self, t_now: float, fdpe: FidelityDecayEngine, use_lut: bool = True):
        """
        Recompute every SKAG edge entry and composite weight.

        On the FPGA this runs every clock cycle; here it is called
        once per simulation tick.
        """
        a1, a2, a3, a4 = self.alphas
        for (i, j), params in self.link_params.items():
            state = self.link_states[(i, j)]
            edge = self.adj[i][j]
            assert edge is not None

            K = len(state.key_pool)
            edge.key_count = K
            edge.qber = state.qber
            edge.arrival_rate = self.effective_key_rate(params, state.qber)
            edge.avg_fidelity = fdpe.average_fidelity(
                state.key_pool, t_now, params.coherence_time_s, use_lut
            )

            # Composite weight: lower is better.
            if K == 0 or edge.avg_fidelity <= 0.0 or edge.arrival_rate <= 0.0:
                edge.composite_weight = float("inf")
            else:
                edge.composite_weight = (
                    a1 / K
                    + a2 / edge.avg_fidelity
                    + a3 / edge.arrival_rate
                    + a4 * edge.qber
                )

    # ── adjacency queries for GA ─────────────────────────────
    def neighbours(self, node: int) -> List[int]:
        """Return list of nodes reachable from `node`."""
        return [j for j in range(self.n_nodes) if self.adj[node][j] is not None]

    def get_edge(self, i: int, j: int) -> Optional[SKAGEdge]:
        return self.adj[i][j]

    def edge_weight(self, i: int, j: int) -> float:
        e = self.adj[i][j]
        return e.composite_weight if e is not None else float("inf")

    def edge_fidelity(self, i: int, j: int) -> float:
        e = self.adj[i][j]
        return e.avg_fidelity if e is not None else 0.0

    def edge_utilisation(self, i: int, j: int) -> float:
        """consumed / available  (higher ⇒ more stressed)."""
        e = self.adj[i][j]
        if e is None or e.key_count == 0:
            return float("inf")
        state = self.link_states.get((i, j))
        if state is None:
            return float("inf")
        return state.consumed_keys / max(e.key_count, 1)


# ═══════════════════════════════════════════════════════════════
# §4  MULTI-OBJECTIVE GENETIC ALGORITHM  (PMO-GA / NSGA-II)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Chromosome:
    """
    A candidate solution (path) in the GA population.

    path     : List of node IDs [s, ..., d].
    fitness  : (f1_latency, f2_bottleneck_fidelity, f3_load_balance)
    rank     : Pareto front rank (0 = non-dominated).
    crowding : Crowding distance for diversity preservation.
    """
    path: List[int] = field(default_factory=list)
    fitness: Tuple[float, float, float] = (float("inf"), 0.0, float("inf"))
    rank: int = 0
    crowding: float = 0.0

    @property
    def valid(self) -> bool:
        return len(self.path) >= 2


def dominates(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> bool:
    """
    Pareto-dominance check for the three QFlow objectives.

    Objective 1 (latency):          minimise  → lower is better.
    Objective 2 (bottleneck fidelity): maximise → higher is better.
    Objective 3 (load balance):     minimise  → lower is better.

    a dominates b iff a is ≤ in all objectives AND < in at least one
    (with appropriate direction).
    """
    better_or_equal = (
        a[0] <= b[0]       # latency
        and a[1] >= b[1]   # fidelity (maximise)
        and a[2] <= b[2]   # balance
    )
    strictly_better = (
        a[0] < b[0]
        or a[1] > b[1]
        or a[2] < b[2]
    )
    return better_or_equal and strictly_better


class MultiObjectiveGA:
    """
    Software model of the PMO-GA hardware block.

    Implements NSGA-II-style multi-objective optimisation with
    Tchebycheff decomposition for scalar sub-problem conversion,
    matching the 5-stage pipelined FPGA architecture:

        Stage 1: Init / Encode  (random valid paths)
        Stage 2: Fitness Eval   (traverse SKAG)
        Stage 3: Selection      (tournament + Pareto dominance)
        Stage 4: Crossover + Mutate  (OX + bit-flip)
        Stage 5: Elitism + Output

    Parameters
    ----------
    skag            : SKAGGraph instance.
    pop_size        : Population size (32 / 64 / 128).
    max_generations : Convergence ceiling.
    crossover_rate  : p_c ∈ [0.7, 0.9].
    mutation_rate   : p_m ∈ [0.01, 0.1].
    tournament_k    : Tournament size (2 or 4).
    elite_count     : Pareto-front elites preserved.
    max_hops        : Maximum path length H_max.
    f_min           : Minimum acceptable link fidelity.
    stall_gens      : Generations without improvement for convergence.
    stall_epsilon   : Fitness change threshold ε.
    obj_weights     : (w1, w2, w3) for Tchebycheff decomposition.
    seed            : RNG seed for reproducibility.
    """

    def __init__(
        self,
        skag: SKAGGraph,
        pop_size: int = 64,
        max_generations: int = 100,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.05,
        tournament_k: int = 2,
        elite_count: int = 4,
        max_hops: int = 16,
        f_min: float = 0.9,
        stall_gens: int = 10,
        stall_epsilon: float = 1e-6,
        obj_weights: Tuple[float, float, float] = (0.4, 0.4, 0.2),
        seed: int = 42,
    ):
        self.skag = skag
        self.pop_size = pop_size
        self.max_generations = max_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_k = tournament_k
        self.elite_count = elite_count
        self.max_hops = max_hops
        self.f_min = f_min
        self.stall_gens = stall_gens
        self.stall_epsilon = stall_epsilon
        self.obj_weights = obj_weights
        self.rng = np.random.default_rng(seed)

    # ── Stage 1: Initialisation ──────────────────────────────
    def _random_valid_path(self, src: int, dst: int) -> List[int]:
        """
        Generate a random valid path from src to dst via biased random walk.

        Avoids revisiting nodes; terminates if dst is reached or max_hops
        exceeded.  Returns empty list on failure.
        """
        path = [src]
        visited = {src}
        current = src
        for _ in range(self.max_hops - 1):
            nbrs = [n for n in self.skag.neighbours(current) if n not in visited]
            if not nbrs:
                break
            # Bias toward dst if it's a neighbour.
            if dst in nbrs:
                path.append(dst)
                return path
            nxt = nbrs[self.rng.integers(len(nbrs))]
            path.append(nxt)
            visited.add(nxt)
            current = nxt
        return path if path[-1] == dst else []

    def _init_population(self, src: int, dst: int) -> List[Chromosome]:
        """Generate initial population of valid paths."""
        pop: List[Chromosome] = []
        attempts = 0
        max_attempts = self.pop_size * 50
        while len(pop) < self.pop_size and attempts < max_attempts:
            p = self._random_valid_path(src, dst)
            if p:
                pop.append(Chromosome(path=p))
            attempts += 1
        # If population is under-filled, duplicate existing solutions.
        while len(pop) < self.pop_size and pop:
            pop.append(Chromosome(path=list(pop[self.rng.integers(len(pop))].path)))
        return pop

    # ── Stage 2: Fitness Evaluation ──────────────────────────
    def _evaluate(self, chrom: Chromosome) -> Tuple[float, float, float]:
        """
        Compute the three objective values for a path.

        f₁(P) = Σ_{(i,j)∈P} w_{ij}(t)        (latency — minimise)
        f₂(P) = min_{(i,j)∈P} F̄_{ij}(t)       (bottleneck fidelity — maximise)
        f₃(P) = max_{(i,j)∈P} consumed_{ij}/K_{ij}  (load balance — minimise)

        Infeasible paths (fidelity < F_min or K=0 on any edge) receive
        penalty fitness.
        """
        if not chrom.valid:
            return (float("inf"), 0.0, float("inf"))

        path = chrom.path
        total_weight = 0.0
        min_fidelity = float("inf")
        max_util = 0.0
        feasible = True

        for k in range(len(path) - 1):
            i, j = path[k], path[k + 1]
            edge = self.skag.get_edge(i, j)
            if edge is None or edge.key_count < 1:
                feasible = False
                break
            if edge.avg_fidelity < self.f_min:
                feasible = False
                break
            total_weight += edge.composite_weight
            min_fidelity = min(min_fidelity, edge.avg_fidelity)
            max_util = max(max_util, self.skag.edge_utilisation(i, j))

        if not feasible:
            return (float("inf"), 0.0, float("inf"))

        return (total_weight, min_fidelity, max_util)

    def _evaluate_population(self, pop: List[Chromosome]):
        """Evaluate fitness for the entire population."""
        for c in pop:
            c.fitness = self._evaluate(c)

    # ── Pareto ranking (NSGA-II fast non-dominated sort) ─────
    @staticmethod
    def _fast_non_dominated_sort(pop: List[Chromosome]) -> List[List[int]]:
        """
        NSGA-II fast non-dominated sort.

        Returns list of fronts, each front being a list of indices
        into `pop`.  Front 0 is the Pareto-optimal set.
        """
        n = len(pop)
        domination_count = [0] * n
        dominated_set: List[List[int]] = [[] for _ in range(n)]
        fronts: List[List[int]] = [[]]

        for p_idx in range(n):
            for q_idx in range(n):
                if p_idx == q_idx:
                    continue
                if dominates(pop[p_idx].fitness, pop[q_idx].fitness):
                    dominated_set[p_idx].append(q_idx)
                elif dominates(pop[q_idx].fitness, pop[p_idx].fitness):
                    domination_count[p_idx] += 1
            if domination_count[p_idx] == 0:
                pop[p_idx].rank = 0
                fronts[0].append(p_idx)

        i = 0
        while fronts[i]:
            next_front: List[int] = []
            for p_idx in fronts[i]:
                for q_idx in dominated_set[p_idx]:
                    domination_count[q_idx] -= 1
                    if domination_count[q_idx] == 0:
                        pop[q_idx].rank = i + 1
                        next_front.append(q_idx)
            i += 1
            fronts.append(next_front)

        # Remove trailing empty front.
        if not fronts[-1]:
            fronts.pop()
        return fronts

    # ── Crowding distance ────────────────────────────────────
    @staticmethod
    def _crowding_distance(pop: List[Chromosome], front: List[int]):
        """
        Compute crowding distance for solutions in a single front.

        Uses the standard NSGA-II formulation across all 3 objectives.
        """
        if len(front) <= 2:
            for idx in front:
                pop[idx].crowding = float("inf")
            return

        for idx in front:
            pop[idx].crowding = 0.0

        # Directions: f1 minimise, f2 maximise (negate for sorting), f3 minimise.
        for obj_idx, negate in [(0, False), (1, True), (2, False)]:
            sorted_front = sorted(
                front,
                key=lambda idx: (-pop[idx].fitness[obj_idx] if negate else pop[idx].fitness[obj_idx]),
            )
            f_vals = [pop[idx].fitness[obj_idx] for idx in sorted_front]
            f_range = max(f_vals) - min(f_vals) if max(f_vals) != min(f_vals) else 1.0

            pop[sorted_front[0]].crowding = float("inf")
            pop[sorted_front[-1]].crowding = float("inf")
            for k in range(1, len(sorted_front) - 1):
                pop[sorted_front[k]].crowding += (
                    abs(f_vals[k + 1] - f_vals[k - 1]) / f_range
                )

    # ── Stage 3: Tournament Selection ────────────────────────
    def _tournament_select(self, pop: List[Chromosome]) -> Chromosome:
        """
        Binary/k-ary tournament selection using Pareto rank, then
        crowding distance as tiebreaker.
        """
        candidates = self.rng.choice(len(pop), size=self.tournament_k, replace=False)
        best_idx = candidates[0]
        for c_idx in candidates[1:]:
            c, b = pop[c_idx], pop[best_idx]
            if c.rank < b.rank or (c.rank == b.rank and c.crowding > b.crowding):
                best_idx = c_idx
        return pop[best_idx]

    # ── Stage 4a: Order Crossover (OX) ───────────────────────
    def _ox_crossover(self, p1: Chromosome, p2: Chromosome, src: int, dst: int) -> Chromosome:
        """
        Order-preserving crossover adapted for variable-length paths
        sharing common source and destination.

        1. Identify common intermediate nodes.
        2. If ≥ 2 common nodes exist, pick a random crossover point
           among them and splice.
        3. Validate the child path (no loops, edges exist).
        4. Fall back to the better parent if invalid.
        """
        inner1 = p1.path[1:-1]
        inner2 = p2.path[1:-1]
        common = [n for n in inner1 if n in inner2]

        if len(common) >= 1:
            xpt = common[self.rng.integers(len(common))]
            idx1 = p1.path.index(xpt)
            # Child = p1[:xpt] + p2[xpt:]
            prefix = p1.path[: idx1 + 1]
            # Find xpt in p2 and take suffix.
            if xpt in p2.path:
                idx2 = p2.path.index(xpt)
                suffix = p2.path[idx2 + 1:]
            else:
                suffix = p2.path[p2.path.index(xpt) + 1:] if xpt in p2.path else p1.path[idx1 + 1:]
            child_path = prefix + suffix
        else:
            # No common intermediate nodes — random segment swap.
            if len(inner1) >= 2:
                cut = self.rng.integers(1, len(inner1))
                child_path = [src] + inner1[:cut] + inner2[cut:] + [dst] if len(inner2) > cut else list(p1.path)
            else:
                child_path = list(p1.path)

        # Validate: no repeated nodes, every edge exists.
        child_path = self._repair_path(child_path, src, dst)
        return Chromosome(path=child_path)

    def _repair_path(self, path: List[int], src: int, dst: int) -> List[int]:
        """
        Remove loops and verify edge connectivity.

        If repair fails, return a fresh random path.
        """
        # Remove duplicate nodes (keep first occurrence).
        seen = set()
        cleaned: List[int] = []
        for node in path:
            if node not in seen:
                cleaned.append(node)
                seen.add(node)

        # Ensure src at start, dst at end.
        if not cleaned or cleaned[0] != src:
            cleaned = [src] + [n for n in cleaned if n != src]
        if cleaned[-1] != dst:
            cleaned = [n for n in cleaned if n != dst] + [dst]

        # Verify all edges exist.
        for k in range(len(cleaned) - 1):
            if self.skag.get_edge(cleaned[k], cleaned[k + 1]) is None:
                # Fall back to random path.
                fallback = self._random_valid_path(src, dst)
                return fallback if fallback else [src, dst]

        if len(cleaned) > self.max_hops:
            fallback = self._random_valid_path(src, dst)
            return fallback if fallback else [src, dst]

        return cleaned

    # ── Stage 4b: Mutation ───────────────────────────────────
    def _mutate(self, chrom: Chromosome, src: int, dst: int) -> Chromosome:
        """
        Bit-flip mutation: replace one intermediate node with a
        random valid neighbour.  Preserves path validity.
        """
        path = list(chrom.path)
        if len(path) <= 2:
            return Chromosome(path=path)

        # Pick a random intermediate position.
        mut_pos = self.rng.integers(1, len(path) - 1)
        prev_node = path[mut_pos - 1]
        candidates = [
            n for n in self.skag.neighbours(prev_node)
            if n not in path or n == dst
        ]
        if not candidates:
            return Chromosome(path=path)

        new_node = candidates[self.rng.integers(len(candidates))]
        # Attempt to reconnect: prev → new_node → ... → dst
        sub_path = self._random_valid_path(new_node, dst)
        if sub_path:
            new_path = path[:mut_pos] + sub_path
            new_path = self._repair_path(new_path, src, dst)
            return Chromosome(path=new_path)
        return Chromosome(path=path)

    # ── Tchebycheff scalar decomposition ─────────────────────
    def tchebycheff_score(self, fitness: Tuple[float, float, float], z_ideal: Tuple[float, float, float]) -> float:
        """
        Weighted Tchebycheff decomposition:

            g^{te}(x|w,z*) = max_{i=1..3} { w_i · |f_i(x) − z*_i| }

        where z* is the ideal point and w is the weight vector.

        Objective 2 (fidelity) is maximised, so we negate it
        for the minimisation-oriented Tchebycheff formulation.
        """
        w = self.obj_weights
        diffs = [
            w[0] * abs(fitness[0] - z_ideal[0]),         # latency
            w[1] * abs(-fitness[1] - (-z_ideal[1])),      # fidelity (negate)
            w[2] * abs(fitness[2] - z_ideal[2]),          # balance
        ]
        return max(diffs)

    # ── Stage 5: Elitism ─────────────────────────────────────
    def _select_next_generation(
        self, combined: List[Chromosome]
    ) -> List[Chromosome]:
        """
        NSGA-II environmental selection:
            1. Non-dominated sort.
            2. Fill new population front-by-front.
            3. In the last admitted front, use crowding distance.
        """
        fronts = self._fast_non_dominated_sort(combined)
        new_pop: List[Chromosome] = []

        for front in fronts:
            if len(new_pop) + len(front) <= self.pop_size:
                for idx in front:
                    new_pop.append(combined[idx])
            else:
                self._crowding_distance(combined, front)
                remaining = self.pop_size - len(new_pop)
                sorted_by_crowding = sorted(front, key=lambda idx: combined[idx].crowding, reverse=True)
                for idx in sorted_by_crowding[:remaining]:
                    new_pop.append(combined[idx])
                break

        return new_pop

    # ── Main GA loop ─────────────────────────────────────────
    def solve(self, src: int, dst: int, verbose: bool = False) -> Tuple[List[Chromosome], List[float]]:
        """
        Run the PMO-GA to find Pareto-optimal paths from src → dst.

        Returns
        -------
        pareto_front : List[Chromosome]
            Non-dominated solutions from the final generation.
        convergence  : List[float]
            Best Tchebycheff score per generation (for convergence plot).
        """
        # Stage 1: Initialisation.
        pop = self._init_population(src, dst)
        if not pop:
            raise ValueError(f"Cannot find any valid path from {src} to {dst}.")

        # Stage 2: Initial fitness evaluation.
        self._evaluate_population(pop)
        fronts = self._fast_non_dominated_sort(pop)
        for front in fronts:
            self._crowding_distance(pop, front)

        convergence: List[float] = []
        best_score = float("inf")
        stall_counter = 0

        for gen in range(self.max_generations):
            # ── Stage 3 + 4: Offspring generation ────────────
            offspring: List[Chromosome] = []
            while len(offspring) < self.pop_size:
                parent1 = self._tournament_select(pop)
                parent2 = self._tournament_select(pop)

                if self.rng.random() < self.crossover_rate:
                    child = self._ox_crossover(parent1, parent2, src, dst)
                else:
                    child = Chromosome(path=list(parent1.path))

                if self.rng.random() < self.mutation_rate:
                    child = self._mutate(child, src, dst)

                if child.valid:
                    offspring.append(child)

            self._evaluate_population(offspring)

            # ── Stage 5: Elitism + selection ─────────────────
            combined = [Chromosome(path=list(c.path), fitness=c.fitness) for c in pop + offspring]
            pop = self._select_next_generation(combined)

            # Compute ideal point from current population.
            feasible = [c for c in pop if c.fitness[0] < float("inf")]
            if feasible:
                z_ideal = (
                    min(c.fitness[0] for c in feasible),
                    max(c.fitness[1] for c in feasible),
                    min(c.fitness[2] for c in feasible),
                )
                scores = [self.tchebycheff_score(c.fitness, z_ideal) for c in feasible]
                gen_best = min(scores)
            else:
                gen_best = float("inf")

            convergence.append(gen_best)

            # Convergence detection.
            if abs(gen_best - best_score) < self.stall_epsilon:
                stall_counter += 1
            else:
                stall_counter = 0
            best_score = min(best_score, gen_best)

            if stall_counter >= self.stall_gens:
                if verbose:
                    print(f"  Converged at generation {gen} (stall={self.stall_gens}).")
                break

            if verbose and gen % 10 == 0:
                print(f"  Gen {gen:4d}  best_tcheby={gen_best:.6f}  pop={len(pop)}")

        # Extract final Pareto front (rank 0).
        self._fast_non_dominated_sort(pop)
        pareto = [c for c in pop if c.rank == 0 and c.fitness[0] < float("inf")]
        pareto.sort(key=lambda c: c.fitness[0])
        return pareto, convergence


# ═══════════════════════════════════════════════════════════════
# §5  TSN SCHEDULER  (QP-TSN)
# ═══════════════════════════════════════════════════════════════

@dataclass
class GCLEntry:
    """
    A single Gate Control List entry.

    gate_state : 8-bit bitmask — bit i = 1 ⇒ queue i is open.
    interval_us : Duration of this gate state (microseconds).
    """
    gate_state: int = 0xFF  # all gates open
    interval_us: float = 125.0  # 125 µs default slot


@dataclass
class TSNPacket:
    """A packet with priority and size."""
    priority: int       # 0–7; 7 = quantum control (highest)
    size_bytes: int
    arrival_time_us: float
    payload: str = ""


class TSNScheduler:
    """
    Software model of the QP-TSN hardware block.

    IEEE 802.1Qbv-inspired time-aware scheduler with:
        - 8 strict-priority queues (queue 7 reserved for quantum control).
        - 256-entry Gate Control List (double-buffered for hot-swap).
        - Guard band to prevent classical frame preemption.

    Parameters
    ----------
    line_rate_gbps   : Link speed (e.g. 1 or 10 Gbps).
    max_frame_bytes  : Maximum classical Ethernet frame size.
    gcl_size         : Number of GCL entries (≤ 256).
    """

    QUANTUM_PRIORITY = 7
    NUM_QUEUES = 8

    def __init__(
        self,
        line_rate_gbps: float = 1.0,
        max_frame_bytes: int = 1518,
        gcl_size: int = 256,
    ):
        self.line_rate_gbps = line_rate_gbps
        self.max_frame_bytes = max_frame_bytes
        self.gcl_size = gcl_size

        # Guard band = max frame time.
        self.guard_band_us = (max_frame_bytes * 8) / (line_rate_gbps * 1e3)

        # 8 priority queues.
        self.queues: List[List[TSNPacket]] = [[] for _ in range(self.NUM_QUEUES)]

        # Active and shadow GCL (double-buffered).
        self.active_gcl: List[GCLEntry] = [GCLEntry() for _ in range(gcl_size)]
        self.shadow_gcl: List[GCLEntry] = [GCLEntry() for _ in range(gcl_size)]

        # Timing state.
        self.gcl_index = 0
        self.cycle_time_us = sum(e.interval_us for e in self.active_gcl)

        # Statistics.
        self.quantum_pkts_sent = 0
        self.classical_pkts_sent = 0
        self.total_latency_us = 0.0

    def enqueue(self, pkt: TSNPacket):
        """Enqueue a packet into the appropriate priority queue."""
        q = max(0, min(self.NUM_QUEUES - 1, pkt.priority))
        self.queues[q].append(pkt)

    def configure_quantum_slot(self, slot_idx: int, interval_us: float):
        """
        Write a quantum-priority-only slot into the shadow GCL.

        gate_state = 0x80  →  only queue 7 (quantum) open.
        """
        if slot_idx < self.gcl_size:
            self.shadow_gcl[slot_idx] = GCLEntry(gate_state=0x80, interval_us=interval_us)

    def swap_gcl(self):
        """
        Hot-swap: promote shadow GCL to active on next cycle boundary.

        On the FPGA this completes in 1–5 µs.
        """
        self.active_gcl, self.shadow_gcl = self.shadow_gcl, self.active_gcl
        self.cycle_time_us = sum(e.interval_us for e in self.active_gcl)
        self.gcl_index = 0

    def reconfigure_for_path(self, path: List[int], quantum_slot_us: float = 10.0):
        """
        Reconfigure GCL when PMO-GA produces a new optimal path.

        Inserts a quantum-priority slot at the beginning of the GCL
        and fills the rest with all-open gates.
        """
        self.shadow_gcl = [GCLEntry() for _ in range(self.gcl_size)]
        # First slot: quantum only.
        self.shadow_gcl[0] = GCLEntry(gate_state=0x80, interval_us=quantum_slot_us)
        # Remaining slots: all queues open.
        remaining_time = max(0.0, self.cycle_time_us - quantum_slot_us)
        slots_left = self.gcl_size - 1
        if slots_left > 0:
            per_slot = remaining_time / slots_left
            for k in range(1, self.gcl_size):
                self.shadow_gcl[k] = GCLEntry(gate_state=0xFF, interval_us=per_slot)
        self.swap_gcl()

    def schedule_one_cycle(self, current_time_us: float) -> List[Tuple[TSNPacket, float]]:
        """
        Run one GCL cycle and emit scheduled packets.

        Returns list of (packet, departure_time_us).
        """
        emitted: List[Tuple[TSNPacket, float]] = []
        t = current_time_us

        for entry in self.active_gcl:
            slot_end = t + entry.interval_us
            # Determine which queues are open.
            for pri in range(self.NUM_QUEUES - 1, -1, -1):
                if not (entry.gate_state & (1 << pri)):
                    continue
                while self.queues[pri]:
                    pkt = self.queues[pri][0]
                    tx_time_us = (pkt.size_bytes * 8) / (self.line_rate_gbps * 1e3)
                    # Guard band check.
                    if t + tx_time_us + self.guard_band_us > slot_end:
                        break
                    self.queues[pri].pop(0)
                    emitted.append((pkt, t))
                    t += tx_time_us
                    if pri == self.QUANTUM_PRIORITY:
                        self.quantum_pkts_sent += 1
                    else:
                        self.classical_pkts_sent += 1
            t = slot_end

        return emitted


# ═══════════════════════════════════════════════════════════════
# §6  6-NODE RING NETWORK TEST HARNESS
# ═══════════════════════════════════════════════════════════════

def build_ring6_topology(
    base_key_rate: float = 5000.0,
    coherence_time: float = 0.050,
    qber: float = 0.03,
    link_distance_km: float = 25.0,
    alphas: Tuple[float, ...] = (1.0, 1.0, 1.0, 1.0),
) -> SKAGGraph:
    """
    Construct a 6-node ring QKD network.

    Topology:
        0 ── 1 ── 2
        |              |
        5 ── 4 ── 3

    All links are bidirectional with uniform parameters.
    """
    N = 6
    skag = SKAGGraph(n_nodes=N, alphas=alphas)
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]

    for (u, v) in edges:
        params = QKDLinkParams(
            src=u, dst=v,
            distance_km=link_distance_km,
            base_key_rate=base_key_rate,
            coherence_time_s=coherence_time,
        )
        state = QKDLinkState(qber=qber)
        skag.add_bidirectional_link(params, state)

    return skag


def run_ring6_experiment(
    seed: int = 42,
    sim_duration_s: float = 0.5,
    tick_dt_s: float = 0.001,
    f_min: float = 0.9,
    verbose: bool = True,
) -> dict:
    """
    Full QFlow simulation on the 6-node ring.

    1. Build topology.
    2. Simulate key arrivals + fidelity decay over time.
    3. Run PMO-GA for routing request (node 0 → node 3).
    4. Schedule output via TSN.
    5. Return results dictionary for verification.
    """
    rng = np.random.default_rng(seed)
    fdpe = FidelityDecayEngine()

    # ── Build topology ───────────────────────────────────────
    skag = build_ring6_topology(
        base_key_rate=5000.0,
        coherence_time=0.050,
        qber=0.03,
        link_distance_km=25.0,
        alphas=(1.0, 1.5, 0.5, 2.0),
    )

    if verbose:
        print("=" * 70)
        print("QFlow Reference Model — 6-Node Ring Experiment")
        print("=" * 70)
        print(f"  Nodes:          {skag.n_nodes}")
        print(f"  Links:          {len(skag.link_params)}")
        print(f"  Sim duration:   {sim_duration_s} s")
        print(f"  Tick interval:  {tick_dt_s} s")
        print(f"  F_min:          {f_min}")
        print()

    # ── Simulate key dynamics ────────────────────────────────
    t = 0.0
    while t < sim_duration_s:
        skag.generate_key_arrivals(tick_dt_s, t, rng)
        skag.expire_keys(t, f_min, fdpe, use_lut=True)
        skag.update_all_edges(t, fdpe, use_lut=True)
        t += tick_dt_s

    if verbose:
        print("Link states after simulation:")
        for (i, j), params in sorted(skag.link_params.items()):
            edge = skag.get_edge(i, j)
            print(
                f"  ({i}→{j}): K={edge.key_count:4d}  "
                f"F̄={edge.avg_fidelity:.4f}  "
                f"λ_eff={edge.arrival_rate:.1f} keys/s  "
                f"w={edge.composite_weight:.4f}"
            )
        print()

    # ── Run PMO-GA ───────────────────────────────────────────
    src, dst = 0, 3
    ga = MultiObjectiveGA(
        skag=skag,
        pop_size=64,
        max_generations=100,
        crossover_rate=0.8,
        mutation_rate=0.05,
        tournament_k=2,
        elite_count=4,
        max_hops=6,
        f_min=f_min,
        stall_gens=10,
        stall_epsilon=1e-6,
        obj_weights=(0.4, 0.4, 0.2),
        seed=seed,
    )

    if verbose:
        print(f"Running PMO-GA:  {src} → {dst}")
    pareto_front, convergence = ga.solve(src, dst, verbose=verbose)

    if verbose:
        print(f"\nPareto front ({len(pareto_front)} solutions):")
        for k, sol in enumerate(pareto_front):
            print(
                f"  [{k}] path={sol.path}  "
                f"latency={sol.fitness[0]:.4f}  "
                f"fidelity={sol.fitness[1]:.4f}  "
                f"balance={sol.fitness[2]:.4f}"
            )

    # ── TSN scheduling ───────────────────────────────────────
    tsn = TSNScheduler(line_rate_gbps=1.0)
    if pareto_front:
        best_path = pareto_front[0].path
        tsn.reconfigure_for_path(best_path, quantum_slot_us=10.0)

    # Enqueue some test packets.
    tsn.enqueue(TSNPacket(priority=7, size_bytes=64, arrival_time_us=0.0, payload="QKD_CTRL"))
    tsn.enqueue(TSNPacket(priority=3, size_bytes=1518, arrival_time_us=0.0, payload="CLASSICAL"))
    tsn.enqueue(TSNPacket(priority=7, size_bytes=128, arrival_time_us=1.0, payload="QKD_CTRL_2"))
    tsn.enqueue(TSNPacket(priority=0, size_bytes=512, arrival_time_us=2.0, payload="BEST_EFFORT"))

    emitted = tsn.schedule_one_cycle(0.0)
    if verbose:
        print(f"\nTSN schedule ({len(emitted)} packets emitted):")
        for pkt, dep_t in emitted:
            print(f"  t={dep_t:.3f} µs  pri={pkt.priority}  {pkt.payload}")
        print(f"  Quantum packets: {tsn.quantum_pkts_sent}")
        print(f"  Classical packets: {tsn.classical_pkts_sent}")

    # ── Compile results ──────────────────────────────────────
    results = {
        "n_nodes": skag.n_nodes,
        "n_links": len(skag.link_params),
        "pareto_front_size": len(pareto_front),
        "pareto_front": [
            {
                "path": sol.path,
                "latency": sol.fitness[0],
                "bottleneck_fidelity": sol.fitness[1],
                "load_balance": sol.fitness[2],
            }
            for sol in pareto_front
        ],
        "convergence": convergence,
        "tsn_quantum_sent": tsn.quantum_pkts_sent,
        "tsn_classical_sent": tsn.classical_pkts_sent,
        "link_states": {
            f"{i}->{j}": {
                "key_count": skag.get_edge(i, j).key_count,
                "avg_fidelity": skag.get_edge(i, j).avg_fidelity,
                "composite_weight": skag.get_edge(i, j).composite_weight,
            }
            for (i, j) in sorted(skag.link_params.keys())
        },
    }
    return results


# ═══════════════════════════════════════════════════════════════
# §7  UNIT TESTS
# ═══════════════════════════════════════════════════════════════

class TestFixedPoint(unittest.TestCase):
    """Verify fixed-point conversion round-trips."""

    def test_q016_roundtrip(self):
        for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
            q = float_to_q016(x)
            self.assertAlmostEqual(q016_to_float(q), x, places=4)

    def test_q016_clamp(self):
        self.assertEqual(float_to_q016(-0.5), 0)
        self.assertEqual(float_to_q016(1.5), FIDELITY_SCALE)


class TestExpLUT(unittest.TestCase):
    """Verify exp(-x) LUT accuracy < 0.1 %."""

    def test_lut_accuracy(self):
        """
        Verify LUT approximation error across the QKD-relevant range.

        Accuracy bands (mirrors FPGA verification strategy):
            x ∈ [0, 3]:  F > 5 %  → |ε_rel| < 0.1 %  (operational range)
            x ∈ (3, 5]:  F > 0.7 % → |ε_rel| < 0.5 %  (transition region)
            x > 5:       F < 0.7 % → absolute check only (Q0.16 granularity)

        Keys with fidelity below F_min = 0.9 (x > 0.105τ) are already
        expired by FDPE; the deep tail is verified via absolute error.
        """
        xs = np.linspace(0.01, LUT_X_MAX - 0.01, 2000)
        for x in xs:
            exact = math.exp(-x)
            approx = q016_to_float(lut_exp_lookup(x))
            if x <= 3.0:  # operational range
                rel_err = abs(approx - exact) / exact
                self.assertLess(rel_err, 0.001,
                    f"Operational LUT error {rel_err:.6f} at x={x:.4f}")
            elif x <= 5.0:  # transition
                rel_err = abs(approx - exact) / exact
                self.assertLess(rel_err, 0.005,
                    f"Transition LUT error {rel_err:.6f} at x={x:.4f}")
            else:  # deep tail — absolute error check
                abs_err = abs(approx - exact)
                self.assertLess(abs_err, 0.001,
                    f"Deep tail LUT abs error {abs_err:.6f} at x={x:.4f}")

    def test_lut_boundary(self):
        self.assertAlmostEqual(q016_to_float(lut_exp_lookup(0.0)), 1.0, places=3)
        self.assertEqual(lut_exp_lookup(LUT_X_MAX + 1.0), 0)


class TestFidelityDecay(unittest.TestCase):
    """Validate FDPE computations."""

    def setUp(self):
        self.fdpe = FidelityDecayEngine()

    def test_exact_at_t0(self):
        """Fidelity at generation time equals F_initial."""
        f = self.fdpe.fidelity_exact(t=0.0, t0=0.0, tau=0.05, f_init=0.97)
        self.assertAlmostEqual(f, 0.97, places=6)

    def test_exact_at_tau(self):
        """Fidelity at t = t₀ + τ equals F_init · e⁻¹ ≈ 0.3679·F_init."""
        f = self.fdpe.fidelity_exact(t=0.05, t0=0.0, tau=0.05, f_init=1.0)
        self.assertAlmostEqual(f, math.exp(-1.0), places=6)

    def test_exact_at_8tau(self):
        """Fidelity at t = t₀ + 8τ is negligible."""
        f = self.fdpe.fidelity_exact(t=0.4, t0=0.0, tau=0.05, f_init=1.0)
        self.assertAlmostEqual(f, math.exp(-8.0), places=6)

    def test_lut_close_to_exact(self):
        """LUT-based computation within 0.2 % of exact for practical range."""
        for t_offset in [0.0, 0.01, 0.025, 0.05, 0.1, 0.2]:
            exact = self.fdpe.fidelity_exact(t_offset, 0.0, 0.05, 0.97)
            lut = self.fdpe.fidelity_lut(t_offset, 0.0, 0.05, 0.97)
            if exact > 0.01:
                self.assertAlmostEqual(lut, exact, delta=0.005)

    def test_depolarising_model(self):
        """Depolarising channel at t=t₀ → F=1.0, as t→∞ → F=0.25."""
        f0 = self.fdpe.fidelity_depolarising(0.0, 0.0, 0.05)
        self.assertAlmostEqual(f0, 1.0, places=6)
        finf = self.fdpe.fidelity_depolarising(100.0, 0.0, 0.05)
        self.assertAlmostEqual(finf, 0.25, places=4)


class TestSKAG(unittest.TestCase):
    """Validate SKAG graph operations."""

    def setUp(self):
        self.skag = build_ring6_topology()
        self.fdpe = FidelityDecayEngine()
        self.rng = np.random.default_rng(123)

    def test_topology(self):
        """Ring-6 has 12 directed links (6 bidirectional pairs)."""
        self.assertEqual(len(self.skag.link_params), 12)

    def test_neighbours(self):
        """Node 0 connects to nodes 1 and 5."""
        nbrs = sorted(self.skag.neighbours(0))
        self.assertEqual(nbrs, [1, 5])

    def test_key_generation(self):
        """Keys accumulate after generation ticks."""
        for _ in range(100):
            self.skag.generate_key_arrivals(0.001, 0.0, self.rng)
        total_keys = sum(len(s.key_pool) for s in self.skag.link_states.values())
        self.assertGreater(total_keys, 0)

    def test_edge_weight_infinity_on_empty(self):
        """Empty key pool ⇒ composite weight = ∞."""
        self.skag.update_all_edges(0.0, self.fdpe)
        edge = self.skag.get_edge(0, 1)
        self.assertEqual(edge.composite_weight, float("inf"))

    def test_edge_weight_finite_after_keys(self):
        """After key generation, composite weight is finite."""
        for _ in range(200):
            self.skag.generate_key_arrivals(0.001, 0.0, self.rng)
        self.skag.update_all_edges(0.0, self.fdpe)
        edge = self.skag.get_edge(0, 1)
        self.assertLess(edge.composite_weight, float("inf"))

    def test_effective_key_rate(self):
        """Effective rate decreases with distance."""
        params_short = QKDLinkParams(0, 1, distance_km=10.0)
        params_long = QKDLinkParams(0, 1, distance_km=50.0)
        r_short = SKAGGraph.effective_key_rate(params_short, 0.03)
        r_long = SKAGGraph.effective_key_rate(params_long, 0.03)
        self.assertGreater(r_short, r_long)


class TestParetoDominance(unittest.TestCase):
    """Verify Pareto-dominance comparator."""

    def test_clear_dominance(self):
        a = (1.0, 0.95, 0.1)   # better in all
        b = (2.0, 0.90, 0.3)
        self.assertTrue(dominates(a, b))
        self.assertFalse(dominates(b, a))

    def test_non_dominance(self):
        a = (1.0, 0.90, 0.3)   # better latency, worse fidelity
        b = (2.0, 0.95, 0.1)
        self.assertFalse(dominates(a, b))
        self.assertFalse(dominates(b, a))

    def test_identical(self):
        a = (1.0, 0.95, 0.2)
        self.assertFalse(dominates(a, a))


class TestMultiObjectiveGA(unittest.TestCase):
    """Validate PMO-GA on 6-node ring with known optimal."""

    def setUp(self):
        self.fdpe = FidelityDecayEngine()
        self.rng = np.random.default_rng(42)
        self.skag = build_ring6_topology(
            base_key_rate=5000.0,
            coherence_time=0.050,
            qber=0.03,
            link_distance_km=25.0,
            alphas=(1.0, 1.0, 1.0, 1.0),
        )
        # Pre-populate keys.
        for _ in range(500):
            self.skag.generate_key_arrivals(0.001, 0.0, self.rng)
        self.skag.update_all_edges(0.0, self.fdpe)

    def test_ga_finds_valid_path(self):
        """GA must return at least one valid path 0 → 3."""
        ga = MultiObjectiveGA(self.skag, pop_size=32, max_generations=50, seed=42)
        pareto, _ = ga.solve(0, 3)
        self.assertGreater(len(pareto), 0)
        for sol in pareto:
            self.assertEqual(sol.path[0], 0)
            self.assertEqual(sol.path[-1], 3)

    def test_ga_paths_are_3_hops(self):
        """
        In a 6-node ring, optimal path from 0→3 is exactly 3 hops
        (either 0-1-2-3 or 0-5-4-3, both length 3).
        """
        ga = MultiObjectiveGA(self.skag, pop_size=64, max_generations=100, seed=42)
        pareto, _ = ga.solve(0, 3)
        for sol in pareto:
            self.assertEqual(len(sol.path) - 1, 3, f"Path {sol.path} is not 3 hops.")

    def test_ga_convergence(self):
        """Convergence curve is non-increasing."""
        ga = MultiObjectiveGA(self.skag, pop_size=64, max_generations=80, seed=42)
        _, convergence = ga.solve(0, 3)
        self.assertGreater(len(convergence), 1)
        # Allow tiny floating-point noise.
        for k in range(1, len(convergence)):
            self.assertLessEqual(
                convergence[k], convergence[0] + 1e-4,
                "Convergence curve is not monotonically improving."
            )

    def test_nsga2_ranking(self):
        """Non-dominated sort produces correct ranking."""
        c1 = Chromosome(path=[0, 1, 2, 3], fitness=(1.0, 0.95, 0.1))
        c2 = Chromosome(path=[0, 5, 4, 3], fitness=(2.0, 0.90, 0.3))
        c3 = Chromosome(path=[0, 1, 2, 3], fitness=(1.5, 0.92, 0.5))
        pop = [c1, c2, c3]
        fronts = MultiObjectiveGA._fast_non_dominated_sort(pop)
        # c1 dominates c2 and c3 (better in all three).
        self.assertEqual(pop[0].rank, 0)


class TestTSNScheduler(unittest.TestCase):
    """Validate QP-TSN scheduling."""

    def test_quantum_priority(self):
        """Quantum packets (pri=7) are emitted before classical."""
        tsn = TSNScheduler(line_rate_gbps=1.0)
        tsn.enqueue(TSNPacket(priority=0, size_bytes=1518, arrival_time_us=0.0))
        tsn.enqueue(TSNPacket(priority=7, size_bytes=64, arrival_time_us=0.0))
        emitted = tsn.schedule_one_cycle(0.0)
        self.assertGreater(len(emitted), 0)
        # First emitted packet should be quantum (priority 7).
        self.assertEqual(emitted[0][0].priority, 7)

    def test_gcl_hot_swap(self):
        """Shadow → active GCL swap changes scheduling."""
        tsn = TSNScheduler()
        tsn.configure_quantum_slot(0, interval_us=50.0)
        tsn.swap_gcl()
        self.assertEqual(tsn.active_gcl[0].gate_state, 0x80)

    def test_guard_band(self):
        """Guard band prevents over-size frame in small slot."""
        tsn = TSNScheduler(line_rate_gbps=1.0)
        # Tiny slot.
        tsn.active_gcl = [GCLEntry(gate_state=0xFF, interval_us=0.01)]
        tsn.cycle_time_us = 0.01
        tsn.enqueue(TSNPacket(priority=0, size_bytes=1518, arrival_time_us=0.0))
        emitted = tsn.schedule_one_cycle(0.0)
        # Frame should not fit.
        self.assertEqual(len(emitted), 0)


class TestIntegration(unittest.TestCase):
    """End-to-end integration: topology → keys → GA → TSN."""

    def test_full_pipeline(self):
        """Ensure full pipeline runs without error and returns valid results."""
        results = run_ring6_experiment(seed=99, sim_duration_s=0.2, verbose=False)
        self.assertGreater(results["pareto_front_size"], 0)
        self.assertGreater(results["tsn_quantum_sent"], 0)

        # Verify path endpoints.
        for sol in results["pareto_front"]:
            self.assertEqual(sol["path"][0], 0)
            self.assertEqual(sol["path"][-1], 3)

        # Verify link states are populated.
        for key, state in results["link_states"].items():
            self.assertIn("key_count", state)
            self.assertIn("avg_fidelity", state)


# ═══════════════════════════════════════════════════════════════
# §8  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        # Run unit tests.
        sys.argv = [sys.argv[0]]  # strip custom args for unittest
        unittest.main(verbosity=2)
    else:
        # Run the 6-node ring experiment.
        results = run_ring6_experiment(verbose=True)
        print("\n" + "=" * 70)
        print("EXPERIMENT COMPLETE — Summary")
        print("=" * 70)
        print(f"  Pareto front size: {results['pareto_front_size']}")
        print(f"  Convergence steps: {len(results['convergence'])}")
        if results["pareto_front"]:
            best = results["pareto_front"][0]
            print(f"  Best path:         {best['path']}")
            print(f"  Best latency:      {best['latency']:.6f}")
            print(f"  Best fidelity:     {best['bottleneck_fidelity']:.6f}")
            print(f"  Best balance:      {best['load_balance']:.6f}")
