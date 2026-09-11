---
title: "cuSOAP: a GPU-accelerated Generator of Smooth Overlap of Atomic Positions Descriptor"
date: 2026-09-04
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.05709v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# cuSOAP: a GPU-accelerated Generator of Smooth Overlap of Atomic Positions Descriptor

**Authors:** [[Hongyu Yan]], [[Yuqing Xia]], [[Yong Wei]]
**Link:** https://arxiv.org/abs/2609.05709v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces cuSOAP, a GPU-accelerated (fused CUDA/Triton) SOAP descriptor and Jacobian generator that drop-in replaces CPU-based DScribe, matching its outputs to ~1e-6 while drastically accelerating large-

## Abstract
> The Smooth Overlap of Atomic Positions (SOAP) descriptor is one of the most widely adopted representations of atomic environments in molecular machine learning, but the cost of evaluating it and its derivatives remains a principal bottleneck of SOAP-based interatomic potentials, particularly at the large radial and angular basis sizes demanded by complex, multi-species condensed-phase environments. We present cuSOAP, a GPU-accelerated generator of atom-wise SOAP vectors and their analytic derivatives. Built on PyTorch, cuSOAP evaluates closed-form expressions or quadratures for the projection coefficients and their Cartesian gradients for Gaussian-type-orbital and polynomial radial bases, through fused CUDA and Triton kernels that eliminate the multi-gigabyte intermediates of a naive tensor formulation. The package is a drop-in replacement for the CPU-based reference DScribe, reproducing its constructor signature, feature ordering, and output to within ${\sim}10^{-6}$, and accepts structures directly as Atomistic Simulation Environment (ASE) Atoms objects. On an NVIDIA Grace--Blackwell (GB200) node, a single Blackwell GPU generates the full descriptor-plus-Jacobian workload for a 1

## My notes

- 
