# SKAG-W1 OpenROAD-flow Physical Design Status

## Target

- Kernel: SKAG-W1 fixed-alpha shift-add score kernel
- Top module: skag_weight_w1_shiftadd
- Platform: sky130hd
- Flow: OpenROAD-flow-scripts

## Current status

- Synthesis: passed
- Floorplan: passed
- Placement: passed
- CTS: passed
- Route: passed
- Finish/GDS: passed
- Floorplan design area: 5597 µm²
- Floorplan utilization: 22%
- Global placement design area: 5746 µm²
- Global placement utilization: 23%
- Detailed placement / resized design area: 6172 µm²
- Detailed placement / resized utilization: 25%
- CTS design area: 6451 µm²
- CTS utilization: 26%
- Final design area: 6451 µm²
- Final utilization: 26%
- Final GDS generated: 6_final.gds
- Final DEF generated: 6_final.def
- Final SPEF generated: 6_final.spef
- Routing completed with 0 final detailed-route violations
- Antenna check reported 0 net violations and 0 pin violations
- Final IR drop is approximately 0.01%


## Current caveats

- One input port is missing set_input_delay.
- Some endpoints are still unconstrained.
- These warnings should be cleaned before final physical-design reporting.

## Next physical-design step

Collect final reports and create thesis/paper summary tables.

Recommended next implementation target:

- FDPE-V3 OpenROAD physical flow, or
- Pareto-C0 OpenROAD physical flow
