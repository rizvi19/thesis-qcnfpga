#!/usr/bin/env python3
import json
import re
from pathlib import Path

FLOAT_RE = r'[-+]?(?:\d+\.\d+|\d+)(?:[eE][-+]?\d+)?'

def safe_float(s):
    try:
        return float(s)
    except Exception:
        return None

def search_float(pattern, text):
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        return None
    return safe_float(m.group(1))

def parse_timing(timing_text: str, log_text: str = ""):
    out = {
        "WNS_ns": None,
        "TNS_ns": None,
        "WHS_ns": None,
        "THS_ns": None,
        "requirement_ns": 10.0,
        "approx_Fmax_MHz": None,
    }

    patterns = {
        "WNS_ns": [
            rf"\bWNS(?:\(ns\))?\b[^-\d+]*({FLOAT_RE})",
            rf"Slack \(WNS\)\s*[:=]\s*({FLOAT_RE})",
        ],
        "TNS_ns": [rf"\bTNS(?:\(ns\))?\b[^-\d+]*({FLOAT_RE})"],
        "WHS_ns": [rf"\bWHS(?:\(ns\))?\b[^-\d+]*({FLOAT_RE})"],
        "THS_ns": [rf"\bTHS(?:\(ns\))?\b[^-\d+]*({FLOAT_RE})"],
    }

    for key, pats in patterns.items():
        for pat in pats:
            val = search_float(pat, timing_text)
            if val is not None:
                out[key] = val
                break

    if log_text:
        m = re.search(
            rf"Post Routing Timing Summary \|\s*WNS=({FLOAT_RE})\s*\|\s*TNS=({FLOAT_RE})\s*\|\s*WHS=({FLOAT_RE}|N/A)\s*\|\s*THS=({FLOAT_RE}|N/A)",
            log_text
        )
        if m:
            if out["WNS_ns"] is None: out["WNS_ns"] = safe_float(m.group(1))
            if out["TNS_ns"] is None: out["TNS_ns"] = safe_float(m.group(2))
            if out["WHS_ns"] is None and m.group(3) != "N/A": out["WHS_ns"] = safe_float(m.group(3))
            if out["THS_ns"] is None and m.group(4) != "N/A": out["THS_ns"] = safe_float(m.group(4))

    if out["WNS_ns"] is not None:
        period = out["requirement_ns"] - out["WNS_ns"]
        if period > 0:
            out["approx_Fmax_MHz"] = 1000.0 / period
    return out

def parse_route_status(route_text: str, log_text: str = ""):
    out = {
        "failed_nets": None,
        "unrouted_nets": None,
        "partially_routed_nets": None,
        "node_overlaps": None,
    }

    text = route_text + "\n" + log_text
    pats = {
        "failed_nets": r"Number of Failed Nets\s*=\s*(\d+)",
        "unrouted_nets": r"Number of Unrouted Nets\s*=\s*(\d+)",
        "partially_routed_nets": r"Number of Partially Routed Nets\s*=\s*(\d+)",
        "node_overlaps": r"Number of Node Overlaps\s*=\s*(\d+)",
    }
    for k, p in pats.items():
        m = re.search(p, text)
        if m:
            out[k] = int(m.group(1))
    return out

def parse_impl_status(log_text: str):
    return {
        "route_completed": "route_design completed successfully" in log_text,
        "timing_met": "The design met the timing requirement." in log_text,
        "ooc_clock_warning": 'HD.CLK_SRC of clock port "clk" is not set' in log_text,
        "ooc_partpin_warning": "HD.PARTPIN_LOCS" in log_text,
    }

def make_md(summary):
    t = summary["timing"]
    r = summary["route_status"]
    s = summary["status"]
    fmax = None if t["approx_Fmax_MHz"] is None else round(t["approx_Fmax_MHz"], 3)
    lines = [
        "# QFlow TC5 OOC Post-Route Summary",
        "",
        f"- Route completed: **{s['route_completed']}**",
        f"- Timing met: **{s['timing_met']}**",
        f"- WNS (ns): **{t['WNS_ns']}**",
        f"- TNS (ns): **{t['TNS_ns']}**",
        f"- WHS (ns): **{t['WHS_ns']}**",
        f"- THS (ns): **{t['THS_ns']}**",
        f"- Requirement (ns): **{t['requirement_ns']}**",
        f"- Approx. Fmax (MHz): **{fmax}**",
        "",
        "## Route status",
        f"- Failed nets: **{r['failed_nets']}**",
        f"- Unrouted nets: **{r['unrouted_nets']}**",
        f"- Partially routed nets: **{r['partially_routed_nets']}**",
        f"- Node overlaps: **{r['node_overlaps']}**",
        "",
        "## Notes",
        f"- OOC HD.CLK_SRC warning present: **{s['ooc_clock_warning']}**",
        f"- OOC PARTPIN warnings present: **{s['ooc_partpin_warning']}**",
        "",
    ]
    return "\n".join(lines)

def main():
    outdir = Path("results/phase9h_ooc")
    timing_path = outdir / "qflow_top_tc5_impl_ooc_timing_summary.rpt"
    route_path = outdir / "qflow_top_tc5_impl_ooc_route_status.rpt"
    log_path = outdir / "vivado_top_tc5_impl_ooc.log"

    timing_text = timing_path.read_text(errors="ignore") if timing_path.exists() else ""
    route_text = route_path.read_text(errors="ignore") if route_path.exists() else ""
    log_text = log_path.read_text(errors="ignore") if log_path.exists() else ""

    summary = {
        "timing": parse_timing(timing_text, log_text),
        "route_status": parse_route_status(route_text, log_text),
        "status": parse_impl_status(log_text),
        "files": {
            "timing_summary": str(timing_path),
            "route_status": str(route_path),
            "log": str(log_path),
        }
    }

    (outdir / "qflow_top_tc5_impl_ooc_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (outdir / "qflow_top_tc5_impl_ooc_summary.md").write_text(make_md(summary))
    print(f"Wrote {outdir / 'qflow_top_tc5_impl_ooc_summary.json'}")
    print(f"Wrote {outdir / 'qflow_top_tc5_impl_ooc_summary.md'}")

if __name__ == "__main__":
    main()
