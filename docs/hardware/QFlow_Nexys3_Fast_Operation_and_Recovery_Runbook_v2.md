# QFlow Nexys3 Fast Operation and Recovery Runbook v2

**Owner:** Shahriar Rizvi  
**Board:** Digilent Nexys3 Rev. B, Spartan-6 XC6SLX16-CSG324  
**Purpose:** Fast repeatable board startup, raw-FX2 recovery, and safe QFlow programming  
**Updated:** 19 July 2026

## 1. Executive rule

Do not repeat the full EEPROM investigation during normal operation. The official
4,760-byte Digilent controller image has already been verified by multiple exact
readbacks. A block of `0xCD` is VendAX transfer failure-fill, not erased EEPROM.

Routine recovery stops as soon as the board returns to operational USB identity
`1443:0007`. Never write the controller EEPROM unless repeatable stored-byte
corruption is independently proven and explicitly reviewed.

## 2. Verified board identity

| Item | Verified value |
|---|---|
| Operational USB | `1443:0007` |
| Raw Cypress recovery USB | `04b4:8613` |
| Adept product | `Nexys3` |
| Adept serial | `210182697240` |
| FPGA | `XC6SLX16` |
| JTAG ID | `44002093` |
| Repository branch | `rl-nexys3-adaptive` |
| Baseline HEAD before final repair commit | `2b6f8fdd7465e0b2135a3db8ae57cdc2ed1d431a` |

### Rev. B direct-I/O mapping verified from board silkscreen

| Input | FPGA pin | Diagnostic LED | LED pin |
|---|---:|---|---:|
| SW0 | T10 | LD5 | N11 |
| CENTER / BTNS | B8 | LD0 | U16 |
| UP / BTNU | A8 | LD1 | V16 |
| LEFT / BTNL | C4 | LD2 | U15 |
| DOWN / BTND | C9 | LD3 | V15 |
| RIGHT / BTNR | D9 | LD4 | M11 |

LD6/R11 is the loaded-design marker and LD7/T11 is the heartbeat in the direct
diagnostic. All six inputs passed when internal FPGA `PULLDOWN` constraints were
removed.

## 3. Normal power-on workflow

1. Ensure the ISE image is mounted read-only at `/mnt/xilinx-ise14.7`.
2. Connect the Nexys3 USB cable and turn the board power ON.
3. Wait 5 seconds.
4. Run clean USB/Adept enumeration with all ISE library variables removed.
5. If `1443:0007`, program the checksum-verified `.bit` file using system
   `/usr/bin/djtgcfg`.
6. Keep the board powered for the entire FPGA test session because FPGA SRAM is
   volatile.

### Clean enumeration

```bash
env -u LD_LIBRARY_PATH -u LIBRARY_PATH \
  -u XILINX -u XILINX_DSP -u XILINX_EDK \
  /usr/bin/lsusb -d 1443:0007

env -u LD_LIBRARY_PATH -u LIBRARY_PATH \
  -u XILINX -u XILINX_DSP -u XILINX_EDK \
  /usr/bin/djtgcfg enum
```

## 4. Fast raw-mode recovery

### A. One deep cold restart

Use this when `04b4:8613` appears:

1. Turn board power OFF.
2. Disconnect USB and every external power source.
3. With all sources disconnected, move the power switch ON for 30 seconds to
   discharge the board, then return it OFF.
4. Reconnect USB.
5. Turn board power ON and wait 10 seconds.
6. Check for `1443:0007`.

If operational identity returns, stop recovery and program the FPGA. Do not load
VendAX and do not read EEPROM.

### B. If raw mode persists

Use the verified VendAX helper only in volatile FX2 RAM:

- VendAX SHA-256:
  `0e4e5da410b51eb7a111cb8d3627fac02eada997916fefc9ea56f4fc9a673dd9`
- Expected load: 3,359 bytes in 41 segments.
- Run A3 RAM self-test at `0x064D`, length 16.
- Send AA twice to select 100 kHz.
- Make one 16-byte A9 prefix probe.
- Expected prefix:
  `c2 43 14 0d 00 00 00 00 00 04 00 00 02 00 6b 32`.

If the prefix is exact, the EEPROM path is readable. Stop diagnostics and perform
another deep cold restart. Full two-pass EEPROM reads are incident diagnostics,
not a normal startup requirement.

### C. Stop condition

If the stored image is known exact but raw mode repeatedly returns, classify the
problem as intermittent FX2 boot/power-sequencing reliability. Do not keep
rewriting or repeatedly reading EEPROM. Use the next operational window, keep the
board powered, and finish all FPGA tests in that session. For a long-term hardware
solution, use an external JTAG cable or another Nexys3 board.

## 5. Evidence-based decision table

| Observation | Meaning | Action |
|---|---|---|
| `1443:0007`, Adept finds Nexys3 | Controller operational | Program verified bitstream |
| `04b4:8613` after normal start | FX2 raw boot | One deep cold restart |
| A3 mismatch | VendAX RAM helper invalid | Stop; do not access EEPROM |
| A3 exact, A9 prefix exact | Helper and EEPROM read path good | Restart; no EEPROM write |
| A9 returns all `0xCD` | Transfer failure-fill | Wait, reprobe once; do not infer erasure |
| One full pass exact, another differs | Intermittent read transport | Accept exact stored-image evidence; stop repeated reads |
| Repeated stored bytes differ at stable offsets | Possible corruption | Preserve evidence and require review before any write |

## 6. Current P5 B1 repair state

The original B1 UCF incorrectly enabled internal `PULLDOWN` on the externally
driven center button. The no-pulldown C3C diagnostic proved:

- SW0 controls LD5.
- CENTER, UP, LEFT, DOWN, and RIGHT control LD0 through LD4.
- LD6 is steady ON and LD7 blinks.
- All input LEDs are OFF in low/released state.

The repaired real B1 build removed only the active `PULLDOWN` constraint from
`btn_reset` at B8. It passed NGDBuild, Map, PAR, Trace, and BitGen with zero timing
errors.

| Repaired B1 artifact | Verified value |
|---|---|
| Bitstream bytes | 464,294 |
| Bitstream SHA-256 | See exact hash below |
| Minimum period | 6.253 ns |
| Maximum frequency | 159.923 MHz |
| Timing score | 0 |

```text
7eefc2e1cae4089cc47e58c2cca11a8b91efa359630d2e3b70fefe1074bc5347
```

The repaired bitstream must still receive one final physical reset validation:
display counts, CENTER holds display at `0000`, LD1 indicates reset, and counting
restarts from `0001` after release.

## 7. GitHub preservation plan

Commit and push these reusable, non-proprietary assets after the physical gate:

- This runbook in Markdown and PDF.
- Board identity and pin map.
- Normal enumeration and programming scripts.
- Raw-mode detection and safe recovery wrapper.
- A3/AA/16-byte probe script.
- Repaired B1 UCF and deterministic bitstream.
- Sanitized evidence manifests and SHA-256 values.
- A note explaining that `0xCD` is transfer failure-fill.

Do not commit the Xilinx license, the 50 GiB ISE image, USB serial logs containing
unnecessary host details, or proprietary Digilent/Cypress firmware bytes to a
public repository. Store paths, hashes, retrieval instructions, and locally backed
up recovery binaries instead.

## 8. Current incident conclusion

On 19 July 2026, a fresh VendAX session produced an exact A3 result and an exact
first 4,760-byte EEPROM pass with SHA-256
`ad744e1908ab029b9c08400dbab49f00998c0da0300fa16f188782566893c6b8`.
A later pass differed, confirming intermittent transport rather than loss of the
verified official image. No EEPROM write was performed.

The operational priority is therefore to obtain one clean controller boot, keep
the board powered, program the already-built repaired B1 bitstream, finish its
physical reset validation, preserve the reusable assets, and close P5 Step 3.

## 9. Operational USB with the generic `DOnbUsb` Adept name

If USB remains `1443:0007` but clean Adept enumeration reports `DOnbUsb`, do
not enter raw-FX2 recovery. Follow
`docs/hardware/QFlow_Nexys3_Adept_DOnbUsb_Fallback.md`: initialize JTAG using
the exact enumerated name, require XC6SLX16 ID `44002093`, and only then program
the checksum-verified volatile bitstream. This path performs no EEPROM or
configuration-flash access.

