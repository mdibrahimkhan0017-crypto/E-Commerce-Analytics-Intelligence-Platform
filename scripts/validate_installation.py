#!/usr/bin/env python3
"""Installation validation script.

Runs all health checks, generates synthetic data, and exercises
the full analytics pipeline to verify the installation is complete.

Usage:
    python scripts/validate_installation.py
"""

import sys
import time
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_check(name: str, func) -> bool:
    """Run a single check and print result.

    Args:
        name: Human-readable check name.
        func: Callable returning True on success.

    Returns:
        True if check passed, False otherwise.
    """
    try:
        result = func()
        icon = "✓" if result else "✗"
        print(f"  {icon} {name}")
        return result
    except Exception as exc:
        print(f"  ✗ {name}: {exc}")
        return False


def check_imports() -> bool:
    """Verify all required packages are importable."""
    import pandas
    import numpy
    import matplotlib
    import faker
    import click
    import yaml
    return True


def check_database() -> bool:
    """Verify database connectivity and schema."""
    from src.db.database import DatabaseManager
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(db_path=f"{tmp}/validate.db")
        db.connect()
        assert db.table_exists("customers")
        assert db.table_exists("orders")
        db.close()
    return True


def check_data_generation() -> bool:
    """Generate 1,000 synthetic records."""
    from src.ingestion.data_generator import DataGenerator
    gen = DataGenerator(
        n_customers=100, n_products=30, n_orders=1000, seed=42,
    )
    data = gen.generate_all()
    assert len(data["customers"]) == 100
    assert len(data["orders"]) == 1000
    return True


def check_full_pipeline() -> bool:
    """Run the complete analytics pipeline."""
    import tempfile
    from src.db.database import DatabaseManager
    from src.ingestion.data_generator import DataGenerator
    from src.engine.query_engine import QueryEngine
    from src.engine.query_library import QueryLibrary
    from analytics.kpi_calculator import KPICalculator
    from src.analytics.rfm_engine import RFMEngine
    from src.analytics.ltv_engine import LTVEngine

    with tempfile.TemporaryDirectory() as tmp:
        db = DatabaseManager(db_path=f"{tmp}/validate.db")
        db.connect()

        gen = DataGenerator(
            n_customers=50, n_products=20, n_orders=500, seed=42,
        )
        gen.generate_all()
        gen.to_sqlite(db)

        engine = QueryEngine(db, {"pipeline": {"query_timeout_sec": 30}})
        lib = QueryLibrary(engine)

        # Run key queries
        assert not lib.revenue_by_period(
            "2023-01-01", "2024-12-31", "month"
        ).empty
        assert not lib.top_products(
            "2023-01-01", "2024-12-31", 10
        ).empty

        # KPIs
        kpi = KPICalculator(lib)
        sales = kpi.sales_kpis("2023-01-01", "2024-12-31")
        assert sales["total_revenue"] > 0

        # RFM
        rfm = RFMEngine(db)
        rfm_df = rfm.compute_rfm("2025-01-01")
        assert not rfm_df.empty

        # LTV
        ltv = LTVEngine(db)
        ltv_df = ltv.projected_ltv()
        assert not ltv_df.empty

        db.close()
    return True


def check_visualisation() -> bool:
    """Verify chart rendering works."""
    import matplotlib
    matplotlib.use("Agg")
    from src.visualisation.theme import ChartTheme
    from src.visualisation.chart_factory import ChartFactory
    import pandas as pd

    theme = ChartTheme(config={})
    theme.apply()
    chart = ChartFactory.create("line", theme)
    data = pd.DataFrame({
        "period": ["Jan", "Feb", "Mar"],
        "revenue": [100, 200, 150],
    })
    fig = chart.render(data, date_col="period", value_col="revenue")
    assert fig is not None
    import matplotlib.pyplot as plt
    plt.close(fig)
    return True


def main() -> None:
    """Run all validation checks."""
    print("=" * 60)
    print("E-Commerce Analytics Platform — Installation Validation")
    print("=" * 60)
    print()

    start = time.perf_counter()

    checks = [
        ("Package imports", check_imports),
        ("Database connectivity", check_database),
        ("Data generation", check_data_generation),
        ("Visualisation rendering", check_visualisation),
        ("Full pipeline", check_full_pipeline),
    ]

    results = []
    for name, func in checks:
        passed = run_check(name, func)
        results.append(passed)

    elapsed = time.perf_counter() - start
    passed = sum(results)
    total = len(results)

    print()
    print(f"Results: {passed}/{total} passed ({elapsed:.1f}s)")

    if all(results):
        print("\n✅ Installation validated successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
