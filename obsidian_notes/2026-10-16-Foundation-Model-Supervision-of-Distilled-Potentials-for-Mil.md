---
title: "Foundation-Model Supervision of Distilled Potentials for Million-Atom Molecular Dynamics"
date: 2026-10-16
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.23371v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Foundation-Model Supervision of Distilled Potentials for Million-Atom Molecular Dynamics

**Authors:** [[Xiaoqing Liu]], [[Yangshuai Wang]], [[Lei Shen]]
**Link:** https://arxiv.org/abs/2610.23371v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a memory-efficient MACE inference schedule enabling atom-wise, whole-trajectory DFT-level auditing of million-atom MD, exposing rare local failures invisible to averaged metrics or random sampling.

## Abstract
> Machine-learned interatomic potentials distilled from foundation models enable fast large-scale molecular dynamics (MD), but they can fail locally in chemical environments that their training data did not sample. System-averaged error metrics and small random audits often miss such sparse or isolated failures. Here we use an exact equivariant foundation model, MACE-MPA-0, to check every atom of million-atom production simulations. Reorganizing two-layer MACE inference into a receiver-chunked three-pass schedule that keeps no per-edge intermediates resident reduces the marginal memory per atom 340-fold, evaluates up to $2.86\times10^{7}$ atoms on a single H200 GPU, and supervises $10^{6}$-atom trajectories in LAMMPS at 1.3% of the run time. Distilled MACE students run four to nine times slower than NEP89 with 0.95-1.28 times the teacher's force error against density functional theory (DFT). In molten SiO$_2$, whole-system checks uncover a persistent tail of under-coordinated atoms hidden by the system-averaged error and an isolated, unphysical O-O contact that a 1% random audit misses 94% of the time. On-the-fly retraining on teacher-labelled 13-Å clusters, with the force loss restr

## My notes

- 
