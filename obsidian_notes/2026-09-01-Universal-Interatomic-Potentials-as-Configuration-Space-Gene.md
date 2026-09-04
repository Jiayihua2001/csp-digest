---
title: "Universal Interatomic
Potentials as Configuration-Space
Generators for One-Shot and Iterative Fine-Tuning of Ab Initio-Accurate
Material-Specific Models"
date: 2026-09-01
source: journal
venue: "The Journal of Physical
Chemistry Letters"
doi: 10.1021/acs.jpclett.6c02067
arxiv: 
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - benchmark
---

# Universal Interatomic
Potentials as Configuration-Space
Generators for One-Shot and Iterative Fine-Tuning of Ab Initio-Accurate
Material-Specific Models

**Authors:** [[Jonas Hänseroth]], [[Aaron Flötotto]], [[Christian Dreßler]]
**Link:** https://doi.org/10.1021/acs.jpclett.6c02067
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[benchmark]]

## Why it matters
Repurposes universal MLIPs' known PES-softening bias as a deliberate sampling tool to generate diverse configurations for one-shot/iterative DFT-relabeled fine-tuning into accurate material-specific potentials.

## Abstract
> Abstract Universal machine learning interatomic potentials (MLIPs) are rapidly becoming general-purpose tools for atomistic simulation, but their role in quantitative materials modeling when reactive events are involved remains unsettled. We compare five universal MLIPs across seven chemically diverse systems and find that strong performance on standard benchmarks does not guarantee accurate predictions of the target observables. In particular, zero-shot models do not reliably reproduce reactive, transport, or high-barrier processes, exemplified here in particular by the sulfur-vacancy jump in MoS2. We therefore benchmark a practical alternative against target observables: universal MLIPs are used to generate long molecular dynamics trajectories, the resulting configurations are subsampled and relabeled with DFT, and material-specific MLIPs are subsequently trained or fine-tuned on the resulting first-principles data sets. This workflow converts universal models into efficient configuration-space generators while retaining ab initio reference labels for training and turns their systematic softening of the potential energy surface from a liability into a sampling advantage. Across t

## My notes

- 
