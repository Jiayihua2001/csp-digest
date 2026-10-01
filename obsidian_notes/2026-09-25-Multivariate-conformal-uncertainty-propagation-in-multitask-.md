---
title: "Multivariate conformal uncertainty propagation in multitask atomistic simulation: Successes and pitfalls"
date: 2026-09-25
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.31384v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Multivariate conformal uncertainty propagation in multitask atomistic simulation: Successes and pitfalls

**Authors:** [[Katharine Fisher]], [[Michael Herbst]], [[James Kermode]]
**Link:** https://arxiv.org/abs/2609.31384v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Extends conformal prediction to multivariate, multitask, multistage atomistic simulations, introducing hyperrectangle/hyperellipsoid calibration schemes that propagate correlated uncertainty downstream, capturing error cancellation in derived quantities like energy differences

## Abstract
> Machine learning has become the standard tool for the design of interatomic potentials which balance efficiency and accuracy, but uncertainty quantification remains an open problem. Multiscale simulations introduce an additional challenge: robust uncertainty quantification across scales. Even within one scale, computations are often multistage, producing a sequence of target quantities, each dependent on the previous, and each with some uncertainty. Conformal methods have emerged as a model agnostic framework for recalibrating surrogate predictions to produce sets which contain the truth at a user-specified rate. For multistage workflows, we require uncertainty calibration for multiple chemical properties and atomistic configurations, and we want to propagate uncertainty sets to downstream quantities of interest. Such propagation should capture the error cancellations which occur in many downstream targets in materials science; for instance, an approximate energy difference is often more accurate than individual energy predictions. We present the first exploration of multivariate conformal methods for chemical properties, including Bonferroni-corrected hyperrectangles, hyperellipso

## My notes

- 
