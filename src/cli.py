"""CLI interface for the E-Commerce Analytics Platform.

Provides command groups for data generation, ingestion, reporting,
querying, scheduling, and health checks using the Click library.

Usage:
    python -m src.cli generate --records 10000 --seed 42
    python -m src.cli ingest --source data/
    python -m src.cli report --type all --start 2023-01-01 --end 2024-12-31
    python -m src.cli query --name 01_revenue_by_period --params '{"start_date":"2023-01-01","end_date":"2024-12-31","period":"month"}'
    python -m src.cli schedule --mode run-now
    python -m src.cli health
"""

import json
import logging
import sys
import traceback
from datetime import date, timedelta
from typing import Optional

import click
import yaml

from utils.logger import setup_logger

logger = logging.getLogger(__name__)


def _load_config(config_path: str = "config.yaml") -> dict:
    """Load the platform configuration.

    Args:
        config_path: Path to config.yaml.

    Returns:
        Configuration dictionary.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}


# ── Top-level group ──────────────────────────────────────────────────────────

@click.group()
@click.option("--verbose", is_flag=True, help="Enable debug output.")
@click.option("--quiet", is_flag=True, help="Suppress non-error output.")
@click.option(
    "--config", default="config.yaml", help="Path to config file.",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool, config: str) -> None:
    """E-Commerce Analytics & Intelligence Platform CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["config_path"] = config
    ctx.obj["config"] = _load_config(config)

    log_level = "DEBUG" if verbose else "ERROR" if quiet else "INFO"
    setup_logger(level=log_level, console_output=not quiet)


# ── Generate command ─────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--records", default=10000, show_default=True,
    help="Number of orders to generate.",
)
@click.option(
    "--start", default=None,
    help="Start date (YYYY-MM-DD). Default: 2 years ago.",
)
@click.option(
    "--end", default=None,
    help="End date (YYYY-MM-DD). Default: today.",
)
@click.option("--seed", default=None, type=int, help="Random seed.")
@click.option(
    "--output-dir", default="data", show_default=True,
    help="Output directory for CSV files.",
)
@click.pass_context
def generate(
    ctx: click.Context,
    records: int,
    start: Optional[str],
    end: Optional[str],
    seed: Optional[int],
    output_dir: str,
) -> None:
    """Generate synthetic e-commerce data."""
    try:
        from ingestion.data_generator import DataGenerator

        if end is None:
            end = date.today().isoformat()
        if start is None:
            start = (date.today() - timedelta(days=730)).isoformat()

        if not ctx.obj.get("quiet"):
            click.echo(f"Generating {records} orders ({start} to {end})...")

        n_customers = max(100, records // 10)
        n_products = max(50, records // 50)

        gen = DataGenerator(
            n_customers=n_customers,
            n_products=n_products,
            n_orders=records,
            start_date=start,
            end_date=end,
            seed=seed,
        )
        gen.generate_all()
        paths = gen.to_csv(output_dir)

        if not ctx.obj.get("quiet"):
            click.echo("\n✅ Data generated successfully:")
            for name, path in paths.items():
                click.echo(f"   {name}: {path}")

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Ingest command ───────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--source", default="data", show_default=True,
    help="Path to data directory or file.",
)
@click.option(
    "--incremental", is_flag=True,
    help="Skip records already in the database.",
)
@click.pass_context
def ingest(
    ctx: click.Context, source: str, incremental: bool,
) -> None:
    """Load data into the database."""
    try:
        from db.database import DatabaseManager
        from ingestion.pipeline import IngestionPipeline

        db = DatabaseManager()
        pipeline = IngestionPipeline(
            db_manager=db, source_dir=source,
            incremental=incremental,
        )
        summary = pipeline.run()

        if not ctx.obj.get("quiet"):
            click.echo(f"\n✅ Ingestion complete:")
            click.echo(f"   Loaded:   {summary.records_loaded}")
            click.echo(f"   Rejected: {summary.records_rejected}")
            click.echo(f"   Rate:     {summary.rejection_rate:.1f}%")

        db.close()

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Report command ───────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--type", "report_type",
    default="all", show_default=True,
    help="Report type: all, executive, product, customer, sales.",
)
@click.option("--start", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--end", default=None, help="End date (YYYY-MM-DD).")
@click.option(
    "--format", "fmt", default="png",
    help="Output formats (comma-separated: png,pdf).",
)
@click.option(
    "--output-dir", default="reports", show_default=True,
    help="Output directory.",
)
@click.pass_context
def report(
    ctx: click.Context,
    report_type: str,
    start: Optional[str],
    end: Optional[str],
    fmt: str,
    output_dir: str,
) -> None:
    """Generate analytical reports and dashboards."""
    try:
        from analytics.kpi_calculator import KPICalculator
        from analytics.ltv_engine import LTVEngine
        from analytics.rfm_engine import RFMEngine
        from db.database import DatabaseManager
        from engine.query_engine import QueryEngine
        from engine.query_library import QueryLibrary
        from visualisation.dashboard import DashboardComposer
        from visualisation.exporter import ReportExporter
        from visualisation.report_composer import ReportComposer
        from visualisation.theme import ChartTheme

        if end is None:
            end = date.today().isoformat()
        if start is None:
            start = (date.today() - timedelta(days=365)).isoformat()

        formats = [f.strip() for f in fmt.split(",")]
        config = ctx.obj["config"]

        db = DatabaseManager()
        engine = QueryEngine(db, config)
        query_lib = QueryLibrary(engine)
        kpi = KPICalculator(query_lib)
        rfm = RFMEngine(db)
        ltv = LTVEngine(db)

        theme = ChartTheme(config=config)
        theme.apply()

        dashboard = DashboardComposer(theme, kpi, rfm, ltv)
        composer = ReportComposer(dashboard)

        if not ctx.obj.get("quiet"):
            click.echo(f"Generating {report_type} report ({start} to {end})...")

        result = composer.generate_full_report(
            start, end, output_dir, formats,
        )

        if not ctx.obj.get("quiet"):
            click.echo("\n✅ Reports generated:")
            for name, paths in result.items():
                if isinstance(paths, dict):
                    for f, p in paths.items():
                        click.echo(f"   {name}.{f}: {p}")
                else:
                    click.echo(f"   {name}: {paths}")

        db.close()

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Query command ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--name", default=None, help="Named query from the library.")
@click.option("--file", "filepath", default=None, help="Path to .sql file.")
@click.option(
    "--params", default=None,
    help="JSON string of query parameters.",
)
@click.option(
    "--export", "export_fmt", default=None,
    help="Export format: csv or json.",
)
@click.pass_context
def query(
    ctx: click.Context,
    name: Optional[str],
    filepath: Optional[str],
    params: Optional[str],
    export_fmt: Optional[str],
) -> None:
    """Run a named or custom SQL query."""
    try:
        from db.database import DatabaseManager
        from engine.query_engine import QueryEngine

        if not name and not filepath:
            click.echo("Error: Provide --name or --file.", err=True)
            sys.exit(1)

        param_dict = json.loads(params) if params else None
        config = ctx.obj["config"]

        db = DatabaseManager()
        engine = QueryEngine(db, config)

        if name:
            df = engine.run_named_query(name, param_dict)
        else:
            df = engine.run_from_file(filepath, param_dict)

        if export_fmt:
            path = engine.export_result(df, name or "query_result", export_fmt)
            click.echo(f"Exported to: {path}")
        else:
            click.echo(df.to_string(index=False, max_rows=50))

        db.close()

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Schedule command ─────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["daily", "weekly", "run-now"]),
    default="run-now", help="Scheduling mode.",
)
@click.option("--hour", default=6, help="Hour for scheduled runs (0–23).")
@click.pass_context
def schedule(ctx: click.Context, mode: str, hour: int) -> None:
    """Start the report scheduler."""
    try:
        from scheduler import ReportScheduler

        config = ctx.obj["config"]
        scheduler = ReportScheduler(config=config)

        if mode == "run-now":
            result = scheduler.run_now()
            click.echo(f"Status: {result['status']}")
            click.echo(f"Duration: {result['duration_sec']}s")
            click.echo(f"Reports: {result['reports_generated']}")
        elif mode == "daily":
            scheduler.schedule_daily(hour=hour)
            click.echo(f"Scheduled daily at {hour:02d}:00. Running...")
            scheduler.run_forever()
        elif mode == "weekly":
            scheduler.schedule_weekly(hour=hour)
            click.echo(f"Scheduled weekly at {hour:02d}:00. Running...")
            scheduler.run_forever()

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Health command ───────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def health(ctx: click.Context) -> None:
    """Run system health check."""
    try:
        from scheduler import ReportScheduler

        config = ctx.obj["config"]
        scheduler = ReportScheduler(config=config)
        result = scheduler.health_check()

        status_icon = {
            "healthy": "✅", "degraded": "⚠️", "down": "❌",
        }
        click.echo(
            f"\nSystem Status: {status_icon.get(result['status'], '?')} "
            f"{result['status'].upper()}"
        )

        for check in result["checks"]:
            icon = "✓" if check["passed"] else "✗"
            click.echo(f"   {icon} {check['name']}: {check['message']}")

        sys.exit(0 if result["status"] == "healthy" else 1)

    except Exception as exc:
        _handle_error(ctx, exc)


# ── Error handling ───────────────────────────────────────────────────────────

def _handle_error(ctx: click.Context, exc: Exception) -> None:
    """Handle exceptions with user-friendly messages.

    Args:
        ctx: Click context.
        exc: The exception that occurred.
    """
    if ctx.obj.get("verbose"):
        click.echo(traceback.format_exc(), err=True)
    else:
        click.echo(f"Error: {exc}", err=True)
    sys.exit(1)


if __name__ == "__main__":
    cli()
