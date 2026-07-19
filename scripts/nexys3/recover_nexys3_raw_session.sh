#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROBE_SCRIPT="$SCRIPT_DIR/vendax_probe.py"
BRINGUP_ROOT="${QFLOW_NEXYS3_BRINGUP_ROOT:-$HOME/Work/QFlow_Nexys3_Bringup}"
VENDAX="$BRINGUP_ROOT/recovery/extracted/VendAX_official.hex"
EXPECTED_VENDAX_SHA256="0e4e5da410b51eb7a111cb8d3627fac02eada997916fefc9ea56f4fc9a673dd9"
FXLOAD="/usr/sbin/fxload"
EXPECTED_FXLOAD_SHA256="043091fc84631dbb49ec668b211379929b9b69cd39fcae04fa855874c8e8498e"
EVIDENCE_DIR="${QFLOW_EVIDENCE_DIR:-$HOME/Downloads/QFlow_Nexys3_Raw_Recovery_$(date -u +%Y%m%dT%H%M%SZ)}"
CLEAN_ENV=(/usr/bin/env -u LD_LIBRARY_PATH -u LIBRARY_PATH -u XILINX -u XILINX_DSP -u XILINX_EDK)

test "$(id -u)" -ne 0
test -f "$VENDAX"
test -x "$FXLOAD"
test -f "$PROBE_SCRIPT"
test "$(sha256sum "$VENDAX" | awk '{print $1}')" = "$EXPECTED_VENDAX_SHA256"
test "$(sha256sum "$FXLOAD" | awk '{print $1}')" = "$EXPECTED_FXLOAD_SHA256"
test ! -e "$EVIDENCE_DIR"

OPERATIONAL="$("${CLEAN_ENV[@]}" /usr/bin/lsusb -d 1443:0007 2>&1 || true)"
if test -n "$OPERATIONAL"; then
    printf '%s\nNEXYS3_STATE=OPERATIONAL_NO_RECOVERY_NEEDED\n' "$OPERATIONAL"
    exit 0
fi

RAW="$("${CLEAN_ENV[@]}" /usr/bin/lsusb -d 04b4:8613 2>&1 || true)"
printf '%s\n' "$RAW"
test "$(printf '%s\n' "$RAW" | grep -Fc '04b4:8613')" -eq 1
BUS="$(printf '%s\n' "$RAW" | awk 'NR==1 {print $2}')"
DEVICE="$(printf '%s\n' "$RAW" | awk 'NR==1 {gsub(":", "", $4); print $4}')"
case "$BUS:$DEVICE" in
    [0-9][0-9][0-9]:[0-9][0-9][0-9]) ;;
    *) printf 'Unable to parse raw USB node.\n' >&2; exit 5 ;;
esac
USB_NODE="/dev/bus/usb/$BUS/$DEVICE"
test -c "$USB_NODE"

mkdir -p "$EVIDENCE_DIR"
VALIDATION="$EVIDENCE_DIR/probe_validation.json"
FXLOAD_LOG="$EVIDENCE_DIR/vendax_fxload.log"
PROBE_LOG="$EVIDENCE_DIR/vendax_probe.log"
touch "$VALIDATION" "$FXLOAD_LOG" "$PROBE_LOG"

printf 'This operation loads verified VendAX into volatile FX2 RAM only.\n'
printf 'EEPROM writes and FPGA programming are not performed.\n'
sudo -v

sudo -n "${CLEAN_ENV[@]}" "$FXLOAD" -I "$VENDAX" -D "$USB_NODE" -t fx2 -v \
    2>&1 | tee "$FXLOAD_LOG"
grep -Fq 'WROTE: 3359 bytes, 41 segments' "$FXLOAD_LOG"
grep -Fq 'reset CPU' "$FXLOAD_LOG"

sleep 5
sudo -n "${CLEAN_ENV[@]}" /usr/bin/python3 "$PROBE_SCRIPT" \
    --validation "$VALIDATION" 2>&1 | tee "$PROBE_LOG"
grep -Fq 'P5_B1_RECOVERY_R6C_A9_PROBE=16_OF_16_EXACT_PASS' "$PROBE_LOG"
grep -Fq '"eeprom_writes": 0' "$VALIDATION"
grep -Fq '"pass": true' "$VALIDATION"

(
    cd "$EVIDENCE_DIR"
    sha256sum vendax_fxload.log vendax_probe.log probe_validation.json > SHA256SUMS
)

printf 'RAW_SESSION_RECOVERY=VOLATILE_HELPER_AND_PREFIX_PROBE_PASS\n'
printf 'EEPROM_WRITES=0\nFPGA_PROGRAMMING=0\n'
printf 'NEXT_ACTION=Perform deep cold restart from the runbook, then run check_and_program_p5_b1.sh --program\n'
