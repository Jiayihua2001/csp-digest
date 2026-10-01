---
title: "Let CSP Be Your ANCHOR: Adaptive Crystal Search over Frozen Structure Priors"
date: 2026-09-27
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.33407v2
relevance: 80
significance: 0
tags:
  - CSP
---

# Let CSP Be Your ANCHOR: Adaptive Crystal Search over Frozen Structure Priors

**Authors:** [[Emma Lei Hovmand]], [[Jonas Elsborg]], [[Melih Kandemir]]
**Link:** https://arxiv.org/abs/2609.33407v2
**Scores:** relevance 80 / significance 0

## Why it matters
Introduces ANCHOR, a GRPO-trained composition policy with continuous adaptive novelty (CAN) rewards operating over a frozen CSP model, decoupling composition search from structure generation to boost SUN/MSUN rates substantially over fine-tuned de

## Abstract
> De novo crystal generation (DNG) models decide where to search in composition space and how to generate structures with one set of weights. We argue that discovery is better served by separating the two. A crystal structure prediction (CSP) model is a physical prior that should be improved by likelihood training, while rewards, including novelty measured against the search's own history, should act on a search over compositions. We introduce ANCHOR, a GRPO composition policy trained with multi-objective rewards around a frozen CSP model, and continuous adaptive novelty (CAN), a graded novelty score against known structures and a growing discovery history. Using the frozen CSP model as a fixed ruler under one evaluator, we test where adaptation should act. Replacing DNG compositions with ANCHOR's policy on the same CSP backbone raises MSUN from 11.4% to 47.6% and SUN from 1.1% to 22.1% at 99.9% formula uniqueness. Fine-tuning DNG models directly on the same rewards instead moves their composition marginal without raising their on-hull fraction. We show that KL-regularized fine-tuning of a DNG model can only reweight chemistry the pretrained model already supports by a bounded factor

## My notes

- 
