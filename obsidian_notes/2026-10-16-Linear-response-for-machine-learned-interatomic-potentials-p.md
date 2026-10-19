---
title: "Linear response for machine-learned interatomic potentials: phonons at arbitrary wave vectors from the primitive cell"
date: 2026-10-16
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.23545v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - free-energy
---

# Linear response for machine-learned interatomic potentials: phonons at arbitrary wave vectors from the primitive cell

**Authors:** [[Thalis H. B. da Silva]], [[Hai-Chen Wang]], [[Miguel A. L. Marques]]
**Link:** https://arxiv.org/abs/2610.23545v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[free-energy]]

## Why it matters
Introduces a linear-response (Bloch-phase perturbation) method for message-passing interatomic potentials that computes exact phonon dynamical matrices at arbitrary wave vectors directly from the primitive cell, eliminating supercell truncation errors.

## Abstract
> Phonon calculations with machine-learned interatomic potentials are almost exclusively performed with finite displacements in supercells, an approach that is exact only at wave vectors commensurate with the supercell and whose error depends on the range of the force constants. In message-passing networks this range grows with the number of layers, and reaches 140 angstrom for the deepest universal models. Here we show that the dynamical matrix of a message-passing potential can be obtained exactly in the primitive cell, at any wave vector, as the linear response of the forces to a displacement modulated by a Bloch phase, in the spirit of density-functional perturbation theory. The phase enters only where the features of neighboring atoms are gathered, and the trained model is used without modification. One further derivative yields group velocities and mode Grüneisen parameters analytically. We apply the method to NequIP and Prophet, and reproduce the Hessians of supercells to machine precision. Using these results as a reference, we find that the supercells commonly employed in high-throughput calculations lead to errors of several tenths of a THz in the phonon frequencies, and th

## My notes

- 
