#!/usr/bin/env python3
from pathlib import Path

OUT = Path("results/aws_preflight")
OUT.mkdir(parents=True, exist_ok=True)

c_code = """// QFlow AWS F2 host-driver skeleton
// This is a documentation/starter stub for the future EC2 F2 session.
// It is NOT expected to compile locally without AWS SDK/FPGA runtime headers.

#include <stdint.h>
#include <stdio.h>

#define QFLOW_REG_CONTROL              0x000
#define QFLOW_REG_STATUS               0x004
#define QFLOW_REG_SRC_NODE             0x010
#define QFLOW_REG_DST_NODE             0x014
#define QFLOW_REG_TIME_NOW             0x018
#define QFLOW_REG_F_MIN                0x01C
#define QFLOW_EDGE_BASE                0x100
#define QFLOW_CAND_BASE                0x300
#define QFLOW_REG_SELECTED_PATH_ID     0x400
#define QFLOW_REG_BEST_WEIGHT          0x404
#define QFLOW_REG_BOTTLENECK_FIDELITY  0x408
#define QFLOW_REG_LATENCY_CYCLES       0x40C

#define QFLOW_CONTROL_START            0x00000001u
#define QFLOW_CONTROL_SOFT_RESET       0x00000002u
#define QFLOW_STATUS_DONE              0x00000001u
#define QFLOW_STATUS_VALID_PATH        0x00000002u
#define QFLOW_STATUS_NO_PATH           0x00000004u
#define QFLOW_STATUS_BUSY              0x00000008u

static void qflow_write32(uint32_t offset, uint32_t value) {
    printf("WRITE 0x%03x = 0x%08x\\n", offset, value);
}

static uint32_t qflow_read32(uint32_t offset) {
    printf("READ  0x%03x\\n", offset);
    return 0;
}

static int qflow_wait_done(unsigned max_polls) {
    for (unsigned i = 0; i < max_polls; ++i) {
        uint32_t status = qflow_read32(QFLOW_REG_STATUS);
        if (status & QFLOW_STATUS_DONE) return 0;
    }
    return -1;
}

int main(void) {
    qflow_write32(QFLOW_REG_CONTROL, QFLOW_CONTROL_SOFT_RESET);
    qflow_write32(QFLOW_REG_CONTROL, 0);
    // Load vector registers here from golden_vectors.csv.
    qflow_write32(QFLOW_REG_CONTROL, QFLOW_CONTROL_START);
    qflow_write32(QFLOW_REG_CONTROL, 0);
    if (qflow_wait_done(100000) != 0) return 1;
    printf("status=%u selected=%u weight=%u bottleneck=%u latency=%u\\n",
           qflow_read32(QFLOW_REG_STATUS),
           qflow_read32(QFLOW_REG_SELECTED_PATH_ID),
           qflow_read32(QFLOW_REG_BEST_WEIGHT),
           qflow_read32(QFLOW_REG_BOTTLENECK_FIDELITY),
           qflow_read32(QFLOW_REG_LATENCY_CYCLES));
    return 0;
}
"""

py_code = """#!/usr/bin/env python3
\"\"\"QFlow AWS F2 host-driver Python skeleton.
Replace mmio_read32/mmio_write32 with AWS FPGA runtime/MMIO calls later.
\"\"\"
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
    print(f\"WRITE 0x{offset:03x} = 0x{value:08x}\")

def mmio_read32(offset: int) -> int:
    print(f\"READ  0x{offset:03x}\")
    return 0

def wait_done(max_polls: int = 100_000) -> None:
    for _ in range(max_polls):
        if mmio_read32(STATUS) & STATUS_DONE:
            return
    raise TimeoutError(\"QFlow timeout while waiting for DONE\")

def main() -> None:
    mmio_write32(CONTROL, CONTROL_SOFT_RESET)
    mmio_write32(CONTROL, 0)
    # Load vector registers here from golden_vectors.csv.
    mmio_write32(CONTROL, CONTROL_START)
    mmio_write32(CONTROL, 0)
    wait_done()
    print({
        \"status\": mmio_read32(STATUS),
        \"selected_path_id\": mmio_read32(SELECTED_PATH_ID),
        \"best_weight\": mmio_read32(BEST_WEIGHT),
        \"bottleneck_fidelity\": mmio_read32(BOTTLENECK_FIDELITY),
        \"latency_cycles\": mmio_read32(LATENCY_CYCLES),
    })

if __name__ == \"__main__\":
    main()
"""

(OUT / "qflow_aws_host_driver_stub.c").write_text(c_code)
(OUT / "qflow_aws_host_driver_stub.py").write_text(py_code)
print(f"Wrote {OUT / 'qflow_aws_host_driver_stub.c'}")
print(f"Wrote {OUT / 'qflow_aws_host_driver_stub.py'}")
print("HOST_DRIVER_STUB_PASS")
