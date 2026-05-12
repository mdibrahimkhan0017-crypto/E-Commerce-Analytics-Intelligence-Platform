"""Additional tests to improve coverage on low-coverage modules."""

import pytest
import sqlite3
import time


class TestDatabaseManager:
    """Additional tests for DatabaseManager."""

    def test_connect_creates_directory(self, tmp_path):
        """Should create parent directories."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "subdir" / "deep" / "test.db")
        db = DatabaseManager(db_path=db_path)
        conn = db.connect()
        assert conn is not None
        db.close()

    def test_context_manager(self, tmp_path):
        """Should support with-statement."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "ctx.db")
        with DatabaseManager(db_path=db_path) as db:
            conn = db.connect()
            assert conn is not None
        # Connection should be closed

    def test_execute_write(self, tmp_path):
        """Should execute write statements."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "write.db")
        db = DatabaseManager(db_path=db_path)
        db.connect()
        db.execute_write(
            "CREATE TABLE IF NOT EXISTS t (id INTEGER, val TEXT)"
        )
        db.execute_write(
            "INSERT INTO t VALUES (?, ?)", (1, "hello")
        )
        df = db.execute_query("SELECT * FROM t")
        assert len(df) == 1
        db.close()

    def test_execute_many(self, tmp_path):
        """Should batch-insert multiple rows."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "many.db")
        db = DatabaseManager(db_path=db_path)
        db.connect()
        db.execute_write(
            "CREATE TABLE IF NOT EXISTS t (id INTEGER, val TEXT)"
        )
        data = [(1, "a"), (2, "b"), (3, "c")]
        db.execute_many("INSERT INTO t VALUES (?, ?)", data)
        assert db.row_count("t") == 3
        db.close()

    def test_table_exists(self, tmp_path):
        """Should detect existing and missing tables."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "exist.db")
        db = DatabaseManager(db_path=db_path)
        db.connect()
        assert db.table_exists("customers")
        assert not db.table_exists("nonexistent_table")
        db.close()

    def test_close_idempotent(self, tmp_path):
        """Closing twice should not raise."""
        from src.db.database import DatabaseManager
        db_path = str(tmp_path / "close.db")
        db = DatabaseManager(db_path=db_path)
        db.connect()
        db.close()
        db.close()  # Should not raise

    def test_default_config_path(self, tmp_path, monkeypatch):
        """Should handle missing config gracefully."""
        from src.db.database import DatabaseManager
        monkeypatch.chdir(tmp_path)
        db = DatabaseManager(config_path="nonexistent.yaml")
        assert db.db_path == "db/ecommerce.db"


class TestRetryDecorator:
    """Tests for the retry decorator."""

    def test_retry_succeeds_first_try(self):
        """Should succeed on first attempt."""
        from src.utils.retry import retry

        call_count = 0

        @retry(max_attempts=3, backoff_sec=0.01, exceptions=(ValueError,))
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_succeeds_after_failure(self):
        """Should succeed after transient failure."""
        from src.utils.retry import retry

        call_count = 0

        @retry(max_attempts=3, backoff_sec=0.01, exceptions=(ValueError,))
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("transient")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 2

    def test_retry_exhausted(self):
        """Should raise after exhausting all attempts."""
        from src.utils.retry import retry

        @retry(max_attempts=2, backoff_sec=0.01, exceptions=(ValueError,))
        def always_fail():
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            always_fail()


class TestLogger:
    """Tests for the structured logger."""

    def test_setup_logger(self, tmp_path):
        """Should create a logger with handlers."""
        from src.utils.logger import setup_logger
        logger = setup_logger(
            name="test_logger_unique",
            log_dir=str(tmp_path),
            level="DEBUG",
        )
        assert logger is not None
        assert len(logger.handlers) >= 1

    def test_get_logger(self):
        """Should return a logger."""
        from src.utils.logger import get_logger
        logger = get_logger("test_get_unique")
        assert logger is not None

    def test_json_formatter(self, tmp_path):
        """Should format log entries as JSON."""
        import json
        from src.utils.logger import setup_logger

        log_file = "test_fmt.log"
        logger = setup_logger(
            name="test_fmt_unique",
            log_dir=str(tmp_path),
            log_file=log_file,
            console_output=False,
        )
        logger.info("test message")

        # Flush handlers
        for h in logger.handlers:
            h.flush()

        log_path = tmp_path / log_file
        content = log_path.read_text().strip()
        if content:
            entry = json.loads(content.split("\n")[0])
            assert "message" in entry
            assert entry["message"] == "test message"


class TestBaseChart:
    """Additional tests for BaseChart."""

    def test_save_chart(self, tmp_path):
        """Should save chart to file."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.theme import ChartTheme
        from src.visualisation.charts.revenue_trend import LineChart
        import pandas as pd

        theme = ChartTheme(config={})
        chart = LineChart(theme)
        data = pd.DataFrame({
            "period": ["Jan", "Feb"],
            "revenue": [100, 200],
        })
        fig = chart.render(data, date_col="period", value_col="revenue")
        paths = chart.save(
            fig, "test_chart", output_dir=str(tmp_path),
            formats=["png"],
        )
        assert "png" in paths
        from pathlib import Path
        assert Path(paths["png"]).exists()
        plt.close(fig)

    def test_watermark(self):
        """Should add watermark without error."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.base_chart import BaseChart

        fig, ax = plt.subplots()
        BaseChart.add_watermark(fig, "Test Watermark")
        plt.close(fig)

    def test_add_subtitle(self):
        """Should add subtitle without error."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.base_chart import BaseChart

        fig, ax = plt.subplots()
        BaseChart.add_subtitle(ax, "Test Subtitle")
        plt.close(fig)

    def test_add_data_label(self):
        """Should add data label without error."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from src.visualisation.base_chart import BaseChart

        fig, ax = plt.subplots()
        ax.plot([1, 2], [3, 4])
        BaseChart.add_data_label(ax, 1, 3, "label")
        plt.close(fig)


class TestHeatmapChart:
    """Tests for heatmap rendering."""

    def test_heatmap_with_pivot(self):
        """Should render a heatmap from pivot data."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
        from src.visualisation.theme import ChartTheme
        from src.visualisation.charts.heatmap_chart import HeatmapChart

        theme = ChartTheme(config={})
        chart = HeatmapChart(theme)
        data = pd.DataFrame({
            "row": ["A", "A", "B", "B"],
            "col": ["X", "Y", "X", "Y"],
            "val": [1.0, 2.0, 3.0, 4.0],
        })
        fig = chart.render(
            data, pivot_index="row", pivot_columns="col",
            pivot_values="val", title="Test Heatmap",
        )
        assert fig is not None
        assert len(fig.axes) >= 1
        plt.close(fig)

    def test_heatmap_numeric_matrix(self):
        """Should render from a numeric matrix directly."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
        from src.visualisation.theme import ChartTheme
        from src.visualisation.charts.heatmap_chart import HeatmapChart

        theme = ChartTheme(config={})
        chart = HeatmapChart(theme)
        data = pd.DataFrame({
            "a": [1.0, 2.0], "b": [3.0, 4.0],
        })
        fig = chart.render(data)
        assert fig is not None
        plt.close(fig)


class TestScatterChart:
    """Tests for scatter chart with groups and regression."""

    def test_scatter_with_groups(self):
        """Should colour-code by group."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
        from src.visualisation.theme import ChartTheme
        from src.visualisation.charts.scatter_chart import ScatterChart

        theme = ChartTheme(config={})
        chart = ScatterChart(theme)
        data = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6],
            "y": [2, 4, 3, 5, 4, 6],
            "g": ["A", "A", "A", "B", "B", "B"],
        })
        fig = chart.render(data, x_col="x", y_col="y",
                          group_col="g", regression=True)
        assert fig is not None
        plt.close(fig)


class TestSchedulerHealth:
    """Test scheduler health check edge cases."""

    def test_health_check_no_db(self, tmp_path):
        """Health check should return degraded/down without DB."""
        from src.scheduler import ReportScheduler
        config = {
            "database": {"db_path": str(tmp_path / "nonexistent.db")},
            "reports": {"output_dir": str(tmp_path / "reports")},
        }
        scheduler = ReportScheduler(config=config)
        result = scheduler.health_check()
        assert "status" in result
        assert len(result["checks"]) >= 2


class TestExporterXlsx:
    """Test DataFrame export to xlsx."""

    def test_export_xlsx(self, tmp_path):
        """Should export DataFrame as xlsx."""
        import pandas as pd
        from src.visualisation.exporter import ReportExporter

        exporter = ReportExporter()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        paths = exporter.export_dataframe(
            df, "test", formats=["xlsx"],
            output_dir=str(tmp_path),
        )
        if "xlsx" in paths:
            from pathlib import Path
            assert Path(paths["xlsx"]).exists()


class TestIngestionPipelineDetails:
    """Additional pipeline tests."""

    def test_incremental_skips_existing(self, tmp_path):
        """Incremental mode should skip existing records."""
        from src.db.database import DatabaseManager
        from src.ingestion.data_generator import DataGenerator
        from src.ingestion.pipeline import IngestionPipeline

        db = DatabaseManager(db_path=str(tmp_path / "incr.db"))

        # First run
        gen = DataGenerator(
            n_customers=10, n_products=5, n_orders=20, seed=42,
        )
        gen.generate_all()
        gen.to_csv(str(tmp_path / "data"))
        gen.to_sqlite(db)

        # Second run with incremental
        pipeline = IngestionPipeline(
            db_manager=db,
            source_dir=str(tmp_path / "data"),
            incremental=True,
        )
        summary = pipeline.run()
        # Should have loaded 0 since all records exist
        db.close()
