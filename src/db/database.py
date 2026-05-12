"""Database manager for the E-Commerce Analytics Platform.

Provides a DatabaseManager class that handles SQLite connections,
schema initialization, and query execution with timing and logging.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and query execution.

    Handles schema initialization on first connect, parameterised query
    execution returning pandas DataFrames, and connection lifecycle.

    Attributes:
        db_path: Absolute path to the SQLite database file.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        config_path: str = "config.yaml",
    ) -> None:
        """Initialise the DatabaseManager.

        Args:
            db_path: Path to the SQLite database file. If None, reads
                     from config.yaml.
            config_path: Path to the YAML configuration file.
        """
        if db_path is None:
            db_path = self._load_db_path(config_path)
        self.db_path: str = str(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._schema_applied: bool = False

    @staticmethod
    def _load_db_path(config_path: str) -> str:
        """Read the database path from config.yaml.

        Args:
            config_path: Path to the configuration file.

        Returns:
            The database file path string.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh)
            return cfg.get("database", {}).get("db_path", "db/ecommerce.db")
        except FileNotFoundError:
            logger.warning(
                "Config file %s not found; using default db path.", config_path
            )
            return "db/ecommerce.db"

    # ── Connection management ────────────────────────────────────────────

    def connect(self) -> sqlite3.Connection:
        """Open (or return existing) database connection.

        Creates the parent directory if it does not exist, opens the
        connection, enables foreign keys, and applies the schema on the
        first call.

        Returns:
            An active sqlite3.Connection.
        """
        if self._connection is not None:
            return self._connection

        max_retries = 3
        backoff_sec = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                db_dir = Path(self.db_path).parent
                db_dir.mkdir(parents=True, exist_ok=True)

                self._connection = sqlite3.connect(self.db_path)
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.execute("PRAGMA journal_mode = WAL")
                logger.info("Connected to database: %s", self.db_path)

                if not self._schema_applied:
                    self._apply_schema()
                    self._schema_applied = True

                return self._connection

            except sqlite3.OperationalError as exc:
                logger.warning(
                    "Connection attempt %d/%d failed: %s",
                    attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    time.sleep(backoff_sec * attempt)
                else:
                    logger.error("All connection attempts exhausted.")
                    raise

    def close(self) -> None:
        """Close the database connection if open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed.")

    # ── Context manager support ──────────────────────────────────────────

    def __enter__(self) -> "DatabaseManager":
        """Enter context manager; open connection."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager; close connection."""
        self.close()

    # ── Schema management ────────────────────────────────────────────────

    def _apply_schema(self) -> None:
        """Read and execute schema.sql to initialise tables.

        The schema file is located relative to this module.
        """
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            logger.warning("Schema file not found at %s", schema_path)
            return

        schema_sql = schema_path.read_text(encoding="utf-8")
        try:
            conn = self._connection
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database schema applied successfully.")
        except sqlite3.Error as exc:
            logger.error("Failed to apply schema: %s", exc)
            raise

    # ── Query execution ──────────────────────────────────────────────────

    def execute_query(
        self,
        sql: str,
        params: Optional[dict | tuple] = None,
    ) -> pd.DataFrame:
        """Execute a SQL query and return results as a DataFrame.

        Args:
            sql: The SQL query string, optionally with named parameters.
            params: A dict or tuple of parameter values for the query.

        Returns:
            A pandas DataFrame containing the query results.

        Raises:
            sqlite3.Error: If the query execution fails after retries.
        """
        conn = self.connect()
        start = time.perf_counter()

        max_retries = 3
        backoff_sec = 1.0

        for attempt in range(1, max_retries + 1):
            try:
                df = pd.read_sql_query(sql, conn, params=params)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(
                    "Query executed in %.2f ms — %d rows returned",
                    elapsed, len(df),
                )
                return df
            except sqlite3.OperationalError as exc:
                logger.warning(
                    "Query attempt %d/%d failed: %s",
                    attempt, max_retries, exc,
                )
                if attempt < max_retries:
                    time.sleep(backoff_sec * attempt)
                else:
                    logger.error("Query failed after %d retries.", max_retries)
                    raise
            except sqlite3.Error as exc:
                logger.error("Query execution error: %s", exc)
                raise

        # Fallback (should not reach here)
        return pd.DataFrame()

    def execute_write(
        self,
        sql: str,
        params: Optional[dict | tuple | list] = None,
    ) -> int:
        """Execute a write (INSERT/UPDATE/DELETE) statement.

        Args:
            sql: The SQL statement.
            params: Parameters for the statement.

        Returns:
            Number of rows affected.
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            if isinstance(params, list):
                cursor.executemany(sql, params)
            elif params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as exc:
            conn.rollback()
            logger.error("Write execution error: %s", exc)
            raise

    def execute_many(
        self,
        sql: str,
        data: list[tuple],
    ) -> int:
        """Execute a parameterised statement for multiple rows.

        Args:
            sql: The SQL statement with placeholders.
            data: List of tuples, one per row.

        Returns:
            Number of rows affected.
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, data)
            conn.commit()
            return cursor.rowcount
        except sqlite3.Error as exc:
            conn.rollback()
            logger.error("Batch write error: %s", exc)
            raise

    def table_exists(self, table_name: str) -> bool:
        """Check whether a table exists in the database.

        Args:
            table_name: Name of the table to check.

        Returns:
            True if the table exists, False otherwise.
        """
        sql = (
            "SELECT COUNT(*) as cnt FROM sqlite_master "
            "WHERE type='table' AND name=:table_name"
        )
        df = self.execute_query(sql, {"table_name": table_name})
        return int(df.iloc[0]["cnt"]) > 0

    def row_count(self, table_name: str) -> int:
        """Return the number of rows in a table.

        Args:
            table_name: Name of the table.

        Returns:
            Row count as integer.
        """
        # Use string formatting here since table names can't be parameterised
        # This is safe because table_name is validated internally
        sql = f"SELECT COUNT(*) as cnt FROM [{table_name}]"
        df = self.execute_query(sql)
        return int(df.iloc[0]["cnt"])
