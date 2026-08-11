---
title: "ED-CSP: Crystal Structure Prediction from Electron Diffraction"
date: 2026-08-06
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2608.06448v1
relevance: 85
significance: 0
tags:
  - CSP
  - generative-model
  - ML-potential
---

# ED-CSP: Crystal Structure Prediction from Electron Diffraction

**Authors:** [[Germain Poloudenny]], [[Yaël Frégier]], [[Arnaud Demortière]]
**Link:** https://arxiv.org/abs/2608.06448v1
**Scores:** relevance 85 / significance 0
**Field:** [[generative-model]] [[ML-potential]]

## Why it matters
Introduces ED-CSP, a relational set encoder plus periodic flow generator that directly predicts full crystal structures from raw multi-view electron diffraction spots and composition, trained on a new 4.85M-structure simulated ED dataset, outperforming PXRD-based

## Abstract
> Recovering a periodic 3D crystal structure from sparse, unindexed electron diffraction (ED) observations is a challenging generative inverse problem. Existing ED-based learning methods mainly predict crystallographic labels, reconstruct structures from indexed reflections, or retrieve candidates from finite structure libraries. Here, we introduce ED-CSP, a machine learning framework that predicts crystal structures from chemical composition, atom count, and multiple detector-plane ED spot sets. ED-CSP combines a relational set encoder, permutation-invariant multi-view aggregation, and a periodic flow generator to jointly predict lattice parameters and fractional atomic coordinates. To train the model, we construct ED-CS, a dataset of 4.85 million simulated multi-view ED crystal structures, deduplicated across seven materials repositories and filtered to exclude CHILI-100K overlaps. On 2,075 held-out CHILI-100K materials, ED-CSP trained only on CHILI achieves a structural match rate of 57.49% MR@5, outperforming PXRDGen (52.92%), a state-of-the-art crystal structure prediction model conditioned on powder X-ray diffraction. Scaling training data further improves performance: initiali

## My notes

- 
