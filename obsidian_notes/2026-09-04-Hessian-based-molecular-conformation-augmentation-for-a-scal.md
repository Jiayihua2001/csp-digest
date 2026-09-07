---
title: "Hessian-based molecular conformation augmentation for a scalable and efficient strategy of machine learning interatomic potentials"
date: 2026-09-04
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.05233v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - free-energy
---

# Hessian-based molecular conformation augmentation for a scalable and efficient strategy of machine learning interatomic potentials

**Authors:** [[Bumju Kwak]], [[Jeonghee Jo]]
**Link:** https://arxiv.org/abs/2609.05233v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[free-energy]]

## Why it matters
Introduces two plug-and-play Hessian-derived data-augmentation schemes—UniAug (isotropic Gaussian displacement) and ModeAug (normal mode-weighted displacement)—that inject Hessian information into MLIP training without architectural changes or higher-

## Abstract
> While machine-learning interatomic potentials (MLIPs) have successfully learned potential energy surfaces (PES) and atomic forces, many practical applications, such as vibrational analysis and transition state search, rely heavily on the PES Hessian. Yet, standard MLIPs tend to be trained on energy and forces alone, leaving Hessian information largely unexploited. Meanwhile, existing methods that explicitly incorporate the Hessian into training objectives require architectural modifications and introduce significant computational and memory overheads due to higher-order backpropagation. To address these limitations, we propose two Hessian-derived data augmentation schemes: isotropic Gaussian displacement (\textbf{UniAug}) and normal mode-weighted displacement (\textbf{ModeAug}). Both methods utilize simple Taylor expansions, achieving effective augmentation without altering training objectives or extending the autograd graph. This allows seamless, plug-and-play integration with existing architectures and training pipelines. Comprehensive evaluations across non-equilibrium and equilibrium datasets demonstrate that our approach enhances model accuracy while providing practical, task-

## My notes

- 
