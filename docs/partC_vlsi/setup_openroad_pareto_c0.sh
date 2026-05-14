#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

ORFS_ROOT="${OPENROAD_FLOW_ROOT:-$HOME/Documents/VLSI/tools/OpenROAD-flow-scripts}"
FLOW_DIR="$ORFS_ROOT/flow"

PLATFORM="sky130hd"
DESIGN_NICKNAME="qflow_pareto_c0"
DESIGN_NAME="pareto_cmp_c0_full"

SRC_RTL="$ROOT_DIR/asic/pareto_cmp_kernel/src/pareto_cmp_c0_full.v"

ORFS_SRC_DIR="$FLOW_DIR/designs/src/$DESIGN_NICKNAME"
ORFS_CFG_DIR="$FLOW_DIR/designs/$PLATFORM/$DESIGN_NICKNAME"

OUT_DIR="$ROOT_DIR/results/partC_vlsi/openroad_pareto_c0_setup"
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/setup_openroad_pareto_c0.log"
: > "$LOG"

log() {
  echo "$@" | tee -a "$LOG"
}

log "============================================================"
log "QFlow Pareto-C0 OpenROAD-flow setup"
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
# QFlow Pareto-C0 OpenROAD-flow configuration
# Generated from thesis repo: $ROOT_DIR

export DESIGN_NICKNAME = $DESIGN_NICKNAME
export DESIGN_NAME = $DESIGN_NAME
export PLATFORM = $PLATFORM

export VERILOG_FILES = \$(DESIGN_HOME)/src/\$(DESIGN_NICKNAME)/\$(DESIGN_NAME).v
export SDC_FILE = \$(DESIGN_HOME)/\$(PLATFORM)/\$(DESIGN_NICKNAME)/constraint.sdc

# Fixed die/core area method.
# Pareto-C0 is compact, so this is intentionally small but still safe.
export DIE_AREA = 0 0 200 200
export CORE_AREA = 20 20 180 180
EOM

# Generate an OpenROAD-compatible SDC automatically from the RTL port list.
python3 - <<PY
from pathlib import Path
import re

rtl_path = Path("$ORFS_SRC_DIR/$DESIGN_NAME.v")
sdc_path = Path("$ORFS_CFG_DIR/constraint.sdc")

text = rtl_path.read_text()

ports = []
for line in text.splitlines():
    line = line.strip()
    line = line.split("//")[0].strip()
    if not line:
        continue

    m = re.match(r"(input|output)\\s+(?:wire|reg)?\\s*(?:\\[[^\\]]+\\])?\\s*([A-Za-z_][A-Za-z0-9_]*)", line)
    if m:
        direction, name = m.group(1), m.group(2)
        ports.append((direction, name, "[" in line and "]" in line))

inputs = [(n, bus) for d, n, bus in ports if d == "input"]
outputs = [(n, bus) for d, n, bus in ports if d == "output"]

clock_candidates = [n for n, _ in inputs if n in ("clk", "clock", "i_clk")]
clk = clock_candidates[0] if clock_candidates else "clk"

reset_names = {n for n, _ in inputs if n in ("rst_n", "reset_n", "rst", "reset", "areset_n")}

def port_expr(name, is_bus):
    return f"{{{name}[*]}}" if is_bus else name

lines = []
lines.append("# QFlow Pareto-C0 first physical-design constraint file")
lines.append("# Auto-generated from RTL port declarations")
lines.append("")
lines.append("set clk_name " + clk)
lines.append("set clk_period 10.000")
lines.append("")
lines.append("create_clock -name core_clock -period \$clk_period [get_ports \$clk_name]")
lines.append("")

for name, is_bus in inputs:
    if name == clk:
        continue
    if name in reset_names:
        continue
    lines.append(f"set_input_delay 1.000 -clock core_clock [get_ports {port_expr(name, is_bus)}]")

lines.append("")

for name, is_bus in outputs:
    lines.append(f"set_output_delay 1.000 -clock core_clock [get_ports {port_expr(name, is_bus)}]")

lines.append("")

for name in sorted(reset_names):
    lines.append(f"set_false_path -from [get_ports {name}]")

sdc_path.write_text("\\n".join(lines) + "\\n")

print("[PASS] wrote SDC:", sdc_path)
print("[INFO] clock:", clk)
print("[INFO] reset ports:", sorted(reset_names))
print("[INFO] input ports:", [n for n, _ in inputs])
print("[INFO] output ports:", [n for n, _ in outputs])
PY

log "[PASS] copied RTL to: $ORFS_SRC_DIR/$DESIGN_NAME.v"
log "[PASS] wrote config: $ORFS_CFG_DIR/config.mk"
log "[PASS] wrote SDC: $ORFS_CFG_DIR/constraint.sdc"

log ""
log "===== RTL module/port preview ====="
grep -n "module\\|input\\|output" "$ORFS_SRC_DIR/$DESIGN_NAME.v" | head -120 | tee -a "$LOG" || true

log ""
log "===== Generated config.mk ====="
sed -n '1,120p' "$ORFS_CFG_DIR/config.mk" | tee -a "$LOG"

log ""
log "===== Generated constraint.sdc ====="
sed -n '1,180p' "$ORFS_CFG_DIR/constraint.sdc" | tee -a "$LOG"

log ""
log "To run synthesis:"
log "cd $FLOW_DIR"
log "make DESIGN_CONFIG=designs/$PLATFORM/$DESIGN_NICKNAME/config.mk synth"

log ""
log "============================================================"
log "Setup finished. Log:"
log "$LOG"
log "============================================================"
