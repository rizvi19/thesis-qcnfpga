# QFlow AWS F2 Prelaunch Checklist

This checklist must be completed before launching a paid EC2 F2 instance.

## Repository readiness

- [ ] Gate 1 through Gate 7 passed locally.
- [ ] `git status` is clean.
- [ ] Branch is pushed to GitHub.
- [ ] `results/evidence_snapshot_08_aws_preflight_ready/` exists.
- [ ] `docs/aws_mmio_register_map.md` is committed.
- [ ] `results/aws_preflight/aws_preflight_manifest.md` is committed or archived.

## AWS account safety

- [ ] Root MFA/passkey enabled.
- [ ] No root access keys created.
- [ ] Billing budgets/alerts created before launching EC2.
- [ ] EC2 F-instance quota checked or requested.
- [ ] Region selected intentionally.
- [ ] SSH key created and stored safely.
- [ ] Security group permits SSH only from your current IP.

## Cost-control rule

Stop or terminate the instance immediately after each session. Closing SSH does not stop billing.

## First AWS session rule

Run the official AWS FPGA example first. Do not integrate QFlow until the official example proves that the AMI, HDK, SDK, S3/AFI flow, and FPGA load path work.
