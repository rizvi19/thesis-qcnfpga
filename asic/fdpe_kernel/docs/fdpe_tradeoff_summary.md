# FDPE Kernel Area-Accuracy Tradeoff Summary

## Purpose

This document summarizes the first ASIC/VLSI-style kernel study for the QFlow Fidelity Decay Prediction Engine.

The goal is to evaluate how LUT depth and interpolation affect generic synthesis cost and approximation quality.

## Context

FDPE computes stored-key fidelity decay using:

F_stored = F_initial * exp(-x)

where x represents normalized elapsed time. In hardware, exp(-x) is approximated using a fixed-point LUT.

## Variants evaluated

| Variant | LUT entries | Lookup mode | Fidelity format | Purpose |
|---|---:|---|---|---|
| FDPE-V0 | 256 | floor/table lookup | Q0.16 | baseline |
| FDPE-V1 | 128 | floor/table lookup | Q0.16 | reduced-area LUT |
| FDPE-V2 | 128 | linear interpolation | Q0.16 | accuracy-recovery variant |

## Generic Yosys synthesis result

| Variant | Total cells | Delta vs V0 | Cell reduction vs V0 |
|---|---:|---:|---:|
| FDPE-V0 256 LUT floor | 2258 | 0 | 0.00% |
| FDPE-V1 128 LUT floor | 1944 | -314 | +13.91% |
| FDPE-V2 128 LUT linear interpolation | 3399 | +1141 | -50.53% |

## Approximation error result

From dense sampling over x in [0,8):

| LUT entries | Mode | Max relative error in x in [0,3] | Max absolute error all |
|---:|---|---:|---:|
| 256 | floor | 3.1853% | 3.0757e-02 |
| 256 | linear | 0.0238% | 1.2247e-04 |
| 128 | floor | 6.4597% | 6.0568e-02 |
| 128 | linear | 0.0587% | 4.7001e-04 |

## Interpretation

The 128-entry floor-LUT version reduces generic cell count by 13.91% compared with the 256-entry floor-LUT baseline, but its approximation error becomes significantly higher.

The 128-entry interpolated version restores high accuracy, with max relative error below 0.06% over the practical range x in [0,3]. However, its generic logic cost rises to 3399 cells because of interpolation arithmetic and dual LUT reads.

## Important synthesis caveat

In these generic Yosys synthesis runs, the LUT was not preserved as a ROM or SRAM macro. It was mapped into flip-flop and mux logic.

Therefore, these results are best interpreted as generic logic-synthesis baselines. A later OpenRAM or memory-macro version should be evaluated for stronger ASIC-style memory evidence.

## Current conclusion

FDPE has a clear area-accuracy tradeoff:

- FDPE-V1 is the best area-saving option.
- FDPE-V2 is the best accuracy-preserving option.
- FDPE-V0 remains the baseline reference.
- A future memory-macro or interpolated-lite variant may offer a better balance.

## Evidence boundary

These results are generic Yosys synthesis and numerical approximation-analysis results. They are not post-layout OpenROAD results and not fabricated silicon results.
