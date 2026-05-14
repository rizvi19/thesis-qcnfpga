# Section Draft: Kernel Optimization Methods

## Section purpose

This section explains the kernel-level optimization methods used in QFlow before presenting synthesis and physical-design results.

The goal is to show how the FDPE, SKAG, and Pareto selector kernels were transformed into hardware-oriented implementations suitable for RTL synthesis, OpenROAD physical design, and selected CMOS/ngspice primitive analysis.

## Optimization overview

QFlow contains three main decision-kernel families:

1. FDPE: fidelity-decay approximation.
2. SKAG: edge-weight scoring.
3. Pareto selector: route-candidate comparison and selection.

Each kernel has a different optimization goal:

| Kernel | Optimization problem | Hardware-oriented method |
|---|---|---|
| FDPE | Efficiently approximate exponential fidelity decay | LUT depth reduction and optional interpolation |
| SKAG | Reduce cost of weighted edge-score computation | Replace runtime multiplier-heavy scoring with fixed shift-add scoring |
| Pareto selector | Compare route candidates compactly | Evaluate full comparator and score-first selector variants |

## FDPE optimization: LUT depth and interpolation

The FDPE kernel estimates stored-key fidelity decay using an exponential approximation. A direct exponential computation is expensive for hardware, so QFlow uses lookup-table-based approximation.

The evaluated FDPE variants explore two design dimensions:

1. LUT depth: number of stored exponential samples.
2. Lookup mode: floor-index lookup versus linear interpolation.

The evaluated variants are:

| Variant | LUT entries | Lookup mode | Design intent |
|---|---:|---|---|
| FDPE-V0 | 256 | Floor-index lookup | Baseline higher-depth LUT |
| FDPE-V1 | 128 | Floor-index lookup | Smaller LUT with reduced generic logic cost |
| FDPE-V2 | 128 | Linear interpolation | Better approximation behavior with added arithmetic cost |
| FDPE-V3 | 64 | Linear interpolation | Compact interpolated approximation candidate |

### FDPE design tradeoff

The FDPE optimization is not a simple area-only optimization. It is an area-accuracy tradeoff.

Reducing LUT depth can lower some implementation cost, but it can also increase approximation error. Linear interpolation reduces approximation error but adds arithmetic and control logic. Therefore, the FDPE variants are evaluated as a design space rather than as a single universal winner.

FDPE-V3 was selected for OpenROAD physical implementation because it represents a compact interpolated approximation structure and demonstrates that the LUT/interpolation design style can be taken through a complete physical-design flow.

## SKAG optimization: multiplier-heavy scoring to shift-add scoring

The SKAG kernel computes edge or link scores from multiple network-state terms, such as key availability, fidelity, arrival/load condition, and QBER-related penalty.

The baseline SKAG-W0 model uses a weighted-score structure that maps naturally to multiplier-heavy arithmetic. Runtime multipliers are expensive in generic gate-level synthesis and may dominate the kernel area.

The optimized SKAG-W1 model replaces runtime multiplier-style weighting with fixed-alpha shift-add scoring. Instead of multiplying each term by an arbitrary runtime coefficient, the weights are selected so that they can be implemented using shifts and additions.

### SKAG-W0 baseline idea

SKAG-W0 represents the straightforward weighted-score design:

```text
score = alpha_key * key_penalty
      + alpha_fidelity * fidelity_penalty
      + alpha_load * load_penalty
      + alpha_qber * qber_penalty
```

This is flexible, but it is hardware-costly when implemented with general multipliers.

### SKAG-W1 optimized idea

SKAG-W1 uses fixed coefficients that can be implemented as shifts and additions:

```text
coefficient multiplication -> shift-add approximation
```

This reduces the need for runtime multiplier logic while preserving the tested score behavior for the evaluated cases.

### SKAG design intent

The SKAG optimization is the strongest area-oriented optimization in the current QFlow evidence stack. It shows how domain-specific scoring structure can be reformulated into a hardware-friendly datapath.

SKAG-W1 was selected for OpenROAD physical implementation because it represents the optimized edge-scoring kernel and directly supports the QFlow routing-decision datapath.

## Pareto selector optimization: full comparator versus score-first selector

The Pareto selector compares candidate routes and chooses the preferred candidate based on score and tie-break metrics.

Two selector variants were evaluated:

| Variant | Selector model | Design intent |
|---|---|---|
| Pareto-C0 | Full Pareto comparator with tie-break logic | Baseline complete candidate-comparison behavior |
| Pareto-C1 | Score-first priority selector | Reduced priority-style selector logic |

### Pareto-C0

Pareto-C0 implements the full comparator-style selection behavior. It considers route-candidate dominance and tie-break behavior using multiple metrics.

Pareto-C0 was selected for OpenROAD physical implementation because it represents the complete route-candidate selector/comparator path.

### Pareto-C1

Pareto-C1 simplifies the selection behavior by prioritizing score first and then applying tie-break fields. This can reduce some logic cost but represents a more constrained selection policy.

### Pareto design intent

The Pareto selector variants show that route-selection logic can remain compact compared with larger arithmetic-heavy kernels such as FDPE and SKAG. The selector also motivates the CMOS/ngspice primitive study, because selector and comparator behavior maps naturally to mux and XNOR/equality primitives.

## Selection of kernels for OpenROAD physical design

Based on the kernel optimization study, three representative kernels were selected for SKY130/OpenROAD physical implementation:

| Selected kernel | Reason for selection |
|---|---|
| SKAG-W1 | Optimized shift-add edge-scoring kernel with strong generic synthesis reduction |
| FDPE-V3 | Compact interpolated fidelity-decay approximation kernel |
| Pareto-C0 | Full route-candidate selector/comparator baseline |

This selection covers the main QFlow decision path:

```text
FDPE fidelity update -> SKAG edge scoring -> Pareto route selection
```

## Connection to CMOS/ngspice primitive study

The Pareto-C0 selector/comparator path motivates the selected CMOS/ngspice primitives:

- A 2:1 transmission-gate mux represents selector behavior.
- A 1-bit XNOR/equality primitive represents comparator/equality behavior.

These primitives are not intended to model the entire QFlow chip at transistor level. They provide representative circuit-level evidence for repeated primitive behaviors used by the route-selection datapath.

## Safe wording

The correct claim is:

The QFlow kernel optimization methods reduce or restructure selected decision-kernel datapaths to make them more suitable for hardware synthesis and physical implementation.

Do not claim:

- globally optimal hardware implementation,
- universal area reduction across all technology libraries,
- exact fabricated-silicon area or power,
- or complete full-chip ASIC signoff.

## Paper-ready paragraph

The QFlow kernels are optimized according to their architectural role. FDPE uses LUT-depth and interpolation variants to explore the area-accuracy tradeoff of exponential fidelity-decay approximation. SKAG transforms a multiplier-heavy weighted-score baseline into a fixed-alpha shift-add implementation, reducing arithmetic cost for edge-score computation. The Pareto selector evaluates full comparator and score-first selection variants to study compact route-candidate selection logic. These optimization choices guide the selection of FDPE-V3, SKAG-W1, and Pareto-C0 for OpenROAD physical implementation, while the Pareto-C0 selector path further motivates the mux and XNOR/equality primitives used in the CMOS/ngspice study.
