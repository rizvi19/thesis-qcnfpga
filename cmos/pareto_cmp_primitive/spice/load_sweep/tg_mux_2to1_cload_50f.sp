* QFlow Part D TG mux load sweep
* Load = 50 fF
.option post
.param VDD=1.8
.param LMIN=0.15u
.param WN=1.0u
.param WP=2.0u
.param CLOAD=50f

VDD_SUPPLY vdd 0 DC {VDD}

* sel=1 selects in1; sel=0 selects in0
VSEL  sel  0 DC {VDD}
VSELB selb 0 DC 0

VIN0 in0 0 DC 0
VIN1 in1 0 PULSE(0 {VDD} 2n 50p 50p 3n 6n)

* TG for input 0, active when sel=0
M0N out selb in0 0   NMOS_L1 W={WN} L={LMIN}
M0P out sel  in0 vdd PMOS_L1 W={WP} L={LMIN}

* TG for input 1, active when sel=1
M1N out sel  in1 0   NMOS_L1 W={WN} L={LMIN}
M1P out selb in1 vdd PMOS_L1 W={WP} L={LMIN}

COUT out 0 {CLOAD}

.model NMOS_L1 NMOS LEVEL=1 VTO=0.45 KP=120u GAMMA=0.4 LAMBDA=0.05 PHI=0.7
.model PMOS_L1 PMOS LEVEL=1 VTO=-0.45 KP=45u GAMMA=0.4 LAMBDA=0.05 PHI=0.7

.tran 1p 20n

.measure tran tplh TRIG v(in1) VAL=0.9 RISE=1 TARG v(out) VAL=0.9 RISE=1
.measure tran tphl TRIG v(in1) VAL=0.9 FALL=1 TARG v(out) VAL=0.9 FALL=1

.control
run
set wr_singlescale
wrdata results/partD_cmos/pareto_cmp_primitive/load_sweep/tg_mux_2to1_cload_50f_waveform.csv time v(in1) v(out)
quit
.endc

.end
