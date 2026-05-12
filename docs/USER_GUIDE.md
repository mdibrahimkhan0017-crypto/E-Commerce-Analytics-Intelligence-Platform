# User Guide — E-Commerce Analytics Platform

## Prerequisites

- **Python 3.10 or later** (verify with `python3 --version`)
- **pip** package manager

### Installation

```bash
cd ecommerce
pip install -r requirements.txt
python setup_project.py
```

## Quick Start (3 Commands)

```bash
# Step 1: Generate synthetic data
python -m src.cli generate --records 10000 --seed 42

# Step 2: Ingest into database
python -m src.cli ingest --source data/

# Step 3: Generate reports
python -m src.cli report --type all --start 2023-01-01 --end 2024-12-31
```

Reports are saved to `reports/` as PNG and PDF files.

## Full CLI Reference

### `generate` — Generate Synthetic Data

```bash
python -m src.cli generate [OPTIONS]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--records` | INT | 10000 | Number of orders to generate |
| `--start` | TEXT | 2 years ago | Start date (YYYY-MM-DD) |
| `--end` | TEXT | today | End date (YYYY-MM-DD) |
| `--seed` | INT | None | Random seed for reproducibility |
| `--output-dir` | TEXT | data/ | Output directory for CSV files |

**Example:**
```bash
python -m src.cli generate --records 50000 --start 2022-01-01 --end 2024-12-31 --seed 42
```

### `ingest` — Load Data into Database

```bash
python -m src.cli ingest [OPTIONS]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--source` | TEXT | data/ | Path to data directory |
| `--incremental` | FLAG | False | Skip existing records |

### `report` — Generate Reports

```bash
python -m src.cli report [OPTIONS]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--type` | TEXT | all | Report type: all, executive, product, customer, sales |
| `--start` | TEXT | 1 year ago | Start date |
| `--end` | TEXT | today | End date |
| `--format` | TEXT | png | Output formats (comma-separated: png,pdf,svg) |
| `--output-dir` | TEXT | reports/ | Output directory |

### `query` — Run SQL Queries

```bash
python -m src.cli query --name 01_revenue_by_period \
  --params '{"start_date":"2023-01-01","end_date":"2024-12-31","period":"month"}'
```

| Flag | Type | Description |
|------|------|-------------|
| `--name` | TEXT | Named query from the query library |
| `--file` | TEXT | Path to a custom .sql file |
| `--params` | TEXT | JSON string of query parameters |
| `--export` | TEXT | Export format: csv or json |

### `schedule` — Report Scheduler

```bash
python -m src.cli schedule --mode daily --hour 6
```

### `health` — System Health Check

```bash
python -m src.cli health
```

## Configuration Guide

All settings are in `config.yaml`:

| Section | Key | Default | Valid Range | Description |
|---------|-----|---------|-------------|-------------|
| database | db_path | db/ecommerce.db | Any valid path | SQLite database file path |
| reports | output_dir | reports/ | Any valid dir | Report output directory |
| reports | dpi | 150 | 72–300 | Chart resolution |
| reports | figsize | [14, 8] | [w, h] in inches | Default figure size |
| theme | primary_color | #2E86AB | Any hex colour | Brand accent colour |
| theme | font_family | DejaVu Sans | System font | Chart font family |
| theme | palette | 6 hex colours | List of hex | Multi-series colour palette |
| pipeline | chunk_size | 1000 | 100–50000 | DB insert batch size |
| pipeline | query_timeout_sec | 30 | 5–300 | Max query execution time |
| pipeline | log_level | INFO | DEBUG/INFO/WARNING/ERROR | Log verbosity |

## Dashboard Descriptions

### Executive Dashboard
- **KPI Scorecard**: Revenue, orders, AOV, growth, refund rate
- **Revenue Trend**: Monthly revenue line chart
- **Top 10 Products**: Horizontal bar chart of best sellers
- **Category Split**: Pie chart of revenue by category
- **Channel Revenue**: Bar chart of sales channels
- **MoM Growth**: Month-over-month growth rate bars

### Product Dashboard
- **Top/Bottom Products**: Revenue comparison
- **Return Rate by Category**: Category-level return analysis
- **Revenue vs Margin**: Scatter plot with bubble sizing

### Customer Dashboard
- **RFM Segments**: Customer segment distribution
- **LTV Distribution**: Projected lifetime value histogram
- **New vs Returning**: Stacked bar of customer acquisition
- **Churn Risk**: List of at-risk customers

### Sales Trend Dashboard
- **Revenue/Orders/AOV**: Time series at selected granularity

## Troubleshooting

| # | Error | Fix |
|---|-------|-----|
| 1 | `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| 2 | `FileNotFoundError: config.yaml` | Ensure you're in the project root |
| 3 | `sqlite3.OperationalError: no such table` | Run `python -m src.cli ingest --source data/` |
| 4 | Empty reports | Generate data first: `python -m src.cli generate` |
| 5 | `ValueError: DPI must be >= 72` | Check config.yaml reports.dpi |
| 6 | Charts not rendering | Ensure matplotlib backend is available |
| 7 | Permission denied on reports/ | Check directory write permissions |
| 8 | `QueryTimeoutError` | Increase `pipeline.query_timeout_sec` in config |
| 9 | Slow ingestion | Increase `pipeline.chunk_size` |
| 10 | Streamlit not loading | Ensure `streamlit` is installed and DB has data |
