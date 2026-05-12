# Developer Guide — E-Commerce Analytics Platform

## Project Structure

```
ecommerce/
├── data/                          # Raw CSV input files
├── db/                            # SQLite database files
├── reports/                       # Generated charts, PDFs, manifests
├── logs/                          # Pipeline and validation log files
├── docs/                          # User and developer documentation
├── scripts/                       # Utility scripts (validation, etc.)
├── src/
│   ├── ingestion/                 # Data loading and validation
│   │   ├── models.py              # Dataclass definitions + validation
│   │   ├── data_generator.py      # Synthetic data generator (Faker)
│   │   ├── loader.py              # CSV/JSON/SQLite unified loader
│   │   ├── validator.py           # Schema validation engine
│   │   └── pipeline.py            # Ingestion orchestrator
│   ├── db/                        # Database layer
│   │   ├── schema.sql             # DDL for all tables, indexes, views
│   │   └── database.py            # DatabaseManager class
│   ├── engine/                    # SQL query engine
│   │   ├── query_engine.py        # Parameterised query execution
│   │   ├── query_library.py       # Typed wrappers for all queries
│   │   ├── exceptions.py          # Custom exception types
│   │   └── queries/               # 15 parameterised .sql files
│   ├── analytics/                 # Business analytics modules
│   │   ├── kpi_calculator.py      # Sales/product/customer KPIs
│   │   ├── rfm_engine.py          # RFM segmentation engine
│   │   └── ltv_engine.py          # Customer LTV modelling
│   ├── visualisation/             # Chart and report generation
│   │   ├── theme.py               # Matplotlib theme manager
│   │   ├── base_chart.py          # Abstract base chart class
│   │   ├── charts/                # 8 chart type implementations
│   │   ├── chart_factory.py       # Chart type registry/factory
│   │   ├── dashboard.py           # Multi-panel dashboard composer
│   │   ├── exporter.py            # Figure/DataFrame exporter
│   │   └── report_composer.py     # Full report package generator
│   ├── utils/                     # Shared utilities
│   │   ├── logger.py              # Structured JSON logger
│   │   └── retry.py               # Retry decorator
│   ├── scheduler.py               # Report scheduling engine
│   ├── cli.py                     # Click CLI interface
│   └── app.py                     # Streamlit web dashboard
├── tests/                         # pytest test suite
├── config.yaml                    # Central configuration
├── requirements.txt               # Python dependencies
├── Makefile                       # Build/run targets
├── pytest.ini                     # Test configuration
├── pyproject.toml                 # Project metadata
└── .flake8                        # Linting configuration
```

## How to Add a New SQL Query

1. **Create the SQL file** in `src/engine/queries/`:
   ```sql
   -- 16_my_new_query.sql
   -- Description of what this query does
   -- Params: :param1, :param2
   SELECT ... FROM ... WHERE col = :param1;
   ```

2. **Add a wrapper method** in `src/engine/query_library.py`:
   ```python
   def my_new_query(self, param1: str, param2: int) -> pd.DataFrame:
       """Description."""
       return self.engine.run_named_query(
           "16_my_new_query", {"param1": param1, "param2": param2}
       )
   ```

3. **Write a test** in `tests/test_query_library.py`:
   ```python
   def test_my_new_query(self, query_library):
       df = query_library.my_new_query("value", 10)
       assert not df.empty
   ```

## How to Add a New Chart Type

1. **Create the chart class** in `src/visualisation/charts/my_chart.py`:
   ```python
   from src.visualisation.base_chart import BaseChart

   class MyChart(BaseChart):
       def render(self, data, **kwargs):
           if data.empty:
               return self._empty_figure()
           fig, ax = plt.subplots(figsize=self.figsize)
           # ... render logic ...
           return fig
   ```

2. **Register in the factory** (`src/visualisation/chart_factory.py`):
   ```python
   from src.visualisation.charts.my_chart import MyChart
   CHART_REGISTRY["my_chart"] = MyChart
   ```

3. **Write tests** in `tests/test_charts.py`.

## How to Add a New KPI

1. **Write the SQL query** (see above).
2. **Add a method** to `src/analytics/kpi_calculator.py`:
   ```python
   def my_new_kpi(self, start_date, end_date) -> dict:
       df = self.query_lib.my_new_query(start_date, end_date)
       return {"metric_name": computed_value}
   ```
3. **Include in `generate_kpi_report()`**.
4. **Write tests** in `tests/test_kpi_calculator.py`.

## Running Tests

```bash
# Full suite with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific module
pytest tests/test_models.py -v

# Integration test only
pytest tests/test_integration.py -v

# With verbose output
pytest tests/ -v --tb=short
```

Coverage must be ≥80% (enforced by `pytest.ini`).

## Code Quality

```bash
# Lint check
flake8 src/ --max-line-length=100

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Contributing Guidelines

1. **Branch naming**: `feature/description` or `fix/description`
2. **Code style**: PEP-8, 100-char line limit, Google-style docstrings
3. **Type hints**: All function signatures must have parameter and return types
4. **Tests**: Every new function needs a corresponding test
5. **Coverage**: Must maintain ≥80% coverage
6. **Documentation**: Update relevant docs when adding features
