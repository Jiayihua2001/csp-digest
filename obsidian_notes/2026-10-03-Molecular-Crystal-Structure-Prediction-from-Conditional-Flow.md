---
title: "Molecular Crystal Structure Prediction from Conditional Flow on the Unit Cells"
date: 2026-10-03
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2610.04193v1
relevance: 90
significance: 8
tags:
  - CSP
  - space-group
---

# Molecular Crystal Structure Prediction from Conditional Flow on the Unit Cells

**Authors:** [[Qiang Zhu]], [[Yihan Weng]]
**Link:** https://arxiv.org/abs/2610.04193v1
**Scores:** relevance 90 / significance 8
**Field:** [[space-group]]

## Why it matters
Introduces a conditional flow model predicting invariant lattice descriptors (from molecular graph, Hall setting, Z') to decouple symmetry, unit cell, and packing in molecular CSP, achieving 83/84 experimental matches.

## Abstract
> A molecular crystal structure is jointly described by its space group symmetry, unit cell, and the molecular alignment within the asymmetric unit. Concurrently predicting all three variables is a daunting task, as it mixes discrete symmetry choices with a high-dimensional search in the continuous space. To address this challenge, we decouple these variables using a three-step generation process. Specifically, we train a flow model to learn the conditional distribution of invariant lattice descriptors (e.g. direct- and reciprocal-lattice successive minima and Selling scalars) from a molecular graph, a Hall setting, and the number of molecules in the asymmetric unit ($Z'$). Using a two sequential quasi-random sampling processes, we first reconstruct the cell parameters that match the predicted lattice invariants and density requirements, and then conduct a molecular packing search within the give symmetry and unit cell constraint. On 84 single-component systems with $Z' \le 1$, our approach reproduces experimental matches for 83 systems; the remaining failure stems from force-field limitations in preserving the experimental structure. These results demonstrate that learned cell propo

## My notes

- 
