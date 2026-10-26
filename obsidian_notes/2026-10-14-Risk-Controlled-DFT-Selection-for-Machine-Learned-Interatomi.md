---
title: "Risk-Controlled DFT Selection for Machine-Learned Interatomic Potentials"
date: 2026-10-14
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.19630v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Risk-Controlled DFT Selection for Machine-Learned Interatomic Potentials

**Authors:** [[Kun Ryu]], [[Yeo Jin Jung]], [[Shyue Ping Ong]]
**Link:** https://arxiv.org/abs/2610.19630v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a conformal risk control framework with a lightweight disagreement-score predictor to selectively route configurations to DFT, cutting DFT calls 7–14% versus committee baselines under the same error guarantee.

## Abstract
> Automated materials discovery requires evaluating large pools of candidate configurations, with density functional theory (DFT) as a major throughput bottleneck. Pretrained machine-learned interatomic potentials (MLIPs) approximate DFT cheaply, but their errors vary by orders of magnitude across configurations, making it difficult to decide when to trust the MLIP predictions and when to fall back to DFT. We frame this decision as a risk-controlled selection problem and solve it within a conformal risk control (CRC) framework. Each configuration is mapped from atomic numbers and Cartesian coordinates to a fixed geometric descriptor, which a lightweight predictor uses to estimate an MLIP-DFT disagreement score in energy, average force, and maximum force. CRC then calibrates this score into a selection threshold for DFT labeling such that the MLIP error on the unselected configurations, which keep their MLIP labels, stays below a user-chosen fraction $α$ of the expected error. Under an identical guarantee across eight dataset-MLIP pairs, our predictor routes 7% and 14% fewer configurations to DFT at $α=0.3$ than committee baselines. Because committee disagreement overlooks errors the 

## My notes

- 
