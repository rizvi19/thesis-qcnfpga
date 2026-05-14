#!/usr/bin/env python3
"""
Generate Part C paper-ready result figures.

Inputs:
  results/partC_vlsi/partC_kernel_evidence_summary.csv
  asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv

Outputs:
  results/partC_vlsi/figures/kernel_area_comparison.png
  results/partC_vlsi/figures/fdpe_area_accuracy_tradeoff.png
"""

from pathlib import Path
import csv
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "results/partC_vlsi/figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

KERNEL_CSV = ROOT / "results/partC_vlsi/partC_kernel_evidence_summary.csv"
FDPE_ERR_CSV = ROOT / "asic/fdpe_kernel/results/fdpe_lut_error_modes_comparison.csv"

def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

# --------------------------------------------------------------------------
# Figure 1: kernel generic-cell area comparison
# --------------------------------------------------------------------------
rows = read_csv(KERNEL_CSV)

labels = [r["variant"].replace("_", "\n") for r in rows]
cells = [int(r["total_cells"]) for r in rows]

plt.figure(figsize=(12, 5))
plt.bar(labels, cells)
plt.ylabel("Generic Yosys cell count")
plt.xlabel("Kernel variant")
plt.title("QFlow Part C Kernel Area Comparison")
plt.xticks(rotation=0, ha="center", fontsize=8)
plt.tight_layout()
plt.savefig(FIG_DIR / "kernel_area_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------------------------------
# Figure 2: FDPE area-accuracy tradeoff
# --------------------------------------------------------------------------
fdpe_rows = [r for r in rows if r["kernel_family"] == "FDPE"]

fdpe_err_rows = read_csv(FDPE_ERR_CSV)
err_map = {(r["lut_entries"], r["mode"]): float(r["max_rel_error_x0_3"]) * 100.0 for r in fdpe_err_rows}

variant_to_key = {
    "V0_256LUT_Q016": ("256", "floor"),
    "V1_128LUT_Q016_FLOOR": ("128", "floor"),
    "V2_128LUT_Q016_LINEAR_INTERP": ("128", "linear"),
    "V3_64LUT_Q016_LINEAR_INTERP": ("64", "linear"),
}

fdpe_labels = [r["variant"].replace("_", "\n") for r in fdpe_rows]
fdpe_cells = [int(r["total_cells"]) for r in fdpe_rows]
fdpe_errors = [
    err_map.get(variant_to_key.get(r["variant"], ("", "")), 0.0)
    for r in fdpe_rows
]

fig, ax1 = plt.subplots(figsize=(10, 5))

x = list(range(len(fdpe_labels)))
ax1.bar(x, fdpe_cells)
ax1.set_ylabel("Generic Yosys cell count")
ax1.set_xlabel("FDPE variant")
ax1.set_xticks(x)
ax1.set_xticklabels(fdpe_labels, fontsize=8)

ax2 = ax1.twinx()
ax2.plot(x, fdpe_errors, marker="o")
ax2.set_ylabel("Max relative error for x∈[0,3] (%)")

plt.title("FDPE Area–Accuracy Tradeoff")
fig.tight_layout()
plt.savefig(FIG_DIR / "fdpe_area_accuracy_tradeoff.png", dpi=300)
plt.close()

print(f"[PASS] wrote {FIG_DIR / 'kernel_area_comparison.png'}")
print(f"[PASS] wrote {FIG_DIR / 'fdpe_area_accuracy_tradeoff.png'}")
