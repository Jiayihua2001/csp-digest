---
title: "NEMORA: Neural Equivariant Multipole Operators for Long-Range Atomistic Learning"
date: 2026-10-07
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.10776v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# NEMORA: Neural Equivariant Multipole Operators for Long-Range Atomistic Learning

**Authors:** [[Jay L. Kaplan]], [[Samuel Varner]], [[Rebecca Willett]]
**Link:** https://arxiv.org/abs/2610.10776v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces NEMORA, a learnable equivariant generalization of the Fast Multipole Method with trainable multipole/translation operators that couple angular degrees for many-body, strictly equivariant, near-linear-cost long-range interatomic potentials.

## Abstract
> Equivariant graph neural networks have emerged as foundational architectures for machine-learned interatomic potentials, approaching quantum-chemical accuracy at a fraction of the computational cost. These models describe local atomic environments accurately, but finite spatial cutoffs truncate long-range information flow, and stacking message-passing layers can lead to over-smoothing and over-squashing. Existing long-range extensions either prescribe a fixed analytical propagation kernel, restrict long-range communication to scalars or degree-preserving channels, are only approximately equivariant, or incur super-linear computational cost. Combining learnable long-range equivariant transport with multiscale many-body expressivity and efficient scaling for larger systems remains a central challenge. We introduce Neural Equivariant Multipole Operators (NEMORA), a neural equivariant extension of the Fast Multipole Method (FMM) for learning long-range tensorial representations. NEMORA generalizes the FMM's analytical multipole expansion and translation operators to learned equivariant counterparts on an adaptive spatial hierarchy. Its operators couple angular degrees and form many-bod

## My notes

- 
