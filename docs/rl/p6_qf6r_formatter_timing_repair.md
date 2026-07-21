# P6 QF6R Formatter Timing Repair

## Failure

The first H0 XST attempt completed with zero synthesis errors but estimated
a 55.080 ns minimum period. Its critical path was the transport formatter's
single-cycle 32-bit divide/modulo-by-10 network.

The attempt also exposed a script-only artifact-name defect: command-line
XST generated `xst.log`, not the required `p6_h0.syr`. No downstream
implementation stage was reached.

Attempt-1 XST log SHA-256: `a6369f94b6bb1bfb9e992317f44240b9068fadc203b75a251328089642427419`

## Repair

The QF6R formatter now uses an iterative 18-step shift-add-3
binary-to-BCD converter for each field. The exact 44-byte record is
unchanged. Formatting latency is outside the kernel-cycle counter.

Repaired formatter SHA-256: `960b9484df797273ae8900ed78a6593627e929b82937e5bcf3d7f1e918e71669`

## Regression

- 420 QF6R records checked;
- 18,480 formatter bytes checked;
- zero byte mismatches;
- H0-H4 physical-shell simulation rerun;
- 420/420 internal golden comparisons passed;
- no ISE build or physical programming performed in this repair checkpoint.
