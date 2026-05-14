# Part D CMOS Primitive Summary: 1-bit XNOR/Equality Primitive

## Purpose

This experiment adds comparator/equality-side transistor-level evidence to the QFlow Part D CMOS/ngspice study.

The selected primitive is a 1-bit XNOR/equality circuit because the Pareto-C0 route-candidate selector/comparator uses comparison and equality-style logic.

## Circuit

Primitive:

- 1-bit XNOR/equality primitive
- Boolean function: eq = A XNOR B
- Implemented using transmission-gate mux-style logic
- In this first test, A is held high, so the XNOR output follows B
- Load capacitance: 20 fF
- Supply voltage: 1.8 V
- Device model: simple Level-1 MOS model

## Generated artifacts

- SPICE netlist: `cmos/pareto_cmp_primitive/spice/xnor_eq1_tg.sp`
- ngspice log: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_ngspice.log`
- waveform CSV: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_waveform.csv`
- waveform plot: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_waveform.png`
- measurement file: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_measurements.txt`
- summary CSV: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_summary.csv`

## Measured delay

| Metric | Value |
|---|---:|
| Low-to-high delay, tplh | 27.02 ps |
| High-to-low delay, tphl | 26.25 ps |
| Average delay | 26.64 ps |

## Energy interpretation

For first-pass paper-safe interpretation, the output-load switching energy is estimated using:

```text
E_load = 0.5 * CLOAD * VDD^2
       = 0.5 * 20 fF * (1.8 V)^2
       = 32.4 fJ
```

## Interpretation

The XNOR/equality primitive provides representative transistor-level evidence for comparator-style behavior beneath the Pareto-C0 route-candidate selector. The measured average propagation delay is approximately 26.64 ps under a 1.8 V supply and 20 fF load.

## Evidence boundary

This is a representative transistor-level primitive simulation using a simple Level-1 MOS model. It is not full-chip SPICE, fabricated-silicon measurement, foundry signoff, or calibrated SKY130 transistor-level simulation.

## Paper-safe wording

A representative 1-bit XNOR/equality primitive from the Pareto-C0 comparator path was evaluated using ngspice with a first-order MOS model. The simulation produced a transient waveform and measured an average propagation delay of approximately 26.64 ps under a 1.8 V supply and 20 fF load.
