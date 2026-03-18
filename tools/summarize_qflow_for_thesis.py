#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def parse_route_status(path: Optional[Path]) -> Dict[str, Optional[int]]:
    out = {
        "routable_nets": None,
        "fully_routed_nets": None,
        "nets_with_routing_errors": None,
    }
    if not path or not path.exists():
        return out
    text = path.read_text(errors="ignore")
    patterns = {
        "routable_nets": r"# of routable nets\.*\s*:\s*(\d+)",
        "fully_routed_nets": r"# of fully routed nets\.*\s*:\s*(\d+)",
        "nets_with_routing_errors": r"# of nets with routing errors\.*\s*:\s*(\d+)",
    }
    for k, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[k] = int(m.group(1))
    return out


def load_timing_row(label: str, kind: str, path: Path) -> Dict[str, Any]:
    data = read_json(path)
    t = data.get("timing", {})
    return {
        "stage": label,
        "kind": kind,
        "top": data.get("top", "-"),
        "WNS_ns": t.get("WNS_ns"),
        "TNS_ns": t.get("TNS_ns"),
        "Requirement_ns": t.get("Requirement_ns"),
        "Data_path_delay_ns": t.get("Data_path_delay_ns"),
        "approx_Fmax_MHz": t.get("approx_Fmax_MHz"),
        "Worst_source": t.get("Worst_source"),
        "Worst_destination": t.get("Worst_destination"),
        "timing_met": (t.get("WNS_ns") is not None and t.get("WNS_ns") >= 0 and (t.get("TNS_ns") in (0, 0.0, None))),
    }


def best_baseline(rows: List[Dict[str, Any]], key: str, higher_is_better: bool) -> Optional[str]:
    clean = [r for r in rows if r.get(key) is not None]
    if not clean:
        return None
    reverse = higher_is_better
    clean.sort(key=lambda r: r[key], reverse=reverse)
    return clean[0]["baseline"]


def fmt(x: Any, digits: int = 3) -> str:
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        return f"{x:.{digits}f}"
    return str(x)


def main() -> None:
    ap = argparse.ArgumentParser(description="Package QFlow timing and baseline results into thesis-ready summaries.")
    ap.add_argument("--tc3-json", default="results/phase9e/qflow_top_tc3_synth_summary.json")
    ap.add_argument("--tc4-json", default="results/phase9f/qflow_top_tc4_synth_summary.json")
    ap.add_argument("--tc5-json", default="results/phase9g/qflow_top_tc5_synth_summary.json")
    ap.add_argument("--ooc-json", default="results/phase9h_ooc/qflow_top_tc5_impl_ooc_summary.json")
    ap.add_argument("--ooc-route-status", default="results/phase9h_ooc/qflow_top_tc5_impl_ooc_route_status.rpt")
    ap.add_argument("--phase10c-json", default="results/phase10c/qflow_baseline_eval_phase10c_stats.json")
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    tc3 = load_timing_row("tc3", "post-synthesis", Path(args.tc3_json))
    tc4 = load_timing_row("tc4", "post-synthesis", Path(args.tc4_json))
    tc5 = load_timing_row("tc5", "post-synthesis", Path(args.tc5_json))
    ooc_data = read_json(Path(args.ooc_json))
    ooc_t = ooc_data.get("timing", {})
    ooc = {
        "stage": "tc5_ooc_impl",
        "kind": "OOC post-route",
        "top": ooc_data.get("top", "qflow_top_tc5"),
        "WNS_ns": ooc_t.get("WNS_ns"),
        "TNS_ns": ooc_t.get("TNS_ns"),
        "Requirement_ns": ooc_t.get("Requirement_ns"),
        "Data_path_delay_ns": ooc_t.get("Data_path_delay_ns"),
        "approx_Fmax_MHz": ooc_t.get("approx_Fmax_MHz"),
        "Worst_source": ooc_t.get("Worst_source"),
        "Worst_destination": ooc_t.get("Worst_destination"),
        "timing_met": bool(ooc_data.get("timing_met", False)),
        "WHS_ns": ooc_t.get("WHS_ns"),
        "THS_ns": ooc_t.get("THS_ns"),
        "route_completed": ooc_data.get("route_completed"),
    }
    ooc.update(parse_route_status(Path(args.ooc_route_status)))

    phase10c = read_json(Path(args.phase10c_json))
    topo_summaries: List[Dict[str, Any]] = []
    ga_match_rows: List[Dict[str, Any]] = []
    for topo in phase10c.get("topologies", []):
        stats = topo.get("repeated_baseline_stats", [])
        topo_summaries.append({
            "topology": topo.get("name"),
            "best_latency_baseline": best_baseline(stats, "mean_avg_latency", higher_is_better=False),
            "best_fidelity_baseline": best_baseline(stats, "mean_avg_bottleneck_fidelity", higher_is_better=True),
            "best_load_balance_baseline": best_baseline(stats, "mean_avg_load_balance", higher_is_better=False),
            "distance_row": next((r for r in stats if r["baseline"] == "dijkstra_distance"), None),
            "keyaware_row": next((r for r in stats if r["baseline"] == "dijkstra_keyaware"), None),
            "random_row": next((r for r in stats if r["baseline"] == "random_valid_path"), None),
            "ga_row": next((r for r in stats if r["baseline"] == "software_pmo_ga"), None),
        })
        for req in topo.get("ga_vs_keyaware_request_match", []):
            ga_match_rows.append({
                "topology": topo.get("name"),
                "request_index": req.get("request_index", req.get("req_idx")),
                "src": req.get("src"),
                "dst": req.get("dst"),
                "ga_matches_keyaware_rate": req.get("ga_matches_keyaware_rate"),
                "ga_matches_keyaware_count": req.get("ga_matches_keyaware_count"),
            })

    summary = {
        "timing_progression": [tc3, tc4, tc5, ooc],
        "baseline_topology_summaries": topo_summaries,
        "ga_vs_keyaware_match": ga_match_rows,
        "headline_findings": {
            "timing_story": "SKAG-dominated tc3 -> FDPE-dominated tc4 -> tc5 closure at >100 MHz -> OOC post-route timing met.",
            "baseline_story": "Key-aware shortest path consistently outperforms or matches plain distance routing and strongly outperforms random routing on latency; software PMO-GA matches key-aware path choices on the current sequential request suites.",
        },
    }

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2))

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "stage_or_topology", "metric", "value", "extra"])
        for row in [tc3, tc4, tc5, ooc]:
            for metric in ["kind", "WNS_ns", "TNS_ns", "Requirement_ns", "Data_path_delay_ns", "approx_Fmax_MHz", "timing_met", "Worst_source", "Worst_destination"]:
                w.writerow(["timing_progression", row["stage"], metric, row.get(metric), row.get("top")])
        for metric in ["WHS_ns", "THS_ns", "route_completed", "routable_nets", "fully_routed_nets", "nets_with_routing_errors"]:
            w.writerow(["timing_progression", ooc["stage"], metric, ooc.get(metric), ooc.get("top")])
        for topo in topo_summaries:
            topo_name = topo["topology"]
            for name, rowkey in [("dijkstra_distance", "distance_row"), ("dijkstra_keyaware", "keyaware_row"), ("random_valid_path", "random_row"), ("software_pmo_ga", "ga_row")]:
                row = topo.get(rowkey)
                if not row:
                    continue
                for metric in ["mean_avg_hops", "mean_avg_distance_km", "mean_avg_latency", "latency_ci95", "mean_avg_bottleneck_fidelity", "fidelity_ci95", "mean_avg_load_balance", "load_balance_ci95", "mean_total_runtime_ms"]:
                    w.writerow(["baseline_stats", topo_name, f"{name}.{metric}", row.get(metric), None])
        for row in ga_match_rows:
            w.writerow(["ga_keyaware_match", row["topology"], f"request_{row['request_index']}.ga_matches_keyaware_rate", row["ga_matches_keyaware_rate"], f"{row['src']}->{row['dst']}"])

    md: List[str] = []
    md.append("# QFlow thesis packaging summary\n")
    md.append("## Timing-closure progression\n")
    md.append("| stage | kind | WNS_ns | TNS_ns | delay_ns | approx_Fmax_MHz | timing_met | worst_path |")
    md.append("|---|---|---:|---:|---:|---:|---|---|")
    for row in [tc3, tc4, tc5, ooc]:
        worst = f"{row.get('Worst_source','-')} -> {row.get('Worst_destination','-')}"
        md.append(f"| {row['stage']} | {row['kind']} | {fmt(row.get('WNS_ns'))} | {fmt(row.get('TNS_ns'))} | {fmt(row.get('Data_path_delay_ns'))} | {fmt(row.get('approx_Fmax_MHz'))} | {fmt(row.get('timing_met'), 0)} | `{worst}` |")
    md.append("")
    md.append(f"OOC route confirmation: routable={fmt(ooc.get('routable_nets'),0)}, fully_routed={fmt(ooc.get('fully_routed_nets'),0)}, routing_errors={fmt(ooc.get('nets_with_routing_errors'),0)}, WHS_ns={fmt(ooc.get('WHS_ns'))}, THS_ns={fmt(ooc.get('THS_ns'))}.\n")

    md.append("## Baseline comparison by topology\n")
    md.append("| topology | best_latency | best_fidelity | best_load_balance | distance_latency | keyaware_latency | random_latency | ga_latency | keyaware_vs_ga_same_latency |")
    md.append("|---|---|---|---|---:|---:|---:|---:|---|")
    for topo in topo_summaries:
        d = topo["distance_row"]
        k = topo["keyaware_row"]
        r = topo["random_row"]
        g = topo["ga_row"]
        same_lat = (k and g and abs(float(k["mean_avg_latency"]) - float(g["mean_avg_latency"])) < 1e-12)
        md.append(
            f"| {topo['topology']} | {topo['best_latency_baseline']} | {topo['best_fidelity_baseline']} | {topo['best_load_balance_baseline']} | {fmt(d.get('mean_avg_latency') if d else None)} | {fmt(k.get('mean_avg_latency') if k else None)} | {fmt(r.get('mean_avg_latency') if r else None)} | {fmt(g.get('mean_avg_latency') if g else None)} | {fmt(same_lat,0)} |"
        )
    md.append("")

    md.append("## GA vs key-aware path-match stability\n")
    md.append("| topology | request | src | dst | ga_matches_keyaware_rate |")
    md.append("|---|---:|---:|---:|---:|")
    for row in ga_match_rows:
        md.append(f"| {row['topology']} | {row['request_index']} | {row['src']} | {row['dst']} | {fmt(row['ga_matches_keyaware_rate'])} |")
    md.append("")

    md.append("## Thesis-safe interpretation\n")
    md.append("- tc5 is the first post-synthesis variant that clears the 10 ns target.\n")
    md.append("- OOC post-route also meets timing, so the core hardware timing claim is strong.\n")
    md.append("- On the current baseline suites, key-aware shortest path beats plain distance routing on latency in the harder topologies and random routing is clearly weakest.\n")
    md.append("- Software PMO-GA matches key-aware shortest path on the current evaluation suites, so the present data supports hardware/software acceleration claims and key-awareness claims more strongly than GA-vs-key-aware solution-quality superiority claims.\n")

    out_md.write_text("\n".join(md) + "\n")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
