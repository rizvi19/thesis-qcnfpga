# FDPE-V3 OpenROAD-flow Physical Design Status

## Target

- Kernel: FDPE-V3 LUT64 interpolation kernel
- Top module: fdpe_kernel_v3_lut64_interp
- Platform: sky130hd
- Flow: OpenROAD-flow-scripts

## Current status

- Synthesis: passed
- Floorplan: passed
- Placement: passed
- CTS: passed
- Route: passed
- Finish/GDS: passed
- Floorplan design area: 19903 µm²
- Floorplan utilization: 11%
- Detailed placement design area: 21593 µm²
- Detailed placement utilization: 12%
- CTS design area: 22184 µm²
- CTS utilization: 13%
- Final design area: 22186 µm²
- Final utilization: 13%
- Final GDS generated: 6_final.gds
- Final DEF generated: 6_final.def
- Final SPEF generated: 6_final.spef
- Detailed route completed with 0 final violations
- Antenna check reported 0 net violations and 0 pin violations
- Final IR drop is approximately 0.04%

## Interpretation

FDPE-V3 is now physically implemented through the SKY130/OpenROAD flow.

This supports the area-accuracy VLSI feasibility story for the LUT64 linear-interpolation FDPE approximation.

## Evidence boundary

This is open-source SKY130/OpenROAD physical-design evidence. It is not fabricated silicon and not commercial signoff.
