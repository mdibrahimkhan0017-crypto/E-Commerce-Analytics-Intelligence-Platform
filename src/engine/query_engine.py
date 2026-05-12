"""SQL query engine for the E-Commerce Analytics Platform.

Provides a QueryEngine class for safe, parameterised query execution
with timing, logging, type-casting, and export capabilities.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from db.database import DatabaseManager
from engine.exceptions import (
    InvalidParameterError,
    QueryNotFoundError,
    QueryTimeoutError,
)

logger = logging.getLogger(__name__)

# Directory containing .sql query files
QUERIES_DIR = Path(__file__).parent / "queries"


class QueryEngine:
    """Executes SQL queries with parameterisation, timing, and export.

    Wraps DatabaseManager with additional safety (parameterised queries,
    timeout enforcement) and convenience (named queries, type casting,
    export).

    Attributes:
        db_manager: The underlying DatabaseManager.
        config: Pipeline configuration dict.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config: Optional[dict] = None,
    ) -> None:
        """Initialise the QueryEngine.

        Args:
            db_manager: An active DatabaseManager instance.
            config: Pipeline configuration dict. Expected keys:
                    pipeline.query_timeout_sec (int).
        """
        self.db_manager = db_manager
        self.config = config or {}
        self._timeout_sec: int = (
            self.config.get("pipeline", {}).get("query_timeout_sec", 30)
        )
        self._query_log: list[dict[str, Any]] = []

    # ── Core query methods ───────────────────────────────────────────────

    def run_query(
        self,
        sql: str,
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        """Execute a parameterised SQL query and return a DataFrame.

        Args:
            sql: SQL query string with optional :param_name placeholders.
            params: Dict of parameter values.

        Returns:
            DataFrame with type-cast columns.

        Raises:
            QueryTimeoutError: If execution exceeds timeout.
        """
        start = time.perf_counter()
        query_label = sql[:100].replace("\n", " ")

        try:
            df = self.db_manager.execute_query(sql, params)
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Check timeout
            if elapsed_ms > self._timeout_sec * 1000:
                raise QueryTimeoutError(query_label, self._timeout_sec)

            # Type-cast result columns
            df = self._type_cast(df)

            # Log execution
            log_entry = {
                "query_name": query_label,
                "execution_ms": round(elapsed_ms, 2),
                "rows_returned": len(df),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self._query_log.append(log_entry)
            logger.debug(
                "Query completed: %.2f ms, %d rows",
                elapsed_ms, len(df),
            )

            return df

        except QueryTimeoutError:
            raise
        except Exception as exc:
            logger.error("Query execution failed: %s", exc)
            raise

    def run_named_query(
        self,
        query_name: str,
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        """Load and execute a named SQL query from the queries directory.

        Args:
            query_name: Name of the query (without .sql extension).
            params: Dict of parameter values.

        Returns:
            DataFrame with query results.

        Raises:
            QueryNotFoundError: If the query file does not exist.
        """
        sql_path = QUERIES_DIR / f"{query_name}.sql"
        if not sql_path.exists():
            raise QueryNotFoundError(query_name)

        sql = sql_path.read_text(encoding="utf-8")
        return self.run_query(sql, params)

    def run_from_file(
        self,
        filepath: str,
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        """Execute a SQL query from an arbitrary file path.

        Args:
            filepath: Path to the .sql file.
            params: Dict of parameter values.

        Returns:
            DataFrame with query results.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"SQL file not found: {filepath}")

        sql = path.read_text(encoding="utf-8")
        return self.run_query(sql, params)

    # ── Export ───────────────────────────────────────────────────────────

    def export_result(
        self,
        df: pd.DataFrame,
        name: str,
        format: str = "csv",
        output_dir: Optional[str] = None,
    ) -> str:
        """Export a DataFrame to a file.

        Args:
            df: DataFrame to export.
            name: Base filename (without extension).
            format: Output format ('csv', 'json', 'parquet').
            output_dir: Output directory (defaults to 'reports/').

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If the format is not supported.
        """
        out_dir = Path(output_dir or "reports")
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        format_lower = format.lower()

        if format_lower == "csv":
            filepath = out_dir / f"{name}_{timestamp}.csv"
            df.to_csv(filepath, index=False)
        elif format_lower == "json":
            filepath = out_dir / f"{name}_{timestamp}.json"
            df.to_json(filepath, orient="records", indent=2)
        elif format_lower == "parquet":
            filepath = out_dir / f"{name}_{timestamp}.parquet"
            df.to_parquet(filepath, index=False)
        else:
            raise ValueError(
                f"Unsupported format: {format!r}. "
                "Use 'csv', 'json', or 'parquet'."
            )

        logger.info("Exported %d rows to %s", len(df), filepath)
        return str(filepath)

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def query_log(self) -> list[dict[str, Any]]:
        """Return the list of query execution log entries.

        Returns:
            List of dicts with query_name, execution_ms,
            rows_returned, timestamp.
        """
        return self._query_log.copy()

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _type_cast(df: pd.DataFrame) -> pd.DataFrame:
        """Auto-cast DataFrame columns to appropriate types.

        - Columns containing 'date' are cast to pd.Timestamp.
        - Numeric-looking columns are cast to float/int.

        Args:
            df: Raw DataFrame from the database.

        Returns:
            DataFrame with improved column types.
        """
        for col in df.columns:
            col_lower = col.lower()

            # Date columns
            if "date" in col_lower:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass
                continue

            # Numeric columns
            if df[col].dtype == object:
                try:
                    numeric = pd.to_numeric(df[col], errors="coerce")
                    if numeric.notna().sum() > 0:
                        df[col] = numeric
                except Exception:
                    pass

        return df
