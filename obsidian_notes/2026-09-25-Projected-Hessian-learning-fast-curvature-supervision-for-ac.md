---
title: "Projected Hessian learning: fast curvature supervision for accurate machine-learning interatomic potentials"
date: 2026-09-25
source: journal
venue: "Machine Learning: Science and Technology"
doi: 10.1088/2632-2153/aeac9b
arxiv: 
relevance: 70
significance: 12
tags:
  - CSP
  - ML-potential
---

# Projected Hessian learning: fast curvature supervision for accurate machine-learning interatomic potentials

**Authors:** [[Austin Rodriguez]], [[Justin S Smith]], [[Sakib Matin]]
**Link:** https://doi.org/10.1088/2632-2153/aeac9b
**Scores:** relevance 70 / significance 12
**Field:** [[ML-potential]]

## Why it matters
Introduces Projected Hessian Learning, which supervises MLIP training using stochastic Hessian–vector product projections instead of explicit Hessians, cutting curvature-supervision cost to near force-level complexity while remaining unbiased and size-scalable.

## Abstract
> Abstract The Hessian matrix of second derivatives contains substantially richer information about the local geometry of the potential energy surface than energies and forces alone. Although incorporating full Hessians into machine-learning interatomic potential (MLIP) training can significantly improve accuracy and robustness, the quadratic computational and memory cost of explicitly constructing and storing Hessian matrices has limited its practical use. Here, we introduce Projected Hessian Learning (PHL), a scalable second-order training framework that incorporates curvature information using only Hessian–vector products (HVPs). By avoiding explicit Hessian construction and instead projecting curvature along stochastic probe directions, PHL reduces the cost of second-derivative supervision to near force-level complexity. The resulting dense-probe trace estimator is unbiased and exhibits favorable scaling with system size, enabling curvature-informed training without quadratic memory growth. We evaluated various training approaches on a chemically diverse dataset of reactants, products, transition states, intrinsic reaction coordinates, and normal-mode sampled geometries generated

## My notes

- 
