"""Data loader with unified interface for CSV, JSON, and SQLite sources.

Provides a DataLoader class that auto-detects file type and loads data
into pandas DataFrames.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── Supported file extensions ────────────────────────────────────────────────
CSV_EXTENSIONS = {".csv", ".tsv", ".txt"}
JSON_EXTENSIONS = {".json", ".jsonl"}
SQLITE_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}


class DataLoader:
    """Unified data loader supporting CSV, JSON, and SQLite sources.

    Automatically detects file type from the extension and applies
    appropriate loading strategies.
    """

    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> None:
        """Initialise the DataLoader.

        Args:
            delimiter: Default CSV delimiter.
            encoding: Default file encoding.
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def load(
        self,
        source_path: str,
        table_name: str = "",
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Load data from any supported source into a DataFrame.

        Args:
            source_path: Path to the data file or database.
            table_name: Table name (required for SQLite, used as hint
                        for CSV/JSON).
            query: Optional SQL query for SQLite sources.
            **kwargs: Additional keyword arguments passed to the
                      underlying pandas reader.

        Returns:
            A pandas DataFrame containing the loaded data.

        Raises:
            FileNotFoundError: If the source file does not exist.
            ValueError: If the file extension is not supported.
        """
        path = Path(source_path)

        if not path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        ext = path.suffix.lower()

        if ext in CSV_EXTENSIONS:
            return self._load_csv(path, **kwargs)
        elif ext in JSON_EXTENSIONS:
            return self._load_json(path, **kwargs)
        elif ext in SQLITE_EXTENSIONS:
            return self._load_sqlite(path, table_name, query, **kwargs)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def load_all(
        self, config: dict[str, Any],
    ) -> dict[str, pd.DataFrame]:
        """Load multiple data sources defined in a config dict.

        The config dict maps logical names to source definitions::

            {
                "customers": {"path": "data/customers.csv"},
                "orders":    {"path": "data/orders.csv"},
            }

        Args:
            config: Dictionary of source configurations.

        Returns:
            Dict mapping logical names to loaded DataFrames.
        """
        results: dict[str, pd.DataFrame] = {}

        for name, source_cfg in config.items():
            source_path = source_cfg.get("path", "")
            table_name = source_cfg.get("table_name", name)
            query = source_cfg.get("query")

            try:
                df = self.load(source_path, table_name, query)
                results[name] = df
                logger.info(
                    "Loaded %d rows from '%s' (%s)",
                    len(df), name, source_path,
                )
            except Exception as exc:
                logger.error(
                    "Failed to load '%s' from %s: %s",
                    name, source_path, exc,
                )
                results[name] = pd.DataFrame()

        return results

    # ── Private loader methods ───────────────────────────────────────────

    def _load_csv(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        """Load a CSV file, handling BOM and configurable delimiters.

        Args:
            path: Path to the CSV file.
            **kwargs: Additional pandas read_csv arguments.

        Returns:
            Loaded DataFrame.
        """
        default_kwargs = {
            "delimiter": self.delimiter,
            "encoding": "utf-8-sig",  # Handles BOM transparently
        }
        default_kwargs.update(kwargs)

        df = pd.read_csv(path, **default_kwargs)
        logger.debug("Loaded CSV %s: %d rows × %d cols", path, *df.shape)
        return df

    def _load_json(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        """Load a JSON file, auto-detecting records vs. lines format.

        Args:
            path: Path to the JSON file.
            **kwargs: Additional pandas read_json arguments.

        Returns:
            Loaded DataFrame.
        """
        content = path.read_text(encoding=self.encoding).strip()

        # Auto-detect: lines format starts with '{' on first line but
        # is not a valid JSON array
        if content.startswith("["):
            # Standard JSON array of records
            orient = kwargs.pop("orient", "records")
            df = pd.read_json(path, orient=orient, **kwargs)
        else:
            # JSON Lines format (one object per line)
            df = pd.read_json(path, lines=True, **kwargs)

        logger.debug("Loaded JSON %s: %d rows × %d cols", path, *df.shape)
        return df

    def _load_sqlite(
        self,
        path: Path,
        table_name: str,
        query: Optional[str] = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Load data from a SQLite database.

        Args:
            path: Path to the SQLite database file.
            table_name: Table to query if no explicit query given.
            query: Optional SQL query; defaults to SELECT * FROM table.
            **kwargs: Additional pandas read_sql arguments.

        Returns:
            Loaded DataFrame.
        """
        if not query:
            if not table_name:
                raise ValueError(
                    "Either table_name or query must be provided "
                    "for SQLite sources."
                )
            query = f"SELECT * FROM [{table_name}]"

        conn = sqlite3.connect(str(path))
        try:
            df = pd.read_sql_query(query, conn, **kwargs)
            logger.debug(
                "Loaded SQLite %s (%s): %d rows × %d cols",
                path, table_name, *df.shape,
            )
            return df
        finally:
            conn.close()
