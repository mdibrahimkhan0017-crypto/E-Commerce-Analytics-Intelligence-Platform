"""Tests for the data generator module."""

import pytest
from datetime import date

from src.ingestion.data_generator import DataGenerator


class TestDataGenerator:
    """Test DataGenerator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a seeded generator for deterministic tests."""
        return DataGenerator(
            n_customers=50, n_products=20, n_orders=200,
            start_date="2023-01-01", end_date="2024-12-31",
            seed=42,
        )

    def test_generate_customers_count(self, generator):
        """Should generate the correct number of customers."""
        customers = generator.generate_customers()
        assert len(customers) == 50

    def test_generate_products_count(self, generator):
        """Should generate the correct number of products."""
        products = generator.generate_products()
        assert len(products) == 20

    def test_generate_orders_count(self, generator):
        """Should generate the correct number of orders."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()
        assert len(orders) == 200

    def test_generate_order_items_created(self, generator):
        """Should generate at least as many items as orders."""
        generator.generate_all()
        # Each order has 1-5 items
        assert len(generator._order_items) >= 200

    def test_no_duplicate_customer_ids(self, generator):
        """Customer IDs should be unique."""
        customers = generator.generate_customers()
        ids = [c.customer_id for c in customers]
        assert len(ids) == len(set(ids))

    def test_no_duplicate_order_ids(self, generator):
        """Order IDs should be unique."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()
        ids = [o.order_id for o in orders]
        assert len(ids) == len(set(ids))

    def test_date_range_compliance(self, generator):
        """All order dates should be within the specified range."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()
        start = date(2023, 1, 1)
        end = date(2024, 12, 31)
        for order in orders:
            assert start <= order.order_date <= end

    def test_seasonal_distribution(self, generator):
        """Nov/Dec should have higher order density."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()

        seasonal = sum(
            1 for o in orders if o.order_date.month in (11, 12)
        )
        non_seasonal = len(orders) - seasonal

        # Nov/Dec is 2 months out of 24 = ~8.3%, but with 2.5x uplift
        # we expect ~17-25% of orders
        seasonal_pct = seasonal / len(orders)
        assert seasonal_pct > 0.10, (
            f"Seasonal % too low: {seasonal_pct:.1%}"
        )

    def test_seed_reproducibility(self):
        """Same seed should produce identical record counts and IDs."""
        gen1 = DataGenerator(
            n_customers=10, n_products=5, n_orders=50,
            start_date="2023-01-01", end_date="2023-12-31",
            seed=123,
        )
        gen2 = DataGenerator(
            n_customers=10, n_products=5, n_orders=50,
            start_date="2023-01-01", end_date="2023-12-31",
            seed=123,
        )

        c1 = gen1.generate_customers()
        c2 = gen2.generate_customers()
        # Customer IDs are deterministic (CUST-000001, etc.)
        assert [c.customer_id for c in c1] == [c.customer_id for c in c2]
        assert len(c1) == len(c2)

    def test_to_csv(self, generator, tmp_path):
        """CSV export should create 4 files."""
        generator.generate_all()
        paths = generator.to_csv(str(tmp_path))
        assert len(paths) == 4
        for path in paths.values():
            assert path.endswith(".csv")

    def test_generate_all_keys(self, generator):
        """generate_all() should return dict with 4 keys."""
        result = generator.generate_all()
        expected_keys = {"customers", "products", "orders", "order_items"}
        assert set(result.keys()) == expected_keys

    def test_valid_status_distribution(self, generator):
        """All order statuses should be valid."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()
        valid = {"Completed", "Refunded", "Pending", "Cancelled"}
        for o in orders:
            assert o.status in valid

    def test_valid_channel_distribution(self, generator):
        """All channels should be valid."""
        generator.generate_customers()
        generator.generate_products()
        orders = generator.generate_orders()
        valid = {"web", "mobile", "marketplace", "in-store"}
        for o in orders:
            assert o.channel in valid
