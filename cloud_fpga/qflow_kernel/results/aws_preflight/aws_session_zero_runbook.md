# AWS Session Zero Runbook for QFlow F2

This is the first paid session plan. The goal is not to run QFlow yet. The goal is to prove AWS FPGA infrastructure.

## Session objective

1. Launch one F2 development instance.
2. Verify SSH access.
3. Clone/setup AWS FPGA HDK/SDK.
4. Run one official AWS FPGA example.
5. Record logs.
6. Stop the instance.

## Evidence to save

- instance type
- region
- AMI name/ID
- AWS FPGA repo commit
- HDK setup log
- official example build log
- AFI/AGFI ID if created
- host run output if available
- start/stop times
- estimated cost

## Do not do in Session Zero

- Do not debug QFlow RTL.
- Do not launch larger F2 instance sizes.
- Do not leave the instance running after logout.
- Do not claim QFlow cloud validation from AWS example output.
