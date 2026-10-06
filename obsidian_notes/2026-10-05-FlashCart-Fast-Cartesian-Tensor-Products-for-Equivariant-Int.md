---
title: "FlashCart: Fast Cartesian Tensor Products for Equivariant Interatomic Potentials"
date: 2026-10-05
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.06409v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# FlashCart: Fast Cartesian Tensor Products for Equivariant Interatomic Potentials

**Authors:** [[Viktor Zaverkin]], [[Payman Goodarzi]], [[Sergey V. Sukhomlinov]]
**Link:** https://arxiv.org/abs/2610.06409v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces FlashCart, which uses symbolically simplified Cartesian-component tensor products with fixed-width recursive feature compression to generate fused GPU kernels, enabling higher-order equivariant correlations at substantially lower cost than spherical-harmonic implementations

## Abstract
> Machine-learned interatomic potentials extend atomistic simulations beyond the length- and timescales accessible to electronic-structure methods. However, the computational cost of equivariant architectures limits the local correlations they can represent in practice and therefore their achievable accuracy. Here we introduce FlashCart, which makes higher-order correlations affordable by combining generated GPU kernels with an architecture that recursively builds equivariant features and compresses them to a fixed width at each step. We express tensor products in independent Cartesian components and symbolically simplify them and their derivatives, producing fused kernels that often outperform optimized spherical counterparts. We then show that increasing correlation order improves accuracy more efficiently than increasing width, depth, or tensor rank. On SPICE-MACE-OFF, FlashCart models advance the measured accuracy-efficiency frontier: a model with $5.6$ million parameters achieves lower energy and force errors and $10\times$ faster inference than a transformer with $189$ million parameters.

## My notes

- 
