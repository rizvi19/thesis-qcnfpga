
import argparse, csv, json
from pathlib import Path

def q16_16(x: float) -> int:
    return int(round(x * (1 << 16))) & 0xFFFFFFFF

def q0_16(x: float) -> int:
    x = max(0.0, min(1.0, x))
    return int(round(x * 65535.0)) & 0xFFFF

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="results/phase4")
    ap.add_argument("--tb-dir", default="tb")
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    tb_dir = Path(args.tb_dir); tb_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        {"path_id": 0, "path": [0,1,2,3],     "latency": 6.20, "fidelity": 0.8800,   "util": 0.3500},
        {"path_id": 1, "path": [0,5,4,3],     "latency": 5.46, "fidelity": 0.928396, "util": 0.2700},
        {"path_id": 2, "path": [0,1,0,5,4,3], "latency": 8.10, "fidelity": 0.7700,   "util": 0.4400},
        {"path_id": 3, "path": [0,5,0,1,2,3], "latency": 8.00, "fidelity": 0.7600,   "util": 0.4200},
        {"path_id": 4, "path": [0,5,4,3],     "latency": 5.00, "fidelity": 0.9300,   "util": 0.2200},
        {"path_id": 5, "path": [0,5,4,5,4,3], "latency": 7.40, "fidelity": 0.8100,   "util": 0.3900},
        {"path_id": 6, "path": [0,1,2,1,2,3], "latency": 7.00, "fidelity": 0.8200,   "util": 0.3600},
        {"path_id": 7, "path": [0,1,2,3],     "latency": 5.20, "fidelity": 0.9100,   "util": 0.3100},
    ]

    csv_path = out_dir / "pmo_ga_reduced_candidates.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path_id","path","latency","fidelity","util","latency_q16_16","fidelity_q0_16","util_q0_16"])
        writer.writeheader()
        for c in candidates:
            row = {
                "path_id": c["path_id"],
                "path": "-".join(map(str,c["path"])),
                "latency": c["latency"],
                "fidelity": c["fidelity"],
                "util": c["util"],
                "latency_q16_16": q16_16(c["latency"]),
                "fidelity_q0_16": q0_16(c["fidelity"]),
                "util_q0_16": q0_16(c["util"]),
            }
            writer.writerow(row)

    memh_path = tb_dir / "pmo_ga_reduced_candidates.memh"
    with memh_path.open("w") as f:
        for c in candidates:
            packed = ((c["path_id"] & 0xFFFF) << 64) | ((q16_16(c["latency"]) & 0xFFFFFFFF) << 32) | ((q0_16(c["fidelity"]) & 0xFFFF) << 16) | (q0_16(c["util"]) & 0xFFFF)
            f.write(f"{packed:020x}\n")

    expected = {
        "vector_count": len(candidates),
        "expected_best_id": 4,
        "expected_best_path": [0,5,4,3],
        "expected_latency_q16_16": q16_16(5.0),
        "expected_fidelity_q0_16": q0_16(0.93),
        "expected_util_q0_16": q0_16(0.22),
        "notes": [
            "Reduced but correct PMO-GA comparator/elitism milestone.",
            "This step validates the PMO-GA selection kernel before the larger pipelined engine."
        ]
    }
    json_path = out_dir / "pmo_ga_reduced_expected.json"
    json_path.write_text(json.dumps(expected, indent=2))

    print(f"Wrote {len(candidates)} reduced PMO-GA candidates to {memh_path}")
    print(f" - {csv_path}")
    print(f" - {json_path}")

if __name__ == "__main__":
    main()
