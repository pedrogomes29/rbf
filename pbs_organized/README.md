# Benchmarking Set Reconciliation Algorithms

[![Build Status](https://travis-ci.com/long-gong/reconciliation-benchmark.svg?token=YfqHgcbyJqDSJGqLz6ea&branch=master)](https://travis-ci.com/long-gong/reconciliation-benchmark)

Source codes for all experiments conducted in our PBS paper.

## Repository Structure

    .
    ├── estimators            Source codes for various set-difference estimators
    ├── reconciliation        Source codes for various set-reconciliation algorithms
    └── set-generator         Source codes for generating sets

## Install Dependencies

```bash
chmod +x ./install_dependencies.sh && ./install_dependencies.sh
```

## Compile & Usage

Please refer to each of the three subfolders in this order: 
1. set-generator
2. estimators
3. reconciliation