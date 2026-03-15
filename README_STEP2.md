# QFlow Step 2 — Contract Freeze + LUT Generation

This package closes the remaining Phase 0 freeze items and produces the first RTL-facing artifacts for FDPE.

## What this step produces

### Phase 0 freeze outputs
- `phase0_freeze_report.md`
- `qflow_frozen_config.json`
- `axi_register_freeze.csv`
- `math_to_hardware_mapping.csv`

### Phase 1 arithmetic outputs
- `exp_lut.hex`
- `lut_error_summary.json`
- `lut_error_analysis.csv`
- `error_analysis.png`
- `fdpe_golden_vectors.csv`
- `model_crosscheck.json`

## Install

```bash
pip install -r requirements_step2.txt
```

## Run

From the folder containing this package, run:

```bash
python freeze_phase0_contract.py \
  --summary /path/to/reference_model_summary.json \
  --experiment /path/to/ring6_experiment_summary.json \
  --issues /path/to/open_issues_detected.md \
  --out results/phase0

python generate_lut_and_vectors.py \
  --model /path/to/reference_model.py \
  --out results/phase1
```

## Example

```bash
python freeze_phase0_contract.py \
  --summary ../reference_model_summary.json \
  --experiment ../ring6_experiment_summary.json \
  --issues ../open_issues_detected.md \
  --out results/phase0

python generate_lut_and_vectors.py \
  --model ../reference_model.py \
  --out results/phase1
```

## Send these back

Please send me these generated files after you run them:
- `results/phase0/phase0_freeze_report.md`
- `results/phase0/qflow_frozen_config.json`
- `results/phase0/axi_register_freeze.csv`
- `results/phase0/math_to_hardware_mapping.csv`
- `results/phase1/lut_error_summary.json`
- `results/phase1/model_crosscheck.json`
- `results/phase1/fdpe_golden_vectors.csv`

## Why this step matters

This step freezes the arithmetic, register-facing contract, reproducibility defaults, and LUT generation path before any FDPE RTL is written. After this, the next implementation step is `fdpe.v` plus `tb_fdpe.v` against the frozen vectors.
