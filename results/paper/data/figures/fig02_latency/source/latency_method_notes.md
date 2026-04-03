# Latency Method Notes — FIG02

This file defines how the latency comparison is allowed to be interpreted.

## Goal
Show that the hardware decision path is substantially lower-latency than software-side routing evaluation.

## Allowed comparison principles
- Hardware values may come from cycle count and achieved clock information.
- Software values may come from measured runtime, profiled runtime, or carefully labeled derived summaries.
- Measured, derived, and estimated values must not be mixed without labels.
- If conditions differ, the caption and table notes must say so clearly.

## Preferred display items
- QFlow hardware decision path
- Distance software baseline
- Key-aware software baseline
- Software PMO-GA baseline

## Caution
The figure should demonstrate hardware advantage, not claim perfectly identical measurement conditions unless that is truly established.

## Recommended plot type
- horizontal bar chart
- optional log-scale x-axis if ranges differ greatly

## Final paper message
The architecture is not only implementable; it is also operationally attractive because route decisions can be produced with much lower latency in hardware than in software-side routing evaluation.
