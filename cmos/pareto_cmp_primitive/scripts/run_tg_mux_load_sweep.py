#!/usr/bin/env python3
from pathlib import Path
import subprocess
import re
import csv
import matplotlib.pyplot as plt

ROOT = Path.cwd()
OUT_DIR = ROOT / "results/partD_cmos/pareto_cmp_primitive/load_sweep"
SPICE_DIR = ROOT / "cmos/pareto_cmp_primitive/spice/load_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SPICE_DIR.mkdir(parents=True, exist_ok=True)

VDD = 1.8
LOADS_FF = [5, 10, 20, 50]

def write_spice(load_ff: int) -> Path:
    sp = SPICE_DIR / f"tg_mux_2to1_cload_{load_ff}f.sp"
    text = f"""* QFlow Part D TG mux load sweep
* Load = {load_ff} fF
.option post
.param VDD=1.8
.param LMIN=0.15u
.param WN=1.0u
.param WP=2.0u
.param CLOAD={load_ff}f

VDD_SUPPLY vdd 0 DC {{VDD}}

* sel=1 selects in1; sel=0 selects in0
VSEL  sel  0 DC {{VDD}}
VSELB selb 0 DC 0

VIN0 in0 0 DC 0
VIN1 in1 0 PULSE(0 {{VDD}} 2n 50p 50p 3n 6n)

* TG for input 0, active when sel=0
M0N out selb in0 0   NMOS_L1 W={{WN}} L={{LMIN}}
M0P out sel  in0 vdd PMOS_L1 W={{WP}} L={{LMIN}}

* TG for input 1, active when sel=1
M1N out sel  in1 0   NMOS_L1 W={{WN}} L={{LMIN}}
M1P out selb in1 vdd PMOS_L1 W={{WP}} L={{LMIN}}

COUT out 0 {{CLOAD}}

.model NMOS_L1 NMOS LEVEL=1 VTO=0.45 KP=120u GAMMA=0.4 LAMBDA=0.05 PHI=0.7
.model PMOS_L1 PMOS LEVEL=1 VTO=-0.45 KP=45u GAMMA=0.4 LAMBDA=0.05 PHI=0.7

.tran 1p 20n

.measure tran tplh TRIG v(in1) VAL=0.9 RISE=1 TARG v(out) VAL=0.9 RISE=1
.measure tran tphl TRIG v(in1) VAL=0.9 FALL=1 TARG v(out) VAL=0.9 FALL=1

.control
run
set wr_singlescale
wrdata results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_2to1_cload_{load_ff}f_waveform.csv time v(in1) v(out)
quit
.endc

.end
"""
    sp.write_text(text)
    return sp

def parse_measure(log_text: str, name: str):
    m = re.search(rf"^{name}\s*=\s*([0-9.eE+\-]+)", log_text, re.MULTILINE)
    return float(m.group(1)) if m else None

rows = []

for load_ff in LOADS_FF:
    sp = write_spice(load_ff)
    log_path = OUT_DIR / f"tg_mux_2to1_cload_{load_ff}f_ngspice.log"

    print(f"[RUN] CLOAD={load_ff} fF")
    subprocess.run(
        ["ngspice", "-b", "-o", str(log_path), str(sp)],
        check=True,
        cwd=ROOT,
    )

    log_text = log_path.read_text(errors="replace")
    tplh = parse_measure(log_text, "tplh")
    tphl = parse_measure(log_text, "tphl")
    avg = (tplh + tphl) / 2.0 if tplh is not None and tphl is not None else None

    energy_fj = 0.5 * load_ff * (VDD ** 2)

    rows.append({
        "load_fF": load_ff,
        "tplh_ps": tplh * 1e12 if tplh is not None else "",
        "tphl_ps": tphl * 1e12 if tphl is not None else "",
        "average_delay_ps": avg * 1e12 if avg is not None else "",
        "estimated_load_switching_energy_fJ": energy_fj,
        "spice_file": str(sp.relative_to(ROOT)),
        "log_file": str(log_path.relative_to(ROOT)),
    })

csv_path = OUT_DIR / "tg_mux_load_sweep.csv"
with csv_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

# Plot delay vs load.
plt.figure(figsize=(7, 4))
plt.plot([r["load_fF"] for r in rows], [r["average_delay_ps"] for r in rows], marker="o")
plt.xlabel("Load capacitance (fF)")
plt.ylabel("Average delay (ps)")
plt.title("TG Mux Delay vs Load Capacitance")
plt.tight_layout()
delay_fig = OUT_DIR / "tg_mux_delay_vs_load.png"
plt.savefig(delay_fig, dpi=300)
plt.close()

# Plot energy vs load.
plt.figure(figsize=(7, 4))
plt.plot([r["load_fF"] for r in rows], [r["estimated_load_switching_energy_fJ"] for r in rows], marker="o")
plt.xlabel("Load capacitance (fF)")
plt.ylabel("Estimated load switching energy (fJ)")
plt.title("TG Mux Load Switching Energy vs Load")
plt.tight_layout()
energy_fig = OUT_DIR / "tg_mux_energy_vs_load.png"
plt.savefig(energy_fig, dpi=300)
plt.close()

print(f"[PASS] wrote {csv_path}")
print(f"[PASS] wrote {delay_fig}")
print(f"[PASS] wrote {energy_fig}")

for r in rows:
    print(
        f"CLOAD={r['load_fF']:>2} fF | "
        f"tplh={r['tplh_ps']:.2f} ps | "
        f"tphl={r['tphl_ps']:.2f} ps | "
        f"avg={r['average_delay_ps']:.2f} ps | "
        f"Eload={r['estimated_load_switching_energy_fJ']:.2f} fJ"
    )
