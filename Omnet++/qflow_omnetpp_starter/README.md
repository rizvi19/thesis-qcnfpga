# QFlow OMNeT++ Starter Kit

This starter kit is for the missing network-level evaluation layer of QFlow:
dynamic request traffic, blocking under load, fidelity distributions, utilization imbalance,
and scalability sweeps.

## What this starter kit gives you

- A plain OMNeT++ project (no INET required for the first stage)
- A runnable custom simulator with:
  - Poisson request arrivals
  - distance-dependent key generation
  - exponential fidelity decay
  - per-request logging
  - four routing modes:
    - `distance`
    - `keyaware`
    - `random`
    - `ga_tcheby_proxy`
- Topology CSV files:
  - `ring6.csv`
  - `mesh9.csv`
  - `mesh16.csv`
  - `irregular12.csv`
- Batch run and plotting helpers

## Important honesty note

`ga_tcheby_proxy` is a network-simulation proxy for the PMO-GA policy. It is useful to
start the OMNeT++ dynamic-load study immediately, but it is not yet the exact NSGA-II software
GA from `reference_model.py`.

So the correct usage is:

1. Use this starter to build the dynamic-load pipeline quickly.
2. Validate blocking / fidelity / utilization plots.
3. Then align or replace the proxy with the exact Python GA / offline replay.

This matches the thesis plan fallback:
offline alignment is acceptable if full co-simulation is too complex.

## Recommended installation path

### Option A — official Linux tarball (least friction)
The OMNeT++ download page provides Linux tarballs with an `install.sh` script for supported distros.
After extracting the archive, run `install.sh` in the root directory and build OMNeT++.

### Option B — opp_env (officially recommended)
The OMNeT++ download page recommends `opp_env` for installing OMNeT++ and model frameworks.
INET docs also recommend `opp_env`, especially when you want a matching OMNeT++ + INET setup.

### Do you need INET now?
No. For this QFlow work, the first stage is a custom discrete-event simulation, so plain OMNeT++
is enough. Add INET later only if you need advanced packet/network protocol components.

## Suggested workflow

### Step 1 — install OMNeT++
Use either Option A or B above.

### Step 2 — create a workspace and copy this project
Example:
```bash
mkdir -p ~/omnetpp-workspace
cp -r qflow_omnetpp_starter ~/omnetpp-workspace/
cd ~/omnetpp-workspace/qflow_omnetpp_starter
```

### Step 3 — build from terminal
Inside an OMNeT++ shell:
```bash
./scripts/build_project.sh
```

### Step 4 — run the debug config
```bash
./scripts/run_debug_ring6.sh
```

This should create:
- `results/ring6_keyaware_debug.csv`

### Step 5 — open in the IDE (optional)
From an OMNeT++ shell:
```bash
omnetpp
```
Then import the project directory into the workspace and run configs from `omnetpp.ini`.

### Step 6 — run batch experiments
```bash
./scripts/run_batch_small.sh
```

This generates per-run CSV files for several topologies / algorithms / loads.

### Step 7 — generate first figures
```bash
python3 scripts/plot_qflow_omnet_results.py results summary_plots
```

## Project structure

- `src/` — OMNeT++ C++ and NED files
- `topologies/` — CSV edge lists
- `scripts/` — build/run/plot helpers
- `results/` — simulation outputs

## What to do next after this starter runs

1. Verify Ring-6 by hand
2. Verify Mesh-9 and Mesh-16 produce nontrivial blocking under high load
3. Compare `keyaware` vs `ga_tcheby_proxy`
4. Add exact Python-GA replay or co-simulation alignment
5. Generate the must-have paper figures:
   - blocking vs request rate
   - fidelity CDF
   - key utilization heatmap
   - scalability plot
