---
title: "Packora: Systematic Design for Generative Molecular Crystal Structure Prediction"
date: 2026-08-27
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2608.26962v1
relevance: 92
significance: 0
tags:
  - CSP
  - generative-model
  - ML-potential
  - cocrystal-salt
  - conformational
---

# Packora: Systematic Design for Generative Molecular Crystal Structure Prediction

**Authors:** [[Nayoung Kim]], [[Kiyoung Seong]], [[Sungsoo Ahn]]
**Link:** https://arxiv.org/abs/2608.26962v1
**Scores:** relevance 92 / significance 0
**Field:** [[generative-model]] [[ML-potential]] [[cocrystal-salt]] [[conformational]]

## Why it matters
Packora introduces a flow-based generative model jointly predicting atoms and lattice from molecular graphs, supporting multi-component/organometallic crystals with flexible conditioning, plus a systematic architecture/training study.

## Abstract
> Molecular crystal structure prediction (CSP) is important in pharmaceuticals, agrochemicals, and organic electronics, where subtle differences in molecular conformation and packing can strongly affect material properties. We present Packora, a flow-based generative model for molecular CSP that jointly predicts atomic coordinates and the lattice from molecular graphs. Packora supports multi-component and organometallic crystals and can condition on any subset of molecular conformers, stereochemical labels, and space-group information within a single model. Inspired by the CCDC CSP blind test, we evaluate generation and ranking separately, using generation to isolate generator quality and ranking to measure end-to-end performance under a common relaxation and ranking pipeline. We also systematically study architecture, training, conditioning, inference, and scaling, identifying an effective design based on cacheable pairwise reasoning, training objective and numerical solver choices, conditioning dropout, and balanced scaling of pairwise and single representations. Packora outperforms the baselines on both structure generation and ranking benchmarks, achieving the best matched-budget

## My notes

- 
