# QFlow Cloud-FPGA Kernel Specification

## Purpose

This starter kernel prepares the minimum-cost AWS EC2 F2 validation path for QFlow. The first cloud run should validate only the computational kernel, not the full thesis system. The kernel includes:

1. FDPE-style Q0.16 fidelity update using a 256-entry `exp(-x)` LUT.
2. SKAG-style edge rank-score computation using key count, fidelity, arrival-rate bucket, QBER penalty, and distance/cost.
3. Candidate path selector over four candidate paths.
4. Kernel-local latency counter from `start` to `done`.

## Evidence boundary

Safe wording after successful AWS run:

> The selected QFlow computational kernel was deployed on AWS EC2 F2 FPGA fabric as an AFI and tested through host-to-FPGA transactions. Hardware outputs were compared against golden vectors.

Do **not** claim:

- Full Nexys 3 deployment.
- Full QFlow system deployment.
- Spartan-6 result.
- Fabricated silicon.
- AFI creation alone as execution.

## Fixed-point formats

| Quantity | Format | Notes |
|---|---:|---|
| Fidelity | Q0.16 unsigned | `0..65535` represents `0..~1.0` |
| QBER | Q0.16 unsigned | Penalty input for rank score |
| Arrival rate | Q8.8 style integer | Bucketed in the starter SKAG score |
| Distance/cost | Q16.16-like integer | Used as base path score component |
| Edge score | 32-bit unsigned | Lower is better; `0xFFFFFFFF` is invalid/infinite |

## Local top-level interface

The local pre-AWS top is `qflow_cloud_kernel.v`. It is not yet the AWS shell wrapper. It is the deterministic kernel that should later be placed behind the AWS Custom Logic MMIO/register interface.

### Inputs

| Signal | Width | Description |
|---|---:|---|
| `clk` | 1 | Kernel clock |
| `rst_n` | 1 | Active-low reset |
| `start` | 1 | Start transaction pulse |
| `src_node` | 6 | Source node ID, preserved for traceability |
| `dst_node` | 6 | Destination node ID, preserved for traceability |
| `time_now` | 32 | Timestamp input; reserved for later fuller FDPE timing mode |
| `f_min_threshold` | 16 | Minimum acceptable path fidelity |
| `key_counts_flat` | `NUM_EDGES*16` | Per-edge key count |
| `f_init_flat` | `NUM_EDGES*16` | Per-edge initial fidelity |
| `decay_idx_flat` | `NUM_EDGES*8` | Per-edge LUT index for exp(-x) |
| `arrival_rate_flat` | `NUM_EDGES*16` | Per-edge arrival-rate proxy |
| `qber_flat` | `NUM_EDGES*16` | Per-edge QBER |
| `distance_cost_flat` | `NUM_EDGES*32` | Per-edge distance/cost component |
| `cand_edges_flat` | `NUM_CAND*MAX_PATH_EDGES*4` | Candidate path edge IDs |
| `cand_lens_flat` | `NUM_CAND*3` | Candidate path lengths |

### Outputs

| Signal | Width | Description |
|---|---:|---|
| `done` | 1 | One-cycle done pulse |
| `valid_path` | 1 | At least one valid candidate path exists |
| `no_path` | 1 | No valid candidate path exists |
| `selected_path_id` | 2 | Winning candidate path ID |
| `best_weight` | 32 | Winning path score |
| `bottleneck_fidelity` | 16 | Minimum edge fidelity on selected path |
| `latency_cycles` | 32 | Transaction latency in kernel clock cycles |

## Planned AWS MMIO register map

| Offset | Register | Direction | Description |
|---:|---|---|---|
| `0x000` | control | Host -> FPGA | bit0=start, bit1=soft_reset |
| `0x004` | status | FPGA -> Host | bit0=done, bit1=valid_path, bit2=no_path, bit3=error |
| `0x010` | src_node | Host -> FPGA | Source node ID |
| `0x014` | dst_node | Host -> FPGA | Destination node ID |
| `0x018` | time_now | Host -> FPGA | Timestamp used by FDPE |
| `0x01C` | f_min_threshold | Host -> FPGA | Minimum acceptable bottleneck fidelity |
| `0x020-0x05C` | edge registers | Host -> FPGA | Packed edge fields |
| `0x080-0x09C` | candidate path registers | Host -> FPGA | Packed candidate path codes |
| `0x100` | selected_path_id | FPGA -> Host | Winning candidate ID |
| `0x104` | best_weight | FPGA -> Host | Selected path score |
| `0x108` | bottleneck_fidelity | FPGA -> Host | Minimum fidelity along selected path |
| `0x10C` | latency_cycles | FPGA -> Host | Cycle count from start to done |

## Local pass gate

Do not launch AWS until this command passes locally:

```bash
cd cloud_fpga/qflow_kernel
make all
```

Required outputs:

- `vectors/exp_lut.hex`
- `vectors/golden_vectors.csv`
- `results/local_sim_output.txt`
- `results/hardware_output.csv`
- `results/hardware_vs_python.csv`

## Next implementation step after local pass

Add an AWS Custom Logic wrapper around `qflow_cloud_kernel.v` that maps host MMIO writes/reads to the local top-level signals. Keep the local kernel unchanged until the AWS official example passes.
