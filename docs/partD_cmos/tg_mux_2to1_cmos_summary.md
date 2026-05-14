# Part D CMOS Primitive Summary: 2:1 Transmission-Gate Mux

## Purpose

This experiment provides the first transistor-level CMOS/ngspice primitive evidence for the QFlow Part D extension.

The selected primitive is a 2:1 transmission-gate mux because the Pareto-C0 route-candidate selector uses selector-style decision logic.

## Circuit

Primitive:

- 2:1 transmission-gate mux
- Select signal: `sel`
- Complement select signal: `selb`
- `sel = 1` selects `in1`
- `sel = 0` selects `in0`
- Load capacitance: 20 fF
- Supply voltage: 1.8 V
- Device model: simple Level-1 MOS model

## Generated artifacts

- SPICE netlist: `cmos/pareto_cmp_primitive/spice/tg_mux_2to1.sp`
- ngspice log: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_ngspice.log`
- waveform CSV: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.csv`
- waveform plot: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png`
- measurement file: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_measurements.txt`
- summary CSV: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_summary.csv`

## Measured delay

From ngspice transient measurement:

| Metric | Value |
|---|---:|
| Low-to-high delay, `tplh` | 27.02 ps |
| High-to-low delay, `tphl` | 26.25 ps |
| Average delay | 26.64 ps |

## Energy interpretation

The raw VDD-source integration is not used as the main dynamic energy value because the transmission-gate mux charges the output load mainly through the selected input source. With a simple Level-1 MOS model, this makes VDD-source integration unrealistically small.

For paper-safe first-pass energy interpretation, use the output-load switching estimate:

```text
E_load = 0.5 * CLOAD * VDD^2
       = 0.5 * 20 fF * (1.8 V)^2
       = 32.4 fJ
```

## Evidence boundary

This is a representative transistor-level primitive simulation.

It is not:

- full-chip SPICE,
- fabricated-silicon measurement,
- foundry signoff,
- or a calibrated SKY130 transistor-level simulation.

## Paper-safe wording

A representative 2:1 transmission-gate mux from the Pareto-C0 route-selection datapath was evaluated using ngspice with a first-order MOS model. The simulation produced a transient waveform and measured an average propagation delay of approximately 26.64 ps under a 1.8 V supply and 20 fF load. The output-load switching energy is estimated as approximately 32.4 fJ using 0.5CV^2.
