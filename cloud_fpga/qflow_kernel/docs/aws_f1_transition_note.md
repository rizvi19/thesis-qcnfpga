# QFlow AWS Cloud-FPGA Transition Note: F2 to F1

## Decision

The cloud-FPGA execution target is changed from AWS EC2 F2/f2.6xlarge to AWS EC2 F1/f1.2xlarge.

## Reason

The original cloud-FPGA plan targeted f2.6xlarge, which requires 24 F-instance vCPUs. The approved quota is only 8 F-instance vCPUs. Therefore, f2.6xlarge cannot be launched under the current quota.

## New target

- Platform: AWS EC2 F1
- Instance type: f1.2xlarge
- FPGA count: 1
- vCPU count: 8
- Goal: minimum-cost physical cloud-FPGA validation of the QFlow compact kernel

## Current claim boundary

Local QFlow cloud-kernel preparation is complete, including deterministic and randomized regression, reset/control stress, X/Z sanity, static lint/synthesis checks, MMIO-wrapper simulation, and AWS preflight manifest.

No physical AWS FPGA validation claim is allowed until:

1. An official AWS F1 example builds and runs.
2. QFlow CL integration is completed.
3. A QFlow AFI is created.
4. The AGFI is loaded on F1.
5. The host-driver run produces hardware_output.csv.
6. hardware_output.csv matches golden_vectors.csv.

## Safe claim before AWS execution

The compact QFlow cloud-FPGA kernel has been locally prepared and hardened before AWS execution.

## Unsafe claim before AWS execution

The QFlow kernel has been validated on AWS F1 FPGA fabric.
