---
title: "Physics-Aligned Electronic Ground-State Learning Improves Generalization"
date: 2026-10-07
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.10298v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Physics-Aligned Electronic Ground-State Learning Improves Generalization

**Authors:** [[Eike S. Eberhard]], [[Xaver Kainz]], [[Viktor Kotsev]]
**Link:** https://arxiv.org/abs/2610.10298v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces physics-constrained training—ON-Loss, GROOT, and ROCKET—that aligns ground-state descriptor models with KS-DFT equations, slashing out-of-distribution energy/force errors by up to 99.8%.

## Abstract
> Machine-learned interatomic potentials (MLIPs) excel at in-distribution tasks, accelerating drug and material development, yet they struggle to generalize out-of-distribution. We propose to push the cost-accuracy Pareto frontier by designing observable-agnostic electronic ground-state descriptor models (GSMs) with computational costs situated between MLIPs and Kohn-Sham density functional theory (KS-DFT). We align the learning objectives and architectures of GSMs with the governing equations of KS-DFT by enforcing physical constraints and removing optimization pressure on unphysical or irrelevant degrees of freedom. In our size-extrapolation experiments from QM9 to QM40, our combined contributions OrthoNormal-Loss (ON-Loss) and Grassmann Restricted Occupied-Orbital Training (GROOT) reach a 79.1% energy and 83.4% force mean absolute error (MAE) reduction over previous state-of-the-art density GSMs. For Hamiltonian GSMs, ON-Loss and Residual Optimal-gauge Conditioning-aware KS-Eq. Training (ROCKET) together reduce the energy and force MAEs of the strongest baseline by 99.8% and 95.9%, respectively. Using a self-consistency rejection criterion, we filter out extrapolation errors on QM

## My notes

- 
