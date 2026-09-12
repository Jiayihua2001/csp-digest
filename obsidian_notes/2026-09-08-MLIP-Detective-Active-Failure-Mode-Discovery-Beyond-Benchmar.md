---
title: "MLIP Detective: Active Failure Mode Discovery Beyond Benchmark Scores for Machine-Learning Interatomic Potentials"
date: 2026-09-08
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2609.08399v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
  - benchmark
---

# MLIP Detective: Active Failure Mode Discovery Beyond Benchmark Scores for Machine-Learning Interatomic Potentials

**Authors:** [[Ryuhei Okuno]], [[Nontawat Charoenphakdee]], [[Kaoru Hisama]]
**Link:** https://arxiv.org/abs/2609.08399v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]] [[benchmark]]

## Why it matters
Introduces MLIP Detective, an agentic framework that generates and screens physics-informed failure hypotheses for universal MLIPs, autonomously uncovering a systematic MACE-MPA-0 anomaly beyond standard benchmarks.

## Abstract
> Universal machine-learning interatomic potentials (u-MLIPs) aim to generalize across diverse configurations. Benchmarks enable reproducible evaluation but may not expose failures outside their predefined scope. Here, we show that physics-informed search can complement benchmark-based evaluation by uncovering hidden failure modes. We introduce MLIP Detective, an agentic framework for active failure mode discovery. Starting from benchmark evidence, MLIP Detective generates falsifiable, physics-informed failure hypotheses, screens them with inexpensive simulations, and escalates only the most suspicious cases to human experts together with proposed verification protocols. Without issue-specific prompting, MLIP Detective identified and characterized a systematic anomaly in MACE-MPA-0: the model predicted some relaxed adsorbate-surface systems involving O- or F-containing adsorbates to be higher in energy than their corresponding separated fragments. Using cross-model comparisons, MLIP Detective further inferred a likely training-data origin for the anomaly, consistent with recent reports.

## My notes

- 
