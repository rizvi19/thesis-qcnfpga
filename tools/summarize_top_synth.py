#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

def parse_util(path: Path):
    text = path.read_text(errors="ignore")
    data = {}
    # General cell counts
    for key, pattern in {
        "LUT": r"\|\s*CLB LUTs\*?\s*\|\s*([\d,]+)",
        "FF": r"\|\s*CLB Registers\s*\|\s*([\d,]+)",
        "BRAM_18K": r"\|\s*Block RAM Tile\s*\|\s*([\d,\.]+)",
        "DSP": r"\|\s*DSPs\s*\|\s*([\d,]+)",
    }.items():
        m = re.search(pattern, text)
        if m:
            val = m.group(1).replace(",", "")
            data[key] = float(val) if "." in val else int(val)
    # Primitive counts fallback
    for key, pattern in {
        "RAMB36E1": r"\|\s*RAMB36E1\s*\|\s*([\d,]+)",
        "RAMB18E1": r"\|\s*RAMB18E1\s*\|\s*([\d,]+)",
        "DSP48E1": r"\|\s*DSP48E1\s*\|\s*([\d,]+)",
        "LUT6": r"\|\s*LUT6\s*\|\s*([\d,]+)",
        "FDRE": r"\|\s*FDRE\s*\|\s*([\d,]+)",
        "FDCE": r"\|\s*FDCE\s*\|\s*([\d,]+)",
        "FDPE": r"\|\s*FDPE\s*\|\s*([\d,]+)",
    }.items():
        m = re.search(pattern, text)
        if m:
            data[key] = int(m.group(1).replace(",", ""))
    return data

def parse_timing(path: Path):
    text = path.read_text(errors="ignore")
    data = {}
    patterns = {
        "WNS_ns": r"WNS\(ns\)\s*TNS\(ns\).*?\n[-\s]+\n\s*([-\d\.]+)\s+([-\d\.]+)",
        "Clock_period_ns": r"Period\(ns\):\s*([-\d\.]+)",
        "Requirement_ns": r"Requirement:\s*([-\d\.]+)",
        "Data_path_delay_ns": r"Data Path Delay:\s*([-\d\.]+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.S)
        if m:
            if key == "WNS_ns":
                data["WNS_ns"] = float(m.group(1))
                data["TNS_ns"] = float(m.group(2))
            else:
                data[key] = float(m.group(1))
    # derive approximate Fmax from requirement-wns if available
    if "Requirement_ns" in data and "WNS_ns" in data:
        achieved = data["Requirement_ns"] - data["WNS_ns"]
        if achieved > 0:
            data["approx_Fmax_MHz"] = round(1000.0 / achieved, 3)
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--util", type=Path, required=True)
    ap.add_argument("--timing", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    args = ap.parse_args()

    util = parse_util(args.util)
    timing = parse_timing(args.timing)
    out = {
        "top": "qflow_top_synth",
        "utilization": util,
        "timing": timing,
        "notes": [
            "This is the first integrated top-level synthesis baseline using qflow_top_synth.",
            "SKAG uses the BRAM-optimized skag_mem_bram module from Step 9A.",
            "Timing is from synthesis-only reports; implementation/place-route timing is still pending."
        ]
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(out, indent=2))
    md = [
        "# QFlow Top-Level Synthesis Summary",
        "",
        "## Utilization",
    ]
    for k,v in util.items():
        md.append(f"- {k}: {v}")
    md += ["", "## Timing"]
    for k,v in timing.items():
        md.append(f"- {k}: {v}")
    md += ["", "## Notes"] + [f"- {n}" for n in out["notes"]]
    args.out_md.write_text("\n".join(md))

if __name__ == "__main__":
    main()
