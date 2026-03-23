# Block Descriptions for FIG01

## Request Input
Represents the incoming routing request and any request-specific descriptors needed for evaluation.

## Network State Input
Represents the current system/network state used by the routing logic, including quality-related or availability-related information.

## FDPE
Primary internal processing block associated with fidelity/state-aware evaluation in the QFlow pipeline.

## SKAG / Memory Block
State support / key-path support / memory-facing block used by the QFlow routing engine. Final wording must match the thesis/paper terminology exactly.

## Selection Logic
Core decision-making logic that selects the final route or routing action from the internal evaluation path.

## Route Decision Output
Top-level route decision delivered by the hardware accelerator.
