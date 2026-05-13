# QFlow AWS-Style Local MMIO Register Map

This register map is a local pre-AWS contract for the `qflow_mmio_regs` wrapper. It is not yet the final AWS shell integration. The goal is to test host-style register writes and reads before launching EC2 F2.

## Control and status

| Offset | Name | Direction | Meaning |
|---:|---|---|---|
| `0x000` | CONTROL | W | bit0=`start`, bit1=`soft_reset` |
| `0x004` | STATUS | R | bit0=`done`, bit1=`valid_path`, bit2=`no_path`, bit3=`busy` |
| `0x010` | SRC_NODE | W/R | Source node ID |
| `0x014` | DST_NODE | W/R | Destination node ID |
| `0x018` | TIME_NOW | W/R | Timestamp / trace input |
| `0x01C` | F_MIN | W/R | Q0.16 minimum fidelity threshold |

## Edge registers

For edge `i`, base address is `0x100 + i*0x20`.

| Offset inside edge | Name | Format |
|---:|---|---|
| `0x00` | KEY_COUNT | uint16 |
| `0x04` | F_INIT | Q0.16 |
| `0x08` | DECAY_IDX | uint8 LUT index |
| `0x0C` | ARRIVAL_RATE | Q8.8 |
| `0x10` | QBER | Q0.16 |
| `0x14` | DISTANCE_COST | Q16.16 score/cost |

## Candidate path registers

For candidate `c`, base address is `0x300 + c*0x10`.

| Offset inside candidate | Name | Format |
|---:|---|---|
| `0x00` | CAND_EDGES | packed 4 edge IDs, 4 bits each: `{edge3,edge2,edge1,edge0}` |
| `0x04` | CAND_LEN | number of active edges in candidate |

## Output registers

| Offset | Name | Direction | Meaning |
|---:|---|---|---|
| `0x400` | SELECTED_PATH_ID | R | Winning candidate ID |
| `0x404` | BEST_WEIGHT | R | Selected path score |
| `0x408` | BOTTLENECK_FIDELITY | R | Minimum edge fidelity along selected path |
| `0x40C` | LATENCY_CYCLES | R | Kernel-local latency counter |

## Transaction protocol

1. Write all input registers.
2. Write `CONTROL=1` to start.
3. Poll `STATUS.done` until it becomes `1`.
4. Read `SELECTED_PATH_ID`, `BEST_WEIGHT`, `BOTTLENECK_FIDELITY`, and `LATENCY_CYCLES`.
5. Before the next transaction, either write new input registers and start again, or write `CONTROL=2` to soft-reset sticky status.

## Claim boundary

Passing this local MMIO wrapper test proves register-level control readiness in simulation. It does not prove AWS F2 AFI build, AFI load, or physical FPGA execution.
