"""Query library providing typed wrappers for all named SQL queries.

Each method validates parameters and delegates to QueryEngine for
execution, returning typed DataFrames.
"""

import logging
from typing import Optional

import pandas as pd

from engine.exceptions import InvalidParameterError
from engine.query_engine import QueryEngine

logger = logging.getLogger(__name__)


class QueryLibrary:
    """Typed wrapper methods for all 15 named SQL queries.

    Provides parameter validation and consistent return types
    for every query in the platform.

    Attributes:
        engine: The underlying QueryEngine instance.
    """

    def __init__(self, engine: QueryEngine) -> None:
        """Initialise the query library.

        Args:
            engine: An active QueryEngine instance.
        """
        self.engine = engine

    # ── 01: Revenue by Period ────────────────────────────────────────────

    def revenue_by_period(
        self,
        start_date: str,
        end_date: str,
        period: str = "month",
    ) -> pd.DataFrame:
        """Get revenue metrics grouped by time period.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            period: Grouping period — 'day', 'week', 'month', 'quarter'.

        Returns:
            DataFrame with columns: period_label, total_revenue,
            order_count, aov.
        """
        if period not in ("day", "week", "month", "quarter"):
            raise InvalidParameterError(
                f"period must be day/week/month/quarter, got {period!r}"
            )
        return self.engine.run_named_query(
            "01_revenue_by_period",
            {"start_date": start_date, "end_date": end_date,
             "period": period},
        )

    # ── 02: Revenue Growth ───────────────────────────────────────────────

    def revenue_growth(self, year: str) -> pd.DataFrame:
        """Get month-over-month revenue growth.

        Args:
            year: Four-digit year string (e.g. '2024').

        Returns:
            DataFrame with columns: month_label, monthly_revenue,
            prev_month_revenue, growth_pct.
        """
        return self.engine.run_named_query(
            "02_revenue_growth", {"year": year},
        )

    # ── 03: Top Products ─────────────────────────────────────────────────

    def top_products(
        self,
        start_date: str,
        end_date: str,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Get top N products by revenue.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            limit: Number of products to return.

        Returns:
            DataFrame with revenue, units, return rate, and rank.
        """
        if limit < 1:
            raise InvalidParameterError("limit must be >= 1")
        return self.engine.run_named_query(
            "03_top_products",
            {"start_date": start_date, "end_date": end_date,
             "limit": limit},
        )

    # ── 04: Bottom Products ──────────────────────────────────────────────

    def bottom_products(
        self,
        start_date: str,
        end_date: str,
        limit: int = 10,
    ) -> pd.DataFrame:
        """Get bottom N products by revenue.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            limit: Number of products to return.

        Returns:
            DataFrame with revenue and units for worst performers.
        """
        if limit < 1:
            raise InvalidParameterError("limit must be >= 1")
        return self.engine.run_named_query(
            "04_bottom_products",
            {"start_date": start_date, "end_date": end_date,
             "limit": limit},
        )

    # ── 05: Category Performance ─────────────────────────────────────────

    def category_performance(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get performance metrics per product category.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with revenue, margin%, units, return rate per
            category.
        """
        return self.engine.run_named_query(
            "05_category_performance",
            {"start_date": start_date, "end_date": end_date},
        )

    # ── 06: Customer Orders ──────────────────────────────────────────────

    def customer_orders(self, customer_id: str) -> pd.DataFrame:
        """Get order history for a specific customer.

        Args:
            customer_id: The customer's unique identifier.

        Returns:
            Single-row DataFrame with order summary.
        """
        if not customer_id:
            raise InvalidParameterError("customer_id must not be empty")
        return self.engine.run_named_query(
            "06_customer_orders", {"customer_id": customer_id},
        )

    # ── 07: New vs Returning ─────────────────────────────────────────────

    def new_vs_returning(self, year: str) -> pd.DataFrame:
        """Get new vs returning customer split by month.

        Args:
            year: Four-digit year string.

        Returns:
            DataFrame with monthly new/returning counts and revenue.
        """
        return self.engine.run_named_query(
            "07_new_vs_returning", {"year": year},
        )

    # ── 08: Cohort Retention ─────────────────────────────────────────────

    def cohort_retention(self, cohort_year: str) -> pd.DataFrame:
        """Get monthly cohort retention table.

        Args:
            cohort_year: Four-digit year string for cohorts.

        Returns:
            DataFrame with cohort_month, month_offset,
            active_customers, retention_pct.
        """
        return self.engine.run_named_query(
            "08_cohort_retention", {"cohort_year": cohort_year},
        )

    # ── 09: Channel Performance ──────────────────────────────────────────

    def channel_performance(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get performance metrics per sales channel.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with revenue, order count, AOV per channel.
        """
        return self.engine.run_named_query(
            "09_channel_performance",
            {"start_date": start_date, "end_date": end_date},
        )

    # ── 10: Refund Analysis ──────────────────────────────────────────────

    def refund_analysis(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get refund rates by category, product, and month.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with refund analysis breakdown.
        """
        return self.engine.run_named_query(
            "10_refund_analysis",
            {"start_date": start_date, "end_date": end_date},
        )

    # ── 11: Daily Sales Summary ──────────────────────────────────────────

    def daily_sales_summary(self, target_date: str) -> pd.DataFrame:
        """Get daily KPI snapshot for a single date.

        Args:
            target_date: The target date (YYYY-MM-DD).

        Returns:
            Single-row DataFrame with daily KPIs.
        """
        return self.engine.run_named_query(
            "11_daily_sales_summary", {"target_date": target_date},
        )

    # ── 12: Inventory Velocity ───────────────────────────────────────────

    def inventory_velocity(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get inventory velocity (units/day) per product.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with product velocity metrics.
        """
        return self.engine.run_named_query(
            "12_inventory_velocity",
            {"start_date": start_date, "end_date": end_date},
        )

    # ── 13: Discount Impact ──────────────────────────────────────────────

    def discount_impact(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get discount impact on AOV and refund rates.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame comparing discounted vs non-discounted orders.
        """
        return self.engine.run_named_query(
            "13_discount_impact",
            {"start_date": start_date, "end_date": end_date},
        )

    # ── 14: Customer Segments ────────────────────────────────────────────

    def customer_segments(self) -> pd.DataFrame:
        """Get customer count and revenue per segment.

        Returns:
            DataFrame with segment distribution and revenue.
        """
        return self.engine.run_named_query("14_customer_segments")

    # ── 15: Geographic Revenue ───────────────────────────────────────────

    def geographic_revenue(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Get revenue breakdown by customer region.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with regional revenue metrics.
        """
        return self.engine.run_named_query(
            "15_geographic_revenue",
            {"start_date": start_date, "end_date": end_date},
        )
