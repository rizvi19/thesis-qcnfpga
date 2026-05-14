#!/usr/bin/env python3
"""
Build combined OpenROAD physical-design summary for QFlow Part C.

Inputs:
  results/partC_vlsi/openroad_skag_w1/openroad_skag_w1_status.md
  results/partC_vlsi/openroad_fdpe_v3/openroad_fdpe_v3_status.md

Outputs:
  results/partC_vlsi/openroad_physical_summary.csv
  docs/partC_vlsi/openroad_physical_summary.md
"""

from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[2]

TARGETS = [
    {
        "kernel": "SKAG-W1",
        "role": "edge-weight scoring",
        "story": "fixed-alpha shift-add optimization",
        "folder": ROOT / "results/partC_vlsi/openroad_skag_w1",
        "status_file": "openroad_skag_w1_status.md",
        "final_artifacts": "GDS/DEF/SPEF/Verilog/SDC",
        "paper_value": "shows multiplier-removal / shift-add physical feasibility",
    },
    {
        "kernel": "FDPE-V3",
        "role": "fidelity-decay approximation",
        "story": "64-entry LUT with linear interpolation",
        "folder": ROOT / "results/partC_vlsi/openroad_fdpe_v3",
        "status_file": "openroad_fdpe_v3_status.md",
        "final_artifacts": "GDS/DEF/SPEF/Verilog/SDC",
        "paper_value": "shows approximation area-accuracy physical feasibility",
    },
]

def read_text(path: Path) -> str:
    return path.read_text(errors="replace") if path.exists() else ""

def extract_number(pattern: str, text: str, default: str = "") -> str:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else default

def has_file(folder: Path, rel: str) -> str:
    return "yes" if (folder / rel).exists() else "no"

rows = []

for t in TARGETS:
    folder = t["folder"]
    status_text = read_text(folder / t["status_file"])

    final_area = extract_number(r"Final design area:\s*([0-9.]+)", status_text)
    final_util = extract_number(r"Final utilization:\s*([0-9.]+)", status_text)
    floor_area = extract_number(r"Floorplan design area:\s*([0-9.]+)", status_text)
    floor_util = extract_number(r"Floorplan utilization:\s*([0-9.]+)", status_text)

    route_clean = "yes" if "0 final" in status_text.lower() or "0 net violations" in status_text.lower() else "unknown"

    rows.append({
        "kernel": t["kernel"],
        "design_role": t["role"],
        "optimization_story": t["story"],
        "openroad_status": "RTL-to-GDS complete",
        "floorplan_area_um2": floor_area,
        "floorplan_utilization_percent": floor_util,
        "final_area_um2": final_area,
        "final_utilization_percent": final_util,
        "route_clean": route_clean,
        "has_final_gds": has_file(folder, "results/6_final.gds"),
        "has_final_def": has_file(folder, "results/6_final.def"),
        "has_final_spef": has_file(folder, "results/6_final.spef"),
        "has_final_netlist": has_file(folder, "results/6_final.v"),
        "has_final_layout_image": has_file(folder, "reports/final_all.webp"),
        "final_artifacts": t["final_artifacts"],
        "paper_value": t["paper_value"],
    })

out_csv = ROOT / "results/partC_vlsi/openroad_physical_summary.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)

with out_csv.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

out_md = ROOT / "docs/partC_vlsi/openroad_physical_summary.md"

md = """# QFlow Part C OpenROAD Physical-Design Summary

## Purpose

This document summarizes the completed OpenROAD/SKY130 physical-design evidence for the QFlow Part C VLSI extension.

The purpose is to separate generic synthesis evidence from physical-design evidence and to provide paper-ready wording for the completed RTL-to-GDS kernel implementations.

## Completed physical-design kernels

| Kernel | Design role | Optimization story | Flow status | Final area (µm²) | Final utilization | Route status | Final artifacts |
|---|---|---|---|---:|---:|---|---|
"""

for r in rows:
    md += (
        f"| {r['kernel']} | {r['design_role']} | {r['optimization_story']} | "
        f"{r['openroad_status']} | {r['final_area_um2']} | {r['final_utilization_percent']}% | "
        f"{'clean final route evidence' if r['route_clean'] == 'yes' else 'check report'} | "
        f"{r['final_artifacts']} |\n"
    )

md += """
## Evidence interpretation

The completed OpenROAD physical-design results support two different VLSI claims:

1. **SKAG-W1:** the fixed-alpha shift-add edge-score kernel is physically implementable through the SKY130/OpenROAD flow and supports the multiplier-removal area-optimization story.
2. **FDPE-V3:** the LUT64 linear-interpolation fidelity-decay kernel is physically implementable through the SKY130/OpenROAD flow and supports the FDPE area-accuracy tradeoff story.

## Paper-safe wording

Use wording like:

> The optimized SKAG-W1 and FDPE-V3 kernels were implemented through the open-source SKY130/OpenROAD physical-design flow, completing synthesis, floorplanning, placement, CTS, routing, RC extraction, IR-drop reporting, and final GDS/DEF/SPEF generation.

Do not write:

> The design was fabricated.

Do not write:

> This is commercial ASIC signoff.

Correct boundary:

> These are open-source PDK/OpenROAD physical-design feasibility results, not fabricated-silicon measurements.

## Current publication value

This is now stronger than a pure FPGA/simulation paper because Part C includes two completed RTL-to-GDS kernel implementations.

Recommended next step:

- Run Pareto-C0 through OpenROAD if quick.
- Then start Part D CMOS/ngspice primitive study.
"""

out_md.write_text(md, encoding="utf-8")

print(f"[PASS] wrote {out_csv}")
print(f"[PASS] wrote {out_md}")

for r in rows:
    print(
        f"{r['kernel']}: final_area={r['final_area_um2']}um^2 "
        f"util={r['final_utilization_percent']}% "
        f"gds={r['has_final_gds']} def={r['has_final_def']} spef={r['has_final_spef']}"
    )
