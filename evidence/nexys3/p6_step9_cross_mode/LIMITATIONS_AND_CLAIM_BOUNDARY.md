# P6 Step 9 — Limitations and Claim Boundary

## Claims supported directly

1. H0–H4 are independent same-board implementations on one Nexys3.
2. Every mode met the 100 MHz implementation constraint.
3. All 420 physical records and 3780 result fields matched the frozen model.
4. H3 physically changed profiles.
5. H4 physically executed a reinforcement-learned adaptive profile sequence
   with frozen dwell behavior.
6. Kernel latency excludes UART, host capture, JTAG programming and display
   refresh.

## Claims not supported

1. No online learning or runtime Q-table update occurred on the FPGA.
2. No universal network superiority is claimed from this 84-vector replay.
3. Raw scalar scores are not compared across modes because profile weights
   differ.
4. No power or energy superiority is claimed.
5. This reduced Nexys3 QFlow-Mini layer is not presented as the full Artix-7
   implementation.
6. Published software QKD results are not used as direct same-board hardware
   baselines.

## Explicit omissions

- Power/energy status: omitted; no common activity-calibrated estimate or
  measurement exists.
- Photo/video repository status: OMITTED_NOT_ARCHIVED_IN_REPOSITORY.
- Broader repeated network traces and higher-powered statistical analysis:
  journal-strengthening work, not required to validate the physical H0–H4
  execution reported here.
