---
title: "Colour me shocked: Exact Molecular Hessians from local MLIPs in O(N) time using sparse differentiation!"
date: 2026-09-21
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.24720v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - conformational
  - benchmark
---

# Colour me shocked: Exact Molecular Hessians from local MLIPs in O(N) time using sparse differentiation!

**Authors:** [[Luca Thiede]], [[Andreas Burger]], [[Alán Aspuru-Guzik]]
**Link:** https://arxiv.org/abs/2609.24720v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[conformational]] [[benchmark]]

## Why it matters
Applies sparse automatic differentiation, exploiting a closed-form Hessian sparsity pattern for local MLIPs, to compute exact molecular Hessians in O(N) time instead of O(N²).

## Abstract
> The Hessian of the energy with respect to the nuclear positions is indispensable in atomistic modelling. However, constructing this matrix requires $O(N)$ Hessian vector products, traditionally limiting high-accuracy Hessians to small systems. Machine learning interatomic potentials (MLIPs) have accelerated atomistic modelling by providing highly accurate energies and forces at $O(N)$ cost, yet the resulting $O(N^2)$ cost of Hessians remains a practical bottleneck for large systems. Based on the insight that we can derive the sparsity pattern for an MLIP's Hessians in closed form, we show in this paper how to use techniques from sparse automatic differentiation to reduce the cost of a local MLIP's Hessians to a system-size-independent number of Hessian-vector products, yielding overall $O(N)$ total cost without any approximations. We benchmark our approach on a variety of systems ranging from alkane chains to water clusters to $A\beta40$ conformers. Depending on the MLIP configuration, we achieve the linear scaling regime already on relatively small systems, resulting in large runtime reductions between 2$\times$-15$\times$ for these systems. This opens up the possibility of scalin

## My notes

- 
