---
title: "From Energy-Force Weighting to Primal-Dual Optimization of Machine-Learned Interatomic Potentials"
date: 2026-10-01
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.00876v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# From Energy-Force Weighting to Primal-Dual Optimization of Machine-Learned Interatomic Potentials

**Authors:** [[Chenyu Wang]], [[Yangshuai Wang]], [[Lei Zhang]]
**Link:** https://arxiv.org/abs/2610.00876v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a primal-dual, force-constrained optimization scheme (projected dual ascent plus frozen-multiplier quasi-Newton refinement) replacing manual energy-force weight scalarization for fitting machine-learned interatomic potentials, achieving comparable acc

## Abstract
> Machine-learned interatomic potentials are commonly fitted by weighted-sum scalarization, which combines energy and force errors in a single loss. A nominal weight, however, identifies a potential only relative to the complete fitting protocol. We therefore treat energy--force balancing as a protocol-dependent problem of physical model selection. For fixed-basis atomic cluster expansion models of molten LiCl, liquid H$_2$O, and Si, the resulting scalarization paths contain dominated states at extreme weights. Their nondominated subsets depend on the solver, and the out-of-distribution Si path is nonmonotone. We replace direct weight selection by minimizing the regularized energy objective subject to an upper bound on the normalized force loss. Projected dual ascent adjusts the Lagrange multiplier from the force-constraint residual. A frozen-multiplier limited-memory quasi-Newton refinement then returns the final model. Across the three systems, the constrained procedure reaches the solver-matched low-error region and gives measured speedups of $6.7$--$8.9$ over completed scalarization scans under the stated timing convention. Physical-property calculations show that first-shell geo

## My notes

- 
