# P4 Step 9 Status

Step 9 synthesizes the frozen P4 learned-policy controller for the Digilent
Nexys 3 Spartan-6 `XC6SLX16-2-CSG324`. The synthesis-only top is a transparent
port-for-port wrapper around the reviewed `rl_controller`; it adds no state,
policy logic, profile logic, training behavior, or datapath behavior.

The authoritative implementation path is the preserved ISE 14.7 WebPACK image
mounted read-only at `/mnt/xilinx-ise14.7`. XST consumes the exact four reviewed
Verilog-2001 modules, `policy_rom.mem`, and `profile_rom.mem`. NGDBuild then
translates the generated NGC for the exact Spartan-6 part as an independent
netlist-validity gate.

The Spartan-6 XST option set deliberately omits `-verilog2001`: ISE 14.7
rejects that switch for this selected device family. The language boundary is
instead enforced independently by warning-clean host Icarus `-g2001` lint and
source/project contract tests; XST must then accept those same frozen modules.

This step records controller-only XST resources and any XST timing estimate.
An XST estimate is not post-PAR timing closure and must not be reported as
board-achieved timing. There is no UCF in P4 because the controller is not yet
attached to the QFlow-Mini board shell.

Map, PAR, TRCE signoff, BitGen, board programming, UART/QFlow-Mini integration,
EEPROM access, runtime Q-table argmax, and on-chip learning remain outside this
step. The deployed inference artifact remains the frozen policy-index ROM;
`q_table.mem` remains audit-only and `q_update.v` remains absent.

Completion requires all frozen Python/RTL regressions to pass, XST to report
zero errors, a nonempty NGC, successful NGDBuild translation to a nonempty NGD,
machine-readable evidence with checksums, and human review before checkpointing.

## Human review

Decision: **PASS**.

The reviewed flow completed XST with zero errors and translated the resulting
NGC to a nonempty NGD. The 14 `NgdBuild:452` warnings are accepted expected
synthesis optimization: `bottleneck_fidelity_u16[0]` cannot affect comparisons
against the three even frozen fidelity thresholds, and
`utilization_imbalance_u16[12:0]` cannot affect comparisons against the three
frozen thresholds aligned to 8192. No other NGDBuild warning category occurred.

The recorded 4.035 ns / 247.812 MHz values are XST post-synthesis estimates
only. They are not post-PAR timing closure or board-achieved timing. Map, PAR,
TRCE signoff, BitGen, board programming and EEPROM access were not performed.
