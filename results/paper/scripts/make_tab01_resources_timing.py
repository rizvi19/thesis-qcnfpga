#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
import pandas as pd

PHASE9G = Path("results/phase9g")
PHASE9H = Path("results/phase9h")
PHASE9H_OOC = Path("results/phase9h_ooc")

OUT_CSV = Path("results/paper/data/tables/tab01_resources_timing/tab01_resources_timing.csv")
OUT_TEX = Path("docs/paper/latex/tables/qflow_tab01_resources_timing_main.tex")
OUT_DEBUG = Path("results/paper/data/tables/tab01_resources_timing/source/debug_extracted_keys.json")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def flatten(obj, prefix=""):
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            items.update(flatten(v, key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            key = f"{prefix}[{i}]"
            items.update(flatten(v, key))
    else:
        items[prefix] = obj
    return items


def norm_key(s: str) -> str:
    return (
        s.lower()
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def pick_value(flat: dict, aliases: list[str]):
    norm = {norm_key(k): v for k, v in flat.items()}
    for alias in aliases:
        alias_n = norm_key(alias)
        for k, v in norm.items():
            if alias_n == k or alias_n in k:
                return v
    return None


def to_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def fmt_intish(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "--"
    fv = float(v)
    if abs(fv - round(fv)) < 1e-9:
        return str(int(round(fv)))
    return f"{fv:.1f}"


def fmt_float(v, places=3):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "--"
    return f"{float(v):.{places}f}"


def choose_json_file(directory: Path, preferred_keywords: list[str]) -> Path | None:
    candidates = sorted(directory.glob("*summary*.json"))
    if not candidates:
        return None
    scored = []
    for c in candidates:
        name = c.name.lower()
        score = sum(1 for kw in preferred_keywords if kw in name)
        scored.append((score, len(name), c))
    scored.sort(key=lambda x: (-x[0], x[1], x[2].name))
    return scored[0][2]


def choose_report_file(directories: list[Path], preferred_keywords: list[str]) -> Path | None:
    candidates = []
    patterns = [
        "*util*.rpt",
        "*utilization*.rpt",
        "*report_util*.rpt",
        "*synth*.rpt",
    ]
    for d in directories:
        if not d.exists():
            continue
        for pat in patterns:
            candidates.extend(d.glob(pat))
    candidates = sorted(set(candidates))
    if not candidates:
        return None
    scored = []
    for c in candidates:
        name = c.name.lower()
        score = sum(1 for kw in preferred_keywords if kw in name)
        scored.append((score, len(name), c))
    scored.sort(key=lambda x: (-x[0], x[1], x[2].name))
    return scored[0][2]


def extract_from_json(path: Path | None):
    if path is None or not path.exists():
        return {}, []
    data = load_json(path)
    flat = flatten(data)
    aliases = {
        "wns_ns": ["wns_ns", "wns", "worst_negative_slack_ns", "worst_negative_slack"],
        "whs_ns": ["whs_ns", "whs", "worst_hold_slack_ns", "worst_hold_slack"],
        "fmax_mhz": ["approx_fmax_mhz", "fmax_mhz", "fmax", "achievable_fmax_mhz"],
        "lut": ["slice_luts", "lut", "luts", "clb_luts", "clb_lut", "lut_as_logic"],
        "ff": ["slice_registers", "registers", "ff", "ffs", "flip_flops", "clb_registers"],
        "bram": ["bram_18k", "block_ram_tile", "bram", "bram_tiles", "block_ram"],
        "dsp": ["dsp48e1", "dsp", "dsps", "dsp48"],
    }
    out = {
        "wns_ns": to_number(pick_value(flat, aliases["wns_ns"])),
        "whs_ns": to_number(pick_value(flat, aliases["whs_ns"])),
        "fmax_mhz": to_number(pick_value(flat, aliases["fmax_mhz"])),
        "lut": to_number(pick_value(flat, aliases["lut"])),
        "ff": to_number(pick_value(flat, aliases["ff"])),
        "bram": to_number(pick_value(flat, aliases["bram"])),
        "dsp": to_number(pick_value(flat, aliases["dsp"])),
    }
    return out, sorted(flat.keys())


def parse_number_token(s: str):
    s = s.strip().replace(",", "")
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None


def parse_util_report(path: Path | None):
    if path is None or not path.exists():
        return {}

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    result = {"lut": None, "ff": None, "bram": None, "dsp": None}

    # -------- Style A: OOC summary report --------
    patterns = {
        "lut": [
            r"^\|\s*Slice LUTs\s*\|",
            r"^\|\s*LUT as Logic\s*\|",
        ],
        "ff": [
            r"^\|\s*Slice Registers\s*\|",
            r"^\|\s*Registers\s*\|",
        ],
        "bram": [
            r"^\|\s*Block RAM Tile\s*\|",
        ],
        "dsp": [
            r"^\|\s*DSPs\s*\|",
        ],
    }

    for line in lines:
        stripped = line.strip()
        for key, pats in patterns.items():
            if result[key] is not None:
                continue
            if any(re.search(p, stripped, flags=re.IGNORECASE) for p in pats):
                parts = [p.strip() for p in stripped.split("|") if p.strip()]
                nums = [parse_number_token(x) for x in parts[1:]]
                nums = [x for x in nums if x is not None]
                if nums:
                    result[key] = nums[0]

    # -------- Style B: hierarchical synth report --------
    header_idx = None
    for i, line in enumerate(lines):
        if "Instance" in line and "Total LUTs" in line and "DSP Blocks" in line:
            header_idx = i
            break

    if header_idx is not None:
        for line in lines[header_idx + 1:]:
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if len(parts) < 10:
                continue
            instance = parts[0]
            module = parts[1]
            # Top row is qflow_top_tc5 | (top)
            if instance == "qflow_top_tc5" and "(top)" in module:
                # columns:
                # 0 Instance
                # 1 Module
                # 2 Total LUTs
                # 5 FFs
                # 6 RAMB36
                # 7 RAMB18
                # 8 DSP Blocks
                total_luts = parse_number_token(parts[2])
                ffs = parse_number_token(parts[6])
                ramb36 = parse_number_token(parts[7])
                ramb18 = parse_number_token(parts[8])
                dsp = parse_number_token(parts[9])

                if result["lut"] is None:
                    result["lut"] = total_luts
                if result["ff"] is None:
                    result["ff"] = ffs
                if result["bram"] is None:
                    # use block-tile equivalent: RAMB36 + 0.5*RAMB18
                    bram = None
                    if ramb36 is not None or ramb18 is not None:
                        bram = (ramb36 or 0.0) + 0.5 * (ramb18 or 0.0)
                    result["bram"] = bram
                if result["dsp"] is None:
                    result["dsp"] = dsp
                break

    return result


def merge_metrics(json_metrics: dict, rpt_metrics: dict):
    out = dict(json_metrics)
    for k, v in rpt_metrics.items():
        if out.get(k) is None and v is not None:
            out[k] = v
    return out


def build_row(label: str, json_path: Path | None, rpt_path: Path | None):
    json_metrics, debug_keys = extract_from_json(json_path)
    rpt_metrics = parse_util_report(rpt_path)
    merged = merge_metrics(json_metrics, rpt_metrics)
    row = {
        "design": label,
        "lut": merged.get("lut"),
        "ff": merged.get("ff"),
        "bram": merged.get("bram"),
        "dsp": merged.get("dsp"),
        "wns_ns": merged.get("wns_ns"),
        "fmax_mhz": merged.get("fmax_mhz"),
        "json_source": str(json_path) if json_path else "",
        "rpt_source": str(rpt_path) if rpt_path else "",
        "debug_keys": debug_keys,
    }
    return row


def write_latex(df: pd.DataFrame):
    lines = []
    lines.append(r"% Auto-generated by make_tab01_resources_timing.py")
    lines.append(r"% Requires \usepackage{booktabs}")
    lines.append(r"\begin{tabular}{lrrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Design & LUTs & FFs & BRAM & DSP & WNS (ns) & Fmax (MHz) \\")
    lines.append(r"\midrule")
    for _, r in df.iterrows():
        lines.append(
            f"{r['design']} & "
            f"{r['lut_fmt']} & "
            f"{r['ff_fmt']} & "
            f"{r['bram_fmt']} & "
            f"{r['dsp_fmt']} & "
            f"{r['wns_fmt']} & "
            f"{r['fmax_fmt']} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")


def main():
    synth_json = choose_json_file(PHASE9G, ["tc5", "synth", "summary"])
    ooc_json = choose_json_file(PHASE9H_OOC, ["tc5", "impl", "ooc", "summary"])

    synth_rpt = choose_report_file(
        [PHASE9G, PHASE9H],
        ["tc5", "util", "utilization", "synth", "qflow_top"]
    )
    ooc_rpt = choose_report_file(
        [PHASE9H_OOC],
        ["tc5", "util", "utilization", "ooc", "qflow_top"]
    )

    rows = [
        build_row("Final top-level (post-synth)", synth_json, synth_rpt),
        build_row("OOC reference (post-route)", ooc_json, ooc_rpt),
    ]

    debug_dump = {
        row["design"]: {
            "json_source": row["json_source"],
            "rpt_source": row["rpt_source"],
            "available_json_keys": row["debug_keys"],
        }
        for row in rows
    }

    OUT_DEBUG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_DEBUG.open("w", encoding="utf-8") as f:
        json.dump(debug_dump, f, indent=2)

    for row in rows:
        row["lut_fmt"] = fmt_intish(row["lut"])
        row["ff_fmt"] = fmt_intish(row["ff"])
        row["bram_fmt"] = fmt_intish(row["bram"])
        row["dsp_fmt"] = fmt_intish(row["dsp"])
        row["wns_fmt"] = fmt_float(row["wns_ns"], 3)
        row["fmax_fmt"] = fmt_float(row["fmax_mhz"], 3)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["debug_keys"]).to_csv(OUT_CSV, index=False)
    write_latex(df)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_TEX}")
    print(f"Wrote {OUT_DEBUG}")


if __name__ == "__main__":
    main()
