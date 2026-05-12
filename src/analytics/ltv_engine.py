"""Customer Lifetime Value (LTV) engine.

Computes historical and projected LTV with retention-based
probability modelling and segment-level analysis.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from db.database import DatabaseManager

logger = logging.getLogger(__name__)


class LTVEngine:
    """Computes customer lifetime value metrics.

    Supports historical LTV calculation, retention-based projected LTV,
    and analysis by RFM segment and acquisition channel.

    Attributes:
        db_manager: DatabaseManager for data retrieval.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialise the LTV engine.

        Args:
            db_manager: An active DatabaseManager instance.
        """
        self.db_manager = db_manager
        self._ltv_df: Optional[pd.DataFrame] = None

    def historical_ltv(
        self, customer_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Calculate historical lifetime value per customer.

        Args:
            customer_id: Optional single customer ID. If provided,
                         returns a single-row DataFrame.

        Returns:
            DataFrame with customer_id, registration_date,
            total_orders, total_spend (historical LTV).
        """
        sql = """
            SELECT
                c.customer_id,
                c.registration_date,
                COUNT(DISTINCT o.order_id) AS total_orders,
                COALESCE(
                    SUM(o.total_amount - o.discount_amount), 0
                ) AS total_spend
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
                AND o.status = 'Completed'
        """
        params = {}
        if customer_id:
            sql += " WHERE c.customer_id = :customer_id"
            params["customer_id"] = customer_id

        sql += " GROUP BY c.customer_id, c.registration_date"

        df = self.db_manager.execute_query(sql, params)
        logger.info("Computed historical LTV for %d customers.", len(df))
        return df

    def projected_ltv(
        self,
        projection_months: int = 12,
    ) -> pd.DataFrame:
        """Calculate projected LTV for all customers.

        Uses retention probability based on recency:
        - Purchased within 30 days: retention = 1.0
        - 31–60 days: retention = 0.7
        - 61–90 days: retention = 0.4
        - >90 days: retention = 0.1

        Args:
            projection_months: Number of months to project forward.

        Returns:
            DataFrame with customer_id, historical_ltv, projected_ltv,
            retention_probability, ltv_segment.
        """
        today = date.today()

        sql = """
            SELECT
                c.customer_id,
                COALESCE(SUM(CASE WHEN o.status = 'Completed'
                    THEN o.total_amount - o.discount_amount ELSE 0 END),
                0) AS historical_ltv,
                COUNT(DISTINCT CASE WHEN o.status = 'Completed'
                    THEN o.order_id END) AS total_orders,
                MAX(o.order_date) AS last_order_date,
                MIN(o.order_date) AS first_order_date
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id
        """
        df = self.db_manager.execute_query(sql)

        if df.empty:
            return pd.DataFrame(columns=[
                "customer_id", "historical_ltv", "projected_ltv",
                "retention_probability", "ltv_segment",
            ])

        # Calculate recency and retention probability
        df["last_order_date"] = pd.to_datetime(
            df["last_order_date"], errors="coerce"
        )
        df["days_since_last"] = (
            pd.Timestamp(today) - df["last_order_date"]
        ).dt.days.fillna(9999)

        df["retention_probability"] = df["days_since_last"].apply(
            self._retention_probability
        )

        # Calculate monthly spend rate
        df["first_order_date"] = pd.to_datetime(
            df["first_order_date"], errors="coerce"
        )
        df["months_active"] = (
            (pd.Timestamp(today) - df["first_order_date"]).dt.days / 30.44
        ).clip(lower=1)

        df["avg_monthly_spend"] = (
            df["historical_ltv"] / df["months_active"]
        )

        # Projected LTV
        df["projected_ltv"] = (
            df["avg_monthly_spend"]
            * projection_months
            * df["retention_probability"]
        ).round(2)

        # LTV segments based on percentiles
        df["ltv_segment"] = self._assign_ltv_segments(df["projected_ltv"])

        self._ltv_df = df[[
            "customer_id", "historical_ltv", "projected_ltv",
            "retention_probability", "ltv_segment",
        ]].copy()

        logger.info("Computed projected LTV for %d customers.", len(df))
        return self._ltv_df

    def ltv_by_segment(
        self, rfm_segments_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Calculate average projected LTV per RFM segment.

        Args:
            rfm_segments_df: DataFrame with customer_id and segment
                            columns (from RFMEngine).

        Returns:
            DataFrame with segment and avg_projected_ltv.
        """
        if self._ltv_df is None:
            self.projected_ltv()

        merged = self._ltv_df.merge(
            rfm_segments_df[["customer_id", "segment"]],
            on="customer_id",
            how="left",
        )

        result = merged.groupby("segment").agg(
            avg_projected_ltv=("projected_ltv", "mean"),
            customer_count=("customer_id", "count"),
            total_projected_ltv=("projected_ltv", "sum"),
        ).reset_index()

        result["avg_projected_ltv"] = result["avg_projected_ltv"].round(2)
        result["total_projected_ltv"] = result["total_projected_ltv"].round(2)

        return result.sort_values("avg_projected_ltv", ascending=False)

    def ltv_by_channel(self) -> pd.DataFrame:
        """Calculate average LTV grouped by acquisition channel.

        The acquisition channel is the channel of a customer's
        first order.

        Returns:
            DataFrame with channel and avg_ltv.
        """
        sql = """
            WITH first_orders AS (
                SELECT
                    customer_id,
                    channel,
                    ROW_NUMBER() OVER (
                        PARTITION BY customer_id
                        ORDER BY order_date
                    ) AS rn
                FROM orders
            )
            SELECT
                fo.channel AS acquisition_channel,
                COUNT(DISTINCT c.customer_id) AS customer_count,
                ROUND(AVG(COALESCE(totals.total_spend, 0)), 2) AS avg_ltv
            FROM first_orders fo
            JOIN customers c ON fo.customer_id = c.customer_id
            LEFT JOIN (
                SELECT customer_id,
                       SUM(total_amount - discount_amount) AS total_spend
                FROM orders WHERE status = 'Completed'
                GROUP BY customer_id
            ) totals ON c.customer_id = totals.customer_id
            WHERE fo.rn = 1
            GROUP BY fo.channel
            ORDER BY avg_ltv DESC
        """
        return self.db_manager.execute_query(sql)

    def ltv_summary(self) -> dict:
        """Generate an LTV summary with aggregate metrics.

        Returns:
            Dict with keys: avg_ltv, median_ltv,
            total_projected_revenue, high_value_customer_count,
            high_value_revenue_pct.
        """
        if self._ltv_df is None:
            self.projected_ltv()

        df = self._ltv_df
        total_rev = float(df["projected_ltv"].sum())
        high_value = df[df["ltv_segment"] == "High"]
        high_rev = float(high_value["projected_ltv"].sum())

        return {
            "avg_ltv": round(float(df["projected_ltv"].mean()), 2),
            "median_ltv": round(float(df["projected_ltv"].median()), 2),
            "total_projected_revenue": round(total_rev, 2),
            "high_value_customer_count": len(high_value),
            "high_value_revenue_pct": round(
                high_rev / total_rev * 100, 2
            ) if total_rev > 0 else 0.0,
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _retention_probability(days_since: float) -> float:
        """Calculate retention probability from days since last purchase.

        Args:
            days_since: Number of days since last purchase.

        Returns:
            Retention probability between 0 and 1.
        """
        if days_since <= 30:
            return 1.0
        elif days_since <= 60:
            return 0.7
        elif days_since <= 90:
            return 0.4
        else:
            return 0.1

    @staticmethod
    def _assign_ltv_segments(ltv_series: pd.Series) -> pd.Series:
        """Assign LTV segments based on percentile thresholds.

        High: top 20%  (≥ 80th percentile)
        Low:  bottom 30% (≤ 30th percentile)
        Medium: everything in between

        Args:
            ltv_series: Series of projected LTV values.

        Returns:
            Series of segment labels ('High', 'Medium', 'Low').
        """
        p80 = ltv_series.quantile(0.80)
        p30 = ltv_series.quantile(0.30)

        segments = pd.Series("Medium", index=ltv_series.index)
        segments[ltv_series >= p80] = "High"
        segments[ltv_series <= p30] = "Low"
        return segments
