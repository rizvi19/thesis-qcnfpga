#!/usr/bin/env python3
"""Validate VendAX RAM, select 100 kHz, and make one read-only A9 probe."""

import argparse
import json
import os
import sys
import time

import usb.core


VID = 0x04B4
PID = 0x8613
VENDOR_IN = 0xC0
VENDOR_OUT = 0x40
A3_RAM_READ = 0xA3
AA_SET_100KHZ = 0xAA
A9_EEPROM_READ = 0xA9
A3_ADDRESS = 0x064D
INDEX = 0x0000
LENGTH = 16
TIMEOUT_MS = 2000
EXPECTED_A3 = bytes.fromhex(
    "e4 f5 2c f5 2b f5 2a f5 29 c2 03 c2 00 c2 02 c2"
)
EXPECTED_EEPROM_PREFIX = bytes.fromhex(
    "c2 43 14 0d 00 00 00 00 00 04 00 00 02 00 6b 32"
)


def write_existing_regular_file(path, data):
    flags = os.O_WRONLY | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        remaining = memoryview(data)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise RuntimeError(f"failed to write local evidence: {path}")
            remaining = remaining[written:]
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", required=True)
    args = parser.parse_args()

    devices = list(usb.core.find(find_all=True, idVendor=VID, idProduct=PID))
    print(f"RAW_CYPRESS_DEVICE_COUNT={len(devices)}", flush=True)
    if len(devices) != 1:
        raise RuntimeError("expected exactly one raw Cypress device")
    device = devices[0]

    print("===== SAME-SESSION A3 RAM SELF-TEST =====", flush=True)
    a3_data = bytes(
        device.ctrl_transfer(
            VENDOR_IN,
            A3_RAM_READ,
            A3_ADDRESS,
            INDEX,
            LENGTH,
            timeout=TIMEOUT_MS,
        )
    )
    print(f"A3_ACTUAL={a3_data.hex(' ')}", flush=True)
    a3_pass = a3_data == EXPECTED_A3
    print(f"A3_EXACT={str(a3_pass).upper()}", flush=True)
    if not a3_pass:
        raise RuntimeError("VendAX A3 RAM self-test mismatch")

    print("===== SAME-SESSION 100 KHZ SELECTION =====", flush=True)
    aa_first = device.ctrl_transfer(
        VENDOR_OUT, AA_SET_100KHZ, 0, INDEX, b"", timeout=TIMEOUT_MS
    )
    aa_second = device.ctrl_transfer(
        VENDOR_OUT, AA_SET_100KHZ, 0, INDEX, b"", timeout=TIMEOUT_MS
    )
    print(f"FIRST_AA_RETURN={aa_first}", flush=True)
    print(f"SECOND_AA_RETURN={aa_second}", flush=True)
    aa_pass = aa_first == 0 and aa_second == 0
    print(f"AA_COMMANDS_EXACT={str(aa_pass).upper()}", flush=True)
    if not aa_pass:
        raise RuntimeError("100 kHz helper-speed selection failed")

    time.sleep(0.050)

    print("===== ONE READ-ONLY 16-BYTE A9 PROBE =====", flush=True)
    probe = bytes(
        device.ctrl_transfer(
            VENDOR_IN,
            A9_EEPROM_READ,
            0,
            INDEX,
            LENGTH,
            timeout=TIMEOUT_MS,
        )
    )
    print(f"A9_EXPECTED={EXPECTED_EEPROM_PREFIX.hex(' ')}", flush=True)
    print(f"A9_ACTUAL={probe.hex(' ')}", flush=True)
    print(f"A9_RETURNED_LENGTH={len(probe)}", flush=True)
    probe_pass = probe == EXPECTED_EEPROM_PREFIX
    all_cd = probe == bytes([0xCD]) * LENGTH
    print(f"A9_EXACT={str(probe_pass).upper()}", flush=True)
    print(f"A9_ALL_CD_FAILURE_FILL={str(all_cd).upper()}", flush=True)

    validation = {
        "schema": "qflow-p5-b1-recovery-r6c-v1",
        "operation": "same-session A3, AA, and one read-only A9 probe",
        "a3_vendor_in_transfers": 1,
        "aa_vendor_out_speed_commands": 2,
        "a9_vendor_in_read_transfers": 1,
        "a9_read_bytes": LENGTH,
        "eeprom_writes": 0,
        "a3_exact": a3_pass,
        "aa_returns": [aa_first, aa_second],
        "a9_actual_hex": probe.hex(),
        "a9_exact": probe_pass,
        "a9_all_cd_failure_fill": all_cd,
        "pass": probe_pass,
    }
    write_existing_regular_file(
        args.validation,
        (json.dumps(validation, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    if not probe_pass:
        print("P5_B1_RECOVERY_R6C_SAME_SESSION_PROBE=FAIL", flush=True)
        return 1

    print("P5_B1_RECOVERY_R6C_A3_RAM_SELF_TEST=16_OF_16_EXACT_PASS", flush=True)
    print("P5_B1_RECOVERY_R6C_AA_COMMANDS=2_OF_2_ZERO_LENGTH_PASS", flush=True)
    print("P5_B1_RECOVERY_R6C_A9_PROBE=16_OF_16_EXACT_PASS", flush=True)
    print("P5_B1_RECOVERY_R6C_EEPROM_WRITES=0_PASS", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"P5_B1_RECOVERY_R6C_SAME_SESSION_PROBE=FAIL: {exc}", flush=True)
        sys.exit(1)
