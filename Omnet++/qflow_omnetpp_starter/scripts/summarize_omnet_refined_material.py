#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

def main():
    root = Path("summary_plots_paper_refined")
    summ = root / "omnet_final_summary.csv"
    paper = root / "omnet_paper_ready_table.csv"
    high = root / "omnet_final_highlights.json"
    if not summ.exists():
        raise SystemExit("Missing summary_plots_paper_refined/omnet_final_summary.csv")

    df = pd.read_csv(summ)
    out = []
    out.append("# QFlow OMNeT++ Refined Snapshot\n\n")
    out.append("## First 20 rows of omnet_final_summary.csv\n\n")
    out.append(df.head(20).to_markdown(index=False))
    out.append("\n\n")
    if paper.exists():
        p = pd.read_csv(paper)
        out.append("## Paper-ready comparison table preview\n\n")
        out.append(p.head(20).to_markdown(index=False))
        out.append("\n\n")
    if high.exists():
        j = json.loads(high.read_text())
        out.append("## Highlights JSON\n\n```json\n")
        out.append(json.dumps(j, indent=2))
        out.append("\n```\n")
    path = root / "omnet_refined_snapshot.md"
    path.write_text("".join(out), encoding="utf-8")
    print(f"Wrote {path}")

if __name__ == "__main__":
    main()
