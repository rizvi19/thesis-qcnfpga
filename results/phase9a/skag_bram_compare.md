# SKAG BRAM Optimization Comparison

## Baseline `skag_mem`
- BRAM (18K equivalent): 0
- DSP: 2
- LUT: n/a
- FF: n/a

## Optimized `skag_mem_bram`
- BRAM (18K equivalent): 28
- DSP: 2
- LUT: 3884
- FF: 299
- LUTRAM primitives: 0

## Memory mapping
- Block RAM mapped objects: 16, R
- Distributed RAM mapped objects: none

## Delta (optimized - baseline)
- BRAM (18K equivalent): 28
- DSP: 0
- LUT: 3884
- FF: 299
- LUTRAM primitives: 0

**BRAM inference improved:** `True`
**Edge memory fully in BRAM:** `False`
