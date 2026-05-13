# QFlow AWS F2 cloud-kernel local preparation Makefile

IVERILOG ?= iverilog
VVP      ?= vvp
PYTHON   ?= python3

RTL = rtl/fdpe_kernel.v rtl/skag_weight_kernel.v rtl/path_selector_kernel.v rtl/qflow_cloud_kernel.v
TB  = tb/tb_qflow_cloud_kernel.v
OUT = results/qflow_kernel_tb.out

.PHONY: all vectors sim compare clean

all: vectors sim compare

vectors:
	$(PYTHON) sw/generate_golden_vectors.py
	$(PYTHON) sw/generate_tb_from_vectors.py

sim: vectors
	mkdir -p results
	$(IVERILOG) -g2012 -o $(OUT) $(TB) $(RTL)
	$(VVP) $(OUT) | tee results/local_sim_output.txt
	grep -i "ALL TESTS PASS" results/local_sim_output.txt

compare:
	$(PYTHON) sw/compare_hw_vs_golden.py --golden vectors/golden_vectors.csv --hw results/hardware_output.csv --out results/hardware_vs_python.csv

clean:
	rm -f results/qflow_kernel_tb.out results/local_sim_output.txt results/hardware_output.csv results/hardware_vs_python.csv
