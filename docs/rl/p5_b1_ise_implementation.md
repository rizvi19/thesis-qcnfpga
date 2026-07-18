# P5 B1 I/O Sanity — Stage B Offline ISE Implementation

## Scope and evidence boundary

This subgate implements the accepted B1 Stage-A RTL and UCF with Xilinx ISE
14.7 for the Digilent Nexys 3 `XC6SLX16-2-CSG324`. It runs the exact offline
flow XST, NGDBuild, Map, PAR, TRCE and BitGen, retains the reports and exact
bitstream hash, and stops for assistant review. It does not enumerate or
program a board, open a UART device, or access EEPROM.

The frozen source checkpoint is
`097788bb3359e878e600bd74703b86ee6856367e` on
`rl-nexys3-adaptive`. The package verifies the exact hashes of all ten Stage-A
checkpoint files before installing the four Stage-B authored files or starting
ISE.

## Toolchain and build isolation

The authoritative ISE settings file is
`/mnt/xilinx-ise14.7/Xilinx/14.7/ISE_DS/settings64.sh`, with the preserved
license at `/home/shahriar-rizvi/.Xilinx/Xilinx.lic`. The installer requires
the ISE filesystem mount to be read-only. It copies the exact project inputs
to a new dedicated build directory under `~/Downloads`; all intermediate ISE
files remain there for inspection. Only an explicit evidence allowlist is
copied into the repository.

The XST project deliberately omits `-verilog2001`, which ISE 14.7 rejects for
Spartan-6. Stage A already enforced plain synthesizable Verilog with host
static checks and RTL simulation; Stage B requires XST to accept those exact
files.

## Pass conditions

1. XST completes for top `p5_b1_top` and exact part
   `xc6slx16-2-csg324` with zero errors and a nonempty NGC.
2. NGDBuild applies `p5_b1_io_sanity.ucf`, completes with zero errors and
   produces a nonempty NGD and PCF.
3. Map fits the exact device with zero errors and produces a nonempty mapped
   NCD and map report.
4. PAR completes with zero errors, routes all signals, and reports timing score
   zero.
5. TRCE evaluates the routed NCD against the exact PCF, reports the 10 ns clock
   constraint and zero timing errors (or the equivalent all-constraints-met
   sentinel).
6. BitGen completes with zero errors and produces a nonempty `.bit`; its byte
   count and SHA-256 are recorded.
7. Exact reports, command/toolchain records, validation JSON and checksums are
   retained without staging, committing or pushing.

## Claim firewall

A Stage-B pass permits only this statement: the exact B1 design was
successfully implemented by ISE 14.7 and met its declared 10 ns constraint in
the retained post-PAR/TRCE reports. It is not a physical-board result and not
a measured board Fmax. B1 remains incomplete until a separately authorized
volatile-board observation gate passes.

The package contains no board-enumeration, JTAG-programming, UART-device or
EEPROM command. Any later board operation requires a new bounded package and
explicit confirmation that the board is connected.

## Stage B independent assistant review

Decision: **PASS**.

The complete attempt-3 installer transcript was reviewed after execution. The
repository, upstream and live remote all remained at
`097788bb3359e878e600bd74703b86ee6856367e`; the accepted Stage-A hashes and
lower-rung RTL simulation reproduced exactly; and both earlier failed attempts
were preserved with their narrow causes and repairs.

ISE 14.7 completed XST, NGDBuild, Map, PAR, TRCE and BitGen for the exact
`p5_b1_top` design on `XC6SLX16-2-CSG324`. NGDBuild reported zero errors and
zero warnings. Map used 92 slice registers, 192 slice LUTs and 64 occupied
slices; all 17 bonded I/O were LOC constrained. PAR completely routed the
design with timing score zero. TRCE reported zero timing errors, 3.873 ns
positive worst setup slack against the declared 10 ns clock, and a 6.127 ns
minimum implemented period (163.212 MHz). These are post-PAR/TRCE results for
the exact build, not physical-board measurements.

BitGen completed with zero DRC errors and warnings. The retained bitstream is
464294 bytes with SHA-256
`bf657f09f3b6968efd39079d53dfab42348a9de185cf178bc947035b7e59673b`.
The exact repository scope was four authored files plus nineteen evidence
files, with zero staging, commits or pushes before this review.

No live-board enumeration, UART-device access, FPGA programming or EEPROM
access occurred. Stage B is accepted for checkpointing, but B1 and P5 Step 3
remain incomplete until a separately authorized physical-board observation
gate passes.

The first archival/checkpoint wrapper stopped before any repository mutation
because it unnecessarily required the optional `rg` utility. That packaging
failure is preserved as a raw output. The repaired archival wrapper uses
portable `grep` and changes no Stage-B design or implementation evidence.
