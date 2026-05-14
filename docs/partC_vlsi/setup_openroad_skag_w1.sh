#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

ORFS_ROOT="${OPENROAD_FLOW_ROOT:-$HOME/Documents/VLSI/tools/OpenROAD-flow-scripts}"
FLOW_DIR="$ORFS_ROOT/flow"

PLATFORM="sky130hd"
DESIGN_NICKNAME="qflow_skag_w1"
DESIGN_NAME="skag_weight_w1_shiftadd"

SRC_RTL="$ROOT_DIR/asic/skag_weight_kernel/src/skag_weight_w1_shiftadd.v"

ORFS_SRC_DIR="$FLOW_DIR/designs/src/$DESIGN_NICKNAME"
ORFS_CFG_DIR="$FLOW_DIR/designs/$PLATFORM/$DESIGN_NICKNAME"

OUT_DIR="$ROOT_DIR/results/partC_vlsi/openroad_skag_w1_setup"
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/setup_openroad_skag_w1.log"
: > "$LOG"

log() {
  echo "$@" | tee -a "$LOG"
}

log "============================================================"
log "QFlow SKAG-W1 OpenROAD-flow setup"
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

mkdir -p "$ORFS_SRC_DIR"
mkdir -p "$ORFS_CFG_DIR"

cp "$SRC_RTL" "$ORFS_SRC_DIR/$DESIGN_NAME.v"

cat > "$ORFS_CFG_DIR/config.mk" <<EOM
# QFlow SKAG-W1 OpenROAD-flow configuration
# Generated from thesis repo: $ROOT_DIR

export DESIGN_NICKNAME = $DESIGN_NICKNAME
export DESIGN_NAME = $DESIGN_NAME
export PLATFORM = $PLATFORM

export VERILOG_FILES = \$(DESIGN_HOME)/src/\$(DESIGN_NICKNAME)/\$(DESIGN_NAME).v
export SDC_FILE = \$(DESIGN_HOME)/\$(PLATFORM)/\$(DESIGN_NICKNAME)/constraint.sdc

# Conservative first physical-design attempt.
# We keep the die/core generous because this is the first flow bring-up.
# export CORE_UTILIZATION = 30  # disabled: using fixed DIE_AREA/CORE_AREA
# export PLACE_DENSITY = 0.45  # disabled: using fixed DIE_AREA/CORE_AREA

export DIE_AREA = 0 0 200 200
export CORE_AREA = 20 20 180 180
EOM

cat > "$ORFS_CFG_DIR/constraint.sdc" <<'EOM'
# QFlow SKAG-W1 first physical-design constraint file
# OpenROAD-compatible SDC version

set clk_name clk
set clk_period 10.000

create_clock -name core_clock -period $clk_period [get_ports $clk_name]

# Explicit input delays. Avoid remove_from_collection because this OpenROAD/STA
# environment does not support it in the current flow context.
set_input_delay 1.000 -clock core_clock [get_ports start]
set_input_delay 1.000 -clock core_clock [get_ports {key_count[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {avg_fidelity_q016[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {arrival_rate_q88[*]}]
set_input_delay 1.000 -clock core_clock [get_ports {qber_q016[*]}]

set_output_delay 1.000 -clock core_clock [get_ports done]
set_output_delay 1.000 -clock core_clock [get_ports {score_q16[*]}]

# Treat reset as asynchronous control for this first implementation.
set_false_path -from [get_ports rst_n]
EOM

log "[PASS] copied RTL to: $ORFS_SRC_DIR/$DESIGN_NAME.v"
log "[PASS] wrote config: $ORFS_CFG_DIR/config.mk"
log "[PASS] wrote SDC: $ORFS_CFG_DIR/constraint.sdc"

log ""
log "===== Generated config.mk ====="
sed -n '1,120p' "$ORFS_CFG_DIR/config.mk" | tee -a "$LOG"

log ""
log "===== Generated constraint.sdc ====="
sed -n '1,120p' "$ORFS_CFG_DIR/constraint.sdc" | tee -a "$LOG"

log ""
log "To run synthesis:"
log "cd $FLOW_DIR"
log "make DESIGN_CONFIG=designs/$PLATFORM/$DESIGN_NICKNAME/config.mk synth"

log ""
log "============================================================"
log "Setup finished. Log:"
log "$LOG"
log "============================================================"
