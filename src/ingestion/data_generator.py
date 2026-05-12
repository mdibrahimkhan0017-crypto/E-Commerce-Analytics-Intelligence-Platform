"""Synthetic data generator for the E-Commerce Analytics Platform.

Generates realistic e-commerce data (customers, products, orders,
order items) with configurable seasonal patterns, promotional spikes,
and distribution profiles using Faker.

Usage:
    python -m src.ingestion.data_generator \
        --records 10000 --start 2023-01-01 --end 2024-12-31 --seed 42
"""

import logging
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import numpy as np
import pandas as pd
from faker import Faker

from ingestion.models import Customer, Order, OrderItem, Product

logger = logging.getLogger(__name__)

# ── Product catalogue templates ──────────────────────────────────────────────
PRODUCT_TEMPLATES: dict[str, list[str]] = {
    "Electronics": [
        "Wireless Headphones", "Smart Watch", "Bluetooth Speaker",
        "USB-C Hub", "Mechanical Keyboard", "Webcam HD",
        "Portable Charger", "LED Desk Lamp", "Noise Canceller",
        "Digital Thermometer",
    ],
    "Clothing": [
        "Cotton T-Shirt", "Denim Jacket", "Running Shorts",
        "Wool Sweater", "Silk Scarf", "Canvas Sneakers",
        "Yoga Pants", "Linen Shirt", "Beanie Hat", "Leather Belt",
    ],
    "Home": [
        "Scented Candle Set", "Throw Pillow", "Wall Clock",
        "Plant Pot Ceramic", "Kitchen Scale", "Bath Towel Set",
        "Photo Frame", "Door Mat", "Storage Basket", "Coaster Set",
    ],
    "Sports": [
        "Yoga Mat", "Resistance Band Set", "Jump Rope",
        "Water Bottle", "Gym Gloves", "Foam Roller",
        "Tennis Balls Pack", "Hiking Socks", "Swim Goggles",
        "Fitness Tracker Band",
    ],
    "Beauty": [
        "Moisturiser SPF30", "Lip Balm Organic", "Face Serum",
        "Hair Oil", "Nail Polish Set", "Eye Cream",
        "Body Lotion", "Sunscreen Mist", "Face Mask Pack",
        "Perfume Rollerball",
    ],
}

# ── Customer segments ────────────────────────────────────────────────────────
SEGMENTS = ["Premium", "Standard", "Budget", "New", "VIP"]
REGIONS = [
    "North America", "Europe", "Asia Pacific",
    "Latin America", "Middle East", "Africa",
]

# ── Distribution constants ───────────────────────────────────────────────────
STATUS_WEIGHTS = {
    "Completed": 0.85,
    "Refunded": 0.08,
    "Pending": 0.04,
    "Cancelled": 0.03,
}
CHANNEL_WEIGHTS = {
    "web": 0.60,
    "mobile": 0.25,
    "marketplace": 0.10,
    "in-store": 0.05,
}


class DataGenerator:
    """Generates synthetic e-commerce data with realistic distributions.

    Supports seasonal and promotional uplift patterns, log-normal
    price distributions, and configurable seeding for reproducibility.

    Attributes:
        n_customers: Number of customers to generate.
        n_products: Number of products to generate.
        n_orders: Number of orders to generate.
        start_date: Earliest possible order date.
        end_date: Latest possible order date.
    """

    def __init__(
        self,
        n_customers: int = 500,
        n_products: int = 100,
        n_orders: int = 5000,
        start_date: str = "2023-01-01",
        end_date: str = "2024-12-31",
        seed: Optional[int] = None,
    ) -> None:
        """Initialise the data generator.

        Args:
            n_customers: Number of customer records.
            n_products: Number of product records.
            n_orders: Number of order records.
            start_date: Start of the order date range (YYYY-MM-DD).
            end_date: End of the order date range (YYYY-MM-DD).
            seed: Random seed for reproducibility.
        """
        self.n_customers = n_customers
        self.n_products = n_products
        self.n_orders = n_orders
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        self.seed = seed

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            self.fake = Faker()
            Faker.seed(seed)
        else:
            self.fake = Faker()

        self._customers: list[Customer] = []
        self._products: list[Product] = []
        self._orders: list[Order] = []
        self._order_items: list[OrderItem] = []

    # ── Date distribution helpers ────────────────────────────────────────

    def _generate_order_dates(self) -> list[date]:
        """Generate order dates with seasonal, weekend, and promo uplift.

        Returns:
            A list of dates, one per order, respecting the configured
            distribution patterns.
        """
        total_days = (self.end_date - self.start_date).days + 1
        all_dates = [
            self.start_date + timedelta(days=i)
            for i in range(total_days)
        ]

        # Build daily weights
        weights = []
        # Pre-compute promotional spike days (3 random per year)
        years = set(d.year for d in all_dates)
        promo_dates: set[date] = set()
        for year in years:
            year_dates = [d for d in all_dates if d.year == year]
            if len(year_dates) >= 3:
                promo_dates.update(random.sample(year_dates, 3))

        for d in all_dates:
            w = 1.0
            # Seasonal uplift: Nov/Dec at 2.5×
            if d.month in (11, 12):
                w *= 2.5
            # Weekend uplift: Sat/Sun at 1.3×
            if d.weekday() >= 5:
                w *= 1.3
            # Promotional spikes: 4×
            if d in promo_dates:
                w *= 4.0
            weights.append(w)

        # Normalise and sample
        total_w = sum(weights)
        probs = [w / total_w for w in weights]
        chosen_indices = np.random.choice(
            len(all_dates), size=self.n_orders, p=probs
        )
        return [all_dates[i] for i in chosen_indices]

    # ── Generator methods ────────────────────────────────────────────────

    def generate_customers(self) -> list[Customer]:
        """Generate synthetic customer records.

        Returns:
            List of Customer dataclass instances.
        """
        customers: list[Customer] = []
        for i in range(self.n_customers):
            reg_date = self.fake.date_between(
                start_date=self.start_date - timedelta(days=365),
                end_date=self.end_date,
            )
            customer = Customer(
                customer_id=f"CUST-{i+1:06d}",
                email=self.fake.email(),
                registration_date=reg_date,
                region=random.choice(REGIONS),
                segment=random.choice(SEGMENTS),
            )
            customers.append(customer)

        self._customers = customers
        logger.info("Generated %d customers.", len(customers))
        return customers

    def generate_products(self) -> list[Product]:
        """Generate synthetic product records with log-normal pricing.

        Returns:
            List of Product dataclass instances.
        """
        products: list[Product] = []
        all_templates = [
            (cat, name)
            for cat, names in PRODUCT_TEMPLATES.items()
            for name in names
        ]

        for i in range(self.n_products):
            category, base_name = all_templates[i % len(all_templates)]
            # Add variant suffix for uniqueness
            variant = f" v{i // len(all_templates) + 1}" if i >= len(all_templates) else ""

            # Log-normal price: mean ~$45, std ~$30
            list_price = max(
                5.0, float(np.random.lognormal(mean=3.5, sigma=0.7))
            )
            list_price = round(list_price, 2)
            # Cost = 55–70% of list price
            cost_ratio = random.uniform(0.55, 0.70)
            cost_price = round(list_price * cost_ratio, 2)

            product = Product(
                product_id=f"PROD-{i+1:05d}",
                name=f"{base_name}{variant}",
                category=category,
                cost_price=cost_price,
                list_price=list_price,
                is_active=random.random() > 0.05,
            )
            products.append(product)

        self._products = products
        logger.info("Generated %d products.", len(products))
        return products

    def generate_orders(self) -> list[Order]:
        """Generate synthetic order records.

        Requires generate_customers() to have been called first.

        Returns:
            List of Order dataclass instances.
        """
        if not self._customers:
            raise RuntimeError(
                "Must call generate_customers() before generate_orders()"
            )

        statuses = list(STATUS_WEIGHTS.keys())
        status_probs = list(STATUS_WEIGHTS.values())
        channels = list(CHANNEL_WEIGHTS.keys())
        channel_probs = list(CHANNEL_WEIGHTS.values())

        order_dates = self._generate_order_dates()
        orders: list[Order] = []

        for i, order_date in enumerate(order_dates):
            customer = random.choice(self._customers)

            # Total amount placeholder — will be refined by order items
            base_total = max(
                5.0, float(np.random.lognormal(mean=3.8, sigma=0.8))
            )
            base_total = round(base_total, 2)

            # Discount: ~30% of orders get a discount
            has_discount = random.random() < 0.30
            discount = round(
                base_total * random.uniform(0.05, 0.25), 2
            ) if has_discount else 0.0

            order = Order(
                order_id=f"ORD-{i+1:07d}",
                customer_id=customer.customer_id,
                order_date=order_date,
                status=random.choices(statuses, weights=status_probs, k=1)[0],
                total_amount=base_total,
                discount_amount=discount,
                channel=random.choices(
                    channels, weights=channel_probs, k=1
                )[0],
            )
            orders.append(order)

        self._orders = orders
        logger.info("Generated %d orders.", len(orders))
        return orders

    def generate_order_items(self) -> list[OrderItem]:
        """Generate synthetic order item records.

        Requires generate_orders() and generate_products() to have been
        called first.  Each order gets 1–5 line items.

        Returns:
            List of OrderItem dataclass instances.
        """
        if not self._orders:
            raise RuntimeError(
                "Must call generate_orders() before generate_order_items()"
            )
        if not self._products:
            raise RuntimeError(
                "Must call generate_products() before generate_order_items()"
            )

        items: list[OrderItem] = []
        item_counter = 0

        for order in self._orders:
            n_items = random.randint(1, 5)
            chosen_products = random.sample(
                self._products, min(n_items, len(self._products))
            )

            for product in chosen_products:
                item_counter += 1
                quantity = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.50, 0.25, 0.15, 0.07, 0.03],
                    k=1,
                )[0]

                # Return flag: 12% of completed order items
                is_returned = (
                    order.status == "Completed" and random.random() < 0.12
                )

                item = OrderItem(
                    item_id=f"ITEM-{item_counter:08d}",
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=quantity,
                    unit_price=product.list_price,
                    return_flag=is_returned,
                )
                items.append(item)

        self._order_items = items
        logger.info("Generated %d order items.", len(items))
        return items

    def generate_all(self) -> dict[str, list]:
        """Generate all entity types in correct dependency order.

        Returns:
            Dict with keys 'customers', 'products', 'orders',
            'order_items', each mapping to a list of dataclass instances.
        """
        return {
            "customers": self.generate_customers(),
            "products": self.generate_products(),
            "orders": self.generate_orders(),
            "order_items": self.generate_order_items(),
        }

    # ── Export methods ───────────────────────────────────────────────────

    def to_csv(self, output_dir: str = "data") -> dict[str, str]:
        """Save all generated data to CSV files.

        Args:
            output_dir: Directory to write CSV files into.

        Returns:
            Dict mapping entity name to the saved file path.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths: dict[str, str] = {}

        for name, records in [
            ("customers", self._customers),
            ("products", self._products),
            ("orders", self._orders),
            ("order_items", self._order_items),
        ]:
            if not records:
                logger.warning("No %s to export — skipping.", name)
                continue

            df = pd.DataFrame([vars(r) for r in records])
            filepath = str(out / f"{name}.csv")
            df.to_csv(filepath, index=False)
            paths[name] = filepath
            logger.info("Saved %d %s to %s", len(records), name, filepath)

        return paths

    def to_sqlite(self, db_manager: "DatabaseManager") -> None:
        """Insert all generated records into the SQLite database.

        Args:
            db_manager: An initialised DatabaseManager instance.
        """
        from db.database import DatabaseManager  # noqa: F811

        for name, records, sql in [
            (
                "customers", self._customers,
                "INSERT OR IGNORE INTO customers "
                "(customer_id, email, registration_date, region, segment) "
                "VALUES (?, ?, ?, ?, ?)",
            ),
            (
                "products", self._products,
                "INSERT OR IGNORE INTO products "
                "(product_id, name, category, cost_price, list_price, "
                "is_active) VALUES (?, ?, ?, ?, ?, ?)",
            ),
            (
                "orders", self._orders,
                "INSERT OR IGNORE INTO orders "
                "(order_id, customer_id, order_date, status, total_amount, "
                "discount_amount, channel) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ),
            (
                "order_items", self._order_items,
                "INSERT OR IGNORE INTO order_items "
                "(item_id, order_id, product_id, quantity, unit_price, "
                "return_flag) VALUES (?, ?, ?, ?, ?, ?)",
            ),
        ]:
            if not records:
                continue

            data = []
            for r in records:
                vals = list(vars(r).values())
                # Convert date objects to ISO strings
                vals = [
                    v.isoformat() if isinstance(v, date) else v
                    for v in vals
                ]
                # Convert booleans to integers for SQLite
                vals = [int(v) if isinstance(v, bool) else v for v in vals]
                data.append(tuple(vals))

            db_manager.execute_many(sql, data)
            logger.info(
                "Inserted %d %s into database.", len(records), name
            )


# ── CLI entry point ──────────────────────────────────────────────────────────

@click.command("generate")
@click.option(
    "--records", default=10000, show_default=True,
    help="Number of orders to generate.",
)
@click.option(
    "--start", default="2023-01-01", show_default=True,
    help="Start date (YYYY-MM-DD).",
)
@click.option(
    "--end", default="2024-12-31", show_default=True,
    help="End date (YYYY-MM-DD).",
)
@click.option(
    "--seed", default=None, type=int,
    help="Random seed for reproducibility.",
)
@click.option(
    "--output-dir", default="data", show_default=True,
    help="Output directory for CSV files.",
)
def main(
    records: int,
    start: str,
    end: str,
    seed: Optional[int],
    output_dir: str,
) -> None:
    """Generate synthetic e-commerce data."""
    click.echo(f"Generating {records} orders ({start} to {end})...")
    n_customers = max(100, records // 10)
    n_products = max(50, records // 50)

    gen = DataGenerator(
        n_customers=n_customers,
        n_products=n_products,
        n_orders=records,
        start_date=start,
        end_date=end,
        seed=seed,
    )
    gen.generate_all()
    paths = gen.to_csv(output_dir)

    click.echo("\n✅ Data generated successfully:")
    for name, path in paths.items():
        click.echo(f"   {name}: {path}")


if __name__ == "__main__":
    main()
