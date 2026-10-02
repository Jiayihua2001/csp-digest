---
title: "Cluster-based Structural Similarity for Dataset Visualization and Data Selection for Machine Learning Interatomic Potentials"
date: 2026-09-30
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.39984v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - benchmark
---

# Cluster-based Structural Similarity for Dataset Visualization and Data Selection for Machine Learning Interatomic Potentials

**Authors:** [[Yuto Iwasaki]], [[Miguel A. Caro]]
**Link:** https://arxiv.org/abs/2609.39984v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[benchmark]]

## Why it matters
Introduces a k-medoids-clustered, optimal-matching structural similarity metric that is ~50x faster than existing methods and improves data-efficient selection for MLIP training.

## Abstract
> Machine learning interatomic potentials (MLIPs) are essential components for accelerating simulation-driven materials design. Data-efficient MLIP training relies on data-selection strategies that maximize structural diversity while limiting computationally expensive first-principles calculations. A key challenge in such strategies is evaluating structural similarity, which involves a trade-off between retaining information on individual atomic environments and reducing computational cost. Here, we propose similarity evaluation methods that achieve both representational fidelity and computational efficiency. Our method represents each structure using a small set of characteristic atomic environments identified by k-medoids clustering and computes pairwise similarity through optimal matching between these representatives or their distributions. Molecular benchmarks demonstrate that our method is approximately 50 times faster than the baseline method while also more clearly distinguishing structures with different chemical compositions. Similarity-based data-selection benchmarks demonstrate that our methods improve the data efficiency and stability of force prediction in MLIPs.

## My notes

- 
