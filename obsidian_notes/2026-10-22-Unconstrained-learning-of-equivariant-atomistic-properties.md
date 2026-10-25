---
title: "Unconstrained learning of equivariant atomistic properties"
date: 2026-10-22
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.31183v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Unconstrained learning of equivariant atomistic properties

**Authors:** [[Joseph W. Abbott]], [[Paolo Pegolo]], [[Pol Febrer]]
**Link:** https://arxiv.org/abs/2610.31183v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Demonstrates that a symmetry-unconstrained Point-Edge Transformer backbone can accurately learn diverse O(3)-equivariant/pseudotensorial atomistic properties—dipoles, polarizabilities, NMR shieldings, electron-density expans

## Abstract
> Machine-learned interatomic potentials based on graph neural networks (GNNs) have made first-principles accuracy routine for the potential energy surface (PES). Their backbones, often O(3)-equivariant by design, are increasingly used to learn other atomistic properties. Many of these are of high angular order or pseudotensorial character, defined per atom, or expanded on large atom-centered basis sets. Such targets strain equivariant GNNs, whose tensor products grow steeply in cost with angular order and can fail to represent the target if truncated, forcing difficult trade-offs between hyperparameters. Unconstrained models like the Point-Edge Transformer (PET) instead replace explicit O(3) algebra with edge-to-edge attention and learn equivariance from data, so that the same backbone can in principle learn any equivariant property. We demonstrate how to use PET to learn molecular dipoles and polarizabilities, NMR chemical shielding tensors, and auxiliary-basis expansions of the electron density. Increasing the backbone size systematically improves both accuracy and equivariance error, and targeted architectural and training choices reduce the symmetry breaking further. PET matches

## My notes

- 
