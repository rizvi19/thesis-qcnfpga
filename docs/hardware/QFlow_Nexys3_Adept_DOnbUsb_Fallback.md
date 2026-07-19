# Nexys3 Adept `DOnbUsb` Session Fallback

Use this only when all of the following are true:

1. system USB still reports Digilent `1443:0007`;
2. clean `djtgcfg enum` reports `Device: DOnbUsb` instead of `Nexys3`;
3. no raw Cypress `04b4:8613` device is present; and
4. read-only `djtgcfg init -d DOnbUsb` finds XC6SLX16 ID `44002093`.

In that state the controller and JTAG chain remain usable. Address the exact
name returned by Adept:

```bash
env -u LD_LIBRARY_PATH -u LIBRARY_PATH \
  -u XILINX -u XILINX_DSP -u XILINX_EDK \
  /usr/bin/djtgcfg init -d DOnbUsb

env -u LD_LIBRARY_PATH -u LIBRARY_PATH \
  -u XILINX -u XILINX_DSP -u XILINX_EDK \
  /usr/bin/djtgcfg prog -d DOnbUsb -i 0 -f CHECKSUM_VERIFIED_BITSTREAM
```

Do not accept the generic name alone. Programming is allowed only after the
exact FPGA device and JTAG ID pass. This fallback does not access the FX2
EEPROM or FPGA configuration flash. If JTAG initialization fails, stop before
programming and use the existing controlled-restart decision tree.

Observed validation on 20 July 2026:

- USB: `1443:0007`
- Adept device: `DOnbUsb`
- JTAG device: `XC6SLX16`
- JTAG ID: `44002093`
- exact B3 bitstream programmed successfully
- B3 physical self-test: 6 of 6 pass
