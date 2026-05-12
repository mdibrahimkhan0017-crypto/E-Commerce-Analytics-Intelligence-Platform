"""Report scheduler for automated pipeline execution.

Provides scheduled and on-demand report generation with health
checking capabilities.

Usage:
    python -m src.scheduler --mode run-now --report full
    python -m src.scheduler --mode daily --hour 6
"""

import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import click
import yaml

from analytics.kpi_calculator import KPICalculator
from analytics.ltv_engine import LTVEngine
from analytics.rfm_engine import RFMEngine
from db.database import DatabaseManager
from engine.query_engine import QueryEngine
from engine.query_library import QueryLibrary
from ingestion.data_generator import DataGenerator
from ingestion.pipeline import IngestionPipeline
from visualisation.dashboard import DashboardComposer
from visualisation.exporter import ReportExporter
from visualisation.report_composer import ReportComposer
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Automated report scheduling and execution.

    Runs the full analytics pipeline on demand or on a schedule,
    and provides system health checks.

    Attributes:
        config: Configuration dictionary.
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        config_path: str = "config.yaml",
    ) -> None:
        """Initialise the scheduler.

        Args:
            config: Pre-loaded configuration dict.
            config_path: Path to config.yaml (used if config is None).
        """
        if config is None:
            try:
                with open(config_path, "r", encoding="utf-8") as fh:
                    config = yaml.safe_load(fh) or {}
            except FileNotFoundError:
                config = {}
        self.config = config

    def run_now(
        self,
        report_type: str = "full",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute the full analytics pipeline immediately.

        Args:
            report_type: Report type ('full', 'executive', 'product',
                         'customer', 'sales').
            start_date: Start date (YYYY-MM-DD). Defaults to 30 days ago.
            end_date: End date (YYYY-MM-DD). Defaults to today.

        Returns:
            Execution summary dict with status, duration, reports,
            and errors.
        """
        start_time = time.perf_counter()
        errors: list[str] = []

        if end_date is None:
            end_date = date.today().isoformat()
        if start_date is None:
            start_date = (
                date.today() - timedelta(days=30)
            ).isoformat()

        try:
            # Setup components
            db_path = self.config.get("database", {}).get(
                "db_path", "db/ecommerce.db"
            )
            db = DatabaseManager(db_path=db_path)
            db.connect()

            # Check if data exists, if not generate
            try:
                count = db.row_count("orders")
                if count == 0:
                    logger.info("No orders found. Generating data...")
                    gen = DataGenerator(
                        n_customers=500, n_products=100,
                        n_orders=5000, seed=42,
                    )
                    gen.generate_all()
                    gen.to_sqlite(db)
            except Exception:
                logger.info("Generating initial data...")
                gen = DataGenerator(
                    n_customers=500, n_products=100,
                    n_orders=5000, seed=42,
                )
                gen.generate_all()
                gen.to_sqlite(db)

            engine = QueryEngine(db, self.config)
            query_lib = QueryLibrary(engine)
            kpi = KPICalculator(query_lib)
            rfm = RFMEngine(db)
            ltv = LTVEngine(db)

            theme = ChartTheme(config=self.config)
            theme.apply()

            dashboard = DashboardComposer(theme, kpi, rfm, ltv)
            composer = ReportComposer(dashboard)

            output_dir = self.config.get("reports", {}).get(
                "output_dir", "reports"
            )
            report_paths = composer.generate_full_report(
                start_date, end_date, output_dir,
            )

            db.close()

            duration = time.perf_counter() - start_time

            return {
                "status": "success",
                "duration_sec": round(duration, 2),
                "reports_generated": len(
                    [v for v in report_paths.values()
                     if isinstance(v, dict) and "error" not in v]
                ),
                "errors": errors,
                "paths": report_paths,
            }

        except Exception as exc:
            duration = time.perf_counter() - start_time
            error_msg = str(exc)
            errors.append(error_msg)
            logger.error("Pipeline execution failed: %s", exc)
            return {
                "status": "failed",
                "duration_sec": round(duration, 2),
                "reports_generated": 0,
                "errors": errors,
            }

    def schedule_daily(
        self, hour: int = 6, minute: int = 0,
    ) -> None:
        """Schedule daily report generation.

        Args:
            hour: Hour of the day (0–23).
            minute: Minute of the hour (0–59).
        """
        try:
            import schedule as sched_lib
        except ImportError:
            logger.error("'schedule' library not installed.")
            return

        time_str = f"{hour:02d}:{minute:02d}"
        sched_lib.every().day.at(time_str).do(self._scheduled_run)
        logger.info("Scheduled daily report at %s", time_str)

    def schedule_weekly(
        self, day: str = "monday", hour: int = 6,
    ) -> None:
        """Schedule weekly report generation.

        Args:
            day: Day of the week (e.g. 'monday').
            hour: Hour of the day (0–23).
        """
        try:
            import schedule as sched_lib
        except ImportError:
            logger.error("'schedule' library not installed.")
            return

        time_str = f"{hour:02d}:00"
        getattr(sched_lib.every(), day).at(time_str).do(
            self._scheduled_run
        )
        logger.info("Scheduled weekly report on %s at %s", day, time_str)

    def run_forever(self) -> None:
        """Run the scheduler loop until interrupted."""
        try:
            import schedule as sched_lib
        except ImportError:
            logger.error("'schedule' library not installed.")
            return

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                sched_lib.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")

    def health_check(self) -> dict[str, Any]:
        """Run system health checks.

        Returns:
            Dict with status ('healthy', 'degraded', 'down') and
            individual check results.
        """
        checks: list[dict[str, Any]] = []

        # Check DB connection
        try:
            db_path = self.config.get("database", {}).get(
                "db_path", "db/ecommerce.db"
            )
            db = DatabaseManager(db_path=db_path)
            db.connect()
            checks.append({
                "name": "database_connection",
                "passed": True,
                "message": "Connected successfully",
            })

            # Check data exists
            try:
                count = db.row_count("orders")
                checks.append({
                    "name": "data_availability",
                    "passed": count > 0,
                    "message": f"{count} orders in database",
                })
            except Exception as exc:
                checks.append({
                    "name": "data_availability",
                    "passed": False,
                    "message": str(exc),
                })

            db.close()
        except Exception as exc:
            checks.append({
                "name": "database_connection",
                "passed": False,
                "message": str(exc),
            })

        # Check output directory writable
        output_dir = self.config.get("reports", {}).get(
            "output_dir", "reports"
        )
        try:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            test_file = out / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            checks.append({
                "name": "output_directory",
                "passed": True,
                "message": f"{output_dir} is writable",
            })
        except Exception as exc:
            checks.append({
                "name": "output_directory",
                "passed": False,
                "message": str(exc),
            })

        # Determine overall status
        failed = sum(1 for c in checks if not c["passed"])
        if failed == 0:
            status = "healthy"
        elif failed < len(checks):
            status = "degraded"
        else:
            status = "down"

        return {"status": status, "checks": checks}

    def _scheduled_run(self) -> None:
        """Execute a scheduled pipeline run with logging."""
        logger.info("Starting scheduled run...")
        result = self.run_now()
        logger.info(
            "Scheduled run complete: %s (%.1f sec)",
            result["status"], result["duration_sec"],
        )


# ── CLI entry point ──────────────────────────────────────────────────────────

@click.command("schedule")
@click.option(
    "--mode", type=click.Choice(["daily", "weekly", "run-now"]),
    default="run-now", help="Scheduling mode.",
)
@click.option("--hour", default=6, help="Hour for scheduled runs.")
@click.option(
    "--report", default="full", help="Report type for run-now mode.",
)
def main(mode: str, hour: int, report: str) -> None:
    """Start the report scheduler."""
    scheduler = ReportScheduler()

    if mode == "run-now":
        result = scheduler.run_now(report_type=report)
        click.echo(f"Status: {result['status']}")
        click.echo(f"Duration: {result['duration_sec']}s")
        click.echo(f"Reports: {result['reports_generated']}")
    elif mode == "daily":
        scheduler.schedule_daily(hour=hour)
        scheduler.run_forever()
    elif mode == "weekly":
        scheduler.schedule_weekly(hour=hour)
        scheduler.run_forever()


if __name__ == "__main__":
    main()
