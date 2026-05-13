#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
QFlow AWS CL build command block
================================
Use only after the official AWS example succeeds.

cd ~/aws-fpga
source hdk_setup.sh
cd hdk/cl/examples

# Preferred if available in the active AWS F2 HDK:
./create_new_cl.py --new_cl_name cl_qflow_kernel
cd cl_qflow_kernel
export CL_DIR=$(pwd)

# Copy QFlow RTL from your Git repo into the CL RTL area.
# You must adapt the AWS CL shell/MMIO wrapper to expose the register map in docs/kernel_spec.md.
# Start by placing these files in the custom logic source tree:
#   fdpe_kernel.v
#   skag_weight_kernel.v
#   path_selector_kernel.v
#   qflow_cloud_kernel.v

cd build/scripts
./aws_build_dcp_from_cl.py -c cl_qflow_kernel | tee ~/qflow_aws_results/qflow_kernel_build.log

find $CL_DIR/build -type f \( -name "*.rpt" -o -name "*.log" -o -name "*.dcp" -o -name "*.tar" -o -name "*.tar.gz" \) \
  | tee ~/qflow_aws_results/qflow_kernel_build_artifacts.txt

# AFI registration skeleton
export AWS_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export BUCKET=qflow-fpga-${ACCOUNT_ID}-$(date +%Y%m%d)
aws s3 mb s3://${BUCKET} --region ${AWS_REGION}
aws s3api put-object --bucket ${BUCKET} --key dcp/
aws s3api put-object --bucket ${BUCKET} --key logs/
aws s3api put-object --bucket ${BUCKET} --key results/

export QFLOW_DCP_TARBALL=$(find $CL_DIR -type f \( -name "*.tar" -o -name "*.tar.gz" \) | head -1)
aws s3 cp "$QFLOW_DCP_TARBALL" s3://${BUCKET}/dcp/qflow_kernel_dcp.tar

aws ec2 create-fpga-image \
  --region ${AWS_REGION} \
  --name qflow-kernel-$(date +%Y%m%d-%H%M) \
  --description "QFlow FDPE SKAG path-selector cloud FPGA kernel" \
  --input-storage-location Bucket=${BUCKET},Key=dcp/qflow_kernel_dcp.tar \
  --logs-storage-location Bucket=${BUCKET},Key=logs/qflow_kernel/ \
  | tee ~/qflow_aws_results/qflow_create_afi_output.json

aws ec2 describe-fpga-images \
  --region ${AWS_REGION} \
  --owners self \
  --query 'FpgaImages[*].[Name,FpgaImageId,FpgaImageGlobalId,State.Code]' \
  --output table \
  | tee ~/qflow_aws_results/qflow_afi_status.txt

# After AFI state is available:
export QFLOW_AGFI=agfi-xxxxxxxxxxxxxxxxx
sudo fpga-describe-local-image-slots -H | tee ~/qflow_aws_results/fpga_slots_before_load.txt
sudo fpga-clear-local-image -S 0 -H | tee ~/qflow_aws_results/qflow_clear_before_load.txt
sudo fpga-load-local-image -S 0 -I ${QFLOW_AGFI} -H | tee ~/qflow_aws_results/qflow_load_afi.txt
sudo fpga-describe-local-image -S 0 -R -H | tee ~/qflow_aws_results/qflow_loaded_status.txt
EOF
