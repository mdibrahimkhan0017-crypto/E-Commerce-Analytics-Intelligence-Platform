"""Tests for the query library — runs each named query against test DB."""

import pytest
import pandas as pd

from src.engine.query_library import QueryLibrary
from src.engine.exceptions import InvalidParameterError


class TestQueryLibrary:
    """Test all 15 named queries through the QueryLibrary."""

    def test_revenue_by_period(self, query_library):
        """01: Revenue by period should return non-empty DataFrame."""
        df = query_library.revenue_by_period(
            "2023-01-01", "2024-12-31", "month"
        )
        assert not df.empty
        assert "total_revenue" in df.columns

    def test_revenue_by_period_invalid(self, query_library):
        """01: Invalid period should raise InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            query_library.revenue_by_period(
                "2023-01-01", "2024-12-31", "decade"
            )

    def test_revenue_growth(self, query_library):
        """02: Revenue growth should return DataFrame with growth_pct."""
        df = query_library.revenue_growth("2023")
        assert not df.empty
        assert "growth_pct" in df.columns

    def test_top_products(self, query_library):
        """03: Top products should return ranked products."""
        df = query_library.top_products(
            "2023-01-01", "2024-12-31", limit=5
        )
        assert not df.empty
        assert "total_revenue" in df.columns

    def test_bottom_products(self, query_library):
        """04: Bottom products should return DataFrame."""
        df = query_library.bottom_products(
            "2023-01-01", "2024-12-31", limit=5
        )
        assert not df.empty

    def test_category_performance(self, query_library):
        """05: Category performance should have margin_pct."""
        df = query_library.category_performance(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty
        assert "margin_pct" in df.columns

    def test_customer_orders(self, query_library):
        """06: Customer orders for a known customer."""
        df = query_library.customer_orders("CUST-000001")
        assert not df.empty

    def test_new_vs_returning(self, query_library):
        """07: New vs returning should have both columns."""
        df = query_library.new_vs_returning("2023")
        assert not df.empty
        assert "new_customers" in df.columns

    def test_cohort_retention(self, query_library):
        """08: Cohort retention should return retention_pct."""
        df = query_library.cohort_retention("2023")
        assert not df.empty
        assert "retention_pct" in df.columns

    def test_channel_performance(self, query_library):
        """09: Channel performance should return per-channel data."""
        df = query_library.channel_performance(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty
        assert "channel" in df.columns

    def test_refund_analysis(self, query_library):
        """10: Refund analysis should return refund metrics."""
        df = query_library.refund_analysis(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty

    def test_daily_sales_summary(self, query_library):
        """11: Daily sales summary should return a single row."""
        df = query_library.daily_sales_summary("2023-06-15")
        assert len(df) == 1

    def test_inventory_velocity(self, query_library):
        """12: Inventory velocity should have units_per_day."""
        df = query_library.inventory_velocity(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty
        assert "units_per_day" in df.columns

    def test_discount_impact(self, query_library):
        """13: Discount impact should compare groups."""
        df = query_library.discount_impact(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty

    def test_customer_segments(self, query_library):
        """14: Customer segments should return segment data."""
        df = query_library.customer_segments()
        assert not df.empty
        assert "segment" in df.columns

    def test_geographic_revenue(self, query_library):
        """15: Geographic revenue should return regional data."""
        df = query_library.geographic_revenue(
            "2023-01-01", "2024-12-31"
        )
        assert not df.empty
        assert "region" in df.columns
