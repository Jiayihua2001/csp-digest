---
title: "Why Multi-Layer Message Passing Works: Completeness Theory for Graph Neural Network Interatomic Potentials"
date: 2026-09-01
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.00528v2
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# Why Multi-Layer Message Passing Works: Completeness Theory for Graph Neural Network Interatomic Potentials

**Authors:** [[Pingbing Ming]], [[Han Wang]]
**Link:** https://arxiv.org/abs/2609.00528v2
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Establishes the first completeness theorem proving that multi-layer message passing on sparse cutoff graphs matches full L-hop neighborhood expressivity, rigorously justifying universal approximation in DPA3 and CHGNet.

## Abstract
> We prove that the Hypergraph Neural Network, an invariant architecture with 3-body message passing, is a universal approximator for potential energy surfaces. Our main contribution is a multi-layer completeness theory. We show that $L$ layers of message passing on sparse, cutoff-based graphs achieve the same representational power as having access to the full $L$-hop neighborhood, provided the configurations are generic, satisfy an overlap condition and a connectivity condition. This provides the first rigorous justification for the common practice of using multi-layer message passing with a per-layer cutoff smaller than the physical interaction range, the setting used by virtually all practical graph neural network based machine-learned interatomic potentials. As immediate consequences, we show that both DPA3 and CHGNet architectures inherit universal approximation.

## My notes

- 
