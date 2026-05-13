#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / "results" / "aws_preflight"
OUT.mkdir(parents=True, exist_ok=True)

FILES_TO_HASH = [
    "rtl/fdpe_kernel.v",
    "rtl/skag_weight_kernel.v",
    "rtl/path_selector_kernel.v",
    "rtl/qflow_cloud_kernel.v",
    "rtl/qflow_mmio_regs.v",
    "vectors/golden_vectors.csv",
    "vectors/exp_lut.hex",
    "docs/aws_mmio_register_map.md",
]

SNAPSHOTS = [
    "results/evidence_snapshot_02_extended_local_pass",
    "results/evidence_snapshot_03_fixed_seed_random_pass",
    "results/evidence_snapshot_04_control_stress_pass",
    "results/evidence_snapshot_05_x_sanity_pass",
    "results/evidence_snapshot_06_static_lint_pass",
    "results/evidence_snapshot_07_mmio_wrapper_pass",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open(newline="") as f:
        return max(0, sum(1 for _ in f) - 1)

def pass_fail_counts(path: Path) -> tuple[int, int]:
    if not path.exists():
        return (-1, -1)
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return (0, 0)
    col = None
    for candidate in ("pass_fail", "status", "match"):
        if candidate in rows[0]:
            col = candidate
            break
    if col is None:
        return (-1, -1)
    if col == "match":
        passed = sum(str(r[col]).lower() in {"1", "true", "pass"} for r in rows)
    else:
        passed = sum(str(r[col]).upper() == "PASS" for r in rows)
    return (passed, len(rows) - passed)

manifest = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "project": "QFlow Cloud FPGA Kernel",
    "stage": "local_pre_aws_f2_preflight",
    "claim_boundary": "Local RTL/MMIO/static readiness only; not AWS F2 physical execution evidence.",
    "files": [],
    "snapshots": [],
    "quick_metrics": {},
}

for rel in FILES_TO_HASH:
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"Missing required file: {rel}")
    manifest["files"].append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})

for rel in SNAPSHOTS:
    p = ROOT / rel
    if not p.exists():
        raise SystemExit(f"Missing required snapshot directory: {rel}")
    manifest["snapshots"].append({
        "path": rel,
        "has_readme": (p / "README.md").exists(),
        "file_count": len([x for x in p.rglob("*") if x.is_file()]),
    })

metrics = manifest["quick_metrics"]
metrics["golden_vector_rows"] = count_csv_rows(ROOT / "vectors" / "golden_vectors.csv")
metrics["static_compare_rows"] = count_csv_rows(ROOT / "results" / "lint_static" / "hardware_vs_python_static.csv")
metrics["mmio_compare_rows"] = count_csv_rows(ROOT / "results" / "mmio_wrapper" / "mmio_vs_python.csv")
metrics["static_compare_pass_fail"] = pass_fail_counts(ROOT / "results" / "lint_static" / "hardware_vs_python_static.csv")
metrics["mmio_compare_pass_fail"] = pass_fail_counts(ROOT / "results" / "mmio_wrapper" / "mmio_vs_python.csv")

if metrics["golden_vector_rows"] != 215:
    raise SystemExit(f"Expected 215 golden rows, got {metrics['golden_vector_rows']}")
if metrics["mmio_compare_pass_fail"] != (215, 0):
    raise SystemExit(f"Expected MMIO compare PASS=215 FAIL=0, got {metrics['mmio_compare_pass_fail']}")

json_path = OUT / "aws_preflight_manifest.json"
json_path.write_text(json.dumps(manifest, indent=2))

md = []
md += ["# QFlow AWS F2 Preflight Manifest", "", f"Generated UTC: `{manifest['generated_utc']}`", ""]
md += ["## Claim boundary", "", manifest["claim_boundary"], ""]
md += ["## Quick metrics", ""]
for k, v in metrics.items():
    md.append(f"- {k}: `{v}`")
md += ["", "## Hashed files", ""]
for item in manifest["files"]:
    md.append(f"- `{item['path']}` — bytes={item['bytes']}, sha256=`{item['sha256']}`")
md += ["", "## Evidence snapshots", ""]
for snap in manifest["snapshots"]:
    md.append(f"- `{snap['path']}` — readme={snap['has_readme']}, files={snap['file_count']}")

(OUT / "aws_preflight_manifest.md").write_text("\n".join(md) + "\n")
print(f"Wrote {json_path}")
print(f"Wrote {OUT / 'aws_preflight_manifest.md'}")
print("PREFLIGHT_MANIFEST_PASS")
