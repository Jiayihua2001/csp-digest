---
title: "Hessian-based molecular conformation augmentation for a scalable and efficient strategy of machine learning interatomic potentials"
date: 2026-09-04
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.05233v2
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - free-energy
---

# Hessian-based molecular conformation augmentation for a scalable and efficient strategy of machine learning interatomic potentials

**Authors:** [[Bumju Kwak]], [[Jeonghee Jo]]
**Link:** https://arxiv.org/abs/2609.05233v2
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[free-energy]]

## Why it matters
Introduces Hessian-derived data augmentation (UniAug and ModeAug) that uses Taylor-expansion displacements to inject curvature information into MLIP training without architectural changes or extended backpropagation.

## Abstract
> While machine-learning interatomic potentials (MLIPs) have successfully learned potential energy surfaces (PES) and atomic forces, many practical applications, such as vibrational analysis and transition state search, rely heavily on the PES Hessian. Yet standard MLIPs are trained on energy and forces alone, and existing methods that incorporate the Hessian into training objectives require architectural modifications and incur significant computational and memory overheads from higher-order backpropagation. To address these limitations, we propose two Hessian-derived data augmentation schemes: isotropic Gaussian displacement (\textbf{UniAug}) and normal mode-weighted displacement (\textbf{ModeAug}). Both methods utilize simple Taylor expansions, achieving effective augmentation without altering training objectives or extending the autograd graph. This allows seamless, plug-and-play integration with existing architectures and training pipelines. Comprehensive evaluations across non-equilibrium and equilibrium datasets demonstrate that our approach enhances model accuracy where reference forces are large while providing practical, task-specific guidelines.

## My notes

- 
