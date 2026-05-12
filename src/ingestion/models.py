"""Data models for the E-Commerce Analytics Platform.

Defines dataclass models for Customer, Product, Order, and OrderItem
entities with built-in validation logic.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


# ── Allowed values ───────────────────────────────────────────────────────────
ALLOWED_STATUSES = {"Completed", "Refunded", "Pending", "Cancelled"}
ALLOWED_CATEGORIES = {"Electronics", "Clothing", "Home", "Sports", "Beauty"}
ALLOWED_CHANNELS = {"web", "mobile", "marketplace", "in-store"}
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@dataclass
class Customer:
    """Represents a customer entity.

    Attributes:
        customer_id: Unique identifier for the customer.
        email: Customer email address.
        registration_date: Date the customer registered.
        region: Geographic region of the customer.
        segment: Customer segment classification.
    """

    customer_id: str
    email: str
    registration_date: date
    region: str
    segment: str

    def validate(self) -> None:
        """Validate all fields and raise ValueError on invalid data.

        Raises:
            ValueError: If any field violates business rules.
        """
        if not self.customer_id or not self.customer_id.strip():
            raise ValueError("customer_id must not be empty")
        if not self.email or not EMAIL_REGEX.match(self.email):
            raise ValueError(f"Invalid email format: {self.email!r}")
        if isinstance(self.registration_date, datetime):
            self.registration_date = self.registration_date.date()
        if self.registration_date > date.today():
            raise ValueError(
                f"registration_date {self.registration_date} is in the future"
            )
        if not self.region or not self.region.strip():
            raise ValueError("region must not be empty")
        if not self.segment or not self.segment.strip():
            raise ValueError("segment must not be empty")


@dataclass
class Product:
    """Represents a product entity.

    Attributes:
        product_id: Unique identifier for the product.
        name: Product display name.
        category: Product category (must be in ALLOWED_CATEGORIES).
        cost_price: Cost to acquire/produce the product.
        list_price: Retail selling price.
        is_active: Whether the product is currently active.
    """

    product_id: str
    name: str
    category: str
    cost_price: float
    list_price: float
    is_active: bool = True

    def validate(self) -> None:
        """Validate all fields and raise ValueError on invalid data.

        Raises:
            ValueError: If any field violates business rules.
        """
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must not be empty")
        if not self.name or not self.name.strip():
            raise ValueError("product name must not be empty")
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"category {self.category!r} not in {ALLOWED_CATEGORIES}"
            )
        if self.list_price <= 0:
            raise ValueError(f"list_price must be > 0, got {self.list_price}")
        if self.cost_price < 0:
            raise ValueError(
                f"cost_price must be >= 0, got {self.cost_price}"
            )
        if self.cost_price >= self.list_price:
            raise ValueError(
                f"cost_price ({self.cost_price}) must be < "
                f"list_price ({self.list_price})"
            )


@dataclass
class Order:
    """Represents an order entity.

    Attributes:
        order_id: Unique identifier for the order.
        customer_id: ID of the customer who placed the order.
        order_date: Date the order was placed.
        status: Order status (must be in ALLOWED_STATUSES).
        total_amount: Total order value before discount.
        discount_amount: Discount applied to the order.
        channel: Sales channel through which the order was placed.
    """

    order_id: str
    customer_id: str
    order_date: date
    status: str
    total_amount: float
    discount_amount: float
    channel: str

    def validate(self) -> None:
        """Validate all fields and raise ValueError on invalid data.

        Raises:
            ValueError: If any field violates business rules.
        """
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must not be empty")
        if not self.customer_id or not self.customer_id.strip():
            raise ValueError("customer_id must not be empty")
        if isinstance(self.order_date, datetime):
            self.order_date = self.order_date.date()
        if self.order_date > date.today():
            raise ValueError(
                f"order_date {self.order_date} is in the future"
            )
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in {ALLOWED_STATUSES}"
            )
        if self.total_amount < 0:
            raise ValueError(
                f"total_amount must be >= 0, got {self.total_amount}"
            )
        if self.discount_amount < 0:
            raise ValueError(
                f"discount_amount must be >= 0, got {self.discount_amount}"
            )
        if self.discount_amount > self.total_amount:
            raise ValueError(
                f"discount_amount ({self.discount_amount}) cannot exceed "
                f"total_amount ({self.total_amount})"
            )
        if self.channel not in ALLOWED_CHANNELS:
            raise ValueError(
                f"channel {self.channel!r} not in {ALLOWED_CHANNELS}"
            )


@dataclass
class OrderItem:
    """Represents an individual line item within an order.

    Attributes:
        item_id: Unique identifier for the line item.
        order_id: Parent order ID.
        product_id: ID of the product in this line item.
        quantity: Number of units ordered.
        unit_price: Price per unit at time of purchase.
        return_flag: Whether this item was returned.
    """

    item_id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    return_flag: bool = False

    def validate(self) -> None:
        """Validate all fields and raise ValueError on invalid data.

        Raises:
            ValueError: If any field violates business rules.
        """
        if not self.item_id or not self.item_id.strip():
            raise ValueError("item_id must not be empty")
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id must not be empty")
        if not self.product_id or not self.product_id.strip():
            raise ValueError("product_id must not be empty")
        if self.quantity < 1:
            raise ValueError(f"quantity must be >= 1, got {self.quantity}")
        if self.unit_price <= 0:
            raise ValueError(
                f"unit_price must be > 0, got {self.unit_price}"
            )
