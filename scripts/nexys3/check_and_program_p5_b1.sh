#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
BITSTREAM="$REPO/fpga/ise_nexys3/bitstreams/p5_b1_repaired.bit"
EXPECTED_BITSTREAM_SHA256="7eefc2e1cae4089cc47e58c2cca11a8b91efa359630d2e3b70fefe1074bc5347"
MODE="${1:---status}"
CLEAN_ENV=(/usr/bin/env -u LD_LIBRARY_PATH -u LIBRARY_PATH -u XILINX -u XILINX_DSP -u XILINX_EDK)

case "$MODE" in
    --status|--program) ;;
    *) printf 'Usage: %s [--status|--program]\n' "$0" >&2; exit 2 ;;
esac

test -f "$BITSTREAM"
test "$(stat -c '%s' "$BITSTREAM")" -eq 464294
test "$(sha256sum "$BITSTREAM" | awk '{print $1}')" = "$EXPECTED_BITSTREAM_SHA256"

OPERATIONAL="$("${CLEAN_ENV[@]}" /usr/bin/lsusb -d 1443:0007 2>&1 || true)"
RAW="$("${CLEAN_ENV[@]}" /usr/bin/lsusb -d 04b4:8613 2>&1 || true)"
printf 'OPERATIONAL_USB=%s\n' "${OPERATIONAL:-NONE}"
printf 'RAW_CYPRESS_USB=%s\n' "${RAW:-NONE}"

if test -n "$RAW"; then
    printf 'NEXYS3_STATE=RAW_CYPRESS\n'
    printf 'ACTION=Follow docs/hardware/QFlow_Nexys3_Fast_Operation_and_Recovery_Runbook_v2.pdf\n'
    exit 3
fi
test -n "$OPERATIONAL" || { printf 'NEXYS3_STATE=NOT_FOUND\n'; exit 4; }

cd "${QFLOW_EVIDENCE_DIR:-$HOME/Downloads}"
"${CLEAN_ENV[@]}" /usr/bin/djtgcfg enum
"${CLEAN_ENV[@]}" /usr/bin/djtgcfg init -d Nexys3
printf 'NEXYS3_STATE=OPERATIONAL_EXACT_PASS\n'

if test "$MODE" = "--status"; then
    printf 'PROGRAMMING=0_STATUS_ONLY\n'
    exit 0
fi

"${CLEAN_ENV[@]}" /usr/bin/djtgcfg prog -d Nexys3 -i 0 -f "$BITSTREAM"
printf 'BITSTREAM_SHA256=%s\n' "$EXPECTED_BITSTREAM_SHA256"
printf 'P5_B1_VOLATILE_PROGRAMMING=PASS\n'
printf 'EEPROM_ACCESS=0\n'
printf 'BOARD_POWER_MUST_REMAIN_ON=YES\n'
