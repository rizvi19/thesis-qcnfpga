#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
ORFS_ROOT="${OPENROAD_FLOW_ROOT:-$HOME/Documents/VLSI/tools/OpenROAD-flow-scripts}"
FLOW_DIR="$ORFS_ROOT/flow"

PLATFORM="sky130hd"
DESIGN="qflow_skag_w1"
VARIANT="base"

SRC_BASE="$FLOW_DIR"
OUT_DIR="$ROOT_DIR/results/partC_vlsi/openroad_skag_w1"
mkdir -p "$OUT_DIR"/{logs,reports,results,config}

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -e "$src" ]]; then
    cp -r "$src" "$dst"
    echo "[PASS] copied $src -> $dst"
  else
    echo "[MISS] $src"
  fi
}

copy_if_exists "$SRC_BASE/designs/$PLATFORM/$DESIGN/config.mk" "$OUT_DIR/config/config.mk"
copy_if_exists "$SRC_BASE/designs/$PLATFORM/$DESIGN/constraint.sdc" "$OUT_DIR/config/constraint.sdc"
copy_if_exists "$SRC_BASE/designs/src/$DESIGN/skag_weight_w1_shiftadd.v" "$OUT_DIR/config/skag_weight_w1_shiftadd.v"

copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/1_1_yosys.log" "$OUT_DIR/logs/1_1_yosys.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/2_1_floorplan.log" "$OUT_DIR/logs/2_1_floorplan.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/2_1_floorplan.json" "$OUT_DIR/logs/2_1_floorplan.json"

copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/synth_check.txt" "$OUT_DIR/reports/synth_check.txt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/synth_stat.txt" "$OUT_DIR/reports/synth_stat.txt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/2_floorplan_final.rpt" "$OUT_DIR/reports/2_floorplan_final.rpt"

copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/1_synth.v" "$OUT_DIR/results/1_synth.v"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/1_synth.sdc" "$OUT_DIR/results/1_synth.sdc"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/2_floorplan.odb" "$OUT_DIR/results/2_floorplan.odb"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/2_floorplan.sdc" "$OUT_DIR/results/2_floorplan.sdc"

copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/3_1_place_gp_skip_io.log" "$OUT_DIR/logs/3_1_place_gp_skip_io.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/3_2_place_iop.log" "$OUT_DIR/logs/3_2_place_iop.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/3_3_place_gp.log" "$OUT_DIR/logs/3_3_place_gp.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/3_4_place_resized.log" "$OUT_DIR/logs/3_4_place_resized.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/3_5_place_dp.log" "$OUT_DIR/logs/3_5_place_dp.log"

copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/3_global_place.rpt" "$OUT_DIR/reports/3_global_place.rpt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/3_detailed_place.rpt" "$OUT_DIR/reports/3_detailed_place.rpt"

copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/3_place.odb" "$OUT_DIR/results/3_place.odb"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/3_place.sdc" "$OUT_DIR/results/3_place.sdc"

copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/4_1_cts.log" "$OUT_DIR/logs/4_1_cts.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/5_1_grt.log" "$OUT_DIR/logs/5_1_grt.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/5_2_route.log" "$OUT_DIR/logs/5_2_route.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/5_3_fillcell.log" "$OUT_DIR/logs/5_3_fillcell.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/6_1_fill.log" "$OUT_DIR/logs/6_1_fill.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/6_1_merge.log" "$OUT_DIR/logs/6_1_merge.log"
copy_if_exists "$SRC_BASE/logs/$PLATFORM/$DESIGN/$VARIANT/6_report.log" "$OUT_DIR/logs/6_report.log"

copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/4_cts_final.rpt" "$OUT_DIR/reports/4_cts_final.rpt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/5_global_route.rpt" "$OUT_DIR/reports/5_global_route.rpt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/5_route_drc.rpt" "$OUT_DIR/reports/5_route_drc.rpt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/6_finish.rpt" "$OUT_DIR/reports/6_finish.rpt"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/final_all.webp" "$OUT_DIR/reports/final_all.webp"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/final_clocks.webp" "$OUT_DIR/reports/final_clocks.webp"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/final_ir_drop.webp" "$OUT_DIR/reports/final_ir_drop.webp"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/final_placement.webp" "$OUT_DIR/reports/final_placement.webp"
copy_if_exists "$SRC_BASE/reports/$PLATFORM/$DESIGN/$VARIANT/final_routing.webp" "$OUT_DIR/reports/final_routing.webp"

copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/4_cts.odb" "$OUT_DIR/results/4_cts.odb"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/4_cts.sdc" "$OUT_DIR/results/4_cts.sdc"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/5_route.odb" "$OUT_DIR/results/5_route.odb"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/5_route.sdc" "$OUT_DIR/results/5_route.sdc"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.gds" "$OUT_DIR/results/6_final.gds"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.def" "$OUT_DIR/results/6_final.def"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.odb" "$OUT_DIR/results/6_final.odb"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.spef" "$OUT_DIR/results/6_final.spef"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.v" "$OUT_DIR/results/6_final.v"
copy_if_exists "$SRC_BASE/results/$PLATFORM/$DESIGN/$VARIANT/6_final.sdc" "$OUT_DIR/results/6_final.sdc"

cat > "$OUT_DIR/openroad_skag_w1_status.md" <<'EOM'
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
EOM

echo "[PASS] wrote $OUT_DIR/openroad_skag_w1_status.md"
echo "[PASS] SKAG-W1 OpenROAD artifacts collected into $OUT_DIR"
