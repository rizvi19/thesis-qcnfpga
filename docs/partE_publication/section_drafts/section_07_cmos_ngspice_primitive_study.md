# Section Draft: CMOS/ngspice Primitive Study

## Section purpose

This section reports the representative transistor-level CMOS/ngspice primitive study used to complement the OpenROAD standard-cell physical-design evidence.

The purpose of this section is not to claim full-chip SPICE simulation. Instead, it provides circuit-level supporting evidence for primitive selector and comparator behaviors used in the Pareto-C0 route-candidate selection path.

## Connection to QFlow

The Pareto-C0 kernel performs route-candidate selection and comparison. At the circuit level, this behavior contains two important primitive classes:

1. selector/mux behavior, represented by a 2:1 transmission-gate mux;
2. comparator/equality behavior, represented by a 1-bit XNOR/equality primitive.

These primitives were selected because they directly support the route-selection datapath and avoid turning the CMOS study into unrelated textbook circuit experiments.

## Simulation setup

The CMOS primitive simulations were performed using ngspice with simple first-order Level-1 MOS models. The supply voltage was set to 1.8 V. The baseline load capacitance was 20 fF. For the mux primitive, an additional load sweep was performed for 5 fF, 10 fF, 20 fF, and 50 fF.

Because these simulations use first-order transistor models, they are interpreted as representative primitive-level evidence, not foundry-calibrated signoff.

## 2:1 transmission-gate mux result

The 2:1 transmission-gate mux represents selector behavior in the Pareto-C0 route-selection path. In the baseline 20 fF case, the mux produced the following delay measurements:

| Metric | Value |
|---|---:|
| Low-to-high delay, tplh | 27.02 ps |
| High-to-low delay, tphl | 26.25 ps |
| Average delay | 26.64 ps |
| Estimated load switching energy | 32.40 fJ |

The estimated energy is computed using the first-pass capacitive switching estimate E = 0.5CV^2.

## Mux load-sweep result

The mux load sweep shows the expected CMOS trend: increasing output capacitance increases both delay and estimated load-switching energy.

| Load capacitance | Average delay | Estimated load switching energy |
|---:|---:|---:|
| 5 fF | 10.38 ps | 8.10 fJ |
| 10 fF | 17.27 ps | 16.20 fJ |
| 20 fF | 26.64 ps | 32.40 fJ |
| 50 fF | 54.31 ps | 81.00 fJ |

The delay increases from approximately 10.38 ps at 5 fF to 54.31 ps at 50 fF, while the estimated load-switching energy increases from 8.10 fJ to 81.00 fJ.

## 1-bit XNOR/equality primitive result

The XNOR/equality primitive represents comparator/equality behavior in the Pareto-C0 route-candidate comparison path. In the 20 fF case, ngspice reported:

| Metric | Value |
|---|---:|
| Low-to-high delay, tplh | 27.02 ps |
| High-to-low delay, tphl | 26.25 ps |
| Average delay | 26.64 ps |
| Estimated load switching energy | 32.40 fJ |

This result provides comparator-side primitive evidence that complements the mux/selector experiment.

## Generated artifacts

The main artifacts for this section are:

- TG mux waveform: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png`
- TG mux summary: `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_summary.csv`
- TG mux load sweep: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv`
- TG mux delay plot: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_delay_vs_load.png`
- TG mux energy plot: `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_energy_vs_load.png`
- XNOR waveform: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_waveform.png`
- XNOR summary: `results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_summary.csv`
- Part D final summary: `docs/partD_cmos/partD_cmos_final_summary.md`

## Interpretation

The CMOS/ngspice results support the expected transistor-level behavior of selected route-selection primitives. The mux experiment shows selector delay and capacitive-load scaling, while the XNOR/equality experiment shows comparator-style primitive behavior. Together, they provide a circuit-level support layer beneath the OpenROAD standard-cell implementation.

## Evidence boundary

These results are representative primitive-level ngspice simulations using simple Level-1 MOS models.

They are not:

- full-chip SPICE simulations,
- fabricated-silicon measurements,
- foundry signoff,
- commercial signoff,
- calibrated SKY130 transistor-level simulations,
- or extracted-layout SPICE simulations.

## Paper-ready paragraph

To complement the standard-cell OpenROAD physical implementation, representative CMOS primitives from the Pareto-C0 route-selection path were evaluated using ngspice. A 2:1 transmission-gate mux was used to study selector behavior, and a 1-bit XNOR/equality primitive was used to study comparator-side behavior. Under a 1.8 V supply and 20 fF load, both primitives showed an average propagation delay of approximately 26.64 ps. A mux load sweep from 5 fF to 50 fF showed delay increasing from approximately 10.38 ps to 54.31 ps, while the estimated output-load switching energy increased from 8.10 fJ to 81.00 fJ using the 0.5CV^2 estimate. These results provide representative transistor-level support for the route-selection datapath while remaining distinct from full-chip SPICE, foundry signoff, or fabricated-silicon measurement.
