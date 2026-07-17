# P1 Evidence Notes - Batch 3 (P033-P050)

Verification date: 2026-07-17

Scope: final matrix rows covering fidelity-aware routing, TSN and programmable
data planes, quantum-network simulation, multi-objective algorithms, and
complexity/approximation theory. The original workbook remains immutable.

## Main corrections

- P033 has named authors and simulated networks up to 100 nodes; the workbook's
  anonymous authorship, 300-node scale and exact metric bundle were removed.
- P034 is by Popa and Popescu, not Mehic et al.
- P035-P037 are TSN surveys/scheduling works and remain Class D context.
- P038 conflated the canonical P4 paper with an in-network-computing title.
- P039 is explicitly replaced by the canonical Sivaraman packet-transactions paper.
- P040 and P041 are excluded because their exact citation identities were not verified.
- P042 is a GCAT paper by Aji, Jain and Krishnan, not an HPSR paper by unspecified authors.
- P043-P045 are simulator, reconciliation-review and QKD-networking context only.
- P048 is explicitly replaced by the verified Zajac-Huber routing survey.
- P050 is Hassin's `Approximation Schemes for the Restricted Shortest Path Problem`,
  not the title and issue shown in the workbook.
- No P033-P050 paper is a Class A or Class B same-function QFlow baseline.

| ID | Disposition | Class | Latency treatment | Primary/official source |
|---|---|---:|---|---|
| P033 | Verified with claim restriction | C | Decision/inference runtime not reported | https://arxiv.org/abs/2509.08654 |
| P034 | Verified with bibliographic correction | C | Solver/runtime is not a QFlow-equivalent routing-decision latency | https://www.nature.com/articles/s41598-024-64994-6 |
| P035 | Verified with bibliographic correction | D | No QFlow-equivalent routing-decision latency | https://doi.org/10.1145/3695248 |
| P036 | Verified with bibliographic correction | D | Measured TSN delays are not QFlow decision latency | https://ieeexplore.ieee.org/document/10568056 |
| P037 | Verified with claim restriction | D | No QFlow-equivalent measured decision latency | https://cea.hal.science/cea-04156793 |
| P038 | Repaired to canonical source | D | No QFlow-equivalent decision latency | https://dl.acm.org/doi/10.1145/2656877.2656890 |
| P039 | Repaired with replacement source | D | Packet-pipeline rate is not optimization-decision latency | https://dl.acm.org/doi/10.1145/2934872.2934900 |
| P040 | Excluded - identity not verified | D | Not reported | https://ieeexplore.ieee.org/search/searchresult.jsp?queryText=%22Piecewise-Linear%20Approximation%20of%20Mathematical%20Functions%20in%20FPGA%22 |
| P041 | Excluded - identity not verified | D | Not reported | https://dl.acm.org/action/doSearch?AllField=%22Hardware-Efficient+Random+Number+Generation+for+FPGAs%22 |
| P042 | Verified with bibliographic correction | D | No routing-decision latency | https://ieeexplore.ieee.org/document/9587708 |
| P043 | Verified with title normalization | D | Simulation runtime is not routing-decision latency | https://www.nature.com/articles/s42005-021-00647-8 |
| P044 | Verified with bibliographic correction | D | Routing-decision latency not applicable | https://link.springer.com/article/10.1140/epjqt/s40507-023-00197-8 |
| P045 | Verified with full authorship | D | No single routing-decision latency | https://dl.acm.org/doi/10.1145/3402192 |
| P046 | Verified | D | No hardware routing-decision latency | https://ieeexplore.ieee.org/document/996017 |
| P047 | Verified | D | No hardware routing-decision latency | https://ieeexplore.ieee.org/document/4358754 |
| P048 | Repaired with replacement source | D | No hardware routing-decision latency | https://www.sciencedirect.com/science/article/pii/S0377221720306160 |
| P049 | Verified | D | Not applicable | https://books.google.com/books?vid=ISBN0716710455 |
| P050 | Verified with bibliographic correction | D | Not applicable | https://pubsonline.informs.org/doi/10.1287/moor.17.1.36 |
