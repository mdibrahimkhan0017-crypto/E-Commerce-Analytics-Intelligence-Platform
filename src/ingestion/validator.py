"""Schema validator for the E-Commerce Analytics Platform.

Validates DataFrames against business rules for each entity type,
producing structured error reports and validation summaries.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from ingestion.models import (
    ALLOWED_CATEGORIES,
    ALLOWED_CHANNELS,
    ALLOWED_STATUSES,
    EMAIL_REGEX,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation results.

    Attributes:
        valid_df: DataFrame containing rows that passed validation.
        rejected_df: DataFrame containing rows that failed validation.
        errors: List of error detail dicts.
    """

    valid_df: pd.DataFrame
    rejected_df: pd.DataFrame
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate the validation pass rate as a percentage."""
        total = len(self.valid_df) + len(self.rejected_df)
        if total == 0:
            return 100.0
        return (len(self.valid_df) / total) * 100.0


class SchemaValidator:
    """Validates DataFrames against entity-specific business rules.

    Supports validation for customers, products, orders, and
    order_items tables with referential integrity checks.
    """

    def __init__(self, log_dir: str = "logs") -> None:
        """Initialise the validator.

        Args:
            log_dir: Directory for validation error log files.
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        db_manager: Optional[Any] = None,
    ) -> ValidationResult:
        """Validate a DataFrame according to the rules for table_name.

        Args:
            df: The DataFrame to validate.
            table_name: One of 'customers', 'products', 'orders',
                        'order_items'.
            db_manager: Optional DatabaseManager for referential checks.

        Returns:
            A ValidationResult with valid/rejected frames and errors.
        """
        validators = {
            "customers": self._validate_customers,
            "products": self._validate_products,
            "orders": self._validate_orders,
            "order_items": self._validate_order_items,
        }

        if table_name not in validators:
            raise ValueError(
                f"Unknown table: {table_name!r}. "
                f"Expected one of {list(validators.keys())}"
            )

        errors: list[dict[str, Any]] = []
        valid_mask = pd.Series(True, index=df.index)

        validator_fn = validators[table_name]
        valid_mask, errors = validator_fn(df, db_manager)

        valid_df = df[valid_mask].copy()
        rejected_df = df[~valid_mask].copy()

        result = ValidationResult(
            valid_df=valid_df,
            rejected_df=rejected_df,
            errors=errors,
        )

        # Persist error log
        if errors:
            self._save_errors(errors, table_name)

        logger.info(
            "Validation %s: %d valid, %d rejected (%.1f%% pass rate)",
            table_name, len(valid_df), len(rejected_df), result.pass_rate,
        )

        return result

    # ── Per-table validators ─────────────────────────────────────────────

    def _validate_customers(
        self,
        df: pd.DataFrame,
        db_manager: Optional[Any] = None,
    ) -> tuple[pd.Series, list[dict]]:
        """Validate customer records.

        Args:
            df: Customers DataFrame.
            db_manager: Unused for customers.

        Returns:
            Tuple of (valid_mask, errors_list).
        """
        errors: list[dict] = []
        valid_mask = pd.Series(True, index=df.index)

        for idx, row in df.iterrows():
            record_id = row.get("customer_id", f"row_{idx}")

            # Email format
            email = str(row.get("email", ""))
            if not EMAIL_REGEX.match(email):
                valid_mask[idx] = False
                errors.append(self._error(
                    "customers", record_id, "email",
                    "invalid_email_format", email,
                ))

            # Registration date not in future
            reg_date = row.get("registration_date")
            if reg_date:
                try:
                    if isinstance(reg_date, str):
                        reg_date = datetime.strptime(
                            reg_date, "%Y-%m-%d"
                        ).date()
                    elif isinstance(reg_date, datetime):
                        reg_date = reg_date.date()
                    if reg_date > date.today():
                        valid_mask[idx] = False
                        errors.append(self._error(
                            "customers", record_id, "registration_date",
                            "future_date", str(reg_date),
                        ))
                except (ValueError, TypeError):
                    valid_mask[idx] = False
                    errors.append(self._error(
                        "customers", record_id, "registration_date",
                        "invalid_date", str(reg_date),
                    ))

            # Region non-empty
            region = str(row.get("region", "")).strip()
            if not region:
                valid_mask[idx] = False
                errors.append(self._error(
                    "customers", record_id, "region",
                    "empty_value", "",
                ))

        return valid_mask, errors

    def _validate_products(
        self,
        df: pd.DataFrame,
        db_manager: Optional[Any] = None,
    ) -> tuple[pd.Series, list[dict]]:
        """Validate product records.

        Args:
            df: Products DataFrame.
            db_manager: Unused for products.

        Returns:
            Tuple of (valid_mask, errors_list).
        """
        errors: list[dict] = []
        valid_mask = pd.Series(True, index=df.index)

        for idx, row in df.iterrows():
            record_id = row.get("product_id", f"row_{idx}")

            # list_price > 0
            list_price = float(row.get("list_price", 0))
            if list_price <= 0:
                valid_mask[idx] = False
                errors.append(self._error(
                    "products", record_id, "list_price",
                    "non_positive_price", str(list_price),
                ))

            # cost_price < list_price
            cost_price = float(row.get("cost_price", 0))
            if cost_price >= list_price:
                valid_mask[idx] = False
                errors.append(self._error(
                    "products", record_id, "cost_price",
                    "cost_exceeds_list", f"{cost_price} >= {list_price}",
                ))

            # Valid category
            category = str(row.get("category", ""))
            if category not in ALLOWED_CATEGORIES:
                valid_mask[idx] = False
                errors.append(self._error(
                    "products", record_id, "category",
                    "invalid_category", category,
                ))

        return valid_mask, errors

    def _validate_orders(
        self,
        df: pd.DataFrame,
        db_manager: Optional[Any] = None,
    ) -> tuple[pd.Series, list[dict]]:
        """Validate order records.

        Args:
            df: Orders DataFrame.
            db_manager: Optional DB for referential integrity checks.

        Returns:
            Tuple of (valid_mask, errors_list).
        """
        errors: list[dict] = []
        valid_mask = pd.Series(True, index=df.index)

        # Load existing customer IDs for referential check
        existing_customers: set[str] = set()
        if db_manager:
            try:
                cust_df = db_manager.execute_query(
                    "SELECT customer_id FROM customers"
                )
                existing_customers = set(cust_df["customer_id"].tolist())
            except Exception:
                logger.warning("Could not load customers for ref check.")

        for idx, row in df.iterrows():
            record_id = row.get("order_id", f"row_{idx}")

            # total_amount >= 0
            total = float(row.get("total_amount", 0))
            if total < 0:
                valid_mask[idx] = False
                errors.append(self._error(
                    "orders", record_id, "total_amount",
                    "negative_amount", str(total),
                ))

            # discount_amount <= total_amount
            discount = float(row.get("discount_amount", 0))
            if discount > total:
                valid_mask[idx] = False
                errors.append(self._error(
                    "orders", record_id, "discount_amount",
                    "discount_exceeds_total",
                    f"{discount} > {total}",
                ))

            # order_date not in future
            order_date = row.get("order_date")
            if order_date:
                try:
                    if isinstance(order_date, str):
                        order_date = datetime.strptime(
                            order_date, "%Y-%m-%d"
                        ).date()
                    elif isinstance(order_date, datetime):
                        order_date = order_date.date()
                    if order_date > date.today():
                        valid_mask[idx] = False
                        errors.append(self._error(
                            "orders", record_id, "order_date",
                            "future_date", str(order_date),
                        ))
                except (ValueError, TypeError):
                    valid_mask[idx] = False
                    errors.append(self._error(
                        "orders", record_id, "order_date",
                        "invalid_date", str(order_date),
                    ))

            # Status in allowed values
            status = str(row.get("status", ""))
            if status not in ALLOWED_STATUSES:
                valid_mask[idx] = False
                errors.append(self._error(
                    "orders", record_id, "status",
                    "invalid_status", status,
                ))

            # Customer exists (referential integrity)
            cust_id = str(row.get("customer_id", ""))
            if existing_customers and cust_id not in existing_customers:
                valid_mask[idx] = False
                errors.append(self._error(
                    "orders", record_id, "customer_id",
                    "missing_customer", cust_id,
                ))

        return valid_mask, errors

    def _validate_order_items(
        self,
        df: pd.DataFrame,
        db_manager: Optional[Any] = None,
    ) -> tuple[pd.Series, list[dict]]:
        """Validate order item records.

        Args:
            df: Order items DataFrame.
            db_manager: Optional DB for referential integrity checks.

        Returns:
            Tuple of (valid_mask, errors_list).
        """
        errors: list[dict] = []
        valid_mask = pd.Series(True, index=df.index)

        # Load existing order and product IDs
        existing_orders: set[str] = set()
        existing_products: set[str] = set()
        if db_manager:
            try:
                ord_df = db_manager.execute_query(
                    "SELECT order_id FROM orders"
                )
                existing_orders = set(ord_df["order_id"].tolist())
                prod_df = db_manager.execute_query(
                    "SELECT product_id FROM products"
                )
                existing_products = set(prod_df["product_id"].tolist())
            except Exception:
                logger.warning(
                    "Could not load orders/products for ref check."
                )

        for idx, row in df.iterrows():
            record_id = row.get("item_id", f"row_{idx}")

            # quantity >= 1
            qty = int(row.get("quantity", 0))
            if qty < 1:
                valid_mask[idx] = False
                errors.append(self._error(
                    "order_items", record_id, "quantity",
                    "invalid_quantity", str(qty),
                ))

            # unit_price > 0
            price = float(row.get("unit_price", 0))
            if price <= 0:
                valid_mask[idx] = False
                errors.append(self._error(
                    "order_items", record_id, "unit_price",
                    "non_positive_price", str(price),
                ))

            # Referential checks
            order_id = str(row.get("order_id", ""))
            if existing_orders and order_id not in existing_orders:
                valid_mask[idx] = False
                errors.append(self._error(
                    "order_items", record_id, "order_id",
                    "missing_order", order_id,
                ))

            product_id = str(row.get("product_id", ""))
            if existing_products and product_id not in existing_products:
                valid_mask[idx] = False
                errors.append(self._error(
                    "order_items", record_id, "product_id",
                    "missing_product", product_id,
                ))

        return valid_mask, errors

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _error(
        table: str,
        record_id: str,
        field_name: str,
        rule: str,
        actual: str,
    ) -> dict[str, Any]:
        """Create a structured error dict.

        Args:
            table: Table name.
            record_id: Record identifier.
            field_name: Name of the invalid field.
            rule: Rule that was violated.
            actual: The actual value that failed.

        Returns:
            Structured error dictionary.
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "table": table,
            "record_id": str(record_id),
            "field": field_name,
            "rule_violated": rule,
            "actual_value": actual,
        }

    def _save_errors(
        self, errors: list[dict], table_name: str,
    ) -> str:
        """Save validation errors to a JSON file.

        Args:
            errors: List of error dicts.
            table_name: Name of the table being validated.

        Returns:
            Path to the saved error file.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_errors_{table_name}_{timestamp}.json"
        filepath = self.log_dir / filename

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(errors, fh, indent=2, default=str)

        logger.info("Validation errors saved to %s", filepath)
        return str(filepath)

    def generate_summary(
        self, results: dict[str, ValidationResult],
    ) -> str:
        """Generate a validation summary text file.

        Args:
            results: Dict mapping table names to ValidationResults.

        Returns:
            Path to the saved summary file.
        """
        lines = [
            "=" * 60,
            "VALIDATION SUMMARY",
            f"Generated: {datetime.utcnow().isoformat()}",
            "=" * 60,
            "",
        ]

        for table, result in results.items():
            total = len(result.valid_df) + len(result.rejected_df)
            lines.extend([
                f"Table: {table}",
                f"  Total records:    {total}",
                f"  Passed:           {len(result.valid_df)}",
                f"  Rejected:         {len(result.rejected_df)}",
                f"  Pass rate:        {result.pass_rate:.1f}%",
                "",
            ])

        summary_path = self.log_dir / "validation_summary.txt"
        summary_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Validation summary saved to %s", summary_path)
        return str(summary_path)
