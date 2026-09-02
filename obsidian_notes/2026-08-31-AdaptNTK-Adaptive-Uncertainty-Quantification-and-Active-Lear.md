---
title: "AdaptNTK: Adaptive Uncertainty Quantification and Active Learning for Neural Network Potentials"
date: 2026-08-31
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.00488v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# AdaptNTK: Adaptive Uncertainty Quantification and Active Learning for Neural Network Potentials

**Authors:** [[Prajwal Ananth]], [[Shuwen Yue]]
**Link:** https://arxiv.org/abs/2609.00488v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
AdaptNTK introduces a single-model, label-free uncertainty measure using regularized Mahalanobis distance in empirical neural tangent kernel space, enabling recursive, redundancy-aware batch active learning without retraining or ensembles.

## Abstract
> Machine learning interatomic potentials bridge the gap between quantum chemical precision and classical computational speed, enabling molecular dynamics simulations with first-principles accuracy. Their reliability is often improved through active learning, which iteratively expands the training set by identifying uncertain, out-of-distribution configurations. Existing uncertainty-quantification methods often involve a trade-off between computational cost and reliability, and generally cannot account for redundancy as an acquisition batch is assembled. Here, we introduce AdaptNTK, a single-model framework that measures uncertainty as a regularized Mahalanobis distance in empirical neural tangent kernel (NTK) feature space. With the NTK features fixed during acquisition, the uncertainty depends on the acquired configurations but not their reference labels. This allows the uncertainty to be updated recursively after each selection without retraining, reducing redundancy within an acquisition batch. On held-out rMD17 data, AdaptNTK achieves the highest mean correlations with force errors (Spearman 0.68, Pearson 0.71) and matches a three-member ensemble in error retention. In active le

## My notes

- 
