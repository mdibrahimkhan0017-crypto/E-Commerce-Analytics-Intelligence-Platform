"""Tests for the data loader module."""

import json
import pytest
import pandas as pd

from src.ingestion.loader import DataLoader


class TestDataLoader:
    """Test DataLoader functionality."""

    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return DataLoader()

    def test_load_csv(self, loader, tmp_path):
        """Should load a CSV file into a DataFrame."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n")
        df = loader.load(str(csv_path))
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "value"]

    def test_load_csv_with_bom(self, loader, tmp_path):
        """Should handle CSV files with BOM."""
        csv_path = tmp_path / "bom.csv"
        csv_path.write_bytes(
            b"\xef\xbb\xbfid,name\n1,Alice\n2,Bob\n"
        )
        df = loader.load(str(csv_path))
        assert "id" in df.columns

    def test_load_json_records(self, loader, tmp_path):
        """Should load JSON array of records."""
        json_path = tmp_path / "test.json"
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        json_path.write_text(json.dumps(data))
        df = loader.load(str(json_path))
        assert len(df) == 2

    def test_load_json_lines(self, loader, tmp_path):
        """Should load JSON Lines format."""
        jsonl_path = tmp_path / "test.jsonl"
        jsonl_path.write_text(
            '{"id":1,"name":"Alice"}\n{"id":2,"name":"Bob"}\n'
        )
        df = loader.load(str(jsonl_path))
        assert len(df) == 2

    def test_load_sqlite(self, loader, tmp_path):
        """Should load from a SQLite database."""
        import sqlite3
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE items (id INTEGER, name TEXT)"
        )
        conn.execute("INSERT INTO items VALUES (1, 'Alice')")
        conn.execute("INSERT INTO items VALUES (2, 'Bob')")
        conn.commit()
        conn.close()

        df = loader.load(str(db_path), table_name="items")
        assert len(df) == 2

    def test_file_not_found(self, loader):
        """Should raise FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path.csv")

    def test_unsupported_extension(self, loader, tmp_path):
        """Should raise ValueError for unsupported extensions."""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text("<data></data>")
        with pytest.raises(ValueError, match="Unsupported"):
            loader.load(str(xml_path))

    def test_load_all(self, loader, tmp_path):
        """Should load multiple sources from config."""
        csv1 = tmp_path / "a.csv"
        csv2 = tmp_path / "b.csv"
        csv1.write_text("x,y\n1,2\n")
        csv2.write_text("a,b\n3,4\n")

        config = {
            "source_a": {"path": str(csv1)},
            "source_b": {"path": str(csv2)},
        }
        result = loader.load_all(config)
        assert "source_a" in result
        assert "source_b" in result
        assert len(result["source_a"]) == 1
