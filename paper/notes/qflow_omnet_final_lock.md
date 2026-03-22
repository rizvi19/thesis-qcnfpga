# QFlow OMNeT++ Final Lock Package

## Final verdict on the OMNeT++ step

The OMNeT++ stage is complete enough for the thesis-core and for the paper draft.

It is not the fully maximal version of the original complete plan, because that would also include:
- a DRL/DQN baseline,
- the full five-topology suite,
- and exact in-simulator software-GA alignment instead of the current `ga_tcheby_proxy`.

However, it already satisfies the stronger and more realistic completion rule from the integrated master plan:
- dynamic-load network evidence exists,
- multiple baselines are compared,
- multiple nontrivial topologies are used,
- repeated-run statistics are available,
- and there are figures and tables answering the network-behavior research question.

## What OMNeT++ is proving

OMNeT++ is not the hardware timing proof.
It is the dynamic-load network comparison layer.

It answers:
- how blocking grows under load,
- how path fidelity is distributed,
- how routes differ in hop count and distance,
- and how policies behave across topology sizes.

## Locked main-paper OMNeT++ artifacts

### Main paper figures
1. Blocking vs load — Mesh-16
2. Blocking vs load — Irregular12
3. Fidelity CDF — Mesh-16
4. Fidelity CDF — Irregular12
5. Per-link usage heatmap — Mesh-16, Keyaware vs GA proxy
6. Scalability plot

### Main paper tables
1. OMNeT representative-rate comparison table
   - Source: `omnet_paper_ready_table.csv`
2. OMNeT run-summary table
   - Source: `omnet_final_summary.csv`
   - Use appendix or supplementary, not the main paper.

## Appendix-only OMNeT++ artifacts
1. Blocking vs load — Mesh-9
2. Fidelity CDF — Mesh-9
3. Additional per-link usage heatmaps for Irregular12 and Mesh-9
4. Full run-level summary (`omnet_final_run_level_summary.csv`)

## Keep but do not overclaim
- The dynamic-load GA comparator is currently `ga_tcheby_proxy`.
- In the final paper text, describe it as a GA-style dynamic-load proxy, not as the exact final software PMO-GA selector.

## Paper-safe interpretation

The current OMNeT++ package supports the following claims:
- Random routing is clearly weaker in path efficiency.
- Key-aware and GA-style routing are much more structured than random routing.
- Blocking grows with request load across all tested topologies.
- Key-aware and GA-style routing have broadly similar blocking behavior, with small topology-dependent quality differences.
- The OMNeT++ evidence complements the hardware package rather than replacing it.

It does not support the following claims:
- exact equivalence between OMNeT++ GA proxy and the final software PMO-GA selector,
- universal dominance of the GA proxy over key-aware routing,
- full completion of every stretch item in the largest original plan.

## Final decision

### Treat OMNeT++ as DONE for:
- thesis defense package,
- final thesis chapter,
- first serious paper draft.

### Treat as OPTIONAL future strengthening only:
- DRL/DQN baseline,
- larger topology ladder,
- exact GA-in-simulator replacement,
- broader journal-extension package.
