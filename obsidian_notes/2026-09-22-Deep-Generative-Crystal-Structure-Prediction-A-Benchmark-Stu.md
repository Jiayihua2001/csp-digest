---
title: "Deep Generative Crystal Structure Prediction: A Benchmark Study and a Controlled Test of Prototype Dependence"
date: 2026-09-22
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.26502v1
relevance: 87
significance: 0
tags:
  - CSP
  - generative-model
  - benchmark
---

# Deep Generative Crystal Structure Prediction: A Benchmark Study and a Controlled Test of Prototype Dependence

**Authors:** [[Lai Wei]], [[Rongzhi Dong]], [[Ying Feng]]
**Link:** https://arxiv.org/abs/2609.26502v1
**Scores:** relevance 87 / significance 0
**Field:** [[generative-model]] [[benchmark]]

## Why it matters
Benchmarking 12 generative CSP models against a template-retrieval baseline (TCSP 2.0) under unified criteria, plus a prototype-family leave-out test, reveals generative success is largely template-overlap-driven, not true novel-structure generalization.

## Abstract
> Deep generative models are widely reported to enable de novo crystal structure prediction (CSP), but their capability has not been measured consistently against template-based methods. We evaluate 12 representative generative CSP models, spanning latent-variable, diffusion, flow-matching, autoregressive, and manifold random-walk architectures, against TCSP 2.0 on 180 test structures and a leakage-controlled subset of 46. All methods use identical structure-matching, symmetry, and consensus criteria. Template retrieval is the strongest single method, reaching 68.3% top-1 success; symmetry-aware EquiCSP (66.4%) and Uni-3DAR (62.9%) form the next tier. However, comparison with TCSP 2.0 shows that most structures correctly predicted by generative models are also correctly predicted by template substitution. Thus, the set of structures uniquely reachable by generation is small, limiting its practical advantage for discovering structures outside existing prototype libraries. To test the source of this performance, we removed entire stoichiometric prototype families from the training set and retrained the strongest generative model. Accuracy declined by 50-78% across four families, establ

## My notes

- 
