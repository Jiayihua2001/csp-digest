---
title: "What an SO(3) orientation flow can and cannot learn in molecular-crystal structure prediction"
date: 2026-09-04
source: ChemRxiv
venue: "ChemRxiv"
doi: 10.26434/chemrxiv.15008279/v1
arxiv: 
relevance: 76
significance: 0
tags:
  - CSP
  - conformational
  - space-group
---

# What an SO(3) orientation flow can and cannot learn in molecular-crystal structure prediction

**Authors:** [[Frank Cai]]
**Link:** https://doi.org/10.26434/chemrxiv.15008279/v1
**Scores:** relevance 76 / significance 0
**Field:** [[conformational]] [[space-group]]

## Why it matters
Introduces SymMC-Flow, a space-group-conditioned rigid-body flow diagnosing that absolute molecular orientation is unlearnable, but re-gauging to isolate the space-group-determined relative rotation enables 13.7% exact multi-copy packing re

## Abstract
> Rigid-body factorization is an appealing route to molecular-crystal structure prediction: freezing each molecule’s conformer reduces a crystal to a lattice, a set of fractional centroids on the torus T3, and a per-molecule orientation on SO(3). Whether the orientation field is actually learnable on real molecular crystals has not been examined. We introduce SymMC-Flow, a space-groupconditioned rigid-body flow on lattice×T3×SO(3), used as a diagnostic study on 1,127 crystals from the Cambridge Structural Database. The lattice and centroid flows learn normally, but the absolute per-molecule orientation flow remains at its predict-zero floor. We trace this to a decomposition of the orientation target, Rm = rot(gm) · Rasym, into a space-group-determined relative rotation between symmetry copies and the asymmetric unit’s gauge-arbitrary free orientation, which is not learnable from composition and packing; the relative part is. Re-gauging to cancel the free part lifts held-out non-reference orientation loss by 27% (versus ∼0% for the absolute target) and reconstructs 13.7% (mean over three seeds) of held-out multi-copy packings exactly under StructureMatcher, against 0% for the predict-

## My notes

- 
