---
title: "Riemannian Flow Models with Reinforcement Learning for Molecular Crystal Structure Prediction"
date: 2026-09-30
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.39773v1
relevance: 94
significance: 0
tags:
  - CSP
  - generative-model
  - polymorphism
  - conformational
  - space-group
---

# Riemannian Flow Models with Reinforcement Learning for Molecular Crystal Structure Prediction

**Authors:** [[Thomas Egg]], [[Harry Winston Sullivan]], [[Maya M. Martirossyan]]
**Link:** https://arxiv.org/abs/2609.39773v1
**Scores:** relevance 94 / significance 0
**Field:** [[generative-model]] [[polymorphism]] [[conformational]] [[space-group]]

## Why it matters
Introduces CG-OMatG, an equivariant Riemannian flow-based generative model using a rigid-body, coarse-grained hierarchical representation of molecules, fine-tuned via policy-gradient reinforcement learning to directly target low-energy molecular crystal pack

## Abstract
> Crystal structure governs material properties, making crystal structure prediction (CSP) a fundamental problem in materials science. Generative models are a promising approach for solving this problem, but the prevalence of polymorphism, coupled with large unit cells and complex packing geometry, makes the molecular CSP task challenging for existing models. To address this, we introduce Coarse-Grained Open Materials Generation (CG-OMatG), an equivariant Riemannian flow-based generative model. CG-OMatG predicts molecular crystal structures \textit{via} a coarse-grained, hierarchical representation. CG-OMatG treats molecules as rigid bodies---performing both inter- and intra-molecular message passing to construct a geometric representation for molecular packings---and learns to reconstruct molecule centroid positions, orientations, and lattice parameters, conditioned on chemical species and conformer geometry. We train the model on subsets of the Open Molecular Crystals (OMC25) and Cambridge Structural Database (CSD) datasets. Further, we fine-tune the model \textit{via} policy gradient reinforcement learning to steer the model towards generating low-energy candidate structures. We v

## My notes

- 
