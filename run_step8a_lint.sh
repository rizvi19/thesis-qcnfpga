#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="results/phase8"
RTL_FILELIST="qflow_rtl_files.f"
LINT_LOG="$OUT_DIR/verilator_lint.log"
LINT_JSON="$OUT_DIR/verilator_lint_summary.json"
STATUS_JSON="$OUT_DIR/project_status_summary.json"
STATUS_MD="$OUT_DIR/project_status_summary.md"
SYNTAX_LOG="$OUT_DIR/iverilog_syntax_compile.log"
SYNTAX_JSON="$OUT_DIR/iverilog_syntax_compile.json"

mkdir -p "$OUT_DIR" sim

python tools/aggregate_project_status.py \
  --phase0 results/phase0/phase0_freeze_report.md \
  --fdpe results/phase1/fdpe_sim_summary.json \
  --skag results/phase2/skag_sim_summary.txt \
  --prng results/phase3/xorshift_randomness.json \
  --pmo_reduced results/phase4/pmo_ga_reduced_sim_summary.json \
  --pmo_family results/phase5/pmo_ga_family_sim_summary.json \
  --pmo_multigen results/phase6/pmo_ga_multigen_sim_summary.json \
  --top_smoke results/phase7/qflow_top_smoke_sim_summary.json \
  --out-json "$STATUS_JSON" \
  --out-md "$STATUS_MD"

if command -v verilator >/dev/null 2>&1; then
  verilator --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL -Wno-WIDTH -Wno-UNDRIVEN -Wno-MULTITOP -f "$RTL_FILELIST" > "$LINT_LOG" 2>&1 || true
  python tools/parse_verilator_lint.py --log "$LINT_LOG" --out "$LINT_JSON"
  echo "Step 8A lint complete (Verilator mode)."
  echo " - $LINT_LOG"
  echo " - $LINT_JSON"
else
  echo "Verilator not found. Falling back to Icarus syntax compile checks." | tee "$LINT_LOG"
  if iverilog -g2012 -t null -f "$RTL_FILELIST" >> "$LINT_LOG" 2>&1; then
    python - <<'PY'
import json
from pathlib import Path
out = {"tool": "iverilog", "mode": "syntax_compile_fallback", "overall_pass": True, "warning": "Verilator not installed; only syntax compile was performed."}
Path("results/phase8/iverilog_syntax_compile.json").write_text(json.dumps(out, indent=2))
PY
  else
    python - <<'PY'
import json
from pathlib import Path
out = {"tool": "iverilog", "mode": "syntax_compile_fallback", "overall_pass": False, "warning": "Verilator not installed; syntax compile failed. Check log."}
Path("results/phase8/iverilog_syntax_compile.json").write_text(json.dumps(out, indent=2))
PY
  fi
  cp "$SYNTAX_JSON" "$LINT_JSON"
  echo "Step 8A lint complete (Icarus fallback mode)."
  echo " - $LINT_LOG"
  echo " - $SYNTAX_JSON"
fi

echo " - $STATUS_JSON"
echo " - $STATUS_MD"
