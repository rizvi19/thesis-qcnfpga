# FDPE Kernel Area-Accuracy Tradeoff Summary

## Purpose

This document summarizes the first ASIC/VLSI-style kernel study for the QFlow Fidelity Decay Prediction Engine. The goal is to evaluate how LUT depth and interpolation affect generic synthesis cost and approximation quality.

## Context

FDPE computes stored-key fidelity decay using:

F_stored = F_initial * exp(-x)

where x represents normalized elapsed time. In hardware, exp(-x) is approximated using a fixed-point LUT.

## Variants evaluated

| Variant | LUT entries | Lookup mode | Fidelity format | Purpose |
|---|---:|---|---|---|
| FDPE-V0 | 256 | floor/table lookup | Q0.16 | baseline |
| FDPE-V1 | 128 | floor/table lookup | Q0.16 | reduced-area LUT |
| FDPE-V2 | 128 | linear interpolation | Q0.16 | high-accuracy interpolation |
| FDPE-V3 | 64 | linear interpolation | Q0.16 | balanced interpolation candidate |

## Generic Yosys synthesis result

| Variant | Total cells | Delta vs V0 | Cell reduction vs V0 |
|---|---:|---:|---:|
| FDPE-V0 256 LUT floor | 2258 | 0 | 0.00% |
| FDPE-V1 128 LUT floor | 1944 | -314 | +13.91% |
| FDPE-V2 128 LUT linear interpolation | 3399 | +1141 | -50.53% |
| FDPE-V3 64 LUT linear interpolation | 3014 | +756 | -33.48% |

## Approximation error result

From dense sampling over x in [0,8):

| LUT entries | Mode | Max relative error in x in [0,3] | Max absolute error all |
|---:|---|---:|---:|
| 256 | floor | 3.1853% | 3.0757e-02 |
| 256 | linear | 0.0238% | 1.2247e-04 |
| 128 | floor | 6.4597% | 6.0568e-02 |
| 128 | linear | 0.0587% | 4.7001e-04 |
| 64 | floor | 13.3235% | 1.1747e-01 |
| 64 | linear | 0.1986% | 1.8323e-03 |

## Interpretation

The 128-entry floor-LUT version reduces generic cell count by 13.91% compared with the 256-entry floor-LUT baseline, but its approximation error becomes significantly higher.

The 128-entry interpolated version restores high accuracy, with max relative error below 0.06% over the practical range x in [0,3]. However, its generic logic cost rises to 3399 cells because of interpolation arithmetic and dual LUT reads.

The 64-entry interpolated version provides a useful middle point. It is less accurate than the 128-entry interpolated design, but it reduces the interpolated design cost from 3399 cells to 3014 cells. That is an 11.33% reduction compared with FDPE-V2 while keeping practical-range relative error around 0.20%.

## Important synthesis caveat

In these generic Yosys synthesis runs, the LUT was not preserved as a ROM or SRAM macro. It was mapped into flip-flop and mux logic. Therefore, these results are best interpreted as generic logic-synthesis baselines.

A later OpenRAM or memory-macro version should be evaluated for stronger ASIC-style memory evidence.

## Current conclusion

FDPE has a clear area-accuracy tradeoff:

- FDPE-V1 is the best area-saving option.
- FDPE-V2 is the best accuracy-preserving option.
- FDPE-V3 is the best balanced interpolation candidate so far.
- FDPE-V0 remains the baseline reference.

## Evidence boundary

These results are generic Yosys synthesis and numerical approximation-analysis results. They are not post-layout OpenROAD results and not fabricated silicon results.
