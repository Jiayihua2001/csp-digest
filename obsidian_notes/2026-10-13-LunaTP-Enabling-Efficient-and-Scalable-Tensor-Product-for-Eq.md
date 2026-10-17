---
title: "LunaTP: Enabling Efficient and Scalable Tensor Product for Equivariant MLIPs"
date: 2026-10-13
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.18393v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# LunaTP: Enabling Efficient and Scalable Tensor Product for Equivariant MLIPs

**Authors:** [[Yuanchang Zhou]], [[Mingzhen Li]], [[Chen Wang]]
**Link:** https://arxiv.org/abs/2610.18393v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
LunaTP introduces path-group parallelism with multi-level reuse for node-centric Clebsch–Gordan tensor product kernels, achieving up to 250× speedup over e3nn and 17.1× over OpenEquivariance.

## Abstract
> Equivariant machine learning interatomic potentials (MLIPs) promise atomistic simulations with accuracy approaching that of quantum-mechanical calculations. However, the high computational cost of their core Clebsch--Gordan tensor product (CGTP) convolutions severely limits model scalability and efficiency. In this paper, we rethink the parallel execution of CGTP convolutions and introduce LunaTP. Built on node-centric execution, LunaTP exploits path-group parallelism and multi-level reuse to accelerate CGTP convolutions and higher-order derivative computation while preserving the underlying mathematical formulation. On an NVIDIA H100 GPU, LunaTP achieves kernel speedups of up to 250.0$\times$ over e3nn and 17.1$\times$ over OpenEquivariance. It also delivers end-to-end training throughput gains of up to 28.7$\times$ over e3nn and 3.11$\times$ over OpenEquivariance. Finally, LunaTP demonstrates scalability and robust performance across models, workload scales, and GPUs, delivering substantial acceleration for training and atomistic simulation with high-accuracy equivariant MLIPs.

## My notes

- 
