"""Dashboard composer for multi-panel analytical dashboards.

Creates executive, product, customer, and sales trend dashboards
by composing individual charts into grid layouts.
"""

import logging
from datetime import datetime
from typing import Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from analytics.kpi_calculator import KPICalculator
from analytics.ltv_engine import LTVEngine
from analytics.rfm_engine import RFMEngine
from visualisation.chart_factory import ChartFactory
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


class DashboardComposer:
    """Composes multi-panel analytical dashboards.

    Combines KPI data with chart renderings to create comprehensive
    dashboard Figures for executive, product, customer, and sales
    trend views.

    Attributes:
        theme: Chart theme for consistent styling.
        kpi: KPICalculator for data retrieval.
        rfm: RFMEngine for segmentation data.
        ltv: LTVEngine for lifetime value data.
    """

    def __init__(
        self,
        theme: ChartTheme,
        kpi_calculator: KPICalculator,
        rfm_engine: RFMEngine,
        ltv_engine: LTVEngine,
    ) -> None:
        """Initialise the dashboard composer.

        Args:
            theme: ChartTheme instance.
            kpi_calculator: KPICalculator instance.
            rfm_engine: RFMEngine instance.
            ltv_engine: LTVEngine instance.
        """
        self.theme = theme
        self.kpi = kpi_calculator
        self.rfm = rfm_engine
        self.ltv = ltv_engine

    def executive_dashboard(
        self, start_date: str, end_date: str,
    ) -> Figure:
        """Create an executive overview dashboard (2×3 grid).

        Panels: KPI scorecard, revenue trend, top 10 products bar,
        category pie, channel bar, MoM growth line.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            A matplotlib Figure.
        """
        try:
            fig, axes = plt.subplots(2, 3, figsize=(20, 12))
            fig.suptitle(
                "Executive Dashboard",
                fontsize=22, fontweight="bold", y=0.98,
            )
            fig.text(
                0.5, 0.94,
                f"{start_date} to {end_date}",
                ha="center", fontsize=12, color="#666666",
            )

            # Panel 1: KPI Scorecard
            kpis = self.kpi.sales_kpis(start_date, end_date)
            ax = axes[0, 0]
            ax.set_axis_off()
            kpi_lines = [
                f"Revenue: ${kpis['total_revenue']:,.0f}",
                f"Orders: {kpis['total_orders']:,}",
                f"AOV: ${kpis['aov']:,.2f}",
                f"Growth: {kpis['revenue_growth_pct']:+.1f}%",
                f"Refund Rate: {kpis['refund_rate_pct']:.1f}%",
            ]
            for i, line in enumerate(kpi_lines):
                ax.text(
                    0.5, 0.85 - i * 0.18, line,
                    transform=ax.transAxes,
                    fontsize=14, fontweight="bold",
                    ha="center", va="center",
                    color=self.theme.primary_color,
                )
            ax.set_title("Key Metrics", **self.theme.title_style)

            # Panel 2: Revenue Trend
            ts_df = self.kpi.time_series_kpis(start_date, end_date)
            ax = axes[0, 1]
            if not ts_df.empty:
                ax.plot(
                    range(len(ts_df)), ts_df["revenue"].values,
                    color=self.theme.primary_color,
                    linewidth=2, marker="o", markersize=3,
                )
                ax.set_xticks(range(len(ts_df)))
                ax.set_xticklabels(
                    ts_df.index.astype(str), rotation=45, ha="right",
                    fontsize=7,
                )
            ax.set_title("Revenue Trend", fontsize=13, fontweight="bold")

            # Panel 3: Top 10 Products
            top_df = self.kpi.query_lib.top_products(
                start_date, end_date, limit=10
            )
            ax = axes[0, 2]
            if not top_df.empty:
                colors = self.theme.get_palette(len(top_df))
                ax.barh(
                    top_df["product_name"].astype(str),
                    top_df["total_revenue"],
                    color=colors,
                )
            ax.set_title("Top 10 Products", fontsize=13, fontweight="bold")

            # Panel 4: Category Pie
            cat_df = self.kpi.query_lib.category_performance(
                start_date, end_date
            )
            ax = axes[1, 0]
            if not cat_df.empty:
                ax.pie(
                    cat_df["total_revenue"],
                    labels=cat_df["category"],
                    colors=self.theme.get_palette(len(cat_df)),
                    autopct="%1.1f%%", startangle=90,
                )
            ax.set_title("Category Split", fontsize=13, fontweight="bold")

            # Panel 5: Channel Bar
            ch_df = self.kpi.query_lib.channel_performance(
                start_date, end_date
            )
            ax = axes[1, 1]
            if not ch_df.empty:
                ax.bar(
                    ch_df["channel"].astype(str),
                    ch_df["total_revenue"],
                    color=self.theme.get_palette(len(ch_df)),
                )
                plt.sca(ax)
                plt.xticks(rotation=45, ha="right")
            ax.set_title("Channel Revenue", fontsize=13, fontweight="bold")

            # Panel 6: MoM Growth
            year = start_date[:4]
            growth_df = self.kpi.query_lib.revenue_growth(year)
            ax = axes[1, 2]
            if not growth_df.empty:
                vals = growth_df["growth_pct"].fillna(0).values
                colors_bar = [
                    "#44BBA4" if v >= 0 else "#C73E1D" for v in vals
                ]
                ax.bar(
                    growth_df["month_label"].astype(str),
                    vals, color=colors_bar,
                )
                plt.sca(ax)
                plt.xticks(rotation=45, ha="right")
            ax.set_title("MoM Growth %", fontsize=13, fontweight="bold")

            # Footer
            fig.text(
                0.5, 0.01,
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                ha="center", fontsize=9, color="#999999",
            )

            fig.tight_layout(rect=[0, 0.02, 1, 0.92])
            return fig
        except Exception as exc:
            logger.error("Executive dashboard failed: %s", exc)
            fig, ax = plt.subplots(figsize=(20, 12))
            ax.text(0.5, 0.5, f"Dashboard Error: {exc}",
                    ha="center", va="center", fontsize=16)
            ax.set_axis_off()
            return fig

    def product_dashboard(
        self, start_date: str, end_date: str,
    ) -> Figure:
        """Create a product performance dashboard (2×2 grid).

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            A matplotlib Figure.
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(
                "Product Dashboard", fontsize=22,
                fontweight="bold", y=0.98,
            )

            # Top/Bottom products
            top_df = self.kpi.query_lib.top_products(
                start_date, end_date, limit=10
            )
            ax = axes[0, 0]
            if not top_df.empty:
                ax.barh(
                    top_df["product_name"].astype(str),
                    top_df["total_revenue"],
                    color=self.theme.get_palette(len(top_df)),
                )
            ax.set_title("Top Products", fontsize=13, fontweight="bold")

            bottom_df = self.kpi.query_lib.bottom_products(
                start_date, end_date, limit=10
            )
            ax = axes[0, 1]
            if not bottom_df.empty:
                ax.barh(
                    bottom_df["product_name"].astype(str),
                    bottom_df["total_revenue"],
                    color="#C73E1D", alpha=0.7,
                )
            ax.set_title("Bottom Products", fontsize=13, fontweight="bold")

            # Return rate
            cat_df = self.kpi.query_lib.category_performance(
                start_date, end_date
            )
            ax = axes[1, 0]
            if not cat_df.empty:
                ax.bar(
                    cat_df["category"].astype(str),
                    cat_df["return_rate_pct"],
                    color=self.theme.get_palette(len(cat_df)),
                )
                plt.sca(ax)
                plt.xticks(rotation=45, ha="right")
            ax.set_title("Return Rate by Category",
                         fontsize=13, fontweight="bold")

            # Margin scatter
            ax = axes[1, 1]
            if not cat_df.empty:
                ax.scatter(
                    cat_df["total_revenue"],
                    cat_df["margin_pct"],
                    s=cat_df["units_sold"] / 10,
                    c=self.theme.get_palette(len(cat_df)),
                    alpha=0.7, edgecolors="white",
                )
                for _, row in cat_df.iterrows():
                    ax.annotate(
                        row["category"],
                        (row["total_revenue"], row["margin_pct"]),
                        fontsize=8,
                    )
                ax.set_xlabel("Revenue")
                ax.set_ylabel("Margin %")
            ax.set_title("Revenue vs Margin",
                         fontsize=13, fontweight="bold")

            fig.tight_layout(rect=[0, 0.02, 1, 0.95])
            return fig
        except Exception as exc:
            logger.error("Product dashboard failed: %s", exc)
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.text(0.5, 0.5, f"Dashboard Error: {exc}",
                    ha="center", va="center", fontsize=16)
            ax.set_axis_off()
            return fig

    def customer_dashboard(
        self, start_date: str, end_date: str,
    ) -> Figure:
        """Create a customer analytics dashboard (2×2 grid).

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).

        Returns:
            A matplotlib Figure.
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(
                "Customer Dashboard", fontsize=22,
                fontweight="bold", y=0.98,
            )

            # RFM segments
            rfm_df = self.rfm.compute_rfm()
            seg_df = self.rfm.assign_segment(rfm_df)
            summary = self.rfm.segment_summary()

            ax = axes[0, 0]
            if not summary.empty:
                ax.barh(
                    summary["segment"].astype(str),
                    summary["customer_count"],
                    color=self.theme.get_palette(len(summary)),
                )
            ax.set_title("RFM Segments", fontsize=13, fontweight="bold")

            # LTV histogram
            ltv_df = self.ltv.projected_ltv()
            ax = axes[0, 1]
            if not ltv_df.empty:
                ax.hist(
                    ltv_df["projected_ltv"].dropna(), bins=20,
                    color=self.theme.primary_color, alpha=0.7,
                    edgecolor="white",
                )
            ax.set_title("LTV Distribution", fontsize=13, fontweight="bold")
            ax.set_xlabel("Projected LTV ($)")

            # New vs returning
            year = start_date[:4]
            nvr_df = self.kpi.query_lib.new_vs_returning(year)
            ax = axes[1, 0]
            if not nvr_df.empty:
                x = range(len(nvr_df))
                ax.bar(x, nvr_df["new_customers"],
                       label="New", color=self.theme.palette[0])
                ax.bar(x, nvr_df["returning_customers"],
                       bottom=nvr_df["new_customers"],
                       label="Returning", color=self.theme.palette[1])
                ax.set_xticks(list(x))
                ax.set_xticklabels(
                    nvr_df["month_label"].astype(str),
                    rotation=45, ha="right", fontsize=7,
                )
                ax.legend()
            ax.set_title("New vs Returning",
                         fontsize=13, fontweight="bold")

            # Churn risk text
            churn_df = self.rfm.churn_risk_customers(days_threshold=90)
            ax = axes[1, 1]
            ax.set_axis_off()
            ax.set_title("Churn Risk (>90 days)",
                         fontsize=13, fontweight="bold")
            if not churn_df.empty:
                top_churn = churn_df.head(10)
                for i, (_, row) in enumerate(top_churn.iterrows()):
                    ax.text(
                        0.1, 0.9 - i * 0.08,
                        f"{row['customer_id']}: {int(row['recency_days'])}d",
                        transform=ax.transAxes, fontsize=10,
                    )

            fig.tight_layout(rect=[0, 0.02, 1, 0.95])
            return fig
        except Exception as exc:
            logger.error("Customer dashboard failed: %s", exc)
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.text(0.5, 0.5, f"Dashboard Error: {exc}",
                    ha="center", va="center", fontsize=16)
            ax.set_axis_off()
            return fig

    def sales_trend_dashboard(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "monthly",
    ) -> Figure:
        """Create a sales trend dashboard (1×3 grid).

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            granularity: Time granularity for the series.

        Returns:
            A matplotlib Figure.
        """
        try:
            fig, axes = plt.subplots(1, 3, figsize=(20, 6))
            fig.suptitle(
                "Sales Trends", fontsize=22,
                fontweight="bold", y=1.02,
            )

            ts_df = self.kpi.time_series_kpis(
                start_date, end_date, granularity
            )

            if not ts_df.empty:
                x = range(len(ts_df))
                labels = ts_df.index.astype(str)

                # Revenue
                axes[0].plot(
                    x, ts_df["revenue"].values,
                    color=self.theme.palette[0],
                    linewidth=2, marker="o", markersize=3,
                )
                axes[0].set_title("Revenue", fontsize=13, fontweight="bold")
                axes[0].set_xticks(list(x))
                axes[0].set_xticklabels(
                    labels, rotation=45, ha="right", fontsize=7,
                )

                # Orders
                axes[1].plot(
                    x, ts_df["orders"].values,
                    color=self.theme.palette[1],
                    linewidth=2, marker="o", markersize=3,
                )
                axes[1].set_title("Orders", fontsize=13, fontweight="bold")
                axes[1].set_xticks(list(x))
                axes[1].set_xticklabels(
                    labels, rotation=45, ha="right", fontsize=7,
                )

                # AOV
                axes[2].plot(
                    x, ts_df["aov"].values,
                    color=self.theme.palette[2],
                    linewidth=2, marker="o", markersize=3,
                )
                axes[2].set_title("AOV", fontsize=13, fontweight="bold")
                axes[2].set_xticks(list(x))
                axes[2].set_xticklabels(
                    labels, rotation=45, ha="right", fontsize=7,
                )

            fig.tight_layout()
            return fig
        except Exception as exc:
            logger.error("Sales trend dashboard failed: %s", exc)
            fig, ax = plt.subplots(figsize=(20, 6))
            ax.text(0.5, 0.5, f"Dashboard Error: {exc}",
                    ha="center", va="center", fontsize=16)
            ax.set_axis_off()
            return fig
