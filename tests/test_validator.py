"""Tests for the schema validator module."""

import pytest
import pandas as pd
from datetime import date, timedelta

from src.ingestion.validator import SchemaValidator, ValidationResult


class TestSchemaValidator:
    """Test SchemaValidator validation rules."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create a SchemaValidator with temp log dir."""
        return SchemaValidator(log_dir=str(tmp_path / "logs"))

    # ── Customer validation ──────────────────────────────────────────

    def test_valid_customers(self, validator):
        """Valid customers should pass validation."""
        df = pd.DataFrame([{
            "customer_id": "C001", "email": "a@b.com",
            "registration_date": "2023-01-01",
            "region": "North America", "segment": "Premium",
        }])
        result = validator.validate_dataframe(df, "customers")
        assert len(result.valid_df) == 1
        assert len(result.rejected_df) == 0

    def test_invalid_email_rejected(self, validator):
        """Invalid emails should be rejected."""
        df = pd.DataFrame([{
            "customer_id": "C001", "email": "not-email",
            "registration_date": "2023-01-01",
            "region": "NA", "segment": "Premium",
        }])
        result = validator.validate_dataframe(df, "customers")
        assert len(result.rejected_df) == 1

    def test_empty_region_rejected(self, validator):
        """Empty region should be rejected."""
        df = pd.DataFrame([{
            "customer_id": "C001", "email": "a@b.com",
            "registration_date": "2023-01-01",
            "region": "", "segment": "Premium",
        }])
        result = validator.validate_dataframe(df, "customers")
        assert len(result.rejected_df) == 1

    # ── Product validation ───────────────────────────────────────────

    def test_valid_products(self, validator):
        """Valid products should pass validation."""
        df = pd.DataFrame([{
            "product_id": "P001", "name": "Widget",
            "category": "Electronics",
            "cost_price": 10.0, "list_price": 20.0,
        }])
        result = validator.validate_dataframe(df, "products")
        assert len(result.valid_df) == 1

    def test_cost_exceeds_list_rejected(self, validator):
        """Cost >= list_price should be rejected."""
        df = pd.DataFrame([{
            "product_id": "P001", "name": "Widget",
            "category": "Electronics",
            "cost_price": 25.0, "list_price": 20.0,
        }])
        result = validator.validate_dataframe(df, "products")
        assert len(result.rejected_df) == 1

    def test_invalid_category_rejected(self, validator):
        """Invalid category should be rejected."""
        df = pd.DataFrame([{
            "product_id": "P001", "name": "Widget",
            "category": "InvalidCat",
            "cost_price": 10.0, "list_price": 20.0,
        }])
        result = validator.validate_dataframe(df, "products")
        assert len(result.rejected_df) == 1

    # ── Order validation ─────────────────────────────────────────────

    def test_valid_orders(self, validator):
        """Valid orders should pass validation."""
        df = pd.DataFrame([{
            "order_id": "O001", "customer_id": "C001",
            "order_date": "2023-06-15", "status": "Completed",
            "total_amount": 100.0, "discount_amount": 10.0,
        }])
        result = validator.validate_dataframe(df, "orders")
        assert len(result.valid_df) == 1

    def test_negative_total_rejected(self, validator):
        """Negative total should be rejected."""
        df = pd.DataFrame([{
            "order_id": "O001", "customer_id": "C001",
            "order_date": "2023-06-15", "status": "Completed",
            "total_amount": -50.0, "discount_amount": 0.0,
        }])
        result = validator.validate_dataframe(df, "orders")
        assert len(result.rejected_df) == 1

    def test_discount_exceeds_total_rejected(self, validator):
        """Discount > total should be rejected."""
        df = pd.DataFrame([{
            "order_id": "O001", "customer_id": "C001",
            "order_date": "2023-06-15", "status": "Completed",
            "total_amount": 50.0, "discount_amount": 60.0,
        }])
        result = validator.validate_dataframe(df, "orders")
        assert len(result.rejected_df) == 1

    def test_invalid_status_rejected(self, validator):
        """Invalid status should be rejected."""
        df = pd.DataFrame([{
            "order_id": "O001", "customer_id": "C001",
            "order_date": "2023-06-15", "status": "Unknown",
            "total_amount": 50.0, "discount_amount": 0.0,
        }])
        result = validator.validate_dataframe(df, "orders")
        assert len(result.rejected_df) == 1

    # ── Order item validation ────────────────────────────────────────

    def test_valid_order_items(self, validator):
        """Valid order items should pass validation."""
        df = pd.DataFrame([{
            "item_id": "I001", "order_id": "O001",
            "product_id": "P001", "quantity": 2,
            "unit_price": 19.99,
        }])
        result = validator.validate_dataframe(df, "order_items")
        assert len(result.valid_df) == 1

    def test_zero_quantity_rejected(self, validator):
        """Zero quantity should be rejected."""
        df = pd.DataFrame([{
            "item_id": "I001", "order_id": "O001",
            "product_id": "P001", "quantity": 0,
            "unit_price": 19.99,
        }])
        result = validator.validate_dataframe(df, "order_items")
        assert len(result.rejected_df) == 1

    # ── Pass rate ────────────────────────────────────────────────────

    def test_pass_rate_calculation(self, validator):
        """Pass rate should be calculated correctly."""
        df = pd.DataFrame([
            {"customer_id": "C001", "email": "a@b.com",
             "registration_date": "2023-01-01",
             "region": "NA", "segment": "P"},
            {"customer_id": "C002", "email": "invalid",
             "registration_date": "2023-01-01",
             "region": "NA", "segment": "P"},
        ])
        result = validator.validate_dataframe(df, "customers")
        assert result.pass_rate == 50.0

    def test_unknown_table_raises(self, validator):
        """Unknown table name should raise ValueError."""
        df = pd.DataFrame({"x": [1]})
        with pytest.raises(ValueError, match="Unknown table"):
            validator.validate_dataframe(df, "unknown_table")
