---
title: "Noise-resilient training of machine learning interatomic potentials"
date: 2026-10-13
source: journal
venue: "The Journal of Chemical Physics"
doi: 10.1063/5.0327092
arxiv: 
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Noise-resilient training of machine learning interatomic potentials

**Authors:** [[Terry C. W. Lam]], [[Niamh O’Neill]], [[Christoph Schran]]
**Link:** https://doi.org/10.1063/5.0327092
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces an unsupervised, single-pass training method that down-weighs noisy reference data via exponential-moving-average loss tracking, matching iterative-refinement accuracy without extra DFT calculations or retraining cycles.

## Abstract
> The accuracy of machine learning interatomic potentials suffers from reference data that contain numerical noise. Often originating from unconverged or inconsistent electronic-structure calculations, this noise is challenging to identify. Existing mitigation strategies, such as manual filtering or iterative refinement of outliers, require either substantial expert effort or multiple expensive retraining cycles, making them difficult to scale to large datasets. Here, we introduce a noise-resilient training method that automatically down-weighs noisy samples, without requiring additional reference calculations. By tracking the loss distribution via an exponential moving average, this unsupervised method identifies outliers throughout a single training run. We show that this approach prevents overfitting and matches the performance of iterative refinement baselines with significantly reduced overhead. The method’s effectiveness is demonstrated by recovering accurate physical observables for liquid water from unconverged reference data, including diffusion coefficients. Furthermore, we validate its scalability by training a foundation model for organic chemistry on the SPICE dataset, w

## My notes

- 
