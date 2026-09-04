---
title: "Diagnosing Latent Energy Decomposition in Machine-Learning Interatomic Potentials via Interacting Quantum Atoms"
date: 2026-09-01
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.00674v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Diagnosing Latent Energy Decomposition in Machine-Learning Interatomic Potentials via Interacting Quantum Atoms

**Authors:** [[Kohei Shimamura]], [[Ken-ichi Nomura]]
**Link:** https://arxiv.org/abs/2609.00674v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces E3D-IQA, a diagnostic framework that supervises an Allegro-type MLIP's node energies with IQA intra-atomic terms to expose whether its latent edge energies genuinely recover physically meaningful pairwise interactions.

## Abstract
> Machine-learning interatomic potentials (MLIPs) can reproduce potential energies and forces accurately, but their internal energy allocation is often difficult to interpret. E3D-IQA is introduced as a diagnostic framework connecting the latent edge-energy representation of an Allegro-type MLIP with Interacting Quantum Atoms (IQA) energy decomposition. The Allegro edge-energy path is retained as a latent pair contribution, while a node-energy path is trained against the IQA intra-atomic energy. IQA interatomic energies are not direct training targets; instead, the learned edge energies are evaluated after training against the IQA pair terms. Tests on H/C/N/O organic reaction structures show that intra-atomic supervision is essential: energy and force training alone does not recover an IQA-like one-body/two-body allocation. With intra-atomic supervision, node energies reproduce IQA intra-atomic terms, and latent edge energies show meaningful correspondence with IQA interatomic terms. Residual errors are concentrated in positive or weak pair interactions, exposing internal allocation failures that remain hidden in total-energy and force metrics. Adding structures labeled only with ene

## My notes

- 
