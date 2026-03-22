#!/usr/bin/env bash
set -euo pipefail

BIN="./qflow_omnetpp_starter"
ALT_BIN="out/clang-release/qflow_omnetpp_starter"

if [[ ! -x "$BIN" && -x "$ALT_BIN" ]]; then
  cp -f "$ALT_BIN" "$BIN"
  chmod +x "$BIN"
fi

if [[ ! -x "$BIN" ]]; then
  echo "Binary not found. Build first with ./scripts/build_project.sh"
  exit 1
fi

mkdir -p results/paper_prelim

REQUEST_LIMIT="${REQUEST_LIMIT:-2000}"
SEEDS="${SEEDS:-3}"
RATES="${RATES:-20 50 100}"
TOPOLOGIES="${TOPOLOGIES:-mesh9 mesh16 irregular12}"
ALGORITHMS="${ALGORITHMS:-distance keyaware random ga_tcheby_proxy}"

echo "Running paper-preliminary matrix"
echo "request_limit=$REQUEST_LIMIT"
echo "seeds=$SEEDS"
echo "rates=$RATES"
echo "topologies=$TOPOLOGIES"
echo "algorithms=$ALGORITHMS"

for topo in $TOPOLOGIES; do
  case "$topo" in
    mesh9) base_cfg="Mesh9SweepKeyAware" ;;
    mesh16) base_cfg="Mesh16LoadSweep" ;;
    irregular12) base_cfg="Irregular12LoadSweep" ;;
    ring6) base_cfg="Ring6KeyAwareDebug" ;;
    *) echo "Unknown topology: $topo"; exit 1 ;;
  esac

  for alg in $ALGORITHMS; do
    for rate in $RATES; do
      for seed in $(seq 1 "$SEEDS"); do
        out_csv="results/paper_prelim/${topo}_${alg}_rate${rate}_seed${seed}.csv"
        echo "Running topo=$topo alg=$alg rate=$rate seed=$seed"

        "$BIN" -u Cmdenv omnetpp.ini \
          -c "$base_cfg" \
          --seed-set="$seed" \
          "--**.controller.topologyFile=\"topologies/${topo}.csv\"" \
          "--**.controller.algorithm=\"${alg}\"" \
          "--**.controller.requestRate=${rate}" \
          "--**.controller.requestLimit=${REQUEST_LIMIT}" \
          "--**.controller.srcNode=-1" \
          "--**.controller.dstNode=-1" \
          "--**.controller.outputCsv=\"${out_csv}\""
      done
    done
  done
done

echo "Done. Results in results/paper_prelim"

