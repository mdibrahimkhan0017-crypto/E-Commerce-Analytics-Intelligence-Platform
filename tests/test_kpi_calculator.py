"""Tests for the KPI calculator module."""

import pytest


class TestKPICalculator:
    """Test KPICalculator methods."""

    def test_sales_kpis(self, kpi_calculator):
        """Sales KPIs should return all expected keys."""
        kpis = kpi_calculator.sales_kpis("2023-01-01", "2024-12-31")
        assert "total_revenue" in kpis
        assert "total_orders" in kpis
        assert "aov" in kpis
        assert kpis["total_revenue"] >= 0
        assert isinstance(kpis["revenue_growth_pct"], float)

    def test_product_kpis(self, kpi_calculator):
        """Product KPIs should return a DataFrame."""
        df = kpi_calculator.product_kpis("2023-01-01", "2024-12-31")
        assert not df.empty
        assert "revenue_contribution_pct" in df.columns

    def test_customer_kpis(self, kpi_calculator):
        """Customer KPIs should return all expected keys."""
        kpis = kpi_calculator.customer_kpis("2023-01-01", "2024-12-31")
        assert "total_customers" in kpis
        assert "repeat_rate_pct" in kpis
        assert kpis["total_customers"] >= 0

    def test_time_series_kpis(self, kpi_calculator):
        """Time series KPIs should be date-indexed."""
        df = kpi_calculator.time_series_kpis(
            "2023-01-01", "2024-12-31", "monthly"
        )
        assert not df.empty
        assert "revenue" in df.columns

    def test_generate_kpi_report(self, kpi_calculator):
        """KPI report should return a KPIResult."""
        from src.analytics.kpi_calculator import KPIResult
        result = kpi_calculator.generate_kpi_report(
            "2023-01-01", "2024-12-31"
        )
        assert isinstance(result, KPIResult)
        assert result.period == "2023-01-01 to 2024-12-31"

    def test_compare_periods(self, kpi_calculator):
        """Period comparison should return delta and pct_change."""
        from src.analytics.kpi_calculator import KPIResult, compare_periods

        kpi1 = KPIResult(
            period="Q1", kpis={"revenue": 1000, "orders": 50}
        )
        kpi2 = KPIResult(
            period="Q2", kpis={"revenue": 1200, "orders": 60}
        )
        df = compare_periods(kpi1, kpi2)
        assert not df.empty
        assert "delta" in df.columns
        assert "pct_change" in df.columns
