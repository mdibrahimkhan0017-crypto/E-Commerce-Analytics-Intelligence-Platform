"""Tests for the RFM engine module."""

import pytest
import pandas as pd


class TestRFMEngine:
    """Test RFMEngine functionality."""

    def test_compute_rfm(self, synthetic_db):
        """Should compute RFM scores for all customers."""
        from src.analytics.rfm_engine import RFMEngine
        rfm = RFMEngine(synthetic_db)
        df = rfm.compute_rfm(as_of_date="2025-01-01")
        assert not df.empty
        assert "r_score" in df.columns
        assert "rfm_score" in df.columns
        # All scores should be 1-5
        assert df["r_score"].between(1, 5).all()
        assert df["f_score"].between(1, 5).all()
        assert df["m_score"].between(1, 5).all()

    def test_assign_segment(self, synthetic_db):
        """Should assign segments to all customers."""
        from src.analytics.rfm_engine import RFMEngine
        rfm = RFMEngine(synthetic_db)
        rfm_df = rfm.compute_rfm(as_of_date="2025-01-01")
        seg_df = rfm.assign_segment(rfm_df)
        assert "segment" in seg_df.columns
        assert len(seg_df) == len(rfm_df)

    def test_segment_summary(self, synthetic_db):
        """Should produce a segment summary."""
        from src.analytics.rfm_engine import RFMEngine
        rfm = RFMEngine(synthetic_db)
        rfm.compute_rfm(as_of_date="2025-01-01")
        rfm.assign_segment()
        summary = rfm.segment_summary()
        assert not summary.empty
        assert "pct_of_customers" in summary.columns

    def test_churn_risk(self, synthetic_db):
        """Should identify churn risk customers."""
        from src.analytics.rfm_engine import RFMEngine
        rfm = RFMEngine(synthetic_db)
        rfm.compute_rfm(as_of_date="2025-01-01")
        churn = rfm.churn_risk_customers(days_threshold=90)
        # All returned customers should have recency > 90
        if not churn.empty:
            assert (churn["recency_days"] > 90).all()

    def test_export_segments(self, synthetic_db, tmp_path):
        """Should export segments to CSV."""
        from src.analytics.rfm_engine import RFMEngine
        rfm = RFMEngine(synthetic_db)
        rfm.compute_rfm(as_of_date="2025-01-01")
        rfm.assign_segment()
        path = rfm.export_segments(str(tmp_path / "segments.csv"))
        assert path.endswith(".csv")

    def test_compute_rfm_no_data(self, tmp_path):
        """Should handle empty database gracefully."""
        from src.db.database import DatabaseManager
        from src.analytics.rfm_engine import RFMEngine
        db = DatabaseManager(db_path=str(tmp_path / "empty.db"))
        db.connect()
        rfm = RFMEngine(db)
        df = rfm.compute_rfm()
        assert df.empty
        db.close()
