# P6 H0 ISE Attempt 1 Diagnosis

## Immediate script stop

XST completed and produced `p6_h0.ngc`, `xst.log` and
`p6_h0_xst.xrpt`. The first build script incorrectly required a
`p6_h0.syr` file, but this command-line invocation used `xst.log` as its
synthesis report. The script therefore stopped before NGDBuild.

## Timing defect discovered

XST reported:

- errors: 0;
- estimated minimum period: 55.080 ns;
- estimated maximum frequency: 18.155 MHz.

The critical path was inside the QF6R decimal formatter. A 32-bit
`work_value % 10` and `work_value / 10` were synthesized into one large
combinational divider/modulo network.

## Repair boundary

Attempt 1 is not a completed implementation and produced no NGD, mapped
NCD, routed NCD or bitstream. Its reports are retained as negative evidence.
The repair replaces only the transport formatter with a multi-cycle
shift-add-3 converter. Kernel timing and result semantics are unchanged.
