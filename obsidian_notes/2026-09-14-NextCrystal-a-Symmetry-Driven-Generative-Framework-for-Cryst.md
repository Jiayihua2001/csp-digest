---
title: "NextCrystal: a Symmetry-Driven Generative Framework for Crystal Structure Prediction"
date: 2026-09-14
source: journal
venue: "Chinese Physics Letters"
doi: 10.1088/0256-307x/43/10/100802
arxiv: 
relevance: 90
significance: 8
tags:
  - CSP
  - generative-model
---

# NextCrystal: a Symmetry-Driven Generative Framework for Crystal Structure Prediction

**Authors:** [[Jinming Mu]], [[Lixin He]], [[Xudong Zhu]]
**Link:** https://doi.org/10.1088/0256-307x/43/10/100802
**Scores:** relevance 90 / significance 8
**Field:** [[generative-model]]

## Why it matters
NextCrystal introduces a language-model-driven, template-free generator that directly predicts Wyckoff site patterns via linear-complexity beam search, enforcing exact symmetry-stoichiometry consistency within a diffusion backbone.

## Abstract
> Abstract Crystal structure prediction (CSP), which aims to predict the 3D atomic arrangement of a crystal from its composition, is central to materials discovery and mechanistic understanding. Crystal symmetry plays a crucial role in CSP, but given the composition in a unit cell, existing methods either struggle with the NP-hard combinatorial challenge of enforcing symmetry rigorously or rely on retrieving known templates, inherently limiting both physical fidelity and the discovery of genuinely new materials. To address this challenge, we introduce NextCrystal, a symmetry-driven generative framework that employs language models to encode chemical semantics and directly generate fine-grained Wyckoff site patterns from atomic stoichiometry, without retrieving pre-existing structural templates at inference. To overcome the combinatorial complexity of site assignments, we incorporate domain knowledge via an efficient, linear-complexity heuristic beam search, rigorously enforcing algebraic consistency between site multiplicities and atomic stoichiometry. By integrating this symmetry-consistent template into a diffusion backbone, the framework constrains the stochastic generative trajec

## My notes

- 
