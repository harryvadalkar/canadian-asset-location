# Optimal Asset Location in the Canadian Registered Account System

**A Computational Search Across TFSA, RRSP, RESP, FHSA, and RDSP**

[![Tests](https://img.shields.io/badge/tests-194%20passing-brightgreen)]()
[![Experiments](https://img.shields.io/badge/experiments-19%2C934-blue)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This repository contains the complete code, data, and paper for a comprehensive computational analysis of optimal asset location across all six Canadian registered investment account types. Using a validated 2026 Canadian tax engine, we simulate **19,934 lifecycle experiments** across five household profiles, three provinces, and four market scenarios.

### Key Findings

| Finding | Detail |
|---------|--------|
| **Most important lever varies by household** | Contribution ordering dominates for lower-income accumulators (65% R²); asset location dominates for higher-income households (90% R²) |
| **TFSA-Heavy beats Conventional by 84–105%** | Pure tax-treatment effect, confirmed under equalized-return conditions |
| **Province explains < 0.3% of variance** | Strategy choice within any province matters ~100× more than province choice |
| **RDSP grant maximization: +$200K** | 300% CDSG match produces outsized returns for DTC-eligible individuals |

---

## Repository Structure

```
canadian-asset-location/
├── src/                              # Tax engine and experiment runner
│   ├── prepare.py                    # Module 1: Federal tax engine (35 tests)
│   ├── prepare_provincial.py         # Module 2: Provincial tax — AB, ON, BC (32 tests)
│   ├── prepare_accounts.py           # Module 3: Account rules — all 6 types (42 tests)
│   ├── prepare_clawbacks.py          # Module 4: OAS/GIS/CCB/GST clawbacks (31 tests)
│   ├── prepare_integration.py        # Module 5: Unified pipeline (32 tests)
│   ├── strategy.py                   # Strategy space + lifecycle simulator (22 tests)
│   └── autoresearch_v2.py            # AutoResearch agent — runs all experiments
├── data/
│   └── experiment_results_v2.csv     # All 19,934 experiment results
├── paper/
│   ├── paper_submission.md           # Full paper (markdown, ~11,000 words)
│   └── figures/                      # Publication-quality figures (300 DPI)
├── run_tests.py                      # Test runner — validates all 194 tests
├── requirements.txt
├── LICENSE                           # MIT License
├── ERRATA.md                         # Corrections log
└── README.md
```

---

## Replication Instructions

### Prerequisites

- **Python 3.10 or later** (tested on 3.11 and 3.12)
- No external packages required for the tax engine and experiments
- `matplotlib` and `numpy` needed only for figure generation

### Step 1: Clone

```bash
git clone https://github.com/[YOUR-USERNAME]/canadian-asset-location.git
cd canadian-asset-location
```

### Step 2: Run All 194 Tests

```bash
python run_tests.py
```

Expected output:
```
TOTAL: 194/194 tests in 0.9s
ALL TESTS PASSED
```

### Step 3: Reproduce the Full 19,934-Experiment Sweep

```bash
cd src
python autoresearch_v2.py
```

Runs all 7 stages in ~50 seconds. Output: `experiment_results_v2.csv`.

### Step 4: Verify Against Published Results

Compare against `data/experiment_results_v2.csv`:

| Metric | Expected |
|--------|----------|
| Total rows | 19,934 |
| Young pro best PV (base, AB) | $1,137,793 |
| Peak earner best PV (base, AB) | $1,643,028 |
| RDSP Grant-Max avg PV | $248,355 |
| Province spread | 2.6% |

### Step 5: Run Individual Modules

```bash
cd src
python prepare.py               # Federal tax: 35 tests
python prepare_provincial.py     # Provincial: 32 tests
python prepare_accounts.py       # Accounts: 42 tests
python prepare_clawbacks.py      # Clawbacks: 31 tests
python prepare_integration.py    # Integration: 32 tests
python strategy.py               # Strategy: 22 tests
```

---

## Tax Engine Architecture

| Module | Tests | Coverage |
|--------|-------|---------|
| Federal Tax | 35 | 5 brackets (14–33%), BPA, capital gains (flat 50%), dividends, CPP/CPP2/EI, pension splitting |
| Provincial Tax | 32 | AB (6 brackets), ON (5 + surtax + health premium), BC (7 + low-income reduction) |
| Account Rules | 42 | TFSA, RRSP/RRIF, RESP (CESG/CLB), FHSA, RDSP (CDSG/CDSB), Non-Reg ACB |
| Clawbacks | 31 | OAS (15%), GIS (50%), CCB, GST/HST credit, ON/BC provincial |
| Integration | 32 | Unified pipeline, per-account returns, terminal wealth |

### Key 2026 Parameters

- Federal lowest bracket: **14%** (reduced from 15%)
- Capital gains inclusion: **flat 50%** (Budget 2024 two-tier not enacted)
- Alberta: **6 graduated brackets** (8–15%), not flat
- BC first bracket: **5.6%** (2026 Budget)

---

## Data Dictionary

| Column | Description |
|--------|------------|
| `id` | Experiment number (1–19,934) |
| `tag` | Stage: `grid`, `sr_10`–`sr_25`, `oas_0`–`oas_5`, `cpp_60`–`cpp_70`, `mc`, etc. |
| `profile` | `young_pro`, `mid_career`, `peak_earner`, `retiree`, `disabled` |
| `province` | `AB`, `ON`, `BC` |
| `contribution` | `conventional`, `fhsa_first`, `tfsa_heavy`, `grant_max`, `bracket_aware`, `hybrid` |
| `location` | `conventional`, `us_in_rrsp`, `bonds_everywhere`, `growth_everywhere`, `tax_optimized`, `reits_sheltered` |
| `withdrawal` | `nonreg_first`, `rrif_meltdown`, `oas_preservation`, `tfsa_last`, `early_rrif`, `balanced_draw` |
| `market` | `base`, `bull`, `bear`, `stochastic` |
| `tw_pv` | Terminal wealth PV-discounted at 3% real |
| `lifetime_tax` | Total income tax paid over lifecycle |
| `lifetime_benefits` | Total government benefits received |

---

## Citation

```bibtex
@article{author2026assetlocation,
  title={Optimal Asset Location in the Canadian Registered Account System:
         A Computational Search Across {TFSA}, {RRSP}, {RESP}, {FHSA}, and {RDSP}},
  author={[Author Name]},
  year={2026}
}
```

## License

MIT License. See [LICENSE](LICENSE).
