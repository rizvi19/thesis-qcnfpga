# P1 Evidence Notes - Batch 2 (P017-P032)

Verification date: 2026-07-17

Scope: FPGA quantum components, FPGA/hardware genetic algorithms, and
fidelity-aware entanglement-routing entries. The original workbook remains
immutable.

## Main corrections

- P017 is a Kintex UltraScale polar-code reconciliation accelerator; the Artix-7,
  power, resource and generic speedup claims in the workbook were removed.
- P018 reports 4.88 M symbols/s, not multi-Gbps throughput.
- P019-P022 are QKD/QEC component or synchronization works, not routing engines.
- P023 is Murat Peker's 2018 GA IP-core paper; the workbook identity was incorrect.
- P026 RapidLayout is a host-side FPGA-placement tool, not an FPGA-resident NSGA-II engine.
- P028 is by Wallace Tang and Leslie Yip, not the authors listed in the workbook.
- P029-P032 are software/simulation entanglement-routing counterparts; none supplies
  a measured millisecond inference value suitable for raw comparison with QFlow.
- No Batch 2 paper is a Class A or Class B same-function QFlow baseline.

| ID | Verified work | Class | Latency treatment | Primary/official source |
|---|---|---:|---|---|
| P017 | Efficient FPGA implementation of polar codes-based information reconciliation for quantum key distribution | D | Routing-decision latency not applicable | https://www.nature.com/articles/s41598-025-20146-y |
| P018 | FPGA-Based Implementation of Multidimensional Reconciliation Encoding in Quantum Key Distribution | D | Routing-decision latency not applicable | https://www.mdpi.com/1099-4300/25/1/80 |
| P019 | Scalable QKD Postprocessing System With Reconfigurable Hardware Accelerator | D | Routing-decision latency not applicable | https://ieeexplore.ieee.org/document/10288091 |
| P020 | The Hitchhiker's Guide to FPGA-Accelerated Quantum Error Correction | D | No QFlow-equivalent routing latency | https://ieeexplore.ieee.org/document/10313923 |
| P021 | FPT-EMS: An FPGA Implementation Using NB-LDPC Code for Continuous-Variable Quantum Key Distribution | D | Routing-decision latency not applicable | https://dl.acm.org/doi/10.1145/3728179.3728183 |
| P022 | FPGA-Based Synchronization of Frequency-Domain Interferometer for QKD | D | Routing-decision latency not applicable | https://ieeexplore.ieee.org/document/10769019 |
| P023 | A fully customizable hardware implementation for general purpose genetic algorithms | D | Not a routing-decision measurement | https://www.sciencedirect.com/science/article/pii/S1568494617305835 |
| P024 | Customizable FPGA IP Core Implementation of a General-Purpose Genetic Algorithm Engine | D | Not a routing-decision measurement | https://ieeexplore.ieee.org/document/5299091 |
| P025 | Automated Framework for General-Purpose Genetic Algorithms in FPGAs | D | Not a routing-decision measurement | https://link.springer.com/chapter/10.1007/978-3-662-45523-4_58 |
| P026 | RapidLayout: Fast Hard Block Placement of FPGA-Optimized Systolic Arrays Using Evolutionary Algorithms | D | Not applicable to network routing latency | https://dl.acm.org/doi/10.1145/3501803 |
| P027 | A High-Performance, Pipelined, FPGA-Based Genetic Algorithm Machine | D | Not a QKD routing-decision measurement | https://link.springer.com/article/10.1023/A:1010018632078 |
| P028 | Hardware Implementation of Genetic Algorithms Using FPGA | D | Not a QKD routing-decision measurement | https://scholars.cityu.edu.hk/en/publications/hardware-implementation-of-genetic-algorithms-using-fpga/ |
| P029 | RELiQ: Scalable Entanglement Routing via Reinforcement Learning in Quantum Networks | C | Inference runtime not reported as a hardware-comparable metric | https://ieeexplore.ieee.org/document/11275902 |
| P030 | qRL: Reinforcement Learning Routing for Quantum Entanglement Networks | C | Decision/inference runtime not reported | https://ieeexplore.ieee.org/document/10733623 |
| P031 | QoS-Aware Reinforcement Learning Routing for Entanglement Networks | C | Decision/inference runtime not reported | https://www.researchsquare.com/article/rs-8455670/v1 |
| P032 | Entanglement Routing for Quantum Networks: A Deep Reinforcement Learning Approach | C | Decision/inference runtime not reported | https://ieeexplore.ieee.org/document/9839240 |
