---
title: "ALIGNN 2.0: A Unified Line-Graph Neural Network Framework for Materials Screening, Force Fields, Inverse Design, Spectroscopy, and Microscopy"
date: 2026-09-16
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.19487v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - lattice-energy
  - benchmark
---

# ALIGNN 2.0: A Unified Line-Graph Neural Network Framework for Materials Screening, Force Fields, Inverse Design, Spectroscopy, and Microscopy

**Authors:** [[Jaehyung Lee]], [[Charles Rhys Campbell]], [[Akshaya Ajith]]
**Link:** https://arxiv.org/abs/2609.19487v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[lattice-energy]] [[benchmark]]

## Why it matters
ALIGNN 2.0 delivers a dependency-free, pure-PyTorch line-graph GNN unifying scalar, spectral, tensorial, per-atom, and force-field prediction in one graph pipeline, outperforming original ALIGNN on 26/30

## Abstract
> Graph neural networks are central to materials property prediction and machine-learning interatomic potentials, yet their reliance on specialized graph libraries hampers portability and reproducibility, and property and force-field models have historically required separate graph pipelines. We present ALIGNN 2.0, a dependency-free, pure-PyTorch reimplementation of the Atomistic Line Graph Neural Network, with the line graph and its batching built from scratch, running on current-generation accelerators and unifying scalar, spectral, tensorial, per-atom, and force-field prediction behind a single graph, a combination that to our knowledge no existing framework provides. Comparing radius and k-nearest-neighbor (kNN) graphs, the wider kNN graph is more accurate for properties while the smoothly varying radius graph is required for energy-conserving molecular dynamics. On the JARVIS-Leaderboard, ALIGNN 2.0 leads on 26 of 30 single-property benchmarks against the original ALIGNN, with large gains for piezoelectric and dielectric maxima, exfoliation energy, moduli, and superconducting Tc. The LAMMPS- and OpenMM-compatible ALIGNN-FF matches leading universal potentials on the Matbench-Dis

## My notes

- 
