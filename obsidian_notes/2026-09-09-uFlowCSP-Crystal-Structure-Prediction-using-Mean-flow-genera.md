---
title: "uFlowCSP: Crystal Structure Prediction using Mean flow generative models"
date: 2026-09-09
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.09799v1
relevance: 80
significance: 0
tags:
  - CSP
  - generative-model
---

# uFlowCSP: Crystal Structure Prediction using Mean flow generative models

**Authors:** [[Sourin Dey]], [[Dipannoy Das Gupta]], [[Lai Wei]]
**Link:** https://arxiv.org/abs/2609.09799v1
**Scores:** relevance 80 / significance 0
**Field:** [[generative-model]]

## Why it matters
Introduces uFlowCSP, a MeanFlow-based CSP generative model with a symmetry-aware Transformer that generates full crystal structures in 1–5 network evaluations, achieving equal-or-better accuracy than diffusion/flow baselines at 5–58

## Abstract
> Crystal structure prediction (CSP) is fundamental to computational materials discovery. Generative models including CDVAE, DiffCSP, FlowMM, and CrystalFlow learn stable-crystal distributions directly, but diffusion and flow-matching inference requires tens to thousands of sequential network evaluations per candidate. We introduce uFlowCSP, a MeanFlow-based CSP model that learns the average, rather than instantaneous, probability-flow velocity. It generates a complete structure in one to five evaluations, delivering 5x-58x faster inference with equal or better performance. A chemistry- and symmetry-aware Transformer uses canonical atom ordering, global composition, and per-token chemistry embeddings. A coarse crystal-system token is used only during training; it provides additive gains, particularly improving space-group agreement despite being absent at inference, which remains formula-only. On MP-20 with 20 candidates per target, one step matches CrystalFlow (78.38% vs. 78.34%) with 100x fewer evaluations and about 10x lower wall-clock time. Five steps reach 83.64%, exceeding CrystalFlow (78.34% at 2,000 evaluations) and DiffCSP (77.93% at about 20,000), while using 20x fewer eval

## My notes

- 
