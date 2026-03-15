# QFlow Step 1 — Phase 0 Consistency Freeze

This is the **first working package** for the thesis.
It follows the updated master plan: start with **Phase 0 consistency freeze**, not new RTL coding.

## Goal of this step
Build the frozen design contract and verify that the current Python golden model is stable enough to become the anchor for later RTL work.

## What you should have in the same folder
Place these existing project files in the same working directory before running:
- `reference_model.py`
- `math_framework.pdf`
- `QFlow_Architecture_Specification.docx`
- `QFlow_Master_Thesis_Plan_v2.pdf`

## Files in this package
- `requirements_phase0.txt` — minimal Python packages for this step
- `Makefile` — one-command entry points
- `init_repo_structure.py` — creates the recommended repository layout
- `audit_reference_model.py` — runs the Python model, tests, and saves audit artifacts
- `phase0_design_contract_draft.md` — pre-filled master contract draft
- `phase0_scope_freeze.md` — mandatory core vs extension scope
- `phase0_issue_log_template.csv` — issue tracker for contradictions/mismatches

## Recommended commands

### 1) Create a virtual environment
#### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements_phase0.txt
```

#### Linux / WSL / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_phase0.txt
```

### 2) Initialize the project structure
```bash
python init_repo_structure.py --root .
```

### 3) Run the Phase 0 audit
```bash
python audit_reference_model.py --model reference_model.py --out results/phase0
```

### 4) Or run everything with one command
```bash
make phase0
```

## What to send back to me after you run it
Please send me these files or their contents:
1. `results/phase0/model_test_output.txt`
2. `results/phase0/reference_model_summary.json`
3. `results/phase0/ring6_experiment_summary.json`
4. `results/phase0/open_issues_detected.md`

## What I already checked from your current materials
- The current `reference_model.py` unit-test suite passes.
- The default 6-node ring experiment runs successfully.
So the project already has a usable software anchor, which is exactly what the v2 plan wants before RTL expansion.

## Important rule for this thesis
For now we do **not** start with FDPE RTL or GA RTL.
We first freeze:
- constants
- formats
- scope
- module names
- validation path

That prevents rework later.
