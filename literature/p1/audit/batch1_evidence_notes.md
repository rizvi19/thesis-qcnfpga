# P1 Evidence Notes - Batch 1 (P001-P016)

Verification date: 2026-07-17

Scope: QKD-routing and SDN/QKD-deployment entries. Technical claims were checked
against publisher pages, official manuscripts or official preprints. The original
workbook remains immutable.

## Main corrections

- Several author lists, titles and publication years were corrected in verified fields.
- No cited software-routing paper in this batch is assigned a millisecond inference
  latency unless the source explicitly reports such a measurement; none did.
- Seconds-scale key-distribution time in P007 is a simulated network metric, not
  routing-controller execution time.
- P001's 18.7% result is a simulation result for mean key-store filling, not a
  hardware-latency result.
- P002 supports the 26-strategy survey scope and abstract percentages, but does not
  prove that every strategy is software or millisecond-latency.
- P013 and P015 are valuable physical-deployment context, not same-function FPGA
  routing baselines.

| ID | Verified work | Class | Latency treatment | Primary/official source |
|---|---|---:|---|---|
| P001 | Adaptive Routing for Meshed QKD Networks of Flexible Size Using Deep Reinforcement Learning | C | Not reported for inference/decision runtime | https://www.mdpi.com/2304-6732/13/2/198 |
| P002 | Overview of Routing Approaches in Quantum Key Distribution Networks | C | Not reported | https://arxiv.org/abs/2511.15465 |
| P003 | Deep reinforcement learning-based routing and resource assignment in quantum key distribution-secured optical networks | C | Not reported for inference/decision runtime | https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/qtc2.12063 |
| P004 | A quantum key distribution routing scheme for hybrid-trusted QKD network system | C | Not reported | https://link.springer.com/article/10.1007/s11128-022-03825-x |
| P005 | A Dynamic-Routing Algorithm Based on a Virtual Quantum Key Distribution Network | C | Not reported | https://www.mdpi.com/2076-3417/13/15/8690 |
| P006 | Routing Algorithm Within the Multiple Non-Overlapping Paths' Approach for Quantum Key Distribution Networks | C | Not reported | https://www.mdpi.com/1099-4300/26/12/1102 |
| P007 | Q-Learning for Resource-Aware and Adaptive Routing in Trusted-Relay QKD Network | C | Inference runtime not reported; seconds are simulated key-delivery time | https://www.mdpi.com/2304-6732/12/10/969 |
| P008 | Fast and Secure Routing Algorithms for Quantum Key Distribution Networks | C | Hardware/decision latency not reported | https://ieeexplore.ieee.org/document/10051661 |
| P009 | Dynamic Security-Aware Resource Allocation in Quantum Key Distribution-Enabled Optical Networks | C | Not reported | https://www.mdpi.com/2304-6732/12/7/645 |
| P010 | Routing With Minimum Activated Trusted Nodes in Quantum Key Distribution Networks for Secure Communications | C | Not reported | https://ieeexplore.ieee.org/document/10380212 |
| P011 | DRL-based progressive recovery for quantum-key-distribution networks | C | Not reported | https://opg.optica.org/jocn/abstract.cfm?uri=jocn-16-9-E36 |
| P012 | Routing, Channel, Key-Rate, and Time-Slot Assignment for QKD in Optical Networks | C | Not reported | https://ieeexplore.ieee.org/document/10168191 |
| P013 | MadQCI: a heterogeneous and scalable SDN-QKD network deployed in production facilities | D | No routing-controller latency verified in this pass | https://www.nature.com/articles/s41534-024-00873-2 |
| P014 | The Evolution of Quantum Key Distribution Networks: On the Road to the Qinternet | C | Not reported as a universal SDN-routing measurement | https://ieeexplore.ieee.org/document/9684555 |
| P015 | Implementation of carrier-grade quantum communication networks over 10000 km | C | No routing-decision latency verified | https://www.nature.com/articles/s41534-025-01089-8 |
| P016 | A Quantum Key Distribution Routing Scheme for a Zero-Trust QKD Network System: A Moving Target Defense Approach | C | Not reported for routing-decision runtime | https://www.mdpi.com/2504-2289/9/4/76 |
