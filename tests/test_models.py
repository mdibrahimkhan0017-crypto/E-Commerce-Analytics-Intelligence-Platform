"""Tests for data models and validation logic."""

import pytest
from datetime import date, timedelta

from src.ingestion.models import Customer, Product, Order, OrderItem


class TestCustomerValidation:
    """Test Customer dataclass validation."""

    def test_valid_customer(self):
        """A valid customer should pass validation."""
        c = Customer(
            customer_id="CUST-001", email="test@example.com",
            registration_date=date(2023, 1, 1),
            region="North America", segment="Premium",
        )
        c.validate()  # Should not raise

    def test_empty_customer_id(self):
        """Empty customer_id should raise ValueError."""
        c = Customer(
            customer_id="", email="test@example.com",
            registration_date=date(2023, 1, 1),
            region="North America", segment="Premium",
        )
        with pytest.raises(ValueError, match="customer_id"):
            c.validate()

    def test_invalid_email(self):
        """Invalid email format should raise ValueError."""
        c = Customer(
            customer_id="CUST-001", email="not-an-email",
            registration_date=date(2023, 1, 1),
            region="North America", segment="Premium",
        )
        with pytest.raises(ValueError, match="email"):
            c.validate()

    def test_future_registration_date(self):
        """Future registration date should raise ValueError."""
        c = Customer(
            customer_id="CUST-001", email="test@example.com",
            registration_date=date.today() + timedelta(days=10),
            region="North America", segment="Premium",
        )
        with pytest.raises(ValueError, match="future"):
            c.validate()

    def test_empty_region(self):
        """Empty region should raise ValueError."""
        c = Customer(
            customer_id="CUST-001", email="test@example.com",
            registration_date=date(2023, 1, 1),
            region="", segment="Premium",
        )
        with pytest.raises(ValueError, match="region"):
            c.validate()

    def test_whitespace_only_region(self):
        """Whitespace-only region should raise ValueError."""
        c = Customer(
            customer_id="CUST-001", email="test@example.com",
            registration_date=date(2023, 1, 1),
            region="   ", segment="Premium",
        )
        with pytest.raises(ValueError, match="region"):
            c.validate()


class TestProductValidation:
    """Test Product dataclass validation."""

    def test_valid_product(self):
        """A valid product should pass validation."""
        p = Product(
            product_id="PROD-001", name="Widget",
            category="Electronics", cost_price=10.0,
            list_price=20.0, is_active=True,
        )
        p.validate()

    def test_negative_list_price(self):
        """Negative list_price should raise ValueError."""
        p = Product(
            product_id="PROD-001", name="Widget",
            category="Electronics", cost_price=10.0,
            list_price=-5.0, is_active=True,
        )
        with pytest.raises(ValueError, match="list_price"):
            p.validate()

    def test_cost_exceeds_list(self):
        """cost_price >= list_price should raise ValueError."""
        p = Product(
            product_id="PROD-001", name="Widget",
            category="Electronics", cost_price=25.0,
            list_price=20.0, is_active=True,
        )
        with pytest.raises(ValueError, match="cost_price"):
            p.validate()

    def test_invalid_category(self):
        """Invalid category should raise ValueError."""
        p = Product(
            product_id="PROD-001", name="Widget",
            category="InvalidCat", cost_price=10.0,
            list_price=20.0, is_active=True,
        )
        with pytest.raises(ValueError, match="category"):
            p.validate()

    def test_empty_product_id(self):
        """Empty product_id should raise ValueError."""
        p = Product(
            product_id="", name="Widget",
            category="Electronics", cost_price=10.0,
            list_price=20.0, is_active=True,
        )
        with pytest.raises(ValueError, match="product_id"):
            p.validate()


class TestOrderValidation:
    """Test Order dataclass validation."""

    def test_valid_order(self):
        """A valid order should pass validation."""
        o = Order(
            order_id="ORD-001", customer_id="CUST-001",
            order_date=date(2023, 6, 15), status="Completed",
            total_amount=100.0, discount_amount=10.0, channel="web",
        )
        o.validate()

    def test_negative_total(self):
        """Negative total_amount should raise ValueError."""
        o = Order(
            order_id="ORD-001", customer_id="CUST-001",
            order_date=date(2023, 6, 15), status="Completed",
            total_amount=-50.0, discount_amount=0.0, channel="web",
        )
        with pytest.raises(ValueError, match="total_amount"):
            o.validate()

    def test_discount_exceeds_total(self):
        """Discount exceeding total should raise ValueError."""
        o = Order(
            order_id="ORD-001", customer_id="CUST-001",
            order_date=date(2023, 6, 15), status="Completed",
            total_amount=50.0, discount_amount=60.0, channel="web",
        )
        with pytest.raises(ValueError, match="discount_amount"):
            o.validate()

    def test_invalid_status(self):
        """Invalid status should raise ValueError."""
        o = Order(
            order_id="ORD-001", customer_id="CUST-001",
            order_date=date(2023, 6, 15), status="Unknown",
            total_amount=50.0, discount_amount=0.0, channel="web",
        )
        with pytest.raises(ValueError, match="status"):
            o.validate()

    def test_invalid_channel(self):
        """Invalid channel should raise ValueError."""
        o = Order(
            order_id="ORD-001", customer_id="CUST-001",
            order_date=date(2023, 6, 15), status="Completed",
            total_amount=50.0, discount_amount=0.0, channel="fax",
        )
        with pytest.raises(ValueError, match="channel"):
            o.validate()


class TestOrderItemValidation:
    """Test OrderItem dataclass validation."""

    def test_valid_order_item(self):
        """A valid order item should pass validation."""
        oi = OrderItem(
            item_id="ITEM-001", order_id="ORD-001",
            product_id="PROD-001", quantity=2,
            unit_price=19.99, return_flag=False,
        )
        oi.validate()

    def test_zero_quantity(self):
        """Zero quantity should raise ValueError."""
        oi = OrderItem(
            item_id="ITEM-001", order_id="ORD-001",
            product_id="PROD-001", quantity=0,
            unit_price=19.99, return_flag=False,
        )
        with pytest.raises(ValueError, match="quantity"):
            oi.validate()

    def test_negative_unit_price(self):
        """Negative unit_price should raise ValueError."""
        oi = OrderItem(
            item_id="ITEM-001", order_id="ORD-001",
            product_id="PROD-001", quantity=1,
            unit_price=-5.0, return_flag=False,
        )
        with pytest.raises(ValueError, match="unit_price"):
            oi.validate()

    def test_empty_item_id(self):
        """Empty item_id should raise ValueError."""
        oi = OrderItem(
            item_id="", order_id="ORD-001",
            product_id="PROD-001", quantity=1,
            unit_price=10.0, return_flag=False,
        )
        with pytest.raises(ValueError, match="item_id"):
            oi.validate()
