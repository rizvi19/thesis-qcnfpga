# FDPE Kernel VLSI Study Plan

## Goal

Study the area, timing, and power cost of the QFlow Fidelity Decay Prediction Engine when mapped into an ASIC-style open-source flow.

## Baseline kernel

FDPE-V0:
- 256-entry exp(-x) LUT
- Q0.16 fidelity format
- canonical stored-fidelity computation
- Python/RTL vector-compatible behavior

## Optimized variants

FDPE-V1:
- 128-entry LUT
- Q0.16 output
- reduced memory footprint

FDPE-V2:
- 64-entry LUT
- Q0.14 or Q0.12 output
- reduced precision

FDPE-V3:
- no interpolation / table-only approximation
- compare route-quality impact

FDPE-V4:
- event-driven update
- avoid updating links whose timestamp/fidelity change is below threshold

## Metrics

For each variant:
- cell count
- area
- core area
- WNS
- maximum frequency
- total power
- dynamic power
- leakage power
- energy per update
- fidelity error
- route match rate against canonical Part A behavior

## Required output tables

1. FDPE ASIC PPA table
2. FDPE approximation error table
3. FDPE route-quality preservation table
4. FDPE critical path table

## Safe claim

This study evaluates ASIC-style physical-design feasibility and approximation tolerance of the QFlow FDPE kernel. It does not claim fabricated silicon.
