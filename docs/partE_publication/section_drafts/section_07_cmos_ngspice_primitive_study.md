# Section Draft: CMOS/ngspice Primitive Study

## Section purpose

This section reports the representative transistor-level CMOS/ngspice primitive study used to complement the OpenROAD standard-cell physical-design evidence.

Part C demonstrated that the selected QFlow kernels can be taken through an open-source SKY130/OpenROAD RTL-to-GDS flow. Part D adds a lower-level circuit perspective by evaluating a representative selector primitive from the Pareto-C0 route-selection datapath.

## Primitive selection

The selected primitive is a 2:1 transmission-gate mux.

This primitive was selected because Pareto-C0 performs route-candidate selection and comparison, where selector/mux-style data movement is a basic circuit-level behavior. The goal is not to transistor-model the complete QFlow system, but to provide a representative primitive-level CMOS view of selector delay and capacitive-load behavior.

## Simulation setup

The mux was simulated using ngspice with a first-order Level-1 MOS model. The supply voltage was set to 1.8 V. The initial single-run experiment used a 20 fF load capacitance, and a load sweep was later performed for 5 fF, 10 fF, 20 fF, and 50 fF.

The transmission-gate mux uses complementary select signals. When sel = 1, input in1 is passed to the output; when sel = 0, input in0 is selected. The transient experiment toggles in1 while sel selects that input, allowing propagation delay to be measured at the output.

## Single-load result

For the 20 fF load case, ngspice reported:

| Metric | Value |
|---|---:|
| Low-to-high delay, tplh | 27.02 ps |
| High-to-low delay, tphl | 26.25 ps |
| Average delay | 26.64 ps |
| Estimated output-load switching energy | 32.4 fJ |

The energy value is reported using the first-pass capacitive switching estimate E = 0.5CV^2. The raw VDD-source current integration is not used as the main switching-energy value because the output node in a transmission-gate mux is primarily charged through the selected input source, and the simple Level-1 MOS model does not provide calibrated transistor/parasitic behavior.

## Load-sweep result

The load sweep shows the expected CMOS behavior: larger output capacitance increases both delay and load-switching energy.

| Load capacitance | tplh | tphl | Average delay | Estimated load switching energy |
|---:|---:|---:|---:|---:|
| 5 fF | 10.24 ps | 10.52 ps | 10.38 ps | 8.10 fJ |
| 10 fF | 17.29 ps | 17.25 ps | 17.27 ps | 16.20 fJ |
| 20 fF | 27.02 ps | 26.25 ps | 26.64 ps | 32.40 fJ |
| 50 fF | 56.60 ps | 52.01 ps | 54.31 ps | 81.00 fJ |

## Interpretation

The ngspice result supports the expected selector-level behavior beneath the Pareto-C0 route-selection datapath. The delay increases from approximately 10.38 ps at 5 fF to 54.31 ps at 50 fF, while the estimated output-load switching energy increases from 8.10 fJ to 81.00 fJ. This provides a small but useful transistor-level complement to the OpenROAD physical-design evidence.

## Figure references

Recommended figures for this section:

- TG mux transient waveform.
- TG mux delay versus load capacitance.
- TG mux estimated load-switching energy versus load capacitance.

Available artifacts:

- `results/partD_cmos/pareto_cmp_primitive/tg_mux_2to1_waveform.png`
- `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_delay_vs_load.png`
- `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_energy_vs_load.png`
- `results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_load_sweep.csv`

## Safe wording

The correct claim is:

A representative 2:1 transmission-gate mux from the Pareto-C0 selector path was evaluated using ngspice with a first-order MOS model. The result provides primitive-level delay and capacitive-load switching evidence.

Do not claim:

- full-chip transistor-level simulation,
- fabricated-silicon measurement,
- foundry signoff,
- calibrated SKY130 transistor-level simulation,
- or full-chip power estimation.

## Limitations

This ngspice experiment uses a simple Level-1 MOS model and is intended only as representative primitive-level evidence. It does not replace calibrated PDK-level transistor simulation, extracted-layout SPICE, or fabricated-silicon measurement. Future work may replace the first-order model with calibrated SKY130 transistor models and extracted parasitics from a layout-level primitive.

## Paper-ready paragraph

To complement the standard-cell OpenROAD implementation, a representative 2:1 transmission-gate mux from the Pareto-C0 route-selection path was evaluated using ngspice. Under a 1.8 V supply and 20 fF load, the mux showed an average propagation delay of approximately 26.64 ps. A load sweep from 5 fF to 50 fF showed delay increasing from approximately 10.38 ps to 54.31 ps, while the estimated output-load switching energy increased from 8.10 fJ to 81.00 fJ using the 0.5CV^2 estimate. These results provide primitive-level CMOS evidence for selector behavior while remaining distinct from full-chip SPICE, calibrated PDK-level signoff, or fabricated-silicon measurement.
