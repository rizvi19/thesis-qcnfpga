# P4 Step 7 Status

Step 7 performs integrated, cycle-exact verification of the reviewed P4
controller checkpoint. It does not change the encoder, policy ROM, profile ROM,
controller RTL, frozen policy, frozen profiles, or any training result.

The primary trace ladder contains two authoritative Python H4 replays. The
first is the eight-decision manual Ring-6 trace frozen in P2. The second is the
first locked 512-decision test-partition trace from the frozen MDP contract and
trace manifest. Each independent trace resets dwell history. Every decision
records its state, policy proposal, dwell-filtered action, exact profile
payload, no-path result, reward, next state, and final status.

Those 520 frozen-trace decisions are converted into the four-feature UNORM16
controller interface using exact representative codes for their decoded bins.
The RTL must reproduce every state, proposal, selected action, profile payload,
dwell count, switch flag, no-path flag, handshake, and three-cycle completion.
A ten-decision directed trace then guarantees all four selected profiles,
dwell holds and switches, plus an explicit no-path completion. Reset dominance,
the one-cycle invalid response, starts while busy, and back-to-back requests are
also covered.

The exhaustive all-256-state and all-threshold-edge gate remains Step 8. ISE
synthesis, timing/resource claims, board programming, EEPROM access, online
learning, Q-table argmax deployment, and `q_update.v` remain outside Step 7.
