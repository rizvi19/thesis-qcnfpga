#!/usr/bin/env bash
set -euo pipefail

# Run from your QFlow repository root.
# Example:
#   cd /media/shahriar-rizvi/Data/CSE/Thesis/from13March/qflow_step1_phase0
#   bash cloud_fpga/qflow_kernel/scripts/00_git_branch_setup.sh

BRANCH="cloud-fpga-f2-kernel"

echo "[1/5] Checking Git repository..."
git rev-parse --show-toplevel >/dev/null
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "[2/5] Current branch: $(git branch --show-current)"
echo "[3/5] Creating/switching to branch: $BRANCH"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH"
fi

echo "[4/5] Creating cloud-FPGA folders..."
mkdir -p cloud_fpga/qflow_kernel/{rtl,tb,sw,vectors,results,docs,scripts}

echo "[5/5] Status:"
git status --short

echo "Branch ready: $BRANCH"
echo "Next: copy/keep the starter files under cloud_fpga/qflow_kernel, run make, then commit."
