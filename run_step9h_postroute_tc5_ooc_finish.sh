#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

OUTDIR="results/phase9h_ooc"
mkdir -p "$OUTDIR"

vivado -mode batch -source tcl/run_top_tc5_impl_ooc_finish.tcl | tee "$OUTDIR/vivado_top_tc5_impl_ooc_finish.log"

python3 tools/summarize_top_tc5_impl_ooc.py \
  --timing-rpt "$OUTDIR/qflow_top_tc5_impl_ooc_timing_summary.rpt" \
  --util-rpt "$OUTDIR/qflow_top_tc5_impl_ooc_utilization.rpt" \
  --route-status-rpt "$OUTDIR/qflow_top_tc5_impl_ooc_route_status.rpt" \
  --out-json "$OUTDIR/qflow_top_tc5_impl_ooc_summary.json" \
  --out-md "$OUTDIR/qflow_top_tc5_impl_ooc_summary.md"

echo "Step 9H OOC post-route implementation finalize complete."
echo " - $OUTDIR/qflow_top_tc5_impl_ooc_summary.json"
echo " - $OUTDIR/qflow_top_tc5_impl_ooc_summary.md"
echo " - $OUTDIR/vivado_top_tc5_impl_ooc_finish.log"
