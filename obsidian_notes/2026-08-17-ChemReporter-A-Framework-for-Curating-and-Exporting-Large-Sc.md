---
title: "ChemReporter: A Framework for Curating and Exporting Large-Scale Chemical Datasets for MLIP Training"
date: 2026-08-17
source: arXiv
venue: "arXiv"
doi: 
arxiv: 2608.16418v1
relevance: 70
significance: 0
tags:
  - CSP
  - ML-potential
---

# ChemReporter: A Framework for Curating and Exporting Large-Scale Chemical Datasets for MLIP Training

**Authors:** [[Marie Bluntzer]], [[Jules Tilly]], [[Christoph Brunken]]
**Link:** https://arxiv.org/abs/2608.16418v1
**Scores:** relevance 70 / significance 0
**Field:** [[ML-potential]]

## Why it matters
Introduces ChemReporter, a modular processing–query–export pipeline that converts heterogeneous molecular/materials datasets into a unified Parquet repository for flexible, criteria-based subsampling and direct HDF5 export for MLIP training.

## Abstract
> Training set quality and diversity are key determinants of the reliability of machine learning interatomic potentials (MLIPs), yet using massive datasets in full is often impractical and redundant, making intelligent data selection essential. A major bottleneck, however, is the lack of infrastructure for uniformly accessing, curating, and subsampling heterogeneous large-scale chemical datasets, which differ widely in structure, metadata, and file format. We address this gap with ChemReporter, a modular, method-agnostic framework that converts arbitrary molecular and materials datasets into a unified, queryable representation and exports the results directly into MLIP-ready training data. ChemReporter operates in three decoupled stages: processing, which parses raw datasets into a partitioned Apache Parquet repository enriched with structural, physical, and chemical metadata; querying, which filters and samples this repository via a CLI or Python API using arbitrary selection criteria, from simple physical constraints to custom, user-defined strategies; and exporting, which streams the selected subset into an HDF5 file ready for direct use in modern MLIP training frameworks. Through

## My notes

- 
