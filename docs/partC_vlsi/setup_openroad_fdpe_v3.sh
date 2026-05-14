#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

ORFS_ROOT="${OPENROAD_FLOW_ROOT:-$HOME/Documents/VLSI/tools/OpenROAD-flow-scripts}"
FLOW_DIR="$ORFS_ROOT/flow"

PLATFORM="sky130hd"
DESIGN_NICKNAME="qflow_fdpe_v3"
DESIGN_NAME="fdpe_kernel_v3_lut64_interp"

SRC_RTL="$ROOT_DIR/asic/fdpe_kernel/src/fdpe_kernel_v3_lut64_interp.v"
SRC_LUT="$ROOT_DIR/asic/fdpe_kernel/config/exp_lut_64.hex"

ORFS_SRC_DIR="$FLOW_DIR/designs/src/$DESIGN_NICKNAME"
ORFS_CFG_DIR="$FLOW_DIR/designs/$PLATFORM/$DESIGN_NICKNAME"

OUT_DIR="$ROOT_DIR/results/partC_vlsi/openroad_fdpe_v3_setup"
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/setup_openroad_fdpe_v3.log"
: > "$LOG"

log() {
  echo "$@" | tee -a "$LOG"
}

log "============================================================"
log "QFlow FDPE-V3 OpenROAD-flow setup"
log "============================================================"
log "Repo: $ROOT_DIR"
log "ORFS_ROOT: $ORFS_ROOT"
log "FLOW_DIR: $FLOW_DIR"
log "Platform: $PLATFORM"
log "Design nickname: $DESIGN_NICKNAME"
log "Design top: $DESIGN_NAME"
log "Date: $(date)"
log ""

if [[ ! -d "$FLOW_DIR" ]]; then
  log "[FAIL] FLOW_DIR missing: $FLOW_DIR"
  exit 1
fi

if [[ ! -f "$FLOW_DIR/Makefile" ]]; then
  log "[FAIL] OpenROAD-flow Makefile missing: $FLOW_DIR/Makefile"
  exit 1
fi

if [[ ! -d "$FLOW_DIR/platforms/$PLATFORM" ]]; then
  log "[FAIL] Platform missing: $FLOW_DIR/platforms/$PLATFORM"
  exit 1
fi

if [[ ! -f "$SRC_RTL" ]]; then
  log "[FAIL] RTL missing: $SRC_RTL"
  exit 1
fi

if [[ ! -f "$SRC_LUT" ]]; then
  log "[FAIL] LUT missing: $SRC_LUT"
  exit 1
fi

mkdir -p "$ORFS_SRC_DIR"
mkdir -p "$ORFS_CFG_DIR"

cp "$SRC_RTL" "$ORFS_SRC_DIR/$DESIGN_NAME.v"
cp "$SRC_LUT" "$ORFS_SRC_DIR/exp_lut_64.hex"

# Patch readmemh path so Yosys/OpenROAD-flow can find the LUT from the flow directory.
python3 - <<PY
from pathlib import Path

rtl = Path("$ORFS_SRC_DIR/$DESIGN_NAME.v")
s = rtl.read_text()

replacements = [
    ('"asic/fdpe_kernel/config/exp_lut_64.hex"', '"designs/src/$DESIGN_NICKNAME/exp_lut_64.hex"'),
    ('"exp_lut_64.hex"', '"designs/src/$DESIGN_NICKNAME/exp_lut_64.hex"'),
]

changed = False
for old, new in replacements:
    if old in s:
        s = s.replace(old, new)
        changed = True

rtl.write_text(s)

if changed:
    print("[PASS] patched readmemh path for exp_lut_64.hex")
else:
    print("[WARN] no readmemh path replacement was applied; inspect RTL manually")
PY

cat > "$ORFS_CFG_DIR/config.mk" <<EOM
# QFlow FDPE-V3 OpenROAD-flow configuration
# Generated from thesis repo: $ROOT_DIR

export DESIGN_NICKNAME = $DESIGN_NICKNAME
export DESIGN_NAME = $DESIGN_NAME
export PLATFORM = $PLATFORM

export VERILOG_FILES = \$(DESIGN_HOME)/src/\$(DESIGN_NICKNAME)/\$(DESIGN_NAME).v
export SDC_FILE = \$(DESIGN_HOME)/\$(PLATFORM)/\$(DESIGN_NICKNAME)/constraint.sdc

# Fixed die/core area method.
# FDPE-V3 is larger than SKAG-W1 because it has LUT/interpolation logic.
export DIE_AREA = 0 0 500 500
export CORE_AREA = 40 40 460 460
EOM

cat > "$ORFS_CFG_DIR/constraint.sdc" <<'EOM'
# QFlow FDPE-V3 first physical-design constraint file
# OpenROAD-compatible SDC version

set clk_name clk
set clk_period 10.000

create_clock -name core_clock -period $clk_period [get_ports $clk_name]

# Explicit delays. Keep this simple for first flow bring-up.
set_input_delay 1.000 -clock core_clock [get_ports start]
set_input_delay 1.000 -clock core_clock [get_ports {f_init_q016[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {lut_index[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {frac_q08[*]}]

set_output_delay 1.000 -clock core_clock [get_ports done]
set_output_delay 1.000 -clock core_clock [get_ports {fidelity_q016[*]}]

set_false_path -from [get_ports rst_n]
EOM

log "[PASS] copied RTL to: $ORFS_SRC_DIR/$DESIGN_NAME.v"
log "[PASS] copied LUT to: $ORFS_SRC_DIR/exp_lut_64.hex"
log "[PASS] wrote config: $ORFS_CFG_DIR/config.mk"
log "[PASS] wrote SDC: $ORFS_CFG_DIR/constraint.sdc"

log ""
log "===== readmemh check ====="
grep -n "readmemh\\|exp_lut_64" "$ORFS_SRC_DIR/$DESIGN_NAME.v" | tee -a "$LOG" || true

log ""
log "===== Generated config.mk ====="
sed -n '1,120p' "$ORFS_CFG_DIR/config.mk" | tee -a "$LOG"

log ""
log "===== Generated constraint.sdc ====="
sed -n '1,160p' "$ORFS_CFG_DIR/constraint.sdc" | tee -a "$LOG"

log ""
log "To run synthesis:"
log "cd $FLOW_DIR"
log "make DESIGN_CONFIG=designs/$PLATFORM/$DESIGN_NICKNAME/config.mk synth"

log ""
log "============================================================"
log "Setup finished. Log:"
log "$LOG"
log "============================================================"
