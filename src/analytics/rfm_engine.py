"""RFM (Recency, Frequency, Monetary) segmentation engine.

Computes RFM scores using quintile-based scoring and assigns
customer segments based on configurable rules.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from db.database import DatabaseManager

logger = logging.getLogger(__name__)

# ── Segment assignment rules (applied in order) ─────────────────────────────
SEGMENT_RULES = [
    ("Champions",   lambda r: r["r_score"] == 5 and r["f_score"] >= 4 and r["m_score"] >= 4),
    ("Loyal",       lambda r: r["f_score"] >= 3 and r["m_score"] >= 3),
    ("Potential",   lambda r: r["r_score"] >= 4 and r["f_score"] <= 2),
    ("At Risk",     lambda r: r["r_score"] <= 2 and r["f_score"] >= 3),
    ("Hibernating", lambda r: r["r_score"] == 2 and r["f_score"] == 2),
    ("Lost",        lambda r: r["r_score"] == 1),
    ("Others",      lambda r: True),
]


class RFMEngine:
    """Computes RFM scores and assigns customer segments.

    Uses quintile-based scoring (1–5) for Recency, Frequency,
    and Monetary dimensions.

    Attributes:
        db_manager: DatabaseManager for data retrieval.
    """

    def __init__(self, db_manager: DatabaseManager) -> None:
        """Initialise the RFM engine.

        Args:
            db_manager: An active DatabaseManager instance.
        """
        self.db_manager = db_manager
        self._rfm_df: Optional[pd.DataFrame] = None
        self._segmented_df: Optional[pd.DataFrame] = None

    def compute_rfm(
        self, as_of_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Compute RFM scores for all customers.

        Args:
            as_of_date: Reference date (YYYY-MM-DD). Defaults to today.

        Returns:
            DataFrame with columns: customer_id, recency_days,
            frequency, monetary, r_score, f_score, m_score, rfm_score.
        """
        if as_of_date:
            ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        else:
            ref_date = date.today()

        # Fetch order data
        sql = """
            SELECT
                customer_id,
                MAX(order_date) AS last_order_date,
                COUNT(DISTINCT order_id) AS frequency,
                COALESCE(SUM(total_amount - discount_amount), 0) AS monetary
            FROM orders
            WHERE status = 'Completed'
            GROUP BY customer_id
        """
        df = self.db_manager.execute_query(sql)

        if df.empty:
            logger.warning("No completed orders found for RFM analysis.")
            return pd.DataFrame(columns=[
                "customer_id", "recency_days", "frequency", "monetary",
                "r_score", "f_score", "m_score", "rfm_score",
            ])

        # Convert dates and compute recency
        df["last_order_date"] = pd.to_datetime(df["last_order_date"])
        df["recency_days"] = (
            pd.Timestamp(ref_date) - df["last_order_date"]
        ).dt.days

        # Quintile scoring (1–5)
        # For recency, lower is better → reverse labels
        df["r_score"] = self._safe_qcut(
            df["recency_days"], labels=[5, 4, 3, 2, 1]
        )
        df["f_score"] = self._safe_qcut(
            df["frequency"], labels=[1, 2, 3, 4, 5]
        )
        df["m_score"] = self._safe_qcut(
            df["monetary"], labels=[1, 2, 3, 4, 5]
        )

        # Combined RFM score
        df["rfm_score"] = (
            df["r_score"].astype(str)
            + df["f_score"].astype(str)
            + df["m_score"].astype(str)
        )

        self._rfm_df = df[[
            "customer_id", "recency_days", "frequency", "monetary",
            "r_score", "f_score", "m_score", "rfm_score",
        ]].copy()

        logger.info("Computed RFM scores for %d customers.", len(df))
        return self._rfm_df

    def assign_segment(
        self, rfm_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Assign customer segments based on RFM scores.

        Args:
            rfm_df: DataFrame with RFM scores. If None, uses the
                    last computed RFM DataFrame.

        Returns:
            DataFrame with an added 'segment' column.
        """
        if rfm_df is None:
            rfm_df = self._rfm_df
        if rfm_df is None or rfm_df.empty:
            raise ValueError("No RFM data. Call compute_rfm() first.")

        df = rfm_df.copy()
        df["segment"] = "Others"

        for _, row in df.iterrows():
            for seg_name, rule_fn in SEGMENT_RULES:
                if rule_fn(row):
                    df.loc[df.index == row.name, "segment"] = seg_name
                    break

        self._segmented_df = df
        logger.info("Assigned segments to %d customers.", len(df))
        return df

    def segment_summary(self) -> pd.DataFrame:
        """Generate a summary of customer segments.

        Returns:
            DataFrame with segment, customer_count, total_revenue,
            avg_monetary, pct_of_customers, pct_of_revenue.
        """
        if self._segmented_df is None:
            raise ValueError("No segments assigned. Call assign_segment().")

        df = self._segmented_df
        total_customers = len(df)
        total_revenue = df["monetary"].sum()

        summary = df.groupby("segment").agg(
            customer_count=("customer_id", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
        ).reset_index()

        summary["pct_of_customers"] = round(
            summary["customer_count"] / total_customers * 100, 2
        )
        summary["pct_of_revenue"] = round(
            summary["total_revenue"] / total_revenue * 100, 2
        ) if total_revenue > 0 else 0.0

        summary["avg_monetary"] = summary["avg_monetary"].round(2)

        return summary.sort_values("total_revenue", ascending=False)

    def churn_risk_customers(
        self, days_threshold: int = 90,
    ) -> pd.DataFrame:
        """Identify customers at risk of churning.

        Args:
            days_threshold: Number of days since last purchase to
                           consider as churn risk.

        Returns:
            DataFrame of at-risk customers with their RFM data.
        """
        if self._rfm_df is None:
            raise ValueError("No RFM data. Call compute_rfm() first.")

        at_risk = self._rfm_df[
            self._rfm_df["recency_days"] > days_threshold
        ].copy()

        logger.info(
            "Found %d customers with no purchase in > %d days.",
            len(at_risk), days_threshold,
        )
        return at_risk.sort_values("recency_days", ascending=False)

    def export_segments(self, output_path: str) -> str:
        """Export segment assignments to a CSV file.

        Args:
            output_path: Path for the output CSV file.

        Returns:
            Path to the saved file.
        """
        if self._segmented_df is None:
            raise ValueError("No segments. Call assign_segment() first.")

        self._segmented_df.to_csv(output_path, index=False)
        logger.info("Exported segments to %s", output_path)
        return output_path

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_qcut(
        series: pd.Series,
        labels: list[int],
        q: int = 5,
    ) -> pd.Series:
        """Apply pd.qcut with fallback for low-cardinality data.

        Args:
            series: Numeric series to bin.
            labels: Labels for each quantile bin.
            q: Number of quantiles.

        Returns:
            Series of integer scores.
        """
        try:
            return pd.qcut(
                series, q=q, labels=labels, duplicates="drop"
            ).astype(int)
        except (ValueError, TypeError):
            # Fallback: rank-based scoring
            ranks = series.rank(method="first", pct=True)
            bins = pd.cut(
                ranks, bins=q, labels=labels, include_lowest=True,
            )
            return bins.astype(int)
