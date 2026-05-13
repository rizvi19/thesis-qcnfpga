// QFlow AWS F2 host-driver skeleton
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
    printf("WRITE 0x%03x = 0x%08x\n", offset, value);
}

static uint32_t qflow_read32(uint32_t offset) {
    printf("READ  0x%03x\n", offset);
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
    printf("status=%u selected=%u weight=%u bottleneck=%u latency=%u\n",
           qflow_read32(QFLOW_REG_STATUS),
           qflow_read32(QFLOW_REG_SELECTED_PATH_ID),
           qflow_read32(QFLOW_REG_BEST_WEIGHT),
           qflow_read32(QFLOW_REG_BOTTLENECK_FIDELITY),
           qflow_read32(QFLOW_REG_LATENCY_CYCLES));
    return 0;
}
