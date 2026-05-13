#!/usr/bin/env python3
"""QFlow AWS F2 host-driver Python skeleton.
Replace mmio_read32/mmio_write32 with AWS FPGA runtime/MMIO calls later.
"""
CONTROL = 0x000
STATUS = 0x004
SRC_NODE = 0x010
DST_NODE = 0x014
TIME_NOW = 0x018
F_MIN = 0x01C
EDGE_BASE = 0x100
CAND_BASE = 0x300
SELECTED_PATH_ID = 0x400
BEST_WEIGHT = 0x404
BOTTLENECK_FIDELITY = 0x408
LATENCY_CYCLES = 0x40C
CONTROL_START = 0x1
CONTROL_SOFT_RESET = 0x2
STATUS_DONE = 0x1

def mmio_write32(offset: int, value: int) -> None:
    print(f"WRITE 0x{offset:03x} = 0x{value:08x}")

def mmio_read32(offset: int) -> int:
    print(f"READ  0x{offset:03x}")
    return 0

def wait_done(max_polls: int = 100_000) -> None:
    for _ in range(max_polls):
        if mmio_read32(STATUS) & STATUS_DONE:
            return
    raise TimeoutError("QFlow timeout while waiting for DONE")

def main() -> None:
    mmio_write32(CONTROL, CONTROL_SOFT_RESET)
    mmio_write32(CONTROL, 0)
    # Load vector registers here from golden_vectors.csv.
    mmio_write32(CONTROL, CONTROL_START)
    mmio_write32(CONTROL, 0)
    wait_done()
    print({
        "status": mmio_read32(STATUS),
        "selected_path_id": mmio_read32(SELECTED_PATH_ID),
        "best_weight": mmio_read32(BEST_WEIGHT),
        "bottleneck_fidelity": mmio_read32(BOTTLENECK_FIDELITY),
        "latency_cycles": mmio_read32(LATENCY_CYCLES),
    })

if __name__ == "__main__":
    main()
