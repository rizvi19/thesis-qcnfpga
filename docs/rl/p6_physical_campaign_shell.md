# P6 Common Physical Campaign Shell

The common Nexys3 campaign shell is frozen for H0 through H4.

For each independently built policy wrapper, the shell:

1. replays the same ordered 84-case manifest;
2. preserves reset boundaries before replay indices 0, 5, 10 and 20;
3. executes the real measurement kernel;
4. normalizes non-OK result sentinels;
5. compares every result against the committed fixed-point golden ROM;
6. emits the actual result through the 44-byte QF6R UART record;
7. displays the policy mode and completed-record count;
8. asserts the pass LED only after 84/84 internal comparisons succeed;
9. asserts the error LED if any comparison fails.

The five-mode RTL regression completed 420/420 internal comparisons with
zero errors.

- Replay ROM SHA-256: `af55f5d04b8721410fad3715448c4d5c0148a44320460339cb7f20d9774dfb26`
- Expected-result ROM SHA-256: `7e53fc889e1248b19512a11d84e28d7359a5180329589938ac7e70751ebac1b0`
- QF6R formatter SHA-256: `270802c61cd94a47d4307f9f4ecf6c58c2da160c248ecd48ba229a138f1272d9`
- Campaign core SHA-256: `37e9bfb9d5d5ec319faf0efb53c95733e794dab6e19d705aec0a5f5ddd8ba7c4`
- Nexys3 wrappers SHA-256: `18782abb474999f9f65b8b920bb1cb7d9fe95bf2c989033ac97dd2f5db05484a`

This checkpoint is RTL simulation evidence. It does not claim an ISE build,
FPGA programming or physical UART capture. Those are separate later gates.
