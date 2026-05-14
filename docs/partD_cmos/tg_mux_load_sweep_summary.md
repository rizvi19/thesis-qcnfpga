# Part D CMOS Load-Sweep Summary: 2:1 Transmission-Gate Mux

## Purpose

This document summarizes the ngspice load-sweep result for the 2:1 transmission-gate mux used as a representative selector primitive from the Pareto-C0 route-selection path.

## Sweep setup

- Primitive: 2:1 transmission-gate mux
- Tool: ngspice
- Device model: simple Level-1 MOS model
- Supply voltage: 1.8 V
- Swept load capacitance: 5 fF, 10 fF, 20 fF, 50 fF
- Energy estimate: E_load = 0.5 * CLOAD * VDD^2

## Results

| Load capacitance | tplh | tphl | Average delay | Estimated load switching energy |
|---:|---:|---:|---:|---:|
| 5 fF | 10.24 ps | 10.52 ps | 10.38 ps | 8.10 fJ |
| 10 fF | 17.29 ps | 17.25 ps | 17.27 ps | 16.20 fJ |
| 20 fF | 27.02 ps | 26.25 ps | 26.64 ps | 32.40 fJ |
| 50 fF | 56.60 ps | 52.01 ps | 54.31 ps | 81.00 fJ |

## Interpretation

The load sweep shows the expected CMOS behavior: increasing capacitive load increases propagation delay and load-switching energy. The 20 fF case matches the earlier single-run mux simulation, giving an average delay of approximately 26.64 ps and an output-load switching energy estimate of approximately 32.4 fJ.

## Generated artifacts

- CSV: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv`
- Delay plot: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_delay_vs_load.png`
- Energy plot: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_energy_vs_load.png`
- ngspice logs: `results/partD_cmos/pareto_cmp_primitive/load_sweep/*_ngspice.log`
- waveform CSVs: `results/partD_cmos/pareto_cmp_primitive/load_sweep/*_waveform.csv`

## Evidence boundary

This is representative primitive-level ngspice evidence using a first-order MOS model. It is not full-chip SPICE, fabricated-silicon measurement, foundry signoff, or calibrated SKY130 transistor-level simulation.

## Paper-safe wording

To complement the standard-cell OpenROAD implementation, a representative 2:1 transmission-gate mux from the Pareto-C0 selector path was evaluated using ngspice. A load sweep from 5 fF to 50 fF showed increasing delay from approximately 10.38 ps to 54.31 ps, while the estimated output-load switching energy increased from 8.10 fJ to 81.00 fJ under a 1.8 V supply.
