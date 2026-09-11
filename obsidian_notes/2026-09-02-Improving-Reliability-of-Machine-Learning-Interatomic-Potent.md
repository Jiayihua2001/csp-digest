---
title: "Improving Reliability
of Machine Learning Interatomic
Potentials with Physics-Informed Pretraining"
date: 2026-09-02
source: journal
venue: "Journal of Chemical Information
and Modeling"
doi: 10.1021/acs.jcim.6c00826
arxiv: 
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Improving Reliability
of Machine Learning Interatomic
Potentials with Physics-Informed Pretraining

**Authors:** [[Qianyu Zheng]], [[Victor Fung]]
**Link:** https://doi.org/10.1021/acs.jcim.6c00826
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a pretraining-finetuning strategy that pretrains MLIPs on cheap embedded atom model (EAM) potential data before finetuning on quantum data, improving MD stability and accuracy across three architectures.

## Abstract
> Abstract Machine Learning interatomic potentials (MLIPs) have emerged as powerful tools for molecular dynamics (MD) simulations with their competitive accuracy and computational efficiency. However, MLIPs often exhibit unphysical behavior when encountering configurations that deviate significantly from their training data distribution, leading to simulation instabilities and unreliable dynamics. This limits their reliability for materials simulations. We therefore present a physics-informed pretraining strategy that leverages simple empirical potentials to improve the robustness and stability of MLIPs for MD simulations. We demonstrate this approach through a pretraining-finetuning pipeline where MLIPs are initially pretrained on data labeled with embedded atom model (EAM) potentials and subsequently finetuned on the quantum mechanical ground truth data. Evaluation across three material systems (phosphorus, silica, and a subset of Materials Project) and three representative MLIP architectures (CGCNN, M3GNet, and TorchMD-NET) demonstrates that this physics-informed pretraining consistently improves both prediction accuracy as well as stability in MD compared to the baseline models.

## My notes

- 
