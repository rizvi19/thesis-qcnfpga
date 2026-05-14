# SKAG-W1 OpenROAD Physical-Design Summary

## Target

- Kernel: SKAG-W1 fixed-alpha shift-add edge-score kernel
- Top module: `skag_weight_w1_shiftadd`
- Platform: `sky130hd`
- Flow: OpenROAD-flow-scripts

## Summary table

| Stage | Status | Area (µm²) | Utilization | Timing / route note | Main output |
|---|---|---:|---:|---|---|
| floorplan | pass | 5597 | 22% | no setup/hold violations reported at floorplan timing repair stage | `2_floorplan.odb` |
| placement | pass | 6172 | 25% | detailed placement completed | `3_place.odb` |
| cts | pass | 6451 | 26% | clock tree synthesized; no setup/hold violations reported | `4_cts.odb` |
| global_route | pass | 6451 | 26% | target=10.000000ns, estimated_period=3.640ns, slack=6.169ns | `5_route.odb` |
| detailed_route | pass | 6451 | 26% | 0 final detailed-route violations observed; antenna=0 net violations, 0 pin violations | `5_route.odb` |
| finish | pass | 6451 | 26% | RC extraction and IR analysis complete; VDD worst IR=9.62e-05V; VSS worst IR=1.37e-04V | `6_final.gds / 6_final.def / 6_final.spef` |

## Final physical artifacts

The final SKAG-W1 OpenROAD run generated:

- `6_final.gds`
- `6_final.def`
- `6_final.odb`
- `6_final.spef`
- `6_final.v`
- `6_final.sdc`

## Paper-safe interpretation

The optimized SKAG-W1 kernel was implemented through the SKY130/OpenROAD physical-design flow from RTL synthesis to final GDS/DEF/SPEF artifacts.

This is open-source physical-design evidence, not fabricated-silicon evidence and not commercial signoff.

## Main conclusion

SKAG-W1 is no longer only an RTL/Yosys optimization. It now has physical-design feasibility evidence with floorplan, placement, CTS, routing, RC extraction, IR-drop analysis, and final GDS generation.
