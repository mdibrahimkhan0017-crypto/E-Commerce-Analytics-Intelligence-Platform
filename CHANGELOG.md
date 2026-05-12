# Changelog

All notable changes to the E-Commerce Analytics & Intelligence Platform.

## [1.0.0] — 2026-05-13

### Added

1. **Project Scaffold** — Complete directory structure with `setup_project.py`, `config.yaml`, `.env.example`, and `requirements.txt`.

2. **Data Models** — Python dataclasses for Customer, Product, Order, and OrderItem with comprehensive `validate()` methods.

3. **Database Schema** — SQLite schema with 4 tables, foreign keys, check constraints, 8 indexes, and a `v_order_summary` view.

4. **DatabaseManager** — Connection management with retry logic, schema auto-initialization, and context manager support.

5. **Data Generator** — Faker-powered synthetic data with seasonal uplift (2.5× Nov/Dec), weekend uplift (1.3×), promotional spikes (4×), and log-normal price distributions.

6. **DataLoader** — Unified loader supporting CSV (BOM-safe), JSON (records/lines auto-detect), and SQLite sources.

7. **Schema Validator** — Per-table validation rules with referential integrity checks, structured JSON error logging, and validation summaries.

8. **Ingestion Pipeline** — Orchestrated data loading with dataclass validation, incremental mode, dry-run mode, and batch error recovery.

9. **Query Engine** — Parameterised SQL execution with timeout enforcement, automatic type-casting, and export capabilities (CSV/JSON/Parquet).

10. **15 SQL Queries** — Revenue by period, MoM growth, top/bottom products, category performance, customer orders, new vs returning, cohort retention, channel performance, refund analysis, daily summary, inventory velocity, discount impact, customer segments, and geographic revenue.

11. **Query Library** — Typed wrapper methods with parameter validation for all 15 queries.

12. **KPI Calculator** — Sales, product, customer, and time-series KPIs with period comparison helpers and `KPIResult` dataclass.

13. **RFM Engine** — Quintile-based RFM scoring with rule-based segmentation (Champions, Loyal, Potential, At Risk, Hibernating, Lost), churn risk identification, and CSV export.

14. **LTV Engine** — Historical and projected LTV with retention-based probability modelling, segment-level analysis, and channel analysis.

15. **Visualisation System** — 8 chart types (Line, Bar, Pie, Scatter, Heatmap, Histogram, BoxPlot, StackedBar) with ChartTheme, BaseChart abstraction, and ChartFactory.

16. **Dashboard Composer** — 4 multi-panel dashboards (Executive 2×3, Product 2×2, Customer 2×2, Sales Trends 1×3) with KPI scorecards, watermarks, and timestamps.

17. **Report Exporter** — Multi-format figure and DataFrame export (PNG/PDF/SVG, CSV/JSON/XLSX) with batch operations and JSON manifests.

18. **CLI Interface** — Click-based command groups (generate, ingest, report, query, schedule, health) with --verbose/--quiet flags and user-friendly error handling.

19. **Report Scheduler** — On-demand and scheduled (daily/weekly) pipeline execution with health checks (database, data availability, output directory).

20. **Streamlit Dashboard** — Interactive web interface with date range pickers, report type selector, KPI metrics row, dashboard rendering, and downloadable data tables.

### Infrastructure

- Structured JSON logging with rotation (5 files × 10 MB)
- Retry decorator for resilient database operations
- Pre-commit hooks (flake8, trailing whitespace, end-of-file)
- pytest configuration with 80% coverage enforcement
- Full test suite: 14 test modules covering models, generator, loader, validator, query engine, query library, KPIs, RFM, LTV, charts, dashboards, exporter, CLI, scheduler, resilience, and integration
- Makefile with install, generate, ingest, report, test, lint, clean targets
- Complete documentation (README, User Guide, Developer Guide)
- Installation validation script
