# QFlow SKAG-W1 OpenROAD-flow configuration
# Generated from thesis repo: /media/shahriar-rizvi/Data/CSE/Thesis/from13March/qflow_step1_phase0

export DESIGN_NICKNAME = qflow_skag_w1
export DESIGN_NAME = skag_weight_w1_shiftadd
export PLATFORM = sky130hd

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/$(DESIGN_NAME).v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

# Conservative first physical-design attempt.
# We keep the die/core generous because this is the first flow bring-up.
# export CORE_UTILIZATION = 30  # disabled: using fixed DIE_AREA/CORE_AREA
# export PLACE_DENSITY = 0.45  # disabled: using fixed DIE_AREA/CORE_AREA

export DIE_AREA = 0 0 200 200
export CORE_AREA = 20 20 180 180
