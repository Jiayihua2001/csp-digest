---
title: "Where Should Physics Enter a Molecular Crystal Generator?"
date: 2026-09-28
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.36398v1
relevance: 92
significance: 0
tags:
  - CSP
  - generative-model
  - ML-potential
  - space-group
---

# Where Should Physics Enter a Molecular Crystal Generator?

**Authors:** [[Haocheng Tang]], [[Junmei Wang]], [[Wengong Jin]]
**Link:** https://arxiv.org/abs/2609.36398v1
**Scores:** relevance 92 / significance 0
**Field:** [[generative-model]] [[ML-potential]] [[space-group]]

## Why it matters
Introduces CrystAF, an all-atom crystal flow-map generator, to systematically compare training-, post-training-, and inference-time physics integration, showing physics-informed post-training cheaply improves validity while remaining complementary to inference-time UMA relaxation.

## Abstract
> Generative models make molecular crystal structure prediction fast, but their samples still exhibit geometric and packing violations. Physics can be introduced during training, post-training, or inference, yet these choices are rarely compared with the generator and physical signal held fixed. We introduce CrystAF, an all-atom crystal flow-map generation model, and use it with the UMA interatomic potential to systematically study where physics should enter. Post-training learns physical preferences directly into CrystAF, improving molecular validity and crystal packing while leaving sampling unchanged: physics is paid for once during training rather than repeatedly at deployment. In contrast, UMA relaxation is effective at repairing local clashes but makes generation 6--26$\times$ slower, while learning from relaxed targets provides little benefit. These routes are complementary rather than competing. Physics-informed post-training first shifts the generated distribution toward more physically reasonable structures, after which inexpensive inference-time corrections further remove clashes and restore stereochemistry that the generator cannot represent. Importantly, the same post-tr

## My notes

- 
