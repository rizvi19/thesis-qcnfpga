# Layout Notes for FIG01

Recommended layout:
- left-to-right top-level architecture
- inputs on the left
- internal processing blocks centered
- selection/output to the right

Panel (a): top-level architecture
- Request Input + Network State Input at left
- FDPE and SKAG / Memory Block in middle
- Selection Logic to the right-middle
- Route Decision Output at far right
- Optional Control / Sequencing block above or below main datapath

Panel (b): pipeline/dataflow
- 5 horizontal stages
- use minimal text per stage
- optional cycle annotation only if clean and justified

Visual principles:
- avoid thin unreadable arrows
- keep block sizes balanced
- do not add every RTL submodule
- main paper figure should stay conceptual but faithful
