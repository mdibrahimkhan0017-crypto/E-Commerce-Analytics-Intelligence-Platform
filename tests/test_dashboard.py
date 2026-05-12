"""Tests for dashboard rendering."""

import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class TestDashboard:
    """Test DashboardComposer rendering."""

    @pytest.fixture
    def dashboard(self, synthetic_db, kpi_calculator):
        """Create a DashboardComposer with synthetic data."""
        from src.analytics.rfm_engine import RFMEngine
        from src.analytics.ltv_engine import LTVEngine
        from src.visualisation.dashboard import DashboardComposer
        from src.visualisation.theme import ChartTheme

        theme = ChartTheme(config={})
        theme.apply()
        rfm = RFMEngine(synthetic_db)
        ltv = LTVEngine(synthetic_db)
        return DashboardComposer(theme, kpi_calculator, rfm, ltv)

    def test_executive_dashboard(self, dashboard):
        """Executive dashboard should produce a 2×3 grid."""
        fig = dashboard.executive_dashboard("2023-01-01", "2024-12-31")
        assert fig is not None
        assert len(fig.axes) >= 6
        plt.close(fig)

    def test_product_dashboard(self, dashboard):
        """Product dashboard should produce a 2×2 grid."""
        fig = dashboard.product_dashboard("2023-01-01", "2024-12-31")
        assert fig is not None
        assert len(fig.axes) >= 4
        plt.close(fig)

    def test_customer_dashboard(self, dashboard):
        """Customer dashboard should produce a 2×2 grid."""
        fig = dashboard.customer_dashboard("2023-01-01", "2024-12-31")
        assert fig is not None
        assert len(fig.axes) >= 4
        plt.close(fig)

    def test_sales_trend_dashboard(self, dashboard):
        """Sales trend dashboard should produce a 1×3 grid."""
        fig = dashboard.sales_trend_dashboard(
            "2023-01-01", "2024-12-31"
        )
        assert fig is not None
        assert len(fig.axes) >= 3
        plt.close(fig)
