---
title: "Interatomic Potential Prediction Based on Charge Equilibration and Equivariant Transformer"
date: 2026-08-24
source: journal
venue: "Computers and Artificial Intelligence"
doi: 10.70267/cai.26v3n4.3545
arxiv: 
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - lattice-energy
  - benchmark
---

# Interatomic Potential Prediction Based on Charge Equilibration and Equivariant Transformer

**Authors:** [[Yijun Shi]], [[Tao Luo]]
**Link:** https://doi.org/10.70267/cai.26v3n4.3545
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[lattice-energy]] [[benchmark]]

## Why it matters
CE-ETNet couples an equivariant Transformer encoder with a differentiable charge-equilibration solver enforcing total-charge conservation, explicitly embedding long-range Coulomb physics to cut energy/force MAE ~8% across QM9, rMD17, and

## Abstract
> Conventional local machine-learning interatomic potentials describe atomic environments with a finite cutoff radius and therefore have difficulty capturing long-range electrostatic coupling in polar, charged, or charge-transfer systems. This paper proposes CE-ETNet (Charge-Equilibration-Enhanced Equivariant Transformer Network), an equivariant Transformer interatomic potential constrained by charge equilibration. The model learns local chemical environments formed by atom types, geometric edges, and radial basis features through an equivariant representation encoder, and predicts atomic electronegativities. Under the constraint of total charge conservation, a differentiable charge equilibration procedure is used to solve partial charges and electrostatic energy, thereby incorporating long-range Coulomb interactions into energy and force prediction. On three benchmark datasets, QM9, revised MD17, and tmQM_wB97MV, CE-ETNet reduces the mean absolute error (MAE) of energy and force prediction by about 8% on average compared with existing models, reaching chemical accuracy. The experimental results show that explicit long-range electrostatic modeling improves the predictive performance 

## My notes

- 
