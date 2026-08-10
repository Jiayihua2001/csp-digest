---
title: "CrystalGRPO: Target-Aligned and Coverage-Preserving Reinforcement Learning for Flow-Based Crystal Structure Prediction"
date: 2026-08-06
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2608.06582v1
relevance: 90
significance: 8
tags:
  - CSP
  - generative-model
  - ML-potential
  - polymorphism
---

# CrystalGRPO: Target-Aligned and Coverage-Preserving Reinforcement Learning for Flow-Based Crystal Structure Prediction

**Authors:** [[Kaixiang Su]], [[Hongfei Xue]], [[Qiang Zhu]]
**Link:** https://arxiv.org/abs/2608.06582v1
**Scores:** relevance 90 / significance 8
**Field:** [[generative-model]] [[ML-potential]] [[polymorphism]]

## Why it matters
CrystalGRPO extends GRPO-style RL post-training to joint coordinate–lattice flow policies, combining energy with a StructureMatcher recovery reward and coverage-aware advantage to preserve Top-N diversity.

## Abstract
> Flow-based generative models can efficiently produce candidate structures for crystal structure prediction (CSP), but their pretrained objectives do not directly optimize downstream target recovery. Reinforcement-learning post-training offers a flexible solution, yet existing approaches rely primarily on energy rewards and coordinate-only stochastic policies. Predicted energy does not identify the reference polymorph, while reward-driven concentration can reduce the candidate coverage required for Top-N recovery. We introduce CrystalGRPO, a CSP-aligned post-training framework that extends existing ODE-to-SDE policy constructions to the joint coordinate--lattice state. CrystalGRPO combines MACE-predicted energy with a StructureMatcher-based recovery score and provides two operating modes: CrystalGRPO-Q, which prioritizes single-draw recovery, and CrystalGRPO-C, which combines full-trajectory reference regularization with a coverage-aware group advantage to preserve finite-budget target recovery. Across MP-20 and MPTS-52 with PXRDGen and OMatG backbones, both variants reduce one- and twenty-sample RMSE relative to coordinate-only reinforcement in all four backbone--dataset settings. 

## My notes

- 
