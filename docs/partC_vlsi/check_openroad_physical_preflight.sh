#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUT_DIR="results/partC_vlsi/openroad_preflight"
mkdir -p "$OUT_DIR"

LOG="$OUT_DIR/openroad_physical_preflight.log"
: > "$LOG"

log() {
  echo "$@" | tee -a "$LOG"
}

check_cmd() {
  local cmd="$1"
  log ""
  log "===== Checking command: $cmd ====="
  if command -v "$cmd" >/dev/null 2>&1; then
    log "[PASS] $cmd found: $(command -v "$cmd")"
    {
      "$cmd" -version 2>/dev/null || \
      "$cmd" -V 2>/dev/null || \
      "$cmd" --version 2>/dev/null || \
      true
    } | head -20 | tee -a "$LOG"
  else
    log "[FAIL] $cmd not found in PATH"
  fi
}

log "============================================================"
log "QFlow Part C OpenROAD Physical Design Preflight"
log "============================================================"
log "Repo: $ROOT_DIR"
log "Date: $(date)"
log "Branch: $(git branch --show-current)"
log ""

log "===== Git status ====="
git status --short | tee -a "$LOG"

log ""
log "===== Kernel RTL existence ====="
for f in \
  asic/skag_weight_kernel/src/skag_weight_w1_shiftadd.v \
  asic/fdpe_kernel/src/fdpe_kernel_v3_lut64_interp.v \
  asic/pareto_cmp_kernel/src/pareto_cmp_c0_full.v
do
  if [[ -f "$f" ]]; then
    log "[PASS] found $f"
  else
    log "[FAIL] missing $f"
  fi
done

check_cmd yosys
check_cmd openroad
check_cmd sta
check_cmd opensta
check_cmd klayout
check_cmd magic
check_cmd make
check_cmd python3

log ""
log "===== OpenROAD-flow-scripts discovery ====="

CANDIDATES=()
if [[ -n "${OPENROAD_FLOW_ROOT:-}" ]]; then
  CANDIDATES+=("$OPENROAD_FLOW_ROOT")
fi

CANDIDATES+=(
  "$HOME/Documents/VLSI/tools/OpenROAD-flow-scripts"
  "$HOME/Work/tools/OpenROAD-flow-scripts"
  "$HOME/tools/OpenROAD-flow-scripts"
  "/opt/OpenROAD-flow-scripts"
)

ORFS_FOUND=""

for d in "${CANDIDATES[@]}"; do
  if [[ -d "$d" ]]; then
    log "[PASS] candidate exists: $d"
    if [[ -d "$d/flow" ]]; then
      log "[PASS] flow directory exists: $d/flow"
      ORFS_FOUND="$d"
      break
    else
      log "[WARN] no flow directory inside: $d"
    fi
  else
    log "[MISS] $d"
  fi
done

if [[ -z "$ORFS_FOUND" ]]; then
  log "[FAIL] OpenROAD-flow-scripts root not found"
else
  log "[PASS] OPENROAD_FLOW_ROOT_CANDIDATE=$ORFS_FOUND"
fi

log ""
log "===== OpenROAD-flow-scripts platform check ====="

if [[ -n "$ORFS_FOUND" ]]; then
  FLOW_DIR="$ORFS_FOUND/flow"

  if [[ -d "$FLOW_DIR/platforms" ]]; then
    log "[PASS] platforms directory exists: $FLOW_DIR/platforms"
    log "Available platforms:"
    find "$FLOW_DIR/platforms" -maxdepth 1 -mindepth 1 -type d -printf "%f\n" | sort | tee -a "$LOG"
  else
    log "[FAIL] platforms directory missing: $FLOW_DIR/platforms"
  fi

  log ""
  log "Checking common SKY130 platform folders:"
  for p in sky130hd sky130hs sky130_fd_sc_hd sky130_fd_sc_hd__tt_025C_1v80; do
    if [[ -d "$FLOW_DIR/platforms/$p" ]]; then
      log "[PASS] found platform: $p"
    else
      log "[MISS] platform not found: $p"
    fi
  done

  log ""
  log "Checking flow Makefile:"
  if [[ -f "$FLOW_DIR/Makefile" ]]; then
    log "[PASS] found $FLOW_DIR/Makefile"
  else
    log "[FAIL] missing $FLOW_DIR/Makefile"
  fi

  log ""
  log "Checking flow designs folder:"
  if [[ -d "$FLOW_DIR/designs" ]]; then
    log "[PASS] found $FLOW_DIR/designs"
  else
    log "[FAIL] missing $FLOW_DIR/designs"
  fi
fi

log ""
log "===== Environment variables ====="
for v in OPENROAD_FLOW_ROOT OPENROAD_EXE YOSYS_EXE PDK_ROOT PLATFORM DESIGN_CONFIG; do
  log "$v=${!v:-<unset>}"
done

log ""
log "============================================================"
log "Preflight finished. Log written to:"
log "$LOG"
log "============================================================"
