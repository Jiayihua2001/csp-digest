---
title: "EP-Flow: Disordered Crystal Structure Prediction without Site-Level Annotations"
date: 2026-10-01
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.01315v1
relevance: 80
significance: 0
tags:
  - CSP
  - generative-model
---

# EP-Flow: Disordered Crystal Structure Prediction without Site-Level Annotations

**Authors:** [[Qiuliang Liu]], [[Liming Wu]], [[Qi Li]]
**Link:** https://arxiv.org/abs/2610.01315v1
**Scores:** relevance 80 / significance 0
**Field:** [[generative-model]]

## Why it matters
Introduces EP-Flow, a flow-matching framework using a novel Occupancy Distribution Matrix and Sinkhorn-based transportation-polytope canonicalization to predict disordered crystal structures directly from chemical formulas without site-level annotations.

## Abstract
> Generative models have made rapid progress in ordered crystal structure prediction, yet many functional materials are intrinsically disordered, with substitutional mixing, vacancies, or interstitial species controlling their properties. Existing crystal generators either assume deterministic site occupations or require site-level disorder annotations, which are often unavailable when the chemical formula is the primary input. We formulate disordered crystal structure prediction through an Occupancy Distribution Matrix (ODM), a continuous site-by-species representation that unifies ordered crystals, solid solutions, vacancy disorder, and interstitial occupancy. A valid ODM must satisfy coupled site-wise occupancy, mass-conservation, and non-negativity constraints, placing each sample on a formula-dependent transportation polytope. We propose Entropic Polytope Flow (EP-Flow), a marginal-constrained flow matching framework that canonicalizes heterogeneous polytopes into a shared double-centered space, learns a marginal-preserving flow, and recovers feasible occupancies through a Sinkhorn inverse map. By jointly generating occupancies, fractional coordinates, and lattice parameters, EP

## My notes

- 
