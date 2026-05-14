# QFlow FDPE-V3 OpenROAD-flow configuration
# Generated from thesis repo: /media/shahriar-rizvi/Data/CSE/Thesis/from13March/qflow_step1_phase0

export DESIGN_NICKNAME = qflow_fdpe_v3
export DESIGN_NAME = fdpe_kernel_v3_lut64_interp
export PLATFORM = sky130hd

export VERILOG_FILES = $(DESIGN_HOME)/src/$(DESIGN_NICKNAME)/$(DESIGN_NAME).v
export SDC_FILE = $(DESIGN_HOME)/$(PLATFORM)/$(DESIGN_NICKNAME)/constraint.sdc

# Fixed die/core area method.
# FDPE-V3 is larger than SKAG-W1 because it has LUT/interpolation logic.
export DIE_AREA = 0 0 500 500
export CORE_AREA = 40 40 460 460
