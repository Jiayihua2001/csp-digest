---
title: "A latent-space extrapolation grade built into graph atomic cluster expansion foundation potentials"
date: 2026-09-30
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.40060v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# A latent-space extrapolation grade built into graph atomic cluster expansion foundation potentials

**Authors:** [[Yury Lysogorskiy]], [[Anton Bochkarev]], [[Ralf Drautz]]
**Link:** https://arxiv.org/abs/2609.40060v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces the CALM extrapolation grade—a calibrated, differentiable per-atom Mahalanobis distance in GRACE's latent cluster-expansion space—enabling single-pass uncertainty estimates to guide active-learning data collection.

## Abstract
> Foundation machine-learning interatomic potentials cover broad configurational and chemical spaces, but their reliability can vary across the atomic environments encountered during a simulation. Here we introduce the calibrated Mahalanobis (CALM) extrapolation grade $γ$, a piecewise differentiable per-atom quantity integrated into GRACE foundation models and evaluated alongside energies and forces in a single model pass. We define $γ$ from nearest-cluster Mahalanobis distances in latent feature space, setting $γ=1$ from the training-distance distribution separately for each element and cluster. Controlled tests show that a normalized random projection of the invariant many-body basis detects structural and chemical extrapolation. On different foundation datasets, OMat24 and SMAX, $γ$ correlates with atomic force errors and separates structures with different error distributions. The CALM grade adds percent-level computational cost, and its spatial gradient guides uncertainty-biased data collection toward configurations with larger absolute force errors.

## My notes

- 
