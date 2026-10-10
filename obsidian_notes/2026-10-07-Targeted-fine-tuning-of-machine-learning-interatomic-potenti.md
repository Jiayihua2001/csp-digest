---
title: "Targeted fine-tuning of machine-learning interatomic potentials for phonons and phase transitions"
date: 2026-10-07
source: journal
venue: "npj Computational Materials"
doi: 10.1038/s41524-026-02338-w
arxiv: 
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - free-energy
---

# Targeted fine-tuning of machine-learning interatomic potentials for phonons and phase transitions

**Authors:** [[Jonas Grandel]], [[Philipp Benner]], [[Janine George]]
**Link:** https://doi.org/10.1038/s41524-026-02338-w
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[free-energy]]

## Why it matters
Introduces targeted L2-SP fine-tuning (regularized, layer-selective updates) for MLIPs, showing ~10 structures per material improve phonon, thermal, elastic, and instability predictions across 53 materials versus standard transfer/multihead/LoRA

## Abstract
> Abstract Machine-learning interatomic potentials are widely used as computationally efficient surrogates for density functional theory in atomistic simulations, enabling large-scale and long-time modeling of materials systems. Here, we investigate how different fine-tuning strategies affect the prediction of harmonic phonon band structures, thermal and elastic properties, and the potential-energy surface along unstable phonon modes. We show that substantial improvements can be achieved with very limited additional data, with as few as 10 material-specific training structures. We investigate targeted L 2 -SP ( L 2 -TSP) for this application, combining regularization toward the pre-trained model with selective fine-tuning of the first two representation-building layers, alongside transfer learning and multihead fine-tuning, with an additional comparison to low-rank LoRA for phonon prediction. Across 53 materials, L 2 -TSP achieves the most consistent overall performance, reducing phonon errors while also improving predictions of thermodynamic and elastic properties. Importantly, models with similar harmonic phonon accuracy can differ substantially in their prediction of dynamical ins

## My notes

- 
