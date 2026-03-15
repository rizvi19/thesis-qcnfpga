#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

INF_WEIGHT = 0xFFFF_FFFF

ALPHA1 = 256  # 1.0 in Q8.8
ALPHA2 = 384  # 1.5 in Q8.8
ALPHA3 = 128  # 0.5 in Q8.8
ALPHA4 = 512  # 2.0 in Q8.8


@dataclass
class Vector:
    cfg_we: int = 0
    cfg_addr: int = 0
    cfg_wdata: int = 0
    fdpe_valid: int = 0
    fdpe_addr: int = 0
    fdpe_fidelity: int = 0
    ga_rd_en: int = 0
    ga_rd_addr: int = 0
    exp_ga_valid: int = 0
    exp_ga_edge: int = 0
    exp_ga_weight: int = 0


def pack_edge(key_count: int, fidelity_q016: int, arrival_rate_q8_8: int, qber_q016: int) -> int:
    return ((qber_q016 & 0xFFFF) << 48) | ((arrival_rate_q8_8 & 0xFFFF) << 32) | ((fidelity_q016 & 0xFFFF) << 16) | (key_count & 0xFFFF)


def unpack_edge(edge: int):
    return {
        "key_count": edge & 0xFFFF,
        "fidelity": (edge >> 16) & 0xFFFF,
        "arrival_rate": (edge >> 32) & 0xFFFF,
        "qber": (edge >> 48) & 0xFFFF,
    }


def compute_weight(edge: int) -> int:
    f = unpack_edge(edge)
    key_count = f["key_count"]
    fidelity = f["fidelity"]
    arrival = f["arrival_rate"]
    qber = f["qber"]
    if key_count == 0 or fidelity == 0 or arrival == 0:
        return INF_WEIGHT
    t1 = (ALPHA1 << 8) // key_count
    t2 = (ALPHA2 << 24) // fidelity
    t3 = (ALPHA3 << 16) // arrival
    t4 = (ALPHA4 * qber) >> 8
    total = t1 + t2 + t3 + t4
    return total if total <= INF_WEIGHT else INF_WEIGHT


class SkagModel:
    def __init__(self, depth: int = 256):
        self.depth = depth
        self.edge_mem = [0] * depth
        self.weight_mem = [INF_WEIGHT] * depth
        self.s0_valid = 0
        self.s1_valid = 0
        self.s2_valid = 0
        self.s0_addr = 0
        self.s1_addr = 0
        self.s2_addr = 0
        self.s0_edge = 0
        self.s1_edge = 0
        self.s2_edge = 0
        self.s0_weight = INF_WEIGHT
        self.s1_weight = INF_WEIGHT
        self.s2_weight = INF_WEIGHT
        self.ga_pending = 0
        self.ga_conflict_pending = 0
        self.ga_addr_d = 0
        self.ga_rd_valid = 0
        self.ga_rd_edge = 0
        self.ga_rd_weight = INF_WEIGHT

    def cycle(self, vec: Vector):
        if self.ga_pending:
            if self.ga_conflict_pending:
                self.ga_rd_valid = 0
                self.ga_rd_edge = 0
                self.ga_rd_weight = INF_WEIGHT
            else:
                self.ga_rd_valid = 1
                self.ga_rd_edge = self.edge_mem[self.ga_addr_d]
                self.ga_rd_weight = self.weight_mem[self.ga_addr_d]
        else:
            self.ga_rd_valid = 0
            self.ga_rd_edge = 0
            self.ga_rd_weight = INF_WEIGHT

        if self.s2_valid:
            self.edge_mem[self.s2_addr] = self.s2_edge
            self.weight_mem[self.s2_addr] = self.s2_weight

        ns2_valid, ns2_addr, ns2_edge, ns2_weight = self.s1_valid, self.s1_addr, self.s1_edge, self.s1_weight
        ns1_valid, ns1_addr, ns1_edge, ns1_weight = self.s0_valid, self.s0_addr, self.s0_edge, self.s0_weight

        if vec.fdpe_valid:
            old_edge = self.edge_mem[vec.fdpe_addr]
            new_edge = (old_edge & ~((0xFFFF) << 16)) | ((vec.fdpe_fidelity & 0xFFFF) << 16)
            ns0_valid = 1
            ns0_addr = vec.fdpe_addr
            ns0_edge = new_edge
            ns0_weight = compute_weight(new_edge)
        else:
            ns0_valid = 0
            ns0_addr = 0
            ns0_edge = 0
            ns0_weight = INF_WEIGHT

        if vec.cfg_we and not (vec.fdpe_valid and vec.fdpe_addr == vec.cfg_addr):
            self.edge_mem[vec.cfg_addr] = vec.cfg_wdata
            self.weight_mem[vec.cfg_addr] = compute_weight(vec.cfg_wdata)

        conflict = vec.ga_rd_en and (
            (vec.fdpe_valid and vec.ga_rd_addr == vec.fdpe_addr)
            or (self.s0_valid and vec.ga_rd_addr == self.s0_addr)
            or (self.s1_valid and vec.ga_rd_addr == self.s1_addr)
            or (self.s2_valid and vec.ga_rd_addr == self.s2_addr)
        )
        self.ga_pending = vec.ga_rd_en
        self.ga_conflict_pending = 1 if conflict else 0
        self.ga_addr_d = vec.ga_rd_addr

        self.s2_valid, self.s2_addr, self.s2_edge, self.s2_weight = ns2_valid, ns2_addr, ns2_edge, ns2_weight
        self.s1_valid, self.s1_addr, self.s1_edge, self.s1_weight = ns1_valid, ns1_addr, ns1_edge, ns1_weight
        self.s0_valid, self.s0_addr, self.s0_edge, self.s0_weight = ns0_valid, ns0_addr, ns0_edge, ns0_weight

        return self.ga_rd_valid, self.ga_rd_edge, self.ga_rd_weight


def to_memh(vec: Vector) -> str:
    value = 0
    value |= (vec.cfg_we & 0x1) << 207
    value |= (vec.cfg_addr & 0xFF) << 199
    value |= (vec.cfg_wdata & ((1 << 64) - 1)) << 135
    value |= (vec.fdpe_valid & 0x1) << 134
    value |= (vec.fdpe_addr & 0xFF) << 126
    value |= (vec.fdpe_fidelity & 0xFFFF) << 110
    value |= (vec.ga_rd_en & 0x1) << 109
    value |= (vec.ga_rd_addr & 0xFF) << 101
    value |= (vec.exp_ga_valid & 0x1) << 100
    value |= (vec.exp_ga_edge & ((1 << 64) - 1)) << 36
    value |= (vec.exp_ga_weight & 0xFFFF_FFFF) << 4
    return f"{value:052x}"


def base_vectors() -> List[Vector]:
    e3 = pack_edge(10, 0xF100, 0x0800, 0x07AE)
    e5 = pack_edge(8,  0xE800, 0x0600, 0x051E)
    e7 = pack_edge(0,  0xD000, 0x0400, 0x028F)
    e9 = pack_edge(6,  0xD800, 0x0000, 0x028F)
    e11= pack_edge(12, 0xEE00, 0x0700, 0x03D7)

    return [
        Vector(),
        Vector(cfg_we=1, cfg_addr=3, cfg_wdata=e3),
        Vector(),
        Vector(ga_rd_en=1, ga_rd_addr=3),
        Vector(),
        Vector(cfg_we=1, cfg_addr=5, cfg_wdata=e5),
        Vector(ga_rd_en=1, ga_rd_addr=5),
        Vector(),
        Vector(fdpe_valid=1, fdpe_addr=3, fdpe_fidelity=0xC800),
        Vector(),
        Vector(),
        Vector(ga_rd_en=1, ga_rd_addr=3),
        Vector(),
        Vector(cfg_we=1, cfg_addr=7, cfg_wdata=e7),
        Vector(ga_rd_en=1, ga_rd_addr=7),
        Vector(),
        Vector(cfg_we=1, cfg_addr=9, cfg_wdata=e9),
        Vector(ga_rd_en=1, ga_rd_addr=9),
        Vector(),
        Vector(cfg_we=1, cfg_addr=11, cfg_wdata=e11),
        Vector(fdpe_valid=1, fdpe_addr=11, fdpe_fidelity=0xB400, ga_rd_en=1, ga_rd_addr=11),
        Vector(ga_rd_en=1, ga_rd_addr=5),
        Vector(),
        Vector(),
        Vector(ga_rd_en=1, ga_rd_addr=11),
        Vector(),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SKAG BRAM golden vectors and memh stimulus.")
    parser.add_argument("--out-dir", type=Path, default=Path("results/phase9a"))
    parser.add_argument("--tb-dir", type=Path, default=Path("tb"))
    args = parser.parse_args()

    out_dir = args.out_dir
    tb_dir = args.tb_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    tb_dir.mkdir(parents=True, exist_ok=True)

    model = SkagModel(depth=256)
    vectors = base_vectors()

    csv_rows: List[Dict[str, int]] = []
    memh_lines: List[str] = []

    for cycle, vec in enumerate(vectors):
        exp_valid, exp_edge, exp_weight = model.cycle(vec)
        vec.exp_ga_valid = exp_valid
        vec.exp_ga_edge = exp_edge
        vec.exp_ga_weight = exp_weight
        memh_lines.append(to_memh(vec))
        csv_rows.append({
            "cycle": cycle,
            "cfg_we": vec.cfg_we,
            "cfg_addr": vec.cfg_addr,
            "cfg_wdata": f"0x{vec.cfg_wdata:016X}",
            "fdpe_valid": vec.fdpe_valid,
            "fdpe_addr": vec.fdpe_addr,
            "fdpe_fidelity": f"0x{vec.fdpe_fidelity:04X}",
            "ga_rd_en": vec.ga_rd_en,
            "ga_rd_addr": vec.ga_rd_addr,
            "exp_ga_valid": vec.exp_ga_valid,
            "exp_ga_edge": f"0x{vec.exp_ga_edge:016X}",
            "exp_ga_weight": f"0x{vec.exp_ga_weight:08X}",
        })

    memh_path = tb_dir / "skag_bram_vectors.memh"
    memh_path.write_text("\n".join(memh_lines) + "\n")

    csv_path = out_dir / "skag_bram_golden_vectors.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    summary = {
        "vector_count": len(vectors),
        "alpha_q8_8": {
            "alpha1": ALPHA1,
            "alpha2": ALPHA2,
            "alpha3": ALPHA3,
            "alpha4": ALPHA4,
        },
        "addresses_touched": [3, 5, 7, 9, 11],
        "notes": [
            "Behavioral contract intentionally matches the validated baseline SKAG model.",
            "Optimized module removes memory reset loops and adds block-RAM style attributes.",
            "OOC synthesis uses the module defaults ADDR_W=12 DEPTH=4096 to encourage BRAM inference."
        ],
    }
    (out_dir / "skag_bram_vector_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(vectors)} SKAG BRAM vectors to {memh_path}")
    print(f" - {csv_path}")
    print(f" - {out_dir / 'skag_bram_vector_summary.json'}")


if __name__ == "__main__":
    main()
