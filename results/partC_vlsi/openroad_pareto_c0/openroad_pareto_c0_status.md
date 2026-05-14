# Pareto-C0 OpenROAD-flow Physical Design Status

## Target

- Kernel: Pareto-C0 full comparator / route-candidate selector
- Top module: pareto_cmp_c0_full
- Platform: sky130hd
- Flow: OpenROAD-flow-scripts

## Current status

- Synthesis: passed
- Floorplan: passed
- Placement: passed
- CTS: passed
- Route: passed
- Finish/GDS: passed
- Detailed placement design area: 3293 µm²
- Detailed placement utilization: 13%
- CTS design area: 3368 µm²
- CTS utilization: 13%
- Final design area: 3368 µm²
- Final utilization: 13%
- Final GDS generated: 6_final.gds
- Final DEF generated: 6_final.def
- Final SPEF generated: 6_final.spef
- Detailed route completed with 0 final violations
- Antenna check reported 0 net violations and 0 pin violations
- Global route estimated period: 3.267 ns
- Global route slack: 6.561 ns
- Final IR drop is approximately 0.00%

## Interpretation

Pareto-C0 is now physically implemented through the SKY130/OpenROAD flow.

This supports the physical feasibility of the QFlow route-candidate selector/comparator block.

## Evidence boundary

This is open-source SKY130/OpenROAD physical-design evidence. It is not fabricated silicon and not commercial signoff.
