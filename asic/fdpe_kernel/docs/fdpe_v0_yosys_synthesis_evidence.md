# FDPE-V0 Yosys Synthesis Evidence

## Kernel

`asic/fdpe_kernel/src/fdpe_kernel_v0.v`

## Synthesis script

`asic/fdpe_kernel/scripts/synth_fdpe_kernel_v0_yosys.ys`

## Run script

`asic/fdpe_kernel/scripts/run_fdpe_kernel_v0_yosys.sh`

## Tool

Yosys 0.51

## Synthesis status

FDPE-V0 generic Yosys synthesis completed successfully.

## Main Yosys statistics

Number of wires: 2178  
Number of wire bits: 2322  
Number of public wires: 12  
Number of public wire bits: 110  
Number of ports: 7  
Number of port bits: 44  
Number of memories: 0  
Number of memory bits: 0  
Number of processes: 0  
Number of cells: 2258  

## Cell breakdown

| Cell type | Count |
|---|---:|
| ANDNOT | 41 |
| AND | 459 |
| MUX | 45 |
| NAND | 1033 |
| NOR | 15 |
| NOT | 5 |
| ORNOT | 46 |
| OR | 92 |
| SDFFE_PN0P | 16 |
| SDFF_PN0 | 46 |
| SDFF_PP0 | 5 |
| XNOR | 36 |
| XOR | 419 |

## Important interpretation

The generated exp(-x) LUT was not preserved as SRAM/ROM in this generic Yosys synthesis run. Yosys mapped the `exp_lut` memory into flip-flop and mux logic.

This is acceptable for the first baseline synthesis sanity check, but it should not be treated as the final optimized ASIC memory implementation.

## Research value

This result establishes FDPE-V0 as a valid baseline for the Part C VLSI study. The next research step is to compare this baseline against reduced-LUT, reduced-precision, and memory-aware versions.

## Evidence boundary

This is generic RTL synthesis evidence. It is not OpenROAD physical-design evidence, not post-layout timing/power evidence, and not fabricated silicon evidence.
