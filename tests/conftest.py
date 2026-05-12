"""Shared pytest fixtures for the E-Commerce Analytics test suite."""

import os
import sys
from pathlib import Path

import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def synthetic_db(tmp_path):
    """Create a temporary database with 500 synthetic records.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        A DatabaseManager connected to the synthetic database.
    """
    from src.db.database import DatabaseManager
    from src.ingestion.data_generator import DataGenerator

    db_path = str(tmp_path / "test.db")
    db = DatabaseManager(db_path=db_path)
    db.connect()

    gen = DataGenerator(
        n_customers=50,
        n_products=20,
        n_orders=500,
        start_date="2023-01-01",
        end_date="2024-12-31",
        seed=42,
    )
    gen.generate_all()
    gen.to_sqlite(db)

    yield db
    db.close()


@pytest.fixture
def query_engine(synthetic_db):
    """Create a QueryEngine on the synthetic database.

    Args:
        synthetic_db: DatabaseManager fixture.

    Returns:
        A QueryEngine instance.
    """
    from src.engine.query_engine import QueryEngine

    config = {"pipeline": {"query_timeout_sec": 30}}
    return QueryEngine(synthetic_db, config)


@pytest.fixture
def query_library(query_engine):
    """Create a QueryLibrary on the synthetic database.

    Args:
        query_engine: QueryEngine fixture.

    Returns:
        A QueryLibrary instance.
    """
    from src.engine.query_library import QueryLibrary
    return QueryLibrary(query_engine)


@pytest.fixture
def kpi_calculator(query_library):
    """Create a KPICalculator with the synthetic database.

    Args:
        query_library: QueryLibrary fixture.

    Returns:
        A KPICalculator instance.
    """
    from analytics.kpi_calculator import KPICalculator
    return KPICalculator(query_library)
