
import argparse, csv, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-txt", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    summary = {}
    for line in Path(args.summary_txt).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip()
            if v.isdigit():
                summary[k] = int(v)
            else:
                summary[k] = v

    rows = list(csv.DictReader(Path(args.csv).open()))
    summary["logged_candidates"] = len(rows)
    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
