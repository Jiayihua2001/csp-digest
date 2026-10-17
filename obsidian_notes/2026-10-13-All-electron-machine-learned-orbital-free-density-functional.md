---
title: "All-electron machine-learned orbital-free density functional for periodic CHNO systems"
date: 2026-10-13
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.17975v1
relevance: 70
significance: 0
tags:
  - CSP
  - generative-model
  - ML-potential
  - lattice-energy
---

# All-electron machine-learned orbital-free density functional for periodic CHNO systems

**Authors:** [[Marc K. Ickler]], [[Andreas Hermann]], [[Fred A. Hamprecht]]
**Link:** https://arxiv.org/abs/2610.17975v1
**Scores:** relevance 70 / significance 0
**Field:** [[generative-model]] [[ML-potential]] [[lattice-energy]]

## Why it matters
STRUCTURES-P introduces an equivariant all-electron orbital-free density functional trained on non-ground-state density energies/gradients, enabling variational density optimization across molecules and periodic CHNO crystals.

## Abstract
> We introduce STRUCTURES-P, a machine-learned all-electron orbital-free density functional for periodic CHNO systems. Electrostatics are evaluated analytically in an atom-centered Gaussian basis, while an equivariant network learns the kinetic and exchange-correlation energy from energies and gradients of non-ground-state densities. Minimizing the functional from a superposition of atomic densities recovers the Kohn-Sham ground state: on held-out crystals, the density error falls from 6.7% to 0.4% of the electron count and the energy error reaches 0.25 mHa per atom, half that of a same-architecture interatomic potential. A single functional can be trained for both isolated molecules and periodic systems, and the model generalizes to larger unit cells. It largely preserves relative-energy rankings and reproduces convex-hull vertices on the tested H-N composition slice. Together, these results demonstrate the viability of machine-learned all-electron orbital-free DFT for variational density optimization and energy evaluation in fixed-geometry solids.

## My notes

- 
