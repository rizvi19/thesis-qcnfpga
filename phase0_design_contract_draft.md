# QFlow Phase 0 Design Contract — Draft v0.1

This draft follows the updated thesis roadmap and is meant to become the **single frozen reference** before RTL implementation begins.

## 1) Frozen thesis scope

### Mandatory thesis core
- FDPE
- SKAG
- PMO-GA
- Python golden-model audit
- Primitive arithmetic verification
- Top-level integration
- Synthesis results
- Baseline comparison against:
  - shortest path
  - key-aware shortest path
  - software GA

### Recommended extension
- QP-TSN
- irregular backbone topology
- FPGA board deployment
- DRL comparator

### Stretch goals
- 32-node scale case
- full DRL / DQN baseline
- extensive hardware board measurement campaign

---

## 2) Canonical constants and formats

| Item | Frozen value / rule | Source basis | RTL implication | Status |
|---|---:|---|---|---|
| Stored fidelity format | Q0.16 unsigned | math framework + architecture spec + reference model | 16-bit unsigned datapath | Freeze |
| `FIDELITY_SCALE` | 65535 | reference model | saturation uses `(1<<16)-1` | Freeze |
| Edge weight format | Q16.16 unsigned | v2 plan + reference model | 32-bit arithmetic, rounding must be defined | Freeze |
| `WEIGHT_SCALE` | 65536 | reference model | fractional scaling factor | Freeze |
| Exponential LUT depth | 256 entries | original plan + architecture spec + reference model | BRAM/LUT ROM sizing | Freeze |
| LUT domain | `x ∈ [0, 8)` | original plan + reference model | hardware LUT address logic | Freeze |
| Infinity sentinel | `0xFFFF_FFFF` | reference model + architecture spec | used for empty/unavailable edges | Freeze |
| Timestamp width | 32 bits | architecture spec | FDPE age computation width | Freeze |
| Default target FPGA | Artix-7 XC7A200T-1FBG484 | architecture spec | synthesis target | Freeze |
| Primary clock target | 200 MHz | architecture spec | timing target for reports | Freeze |
| Secondary acceptable target | 100 MHz | architecture spec | fallback timing target | Freeze |
| Default topology for first validation | Ring-6 | v2 plan + reference model | earliest end-to-end debug case | Freeze |
| Mandatory topology ladder | Ring-6, Mesh-8/9, Mesh-16 | v2 plan | evaluation progression | Freeze |
| Default core modules | `fdpe`, `skag_mem`, `pmo_ga`, `qflow_top` | architecture spec | mandatory RTL path | Freeze |
| QP-TSN scope | extension unless core finishes early | v2 plan | avoid thesis overexpansion | Freeze |

---

## 3) Canonical module naming

| Functional block | Preferred module name | Notes |
|---|---|---|
| Fidelity Decay Prediction Engine | `fdpe` | mandatory |
| Stochastic Key Availability Graph memory | `skag_mem` | mandatory |
| Multi-objective GA engine | `pmo_ga` | mandatory |
| Top-level integration | `qflow_top` | mandatory |
| TSN scheduler | `qp_tsn` or `tsn_sched` | extension |
| AXI-Lite config block | `qflow_axi_lite` | may be stubbed early |

---

## 4) Canonical implementation rules

1. No module may be integrated before it has:
   - a short written spec
   - a passing testbench
   - a Python comparison artifact
   - a synthesis sanity check if arithmetic or memory-heavy

2. No claim may appear in the thesis without one of:
   - a figure
   - a table
   - a citation
   - a log/report artifact

3. Evaluation must use matched seeds/topologies whenever possible.

4. All figure-generating code must be script-based and reproducible.

---

## 5) Open issues to resolve in Phase 0

| ID | Open issue | Why it matters | Planned resolution |
|---|---|---|---|
| P0-01 | Freeze default random seed(s) | reproducibility | define in config file |
| P0-02 | Freeze alpha coefficients | software/RTL comparability | create constants/config sheet |
| P0-03 | Confirm LUT interpolation wording | doc/code consistency | use linear interpolation everywhere |
| P0-04 | Decide whether TSN is core or extension | scope safety | keep as extension for now |
| P0-05 | Freeze address-map philosophy | future AXI-Lite block design | create register map draft later |
| P0-06 | Define Pareto-front dedup policy | cleaner evaluation plots | implement in analysis scripts |

---

## 6) Advisor-facing scope statement

**Recommended thesis statement:**  
The mandatory thesis contribution is the hardware-native routing data path consisting of FDPE + SKAG + PMO-GA, verified against a Python golden model and evaluated against credible software baselines. QP-TSN and board-level deployment are treated as extensions that will be included only if the core path is completed safely.

---

## 7) Immediate next outputs after this document is accepted

1. Frozen default configuration file
2. Golden vectors for:
   - LUT values
   - fixed-point conversions
   - edge weight computations
   - Ring-6 routing decisions
3. Primitive task list:
   - `generate_lut.py`
   - fixed-point helper verification
   - PRNG module and tests
