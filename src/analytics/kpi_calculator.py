"""KPI calculator for the E-Commerce Analytics Platform.

Computes key performance indicators for sales, products, customers,
and time-series analysis with period comparison capabilities.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from engine.query_library import QueryLibrary

logger = logging.getLogger(__name__)


@dataclass
class KPIResult:
    """Container for KPI computation results.

    Attributes:
        period: The reporting period string.
        generated_at: Timestamp when the KPIs were generated.
        kpis: Dictionary of computed KPI values.
        metadata: Additional metadata about the computation.
    """

    period: str
    generated_at: str = ""
    kpis: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Set generation timestamp if not provided."""
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()


def compare_periods(
    kpi1: KPIResult,
    kpi2: KPIResult,
) -> pd.DataFrame:
    """Compare two KPI periods showing delta and % change.

    Args:
        kpi1: The baseline (earlier) KPI result.
        kpi2: The comparison (later) KPI result.

    Returns:
        DataFrame with columns: kpi_name, period_1, period_2,
        delta, pct_change.
    """
    rows = []
    all_keys = set(kpi1.kpis.keys()) | set(kpi2.kpis.keys())

    for key in sorted(all_keys):
        v1 = kpi1.kpis.get(key)
        v2 = kpi2.kpis.get(key)

        # Only compare numeric values
        if not isinstance(v1, (int, float)) or not isinstance(v2, (int, float)):
            continue

        delta = v2 - v1
        pct = (delta / v1 * 100) if v1 != 0 else None

        rows.append({
            "kpi_name": key,
            f"period_1 ({kpi1.period})": v1,
            f"period_2 ({kpi2.period})": v2,
            "delta": round(delta, 2),
            "pct_change": round(pct, 2) if pct is not None else None,
        })

    return pd.DataFrame(rows)


class KPICalculator:
    """Computes key performance indicators from query results.

    Uses QueryLibrary to fetch data and compute sales, product,
    customer, and time-series KPIs.

    Attributes:
        query_lib: The QueryLibrary instance for data retrieval.
    """

    def __init__(self, query_lib: QueryLibrary) -> None:
        """Initialise the KPI calculator.

        Args:
            query_lib: An active QueryLibrary instance.
        """
        self.query_lib = query_lib

    def sales_kpis(
        self, start_date: str, end_date: str,
    ) -> dict[str, Any]:
        """Compute core sales KPIs for the given period.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            Dict with keys: total_revenue, total_orders, aov,
            revenue_growth_pct, refund_rate_pct, discount_rate_pct,
            avg_items_per_order.
        """
        try:
            rev_df = self.query_lib.revenue_by_period(
                start_date, end_date, "month"
            )
            total_revenue = float(rev_df["total_revenue"].sum()) if not rev_df.empty else 0.0
            total_orders = int(rev_df["order_count"].sum()) if not rev_df.empty else 0
            aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

            # Revenue growth
            year = start_date[:4]
            growth_df = self.query_lib.revenue_growth(year)
            growth_pct = float(
                growth_df["growth_pct"].dropna().iloc[-1]
            ) if not growth_df.empty and not growth_df["growth_pct"].dropna().empty else 0.0

            # Refund analysis
            refund_df = self.query_lib.refund_analysis(start_date, end_date)
            total_items = int(refund_df["total_items"].sum()) if not refund_df.empty else 0
            returned = int(refund_df["returned_items"].sum()) if not refund_df.empty else 0
            refund_rate = round(
                returned / total_items * 100, 2
            ) if total_items > 0 else 0.0

            # Discount impact
            disc_df = self.query_lib.discount_impact(start_date, end_date)
            total_disc_orders = int(disc_df["order_count"].sum()) if not disc_df.empty else 0
            disc_orders = int(
                disc_df[disc_df["discount_group"] == "With Discount"]["order_count"].sum()
            ) if not disc_df.empty and "discount_group" in disc_df.columns else 0
            discount_rate = round(
                disc_orders / total_disc_orders * 100, 2
            ) if total_disc_orders > 0 else 0.0

            # Average items per order
            avg_items = round(total_items / total_orders, 2) if total_orders > 0 else 0.0

            return {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "aov": aov,
                "revenue_growth_pct": growth_pct,
                "refund_rate_pct": refund_rate,
                "discount_rate_pct": discount_rate,
                "avg_items_per_order": avg_items,
            }
        except Exception as exc:
            logger.error("Failed to compute sales KPIs: %s", exc)
            return {
                "total_revenue": 0.0, "total_orders": 0, "aov": 0.0,
                "revenue_growth_pct": 0.0, "refund_rate_pct": 0.0,
                "discount_rate_pct": 0.0, "avg_items_per_order": 0.0,
            }

    def product_kpis(
        self, start_date: str, end_date: str,
    ) -> pd.DataFrame:
        """Compute per-product KPIs.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            DataFrame with one row per product: revenue_contribution_pct,
            units_sold, return_rate_pct, margin_pct, rank.
        """
        try:
            top_df = self.query_lib.top_products(
                start_date, end_date, limit=9999
            )
            if top_df.empty:
                return pd.DataFrame()

            total_rev = top_df["total_revenue"].sum()
            top_df["revenue_contribution_pct"] = round(
                top_df["total_revenue"] / total_rev * 100, 2
            )

            # Get category data for margin
            cat_df = self.query_lib.category_performance(
                start_date, end_date
            )
            margin_map = dict(
                zip(cat_df["category"], cat_df["margin_pct"])
            ) if not cat_df.empty else {}

            top_df["margin_pct"] = top_df["category"].map(margin_map).fillna(0)
            top_df["rank"] = top_df["total_revenue"].rank(
                ascending=False, method="dense"
            ).astype(int)

            return top_df[[
                "product_id", "product_name", "category",
                "revenue_contribution_pct", "units_sold",
                "return_rate_pct", "margin_pct", "rank",
            ]]
        except Exception as exc:
            logger.error("Failed to compute product KPIs: %s", exc)
            return pd.DataFrame()

    def customer_kpis(
        self, start_date: str, end_date: str,
    ) -> dict[str, Any]:
        """Compute customer-level KPIs.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            Dict with total_customers, new_customers,
            returning_customers, repeat_rate_pct,
            avg_purchase_frequency.
        """
        try:
            year = start_date[:4]
            nvr_df = self.query_lib.new_vs_returning(year)

            if nvr_df.empty:
                return {
                    "total_customers": 0, "new_customers": 0,
                    "returning_customers": 0, "repeat_rate_pct": 0.0,
                    "avg_purchase_frequency": 0.0,
                }

            new_total = int(nvr_df["new_customers"].sum())
            returning_total = int(nvr_df["returning_customers"].sum())
            total_cust = new_total + returning_total

            repeat_rate = round(
                returning_total / total_cust * 100, 2
            ) if total_cust > 0 else 0.0

            # Segments for frequency
            seg_df = self.query_lib.customer_segments()
            total_seg_customers = int(
                seg_df["customer_count"].sum()
            ) if not seg_df.empty else 0
            total_seg_revenue = float(
                seg_df["total_revenue"].sum()
            ) if not seg_df.empty else 0.0

            avg_freq = round(
                (new_total + returning_total) / max(total_seg_customers, 1), 2
            )

            return {
                "total_customers": total_seg_customers,
                "new_customers": new_total,
                "returning_customers": returning_total,
                "repeat_rate_pct": repeat_rate,
                "avg_purchase_frequency": avg_freq,
            }
        except Exception as exc:
            logger.error("Failed to compute customer KPIs: %s", exc)
            return {
                "total_customers": 0, "new_customers": 0,
                "returning_customers": 0, "repeat_rate_pct": 0.0,
                "avg_purchase_frequency": 0.0,
            }

    def time_series_kpis(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "monthly",
    ) -> pd.DataFrame:
        """Compute time-series KPIs at the given granularity.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            granularity: Time granularity — 'daily', 'weekly',
                         'monthly', 'quarterly'.

        Returns:
            Date-indexed DataFrame with revenue, orders, aov,
            new_customers per period.
        """
        period_map = {
            "daily": "day", "weekly": "week",
            "monthly": "month", "quarterly": "quarter",
        }
        period = period_map.get(granularity, "month")

        try:
            rev_df = self.query_lib.revenue_by_period(
                start_date, end_date, period
            )
            if rev_df.empty:
                return pd.DataFrame()

            result = rev_df.rename(columns={
                "period_label": "period",
                "total_revenue": "revenue",
                "order_count": "orders",
            })

            return result.set_index("period")
        except Exception as exc:
            logger.error("Failed to compute time series KPIs: %s", exc)
            return pd.DataFrame()

    def generate_kpi_report(
        self, start_date: str, end_date: str,
    ) -> dict[str, Any]:
        """Generate a comprehensive KPI report.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            Unified dict with all KPIs structured for reporting.
        """
        report = {
            "period": f"{start_date} to {end_date}",
            "generated_at": datetime.utcnow().isoformat(),
            "sales": self.sales_kpis(start_date, end_date),
            "customers": self.customer_kpis(start_date, end_date),
            "products": self.product_kpis(
                start_date, end_date
            ).to_dict("records") if not self.product_kpis(
                start_date, end_date
            ).empty else [],
            "time_series": self.time_series_kpis(
                start_date, end_date
            ).to_dict("index") if not self.time_series_kpis(
                start_date, end_date
            ).empty else {},
        }

        return KPIResult(
            period=f"{start_date} to {end_date}",
            kpis=report["sales"],
            metadata={
                "customers": report["customers"],
                "product_count": len(report["products"]),
            },
        )
