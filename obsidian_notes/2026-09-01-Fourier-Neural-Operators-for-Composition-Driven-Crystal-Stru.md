---
title: "Fourier Neural Operators for Composition-Driven Crystal Structure Discovery"
date: 2026-09-01
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.00900v1
relevance: 70
significance: 0
tags:
  - CSP
  - generative-model
  - ML-potential
---

# Fourier Neural Operators for Composition-Driven Crystal Structure Discovery

**Authors:** [[Zhijie Yu]], [[Jingyu Li]], [[Yang Huang]]
**Link:** https://arxiv.org/abs/2609.00900v1
**Scores:** relevance 70 / significance 0
**Field:** [[generative-model]] [[ML-potential]]

## Why it matters
Introduces a Fourier Neural Operator crystal-field solver—mapping composition and lattice parameters directly to periodic density fields—paired with a CVAE generator to overcome local-receptive-field and posterior-collapse limits of voxel-based CSP methods.

## Abstract
> Crystalline materials discovery is essential for energy, electronics, and catalysis, but the vast chemical and structural space makes exhaustive screening infeasible. Existing voxel-based methods are limited by the local receptive fields of three-dimensional convolutional neural networks and the posterior collapse of high-dimensional variational autoencoders. Here, we develop a Fourier Neural Operator (FNO)-based crystal-field solver that maps a prescribed chemical formula and lattice parameters to periodic number-density and electron-density fields. By operating on global Fourier modes, the solver captures long-range correlations in periodic crystal fields beyond conventional local convolutions. Building on this solver, we construct a coupled generation-solving framework in which a conditional variational autoencoder generates diverse candidate lattice parameters in a low-dimensional basis-coefficient space, followed by density-field prediction and atomic reconstruction through peak detection, position optimization, and weight optimization. The reconstructed structures are further screened using voxel-level filtering, machine-learning interatomic-potential relaxation, and first-pr

## My notes

- 
