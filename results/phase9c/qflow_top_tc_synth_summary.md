# QFlow Top-Level Timing-Closure Summary

## Utilization

## Timing
- WNS_ns: -72.446
- TNS_ns: -2499.08
- Requirement_ns: 10.0
- Data_path_delay_ns: 82.295
- Worst_source: u_skag/fdpe_s0_fidelity_reg[0]/C
- Worst_destination: u_skag/fdpe_s1_new_weight_reg[0]/D
- approx_Fmax_MHz: 12.151

## Notes
- Step 9C timing-closure build stores GA read weight in memory instead of recomputing it on the read path.
- Critical-path reduction is expected primarily inside u_skag ga-read weight generation.
