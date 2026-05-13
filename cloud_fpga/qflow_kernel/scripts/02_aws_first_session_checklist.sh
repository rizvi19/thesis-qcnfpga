#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
AWS first paid session checklist
================================
Do these BEFORE launching F2:
[ ] MFA/passkey enabled on AWS root account
[ ] No root access keys created
[ ] Budgets set at USD 25, USD 50, USD 100
[ ] Service quota: Running On-Demand F instances >= 24 vCPUs
[ ] Region selected: us-east-1 unless availability/quota forces another F2 region
[ ] Security group: SSH TCP/22 from My IP only
[ ] Key pair: qflow-f2-key.pem saved privately
[ ] Local command `make all` passed in cloud_fpga/qflow_kernel

F2 launch:
AMI: FPGA Developer AMI for F2
Instance type: f2.6xlarge
Name: qflow-f2-dev
Storage: 100-200 GB gp3

After SSH:
mkdir -p ~/qflow_aws_results/session_logs
cat > ~/qflow_aws_results/session_logs/session_00_instance_info.txt <<EOL
Instance type: f2.6xlarge
Region: us-east-1
Purpose: QFlow cloud-FPGA kernel validation
Start time: $(date)
EOL

df -h | tee -a ~/qflow_aws_results/session_logs/session_00_instance_info.txt
lscpu | head -30 | tee -a ~/qflow_aws_results/session_logs/session_00_instance_info.txt

AWS HDK smoke test:
cd ~
git clone https://github.com/aws/aws-fpga.git
cd aws-fpga
source hdk_setup.sh
cd hdk/cl/examples/cl_sde
export CL_DIR=$(pwd)
cd build/scripts
./aws_build_dcp_from_cl.py -c cl_sde | tee ~/qflow_aws_results/session_logs/aws_example_build.log

STOP the instance from the EC2 console when done.
EOF
