#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x ./qflow_omnetpp_starter ]]; then
  ./scripts/build_project.sh
fi

mkdir -p results

declare -a topologies=("mesh9.csv" "mesh16.csv" "irregular12.csv")
declare -a algorithms=("distance" "keyaware" "random" "ga_tcheby_proxy")
declare -a rates=(300 800 1500)

for topo in "${topologies[@]}"; do
  stem="${topo%.csv}"
  for alg in "${algorithms[@]}"; do
    for rate in "${rates[@]}"; do
      out="results/${stem}_${alg}_${rate}.csv"
      echo "Running topo=${stem} alg=${alg} rate=${rate}"
      ./qflow_omnetpp_starter -u Cmdenv omnetpp.ini \
        -c Mesh16LoadSweep \
        --**.controller.topologyFile="topologies/${topo}" \
        --**.controller.algorithm="${alg}" \
        --**.controller.requestRate="${rate}" \
        --**.controller.requestLimit=3000 \
        --**.controller.outputCsv="${out}"
    done
  done
done

echo "Batch run complete."
