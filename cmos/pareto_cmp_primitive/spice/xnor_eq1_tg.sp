* QFlow Part D CMOS primitive study
* 1-bit equality/XNOR primitive using transmission-gate mux style
* eq = A XNOR B
* First-order ngspice model; not foundry signoff.

.option post
.param VDD=1.8
.param LMIN=0.15u
.param WN=1.0u
.param WP=2.0u
.param CLOAD=20f

VDD_SUPPLY vdd 0 DC {VDD}

* A is held high in this first test, so xout should follow B.
VA  a  0 DC {VDD}
VAB ab 0 DC 0

* B toggles and Bbar is the complement.
VB  b  0 PULSE(0 {VDD} 2n 50p 50p 3n 6n)
VBB bb 0 PULSE({VDD} 0 2n 50p 50p 3n 6n)

* XNOR as mux: if A=1 choose B; if A=0 choose Bbar.
* TG path for B, active when A=1.
MBN xout a  b  0   NMOS_L1 W={WN} L={LMIN}
MBP xout ab b  vdd PMOS_L1 W={WP} L={LMIN}

* TG path for Bbar, active when A=0.
MBBN xout ab bb 0   NMOS_L1 W={WN} L={LMIN}
MBBP xout a  bb vdd PMOS_L1 W={WP} L={LMIN}

COUT xout 0 {CLOAD}

.model NMOS_L1 NMOS LEVEL=1 VTO=0.45 KP=120u GAMMA=0.4 LAMBDA=0.05 PHI=0.7
.model PMOS_L1 PMOS LEVEL=1 VTO=-0.45 KP=45u GAMMA=0.4 LAMBDA=0.05 PHI=0.7

.tran 1p 20n

.measure tran tplh TRIG v(b) VAL=0.9 RISE=1 TARG v(xout) VAL=0.9 RISE=1
.measure tran tphl TRIG v(b) VAL=0.9 FALL=1 TARG v(xout) VAL=0.9 FALL=1

.control
run
set wr_singlescale
wrdata results/partD_cmos/pareto_cmp_primitive/xnor_eq1/xnor_eq1_waveform.csv v(a) v(b) v(bb) v(xout)
quit
.endc

.end
