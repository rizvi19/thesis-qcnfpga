# QFlow Pareto-C0 OpenROAD-flow configuration
# Generated from thesis repo: /media/shahriar-rizvi/Data/CSE/Thesis/from13March/qflow_step1_phase0

export DESIGN_NICKNAME = qflow_pareto_c0
export DESIGN_NAME = pareto_cmp_c0_full
export PLATFORM = sky130hd

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/$(DESIGN_NAME).v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

# Fixed die/core area method.
# Pareto-C0 is compact, so this is intentionally small but still safe.
export DIE_AREA = 0 0 200 200
export CORE_AREA = 20 20 180 180
