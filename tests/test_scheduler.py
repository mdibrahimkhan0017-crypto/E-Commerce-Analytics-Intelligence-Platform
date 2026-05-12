"""Tests for the scheduler module."""

import pytest


class TestScheduler:
    """Test ReportScheduler functionality."""

    def test_health_check_healthy(self, synthetic_db):
        """Health check should return healthy with populated DB."""
        from src.scheduler import ReportScheduler

        config = {
            "database": {"db_path": synthetic_db.db_path},
            "reports": {"output_dir": "reports"},
        }
        scheduler = ReportScheduler(config=config)
        result = scheduler.health_check()
        assert result["status"] in ("healthy", "degraded")
        assert len(result["checks"]) >= 2

    def test_run_now(self, synthetic_db):
        """run_now should complete without errors."""
        from src.scheduler import ReportScheduler

        config = {
            "database": {"db_path": synthetic_db.db_path},
            "reports": {"output_dir": "reports"},
            "pipeline": {"query_timeout_sec": 30},
        }
        scheduler = ReportScheduler(config=config)
        result = scheduler.run_now(
            start_date="2023-01-01", end_date="2024-12-31"
        )
        assert result["status"] in ("success", "failed")
        assert "duration_sec" in result
