#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="results/phase8b"
mkdir -p "$OUT_DIR" logs

python tools/check_vivado_env.py --out "$OUT_DIR/synthprep_env.json"
python tools/aggregate_synth_plan.py --out "$OUT_DIR/synth_plan.json"

# Optional lint-cleaned SKAG copy (does not overwrite unless user opts in)
python tools/emit_skag_clean_patch.py --out rtl/skag_mem_lintclean.v

if python - <<'PY'
import json
from pathlib import Path
p = Path('results/phase8b/synthprep_env.json')
info = json.loads(p.read_text())
raise SystemExit(0 if info.get('vivado_available') else 1)
PY
then
  vivado -mode batch -source tcl/run_ooc_synth.tcl | tee "$OUT_DIR/vivado_ooc.log"
  python tools/collect_ooc_reports.py --reports-dir "$OUT_DIR" --out-json "$OUT_DIR/ooc_report_summary.json" --out-md "$OUT_DIR/ooc_report_summary.md"
  echo "Step 8B synthesis-prep complete (Vivado OOC mode)."
  echo " - $OUT_DIR/vivado_ooc.log"
  echo " - $OUT_DIR/ooc_report_summary.json"
  echo " - $OUT_DIR/ooc_report_summary.md"
else
  python tools/emit_vivado_commands.py --out "$OUT_DIR/vivado_commands.txt"
  echo "Vivado not detected. Generated synthesis-prep artifacts only."
  echo " - $OUT_DIR/synthprep_env.json"
  echo " - $OUT_DIR/synth_plan.json"
  echo " - $OUT_DIR/vivado_commands.txt"
fi
