"""Tests for the query engine module."""

import pytest
import pandas as pd

from src.engine.query_engine import QueryEngine
from src.engine.exceptions import QueryNotFoundError


class TestQueryEngine:
    """Test QueryEngine functionality."""

    def test_run_query(self, query_engine):
        """Should execute a simple query and return DataFrame."""
        df = query_engine.run_query("SELECT COUNT(*) as cnt FROM orders")
        assert len(df) == 1
        assert df.iloc[0]["cnt"] > 0

    def test_parameterised_query(self, query_engine):
        """Should support parameterised queries."""
        df = query_engine.run_query(
            "SELECT * FROM orders WHERE status = :status",
            {"status": "Completed"},
        )
        assert len(df) > 0
        assert all(df["status"] == "Completed")

    def test_type_cast_dates(self, query_engine):
        """Should cast date columns to Timestamp."""
        df = query_engine.run_query(
            "SELECT order_date FROM orders LIMIT 5"
        )
        assert pd.api.types.is_datetime64_any_dtype(df["order_date"])

    def test_named_query_not_found(self, query_engine):
        """Should raise QueryNotFoundError for missing queries."""
        with pytest.raises(QueryNotFoundError):
            query_engine.run_named_query("nonexistent_query")

    def test_export_csv(self, query_engine, tmp_path):
        """Should export results to CSV."""
        df = query_engine.run_query("SELECT * FROM customers LIMIT 5")
        path = query_engine.export_result(
            df, "test_export", format="csv",
            output_dir=str(tmp_path),
        )
        assert path.endswith(".csv")

    def test_export_json(self, query_engine, tmp_path):
        """Should export results to JSON."""
        df = query_engine.run_query("SELECT * FROM products LIMIT 5")
        path = query_engine.export_result(
            df, "test_export", format="json",
            output_dir=str(tmp_path),
        )
        assert path.endswith(".json")

    def test_export_invalid_format(self, query_engine, tmp_path):
        """Should raise ValueError for unsupported format."""
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="Unsupported"):
            query_engine.export_result(
                df, "test", format="xml",
                output_dir=str(tmp_path),
            )

    def test_query_log(self, query_engine):
        """Should maintain a query execution log."""
        query_engine.run_query("SELECT 1")
        log = query_engine.query_log
        assert len(log) >= 1
        assert "execution_ms" in log[0]
        assert "rows_returned" in log[0]
