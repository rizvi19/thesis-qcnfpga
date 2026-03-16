# QFlow Top-Level Timing-Closure-4 Summary

## Utilization

## Timing
- WNS_ns: -8.154
- TNS_ns: -178.942
- Requirement_ns: 10.0
- Data_path_delay_ns: 18.002
- Worst_source: u_fdpe/s1_f_init_reg[15]/C
- Worst_destination: u_fdpe/s2_result_reg[0]/D
- approx_Fmax_MHz: 55.549

## Notes
- Step 9F timing-closure build replaces the SKAG variable-division dynamic-term stage with an exact multi-cycle divider and registered commit path.
- The main check is whether the prior one-cycle fidelity-to-dynamic-term divide path disappears from the critical path.
