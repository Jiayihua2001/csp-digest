---
title: "On the Theoretical Limits of Learning Unconstrained Interatomic Potentials"
date: 2026-10-10
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.15078v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# On the Theoretical Limits of Learning Unconstrained Interatomic Potentials

**Authors:** [[Prajwal Ananth]], [[Shuwen Yue]]
**Link:** https://arxiv.org/abs/2610.15078v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a theoretical framework proving that unconstrained MLIPs can achieve exponentially small energy/force errors yet exhibit near-maximal sampling error via kinetic trapping or equilibrium mismatch, exposing fundamental limits unrelated to CSP

## Abstract
> Machine-learned interatomic potentials (MLIPs) accelerate molecular dynamics (MD) simulations by learning the energies and forces that govern atomic motion. Recent work has shown that relaxing physical inductive biases can improve computational efficiency and predictive accuracy, raising the question of whether energy-and-force matching alone is sufficient to ensure accurate sampling. We show that, for unconstrained hypothesis classes, the relationship between prediction error and sampling accuracy is exponentially ill-conditioned in dimension. In particular, prediction errors that decay exponentially with dimension can coexist with nearly maximal total variation distance between the learned and target distributions. We identify two failure mechanisms. The first is kinetic trapping, where relaxation to an accurate learned equilibrium requires exponentially long times, even when simulations are initialized from training configurations at which energies and forces are matched exactly. The second is equilibrium mismatch, where the learned stationary distribution itself remains far from the target. Under explicit assumptions, we show that equilibrium mismatch can persist even in local,

## My notes

- 
