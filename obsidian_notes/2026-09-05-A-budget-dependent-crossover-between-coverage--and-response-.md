---
title: "A budget-dependent crossover between coverage- and response-based training-set selection for machine-learned interatomic potentials"
date: 2026-09-05
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.05877v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# A budget-dependent crossover between coverage- and response-based training-set selection for machine-learned interatomic potentials

**Authors:** [[Jia Bi]], [[Alin-Marin Elena]]
**Link:** https://arxiv.org/abs/2609.05877v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces a budget-resolved comparison showing training-set selection for MLIPs should switch from coverage-based to disagreement-guided (response witness) selection as label budget grows, evidenced by crossover on GAP-20/rMD17 with MACE.

## Abstract
> Selecting compact training sets for machine-learned interatomic potentials requires deciding whether to preserve structural diversity or target configurations on which models disagree. The better choice can depend on how much data is retained, making a comparison at one training-set size insufficient. Here we link selection criteria to prediction accuracy through a budget-resolved comparison of retrained MACE models on GAP-20 Carbon and pooled revised MD17. Structural coverage is compared with a response-guided selector that targets disagreement between a coverage-trained model and a full-data reference. This retrospective response witness tests the value of model disagreement for compressing an already labelled pool. At 5\%, coverage gives smaller absolute deviations from the full-data error than random sampling across four force endpoints in both datasets. The witness has larger deviations than coverage at 1\% and 5\%, but the ordering reverses at 20\%. At 20\%, witness-selected models also lower direct held-out force errors by 0.46--5.89\% relative to coverage, with all eight paired training-seed intervals favouring the witness. Six errors fall below the full-data reference. Mea

## My notes

- 
