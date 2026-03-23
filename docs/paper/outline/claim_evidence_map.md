# Claim–Evidence Map for QFlow Paper

This file defines what the paper is allowed to claim, where the evidence comes from, and where each claim should appear in the manuscript.

---

## C1 — QFlow is a hardware-realizable routing accelerator core
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- Frozen RTL baseline exists:
  - `rtl/fdpe_tc5.v`
  - `rtl/skag_mem_tc4.v`
  - `rtl/qflow_top_tc5.v`
- Timing-closure story completed through tc3 -> tc4 -> tc5
- Functional smoke testing remained correct during timing closure

**Best placement in paper**
- Abstract
- Introduction
- Architecture / Implementation
- Results summary

**Do not overstate**
- Do not say full deployed board demonstration is already completed

---

## C2 — QFlow achieved validated 100 MHz-class implementation
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- tc5 post-synthesis: WNS = +0.033 ns, approx Fmax = 101.885 MHz
- OOC post-route: WNS = +0.039 ns, WHS = +0.098 ns, approx Fmax = 100.392 MHz

**Best placement in paper**
- Abstract
- Implementation Results
- Conclusion

**Required support asset**
- `TAB01`
- optional appendix timing-history figure

**Do not overstate**
- Do not convert OOC post-route into a claim of complete final board deployment

---

## C3 — QFlow provides meaningful latency advantage as a hardware decision engine
**Allowed claim:** Yes  
**Strength:** Medium to Strong

**Evidence**
- Hardware timing-closed design
- Planned latency comparison figure `FIG02`
- Cycle- or timing-based comparison against software-side routing decision flow

**Best placement in paper**
- Motivation
- Implementation Results
- Results Discussion

**Needed before final submission**
- Finalize latency source file and script
- Clearly label measured versus estimated quantities

---

## C4 — Key-aware shortest path is the strongest classical baseline
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- Static baseline evaluation completed
- Frozen interpretation already established in project context

**Best placement in paper**
- Baseline setup
- Static comparison subsection
- Discussion

**Do not overstate**
- Do not call it the strongest overall method in the entire literature
- Keep the qualifier "classical baseline"

---

## C5 — PMO-GA style routing shows tradeoff-aware separation
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- Selection-policy ablation completed
- Final software thesis reference frozen as `ga_tcheby_pick_default`
- Strongest observed benefit is balance / load spreading rather than universal dominance

**Best placement in paper**
- Static comparison subsection
- Dynamic-load discussion
- Summary table `TAB03`

**Do not overstate**
- Do not claim universal superiority over key-aware shortest path on every metric

---

## C6 — Under dynamic load QFlow-relevant routing policies outperform random routing structurally
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- OMNeT++ environment completed and stabilized
- Blocking-vs-load figures generated
- Fidelity CDF figures generated
- Per-link usage analysis concept locked
- Random routing is clearly weaker in path efficiency

**Best placement in paper**
- Dynamic-load results subsection
- Discussion

**Required support assets**
- `FIG03`
- `FIG04`
- `FIG05`

---

## C7 — The dynamic-load study strengthens the routing-quality argument but is not the hardware timing proof
**Allowed claim:** Yes  
**Strength:** Strong

**Evidence**
- OMNeT++ role frozen explicitly as dynamic-load comparison layer
- Hardware timing proof comes from synthesis / OOC timing results instead

**Best placement in paper**
- Experimental Setup
- Dynamic-load subsection introduction
- Threats to validity / limitations

**Why this matters**
- Prevents reviewers from misreading the evaluation stack
- Keeps the paper honest and technically clean

---

## C8 — This work is novel because it combines fidelity-aware routing logic with a hardware-native accelerator framing
**Allowed claim:** Yes  
**Strength:** Medium to Strong

**Evidence**
- Hardware-native architecture with FDPE + SKAG + integrated QFlow top
- Literature positioning table `TABA1`
- Thesis context already identifies a gap between software routing studies and FPGA implementations focused elsewhere

**Best placement in paper**
- Introduction
- Related Work
- Conclusion

**Needed before final submission**
- Finalize related-work positioning table with carefully worded comparison columns

---

## Claims the paper must NOT make

### N1 — “QFlow is universally the best routing method”
**Allowed claim:** No  
**Reason:** Current evidence supports competitiveness and meaningful advantages, not universal domination.

### N2 — “The OMNeT++ GA comparator is exactly identical to the final software PMO-GA selector”
**Allowed claim:** No  
**Reason:** It must be described as a GA-style dynamic-load proxy.

### N3 — “A full physical FPGA board deployment has already been completed”
**Allowed claim:** No  
**Reason:** Current frozen evidence supports post-synthesis and OOC post-route timing closure, not final board demo completion.

---

## Preferred paper-level summary claim

> QFlow is a hardware-realizable, fidelity-aware routing accelerator core that achieves validated 100 MHz-class implementation results and demonstrates meaningful routing-policy advantages over simpler baselines in both static and dynamic evaluation settings.

