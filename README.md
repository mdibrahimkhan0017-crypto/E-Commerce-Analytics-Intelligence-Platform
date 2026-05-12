# 📊 E-Commerce Analytics & Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/Tests-pytest-green)
![PEP8](https://img.shields.io/badge/Code%20Style-PEP8-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-%3E80%25-yellowgreen)

A production-grade analytics platform for e-commerce businesses, providing automated data ingestion, KPI computation, RFM/LTV customer segmentation, and multi-panel dashboard generation — all from a single command line.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    CLI / Streamlit UI                         │
├──────────────────────────────────────────────────────────────┤
│  Layer 4: VISUALISATION                                      │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Charts  │ │ Dashboard │ │ Exporter │ │ Report Composer│  │
│  └─────────┘ └───────────┘ └──────────┘ └───────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: ANALYTICS                                          │
│  ┌───────────────┐ ┌────────────┐ ┌────────────┐           │
│  │ KPI Calculator│ │ RFM Engine │ │ LTV Engine │           │
│  └───────────────┘ └────────────┘ └────────────┘           │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: QUERY ENGINE                                       │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────────┐   │
│  │ Query Engine │ │ Query Library │ │ 15 SQL Queries   │   │
│  └──────────────┘ └───────────────┘ └──────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Layer 1: INGESTION                                          │
│  ┌───────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐  │
│  │ Generator │ │  Loader  │ │ Validator │ │  Pipeline  │  │
│  └───────────┘ └──────────┘ └───────────┘ └────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Foundation: SQLite Database │ Config │ Logger │ Models      │
└──────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.10+**
- pip (package manager)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup project structure
python setup_project.py

# 3. Generate synthetic data (10,000 orders)
python -m src.cli generate --records 10000 --seed 42

# 4. Ingest data into the database
python -m src.cli ingest --source data/

# 5. Generate all reports
python -m src.cli report --type all --format png,pdf

# 6. (Optional) Launch interactive dashboard
streamlit run src/app.py
```

Or use the Makefile:

```bash
make all  # Runs: install → generate → ingest → report
```

## 🧪 Running Tests

```bash
# Run full test suite with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test module
pytest tests/test_models.py -v

# Validate installation
python scripts/validate_installation.py
```

## 📊 Dashboards Generated

| Dashboard | Panels | Description |
|-----------|--------|-------------|
| **Executive** | 6 panels (2×3) | KPI scorecard, revenue trend, top products, category pie, channel bar, MoM growth |
| **Product** | 4 panels (2×2) | Top/bottom products, return rates, revenue vs margin scatter |
| **Customer** | 4 panels (2×2) | RFM segments, LTV histogram, new vs returning, churn risk |
| **Sales Trends** | 3 panels (1×3) | Revenue, orders, and AOV time series |

## 📖 Documentation

- [User Guide](docs/USER_GUIDE.md) — End-user guide with CLI reference
- [Developer Guide](docs/DEVELOPER_GUIDE.md) — Architecture, extensibility, and contributing

## 🛠️ CLI Reference

```
ecommerce-analytics
├── generate     Generate synthetic data
├── ingest       Load data into the database
├── report       Generate analytical reports
├── query        Run a named or custom SQL query
├── schedule     Start the report scheduler
└── health       Run system health check
```

## 📝 License

MIT License
# E-Commerce-Analytics-Intelligence-Platform
