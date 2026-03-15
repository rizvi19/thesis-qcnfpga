`timescale 1ns/1ps

// Optional lint-clean variant of skag_mem reset loops.
// Replace only if you want to eliminate the remaining BLKSEQ warnings before synthesis.
// Apply manually to your current rtl/skag_mem.v reset loop:
//     edge_mem[i]   <= 64'd0;
//     weight_mem[i] <= INF_WEIGHT;
