"""End-to-end integration test for the full analytics pipeline.

Generates synthetic data, ingests it, runs all queries, computes
KPIs/RFM/LTV, generates dashboards, and exports as PNG.
"""

import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


class TestIntegration:
    """Full end-to-end pipeline integration test."""

    def test_full_pipeline(self, tmp_path):
        """Complete pipeline should run without errors.

        Steps:
        1. Generate 1,000 synthetic records (seed=42)
        2. Ingest into temp SQLite database
        3. Run all 15 queries — assert non-empty DataFrames
        4. Compute all KPIs, RFM segments, LTV
        5. Generate executive_dashboard
        6. Export as PNG to tmp_path
        7. Assert: file exists, size > 0, no exceptions raised
        """
        from src.db.database import DatabaseManager
        from src.ingestion.data_generator import DataGenerator
        from src.engine.query_engine import QueryEngine
        from src.engine.query_library import QueryLibrary
        from analytics.kpi_calculator import KPICalculator
        from src.analytics.rfm_engine import RFMEngine
        from src.analytics.ltv_engine import LTVEngine
        from src.visualisation.theme import ChartTheme
        from src.visualisation.dashboard import DashboardComposer
        from src.visualisation.exporter import ReportExporter

        # 1. Generate data
        db_path = str(tmp_path / "integration.db")
        db = DatabaseManager(db_path=db_path)
        db.connect()

        gen = DataGenerator(
            n_customers=100, n_products=30,
            n_orders=1000,
            start_date="2023-01-01", end_date="2024-12-31",
            seed=42,
        )
        gen.generate_all()

        # 2. Ingest into database
        gen.to_sqlite(db)
        assert db.row_count("customers") == 100
        assert db.row_count("products") == 30
        assert db.row_count("orders") == 1000

        # 3. Run all 15 queries
        config = {"pipeline": {"query_timeout_sec": 30}}
        engine = QueryEngine(db, config)
        lib = QueryLibrary(engine)

        start, end = "2023-01-01", "2024-12-31"

        assert not lib.revenue_by_period(start, end, "month").empty
        assert not lib.revenue_growth("2023").empty
        assert not lib.top_products(start, end, 10).empty
        assert not lib.bottom_products(start, end, 10).empty
        assert not lib.category_performance(start, end).empty
        assert not lib.customer_orders("CUST-000001").empty
        assert not lib.new_vs_returning("2023").empty
        assert not lib.cohort_retention("2023").empty
        assert not lib.channel_performance(start, end).empty
        assert not lib.refund_analysis(start, end).empty
        assert not lib.daily_sales_summary("2023-06-15").empty
        assert not lib.inventory_velocity(start, end).empty
        assert not lib.discount_impact(start, end).empty
        assert not lib.customer_segments().empty
        assert not lib.geographic_revenue(start, end).empty

        # 4. Compute KPIs, RFM, LTV
        kpi = KPICalculator(lib)
        sales = kpi.sales_kpis(start, end)
        assert sales["total_revenue"] > 0

        rfm = RFMEngine(db)
        rfm_df = rfm.compute_rfm(as_of_date="2025-01-01")
        assert not rfm_df.empty
        seg_df = rfm.assign_segment(rfm_df)
        assert "segment" in seg_df.columns

        ltv = LTVEngine(db)
        ltv_df = ltv.projected_ltv()
        assert not ltv_df.empty
        assert (ltv_df["projected_ltv"] >= 0).all()

        # 5. Generate executive dashboard
        theme = ChartTheme(config={})
        theme.apply()
        dashboard = DashboardComposer(theme, kpi, rfm, ltv)
        fig = dashboard.executive_dashboard(start, end)
        assert fig is not None

        # 6. Export as PNG
        exporter = ReportExporter()
        output_dir = str(tmp_path / "reports")
        paths = exporter.export_figure(
            fig, "exec_dashboard",
            formats=["png"], output_dir=output_dir,
        )

        # 7. Verify output
        assert "png" in paths
        png_path = Path(paths["png"])
        assert png_path.exists()
        assert png_path.stat().st_size > 0

        db.close()
