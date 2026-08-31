---
title: "Comparative study of ensemble-based uncertainty quantification methods for neural network interatomic potentials"
date: 2026-08-27
source: journal
venue: "Machine Learning: Science and Technology"
doi: 10.1088/2632-2153/ae9fb4
arxiv: 
relevance: 70
significance: 12
tags:
  - CSP
  - ML-potential
---

# Comparative study of ensemble-based uncertainty quantification methods for neural network interatomic potentials

**Authors:** [[Yonatan Kurniawan]], [[Mingjian Wen]], [[Ellad Tadmor]]
**Link:** https://doi.org/10.1088/2632-2153/ae9fb4
**Scores:** relevance 70 / significance 12
**Field:** [[ML-potential]]

## Why it matters
Systematically benchmarks four ensemble-based uncertainty quantification methods (bootstrap, dropout, random init, snapshot) for neural network interatomic potentials, testing precision-accuracy correlation across ID and OOD regimes including emergent system-level properties.

## Abstract
> Abstract Machine learning interatomic potentials (MLIPs) enable atomistic simulations with near first-principles accuracy at substantially reduced computational cost, making them powerful tools for large-scale materials modeling. The accuracy of MLIPs is typically validated on a held-out dataset of ab initio energies and atomic forces. However, accuracy on these small-scale properties does not guarantee reliability for emergent, system-level behavior-precisely the regime where atomistic simulations are most needed, but for which direct validation is often computationally prohibitive. As a practical heuristic, predictive precision-quantified as inverse uncertainty-is commonly used as a proxy for accuracy, but its reliability remains poorly understood, particularly for system-level predictions. In this work, we systematically assess the relationship between predictive precision and accuracy in both in-distribution (ID) and out-of-distribution (OOD) regimes, focusing on ensemble-based uncertainty quantification methods for neural network potentials, including bootstrap, dropout, random initialization, and snapshot ensembles. We use held-out cross-validation for ID assessment and calcu

## My notes

- 
