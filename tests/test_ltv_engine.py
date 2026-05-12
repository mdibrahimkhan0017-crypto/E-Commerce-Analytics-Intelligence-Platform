"""Tests for the LTV engine module."""

import pytest
import pandas as pd


class TestLTVEngine:
    """Test LTVEngine functionality."""

    def test_historical_ltv(self, synthetic_db):
        """Should compute historical LTV for all customers."""
        from src.analytics.ltv_engine import LTVEngine
        ltv = LTVEngine(synthetic_db)
        df = ltv.historical_ltv()
        assert not df.empty
        assert "total_spend" in df.columns
        assert (df["total_spend"] >= 0).all()

    def test_historical_ltv_single(self, synthetic_db):
        """Should return single customer LTV."""
        from src.analytics.ltv_engine import LTVEngine
        ltv = LTVEngine(synthetic_db)
        df = ltv.historical_ltv("CUST-000001")
        assert len(df) == 1

    def test_projected_ltv(self, synthetic_db):
        """Should compute projected LTV with segments."""
        from src.analytics.ltv_engine import LTVEngine
        ltv = LTVEngine(synthetic_db)
        df = ltv.projected_ltv(projection_months=12)
        assert not df.empty
        assert "projected_ltv" in df.columns
        assert "retention_probability" in df.columns
        assert "ltv_segment" in df.columns
        # All retention probabilities should be in [0, 1]
        assert (df["retention_probability"] >= 0).all()
        assert (df["retention_probability"] <= 1).all()
        # All projected LTV should be >= 0
        assert (df["projected_ltv"] >= 0).all()
        # LTV segments should cover all customers
        assert set(df["ltv_segment"].unique()).issubset(
            {"High", "Medium", "Low"}
        )

    def test_ltv_by_channel(self, synthetic_db):
        """Should compute LTV by acquisition channel."""
        from src.analytics.ltv_engine import LTVEngine
        ltv = LTVEngine(synthetic_db)
        df = ltv.ltv_by_channel()
        assert not df.empty
        assert "acquisition_channel" in df.columns

    def test_ltv_summary(self, synthetic_db):
        """Should return summary dict with all expected keys."""
        from src.analytics.ltv_engine import LTVEngine
        ltv = LTVEngine(synthetic_db)
        ltv.projected_ltv()
        summary = ltv.ltv_summary()
        assert "avg_ltv" in summary
        assert "median_ltv" in summary
        assert "total_projected_revenue" in summary
        assert summary["avg_ltv"] >= 0

    def test_ltv_by_segment(self, synthetic_db):
        """Should compute LTV by RFM segment."""
        from src.analytics.ltv_engine import LTVEngine
        from src.analytics.rfm_engine import RFMEngine
        ltv = LTVEngine(synthetic_db)
        rfm = RFMEngine(synthetic_db)
        rfm_df = rfm.compute_rfm(as_of_date="2025-01-01")
        seg_df = rfm.assign_segment(rfm_df)
        ltv.projected_ltv()
        result = ltv.ltv_by_segment(seg_df)
        assert not result.empty
        assert "avg_projected_ltv" in result.columns

    def test_retention_probability_values(self):
        """Retention probability should follow the defined rules."""
        from src.analytics.ltv_engine import LTVEngine
        assert LTVEngine._retention_probability(10) == 1.0
        assert LTVEngine._retention_probability(45) == 0.7
        assert LTVEngine._retention_probability(75) == 0.4
        assert LTVEngine._retention_probability(120) == 0.1
