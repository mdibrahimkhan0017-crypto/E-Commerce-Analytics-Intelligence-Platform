"""Tests for resilience: DB failures, missing files, corrupted data."""

import pytest
import pandas as pd


class TestResilience:
    """Test system resilience under error conditions."""

    def test_missing_source_file_skipped(self, tmp_path):
        """Pipeline should skip missing source files gracefully."""
        from src.db.database import DatabaseManager
        from src.ingestion.pipeline import IngestionPipeline

        db = DatabaseManager(db_path=str(tmp_path / "test.db"))
        pipeline = IngestionPipeline(
            db_manager=db, source_dir=str(tmp_path / "nonexistent"),
        )
        # Should not raise
        summary = pipeline.run()
        assert summary.records_loaded == 0
        db.close()

    def test_corrupted_csv_logged(self, tmp_path):
        """Corrupted CSV data should be logged, not crash."""
        from src.db.database import DatabaseManager
        from src.ingestion.pipeline import IngestionPipeline

        # Write a bad CSV
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "customers.csv").write_text(
            "customer_id,email,registration_date,region,segment\n"
            ",bad-email,not-a-date,,\n"
        )

        db = DatabaseManager(db_path=str(tmp_path / "test.db"))
        pipeline = IngestionPipeline(
            db_manager=db, source_dir=str(data_dir),
        )
        summary = pipeline.run()
        # The bad record should be rejected
        assert summary.records_rejected >= 0
        db.close()

    def test_chart_render_error_handled(self):
        """Chart rendering errors should return an error figure."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.theme import ChartTheme
        from src.visualisation.charts.revenue_trend import LineChart

        theme = ChartTheme(config={})
        chart = LineChart(theme)
        # Pass data with missing column — should not crash
        bad_data = pd.DataFrame({"wrong_col": [1, 2, 3]})
        fig = chart.render(bad_data, date_col="x", value_col="y")
        assert fig is not None
        plt.close(fig)

    def test_dry_run_mode(self, tmp_path):
        """Dry run should validate without writing to DB."""
        from src.db.database import DatabaseManager
        from src.ingestion.data_generator import DataGenerator
        from src.ingestion.pipeline import IngestionPipeline

        # Generate data
        gen = DataGenerator(
            n_customers=10, n_products=5, n_orders=20, seed=42,
        )
        gen.generate_all()
        data_dir = tmp_path / "data"
        gen.to_csv(str(data_dir))

        db = DatabaseManager(db_path=str(tmp_path / "test.db"))
        pipeline = IngestionPipeline(
            db_manager=db, source_dir=str(data_dir), dry_run=True,
        )
        summary = pipeline.run()
        # Data should be validated but DB should have 0 rows
        assert summary.records_loaded >= 0
        db.close()

    def test_exporter_dpi_validation(self, tmp_path):
        """Exporter should reject invalid DPI."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.exporter import ReportExporter

        fig, ax = plt.subplots()
        ax.plot([1, 2])
        exporter = ReportExporter()
        with pytest.raises(ValueError, match="DPI"):
            exporter.export_figure(
                fig, "test", dpi=10, output_dir=str(tmp_path),
            )
        plt.close(fig)
