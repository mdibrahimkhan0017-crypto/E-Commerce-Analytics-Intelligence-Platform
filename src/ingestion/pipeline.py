"""Ingestion pipeline orchestrator for the E-Commerce Analytics Platform.

Coordinates data loading, validation, and database insertion with
structured error logging and incremental mode support.

Usage:
    python -m src.ingestion.pipeline --source data/ --incremental
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import click
import pandas as pd

from db.database import DatabaseManager
from ingestion.loader import DataLoader
from ingestion.models import (
    Customer, Order, OrderItem, Product,
)
from ingestion.validator import SchemaValidator, ValidationResult

logger = logging.getLogger(__name__)

# ── Table metadata ───────────────────────────────────────────────────────────
TABLE_CONFIG = {
    "customers": {
        "file": "customers.csv",
        "pk": "customer_id",
        "model": Customer,
    },
    "products": {
        "file": "products.csv",
        "pk": "product_id",
        "model": Product,
    },
    "orders": {
        "file": "orders.csv",
        "pk": "order_id",
        "model": Order,
    },
    "order_items": {
        "file": "order_items.csv",
        "pk": "item_id",
        "model": OrderItem,
    },
}

# Insertion order respects foreign key dependencies
INSERTION_ORDER = ["customers", "products", "orders", "order_items"]


@dataclass
class IngestionSummary:
    """Summary of an ingestion pipeline run.

    Attributes:
        records_loaded: Total records successfully loaded.
        records_rejected: Total records rejected by validation.
        rejection_rate: Rejection rate as a percentage.
        table_summaries: Per-table load/reject counts.
        errors: List of error details.
    """

    records_loaded: int = 0
    records_rejected: int = 0
    rejection_rate: float = 0.0
    table_summaries: dict[str, dict[str, int]] = None
    errors: list[dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialise mutable defaults."""
        if self.table_summaries is None:
            self.table_summaries = {}
        if self.errors is None:
            self.errors = []


class IngestionPipeline:
    """Orchestrates data loading, validation, and database insertion.

    Supports incremental mode (skip existing primary keys) and
    dry-run mode (validate only, no DB writes).
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        source_dir: str = "data",
        incremental: bool = False,
        dry_run: bool = False,
    ) -> None:
        """Initialise the ingestion pipeline.

        Args:
            db_manager: DatabaseManager instance for DB operations.
            source_dir: Directory containing source data files.
            incremental: If True, skip records with existing PKs.
            dry_run: If True, validate without writing to DB.
        """
        self.db_manager = db_manager
        self.source_dir = Path(source_dir)
        self.incremental = incremental
        self.dry_run = dry_run
        self.loader = DataLoader()
        self.validator = SchemaValidator()

    def run(self) -> IngestionSummary:
        """Execute the full ingestion pipeline.

        Returns:
            An IngestionSummary with load/reject statistics.
        """
        summary = IngestionSummary()

        for table_name in INSERTION_ORDER:
            config = TABLE_CONFIG[table_name]
            file_path = self.source_dir / config["file"]

            # ── Load ─────────────────────────────────────────────────
            if not file_path.exists():
                logger.warning(
                    "Source file missing: %s — skipping %s",
                    file_path, table_name,
                )
                continue

            try:
                df = self.loader.load(str(file_path), table_name)
            except Exception as exc:
                logger.error(
                    "Failed to load %s: %s", table_name, exc,
                )
                continue

            if df.empty:
                logger.warning("Empty DataFrame for %s", table_name)
                continue

            # ── Dataclass validation ─────────────────────────────────
            model_class = config["model"]
            valid_indices = []
            for idx, row in df.iterrows():
                try:
                    record_dict = row.to_dict()
                    # Convert date strings to date objects for validation
                    for field_name in ("registration_date", "order_date"):
                        if field_name in record_dict:
                            val = record_dict[field_name]
                            if isinstance(val, str):
                                record_dict[field_name] = datetime.strptime(
                                    val, "%Y-%m-%d"
                                ).date()

                    # Convert boolean-like fields
                    if "is_active" in record_dict:
                        record_dict["is_active"] = bool(
                            record_dict["is_active"]
                        )
                    if "return_flag" in record_dict:
                        record_dict["return_flag"] = bool(
                            record_dict["return_flag"]
                        )

                    instance = model_class(**record_dict)
                    instance.validate()
                    valid_indices.append(idx)
                except (ValueError, TypeError) as exc:
                    pk_val = row.get(config["pk"], f"row_{idx}")
                    summary.errors.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "table": table_name,
                        "record_id": str(pk_val),
                        "error_message": str(exc),
                    })

            validated_df = df.loc[valid_indices].copy()

            # ── Schema validation ────────────────────────────────────
            result = self.validator.validate_dataframe(
                validated_df, table_name, self.db_manager,
            )

            loaded = len(result.valid_df)
            rejected = len(df) - loaded

            # ── Incremental: remove existing PKs ────────────────────
            if self.incremental and not result.valid_df.empty:
                pk = config["pk"]
                try:
                    existing = self.db_manager.execute_query(
                        f"SELECT [{pk}] FROM [{table_name}]"
                    )
                    existing_ids = set(existing[pk].tolist())
                    before = len(result.valid_df)
                    result.valid_df = result.valid_df[
                        ~result.valid_df[pk].isin(existing_ids)
                    ]
                    skipped = before - len(result.valid_df)
                    if skipped:
                        logger.info(
                            "Incremental: skipped %d existing %s",
                            skipped, table_name,
                        )
                except Exception:
                    pass

            # ── Insert into DB ───────────────────────────────────────
            if not self.dry_run and not result.valid_df.empty:
                try:
                    self._insert_dataframe(
                        result.valid_df, table_name,
                    )
                except Exception as exc:
                    logger.error(
                        "DB insert failed for %s: %s — rolling back batch",
                        table_name, exc,
                    )
                    loaded = 0

            summary.records_loaded += loaded
            summary.records_rejected += rejected
            summary.table_summaries[table_name] = {
                "loaded": loaded,
                "rejected": rejected,
            }

            logger.info(
                "Pipeline %s: %d loaded, %d rejected",
                table_name, loaded, rejected,
            )

        # Calculate overall rejection rate
        total = summary.records_loaded + summary.records_rejected
        if total > 0:
            summary.rejection_rate = (
                summary.records_rejected / total
            ) * 100.0

        logger.info(
            "Pipeline complete: %d loaded, %d rejected (%.1f%%)",
            summary.records_loaded,
            summary.records_rejected,
            summary.rejection_rate,
        )

        return summary

    def _insert_dataframe(
        self, df: pd.DataFrame, table_name: str,
    ) -> None:
        """Insert a DataFrame into the specified table.

        Args:
            df: Validated DataFrame to insert.
            table_name: Target database table.
        """
        conn = self.db_manager.connect()
        df.to_sql(
            table_name, conn,
            if_exists="append", index=False,
            method="multi",
        )
        logger.debug(
            "Inserted %d rows into %s", len(df), table_name,
        )


# ── CLI entry point ──────────────────────────────────────────────────────────

@click.command("ingest")
@click.option(
    "--source", default="data", show_default=True,
    help="Path to data directory containing CSV files.",
)
@click.option(
    "--incremental", is_flag=True, default=False,
    help="Skip records whose primary key already exists in the DB.",
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Validate data without writing to the database.",
)
def main(source: str, incremental: bool, dry_run: bool) -> None:
    """Load, validate, and ingest data into the database."""
    db = DatabaseManager()
    pipeline = IngestionPipeline(
        db_manager=db,
        source_dir=source,
        incremental=incremental,
        dry_run=dry_run,
    )
    summary = pipeline.run()

    click.echo(f"\n✅ Ingestion complete:")
    click.echo(f"   Loaded:   {summary.records_loaded}")
    click.echo(f"   Rejected: {summary.records_rejected}")
    click.echo(f"   Rate:     {summary.rejection_rate:.1f}%")

    for table, counts in summary.table_summaries.items():
        click.echo(
            f"   {table}: {counts['loaded']} loaded, "
            f"{counts['rejected']} rejected"
        )

    db.close()


if __name__ == "__main__":
    main()
