#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

def main():
    root = Path("summary_plots_paper")
    summary_csv = root / "omnet_paper_summary.csv"
    highlights_json = root / "omnet_paper_highlights.json"
    if not summary_csv.exists():
        raise SystemExit("Missing summary_plots_paper/omnet_paper_summary.csv")
    df = pd.read_csv(summary_csv)
    highs = json.loads(highlights_json.read_text()) if highlights_json.exists() else {}

    md = []
    md.append("# OMNeT++ Paper Material Snapshot\n\n")
    md.append("## First 20 aggregated rows\n\n")
    md.append(df.head(20).to_markdown(index=False))
    md.append("\n\n## Highlights JSON\n\n```json\n")
    md.append(json.dumps(highs, indent=2))
    md.append("\n```\n")
    out = root / "omnet_paper_material_snapshot.md"
    out.write_text("".join(md), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
