"""Streamlit interactive dashboard for the E-Commerce Analytics Platform.

Renders analytical dashboards with interactive date pickers,
report type selectors, and downloadable data tables.

Usage:
    streamlit run src/app.py
"""

import logging
from datetime import date, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yaml

from analytics.kpi_calculator import KPICalculator
from analytics.ltv_engine import LTVEngine
from analytics.rfm_engine import RFMEngine
from db.database import DatabaseManager
from engine.query_engine import QueryEngine
from engine.query_library import QueryLibrary
from visualisation.dashboard import DashboardComposer
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from config.yaml.

    Returns:
        Configuration dictionary.
    """
    try:
        with open("config.yaml", "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except FileNotFoundError:
        return {}


@st.cache_resource
def init_platform():
    """Initialise all platform components (cached).

    Returns:
        Tuple of (db_manager, query_library, kpi_calculator,
        rfm_engine, ltv_engine, dashboard_composer).
    """
    config = load_config()

    db = DatabaseManager()
    db.connect()

    engine = QueryEngine(db, config)
    query_lib = QueryLibrary(engine)
    kpi = KPICalculator(query_lib)
    rfm = RFMEngine(db)
    ltv = LTVEngine(db)

    theme = ChartTheme(config=config)
    theme.apply()
    dashboard = DashboardComposer(theme, kpi, rfm, ltv)

    return db, query_lib, kpi, rfm, ltv, dashboard


def main() -> None:
    """Render the Streamlit dashboard application."""
    st.set_page_config(
        page_title="E-Commerce Analytics Platform",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 E-Commerce Analytics Platform")
    st.markdown("---")

    # ── Sidebar controls ─────────────────────────────────────────────
    st.sidebar.header("⚙️ Dashboard Controls")

    start_date = st.sidebar.date_input(
        "Start Date",
        value=date.today() - timedelta(days=365),
    )
    end_date = st.sidebar.date_input(
        "End Date",
        value=date.today(),
    )

    report_type = st.sidebar.selectbox(
        "Report Type",
        ["Executive", "Product", "Customer", "Sales Trends"],
    )

    granularity = st.sidebar.radio(
        "Granularity",
        ["Monthly", "Weekly", "Daily", "Quarterly"],
    )

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    # ── Initialise platform ──────────────────────────────────────────
    try:
        db, query_lib, kpi, rfm, ltv, dashboard = init_platform()
    except Exception as exc:
        st.error(f"Failed to initialise platform: {exc}")
        st.info(
            "Run `python -m src.cli generate --records 10000 --seed 42` "
            "then `python -m src.cli ingest --source data/` first."
        )
        return

    # ── KPI Metrics Row ──────────────────────────────────────────────
    st.subheader("📈 Key Performance Indicators")
    try:
        sales = kpi.sales_kpis(start_str, end_str)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Revenue", f"${sales['total_revenue']:,.0f}")
        col2.metric("Total Orders", f"{sales['total_orders']:,}")
        col3.metric("Avg Order Value", f"${sales['aov']:,.2f}")
        col4.metric("Revenue Growth", f"{sales['revenue_growth_pct']:+.1f}%")
        col5.metric("Refund Rate", f"{sales['refund_rate_pct']:.1f}%")
    except Exception as exc:
        st.warning(f"Could not compute KPIs: {exc}")

    st.markdown("---")

    # ── Dashboard Rendering ──────────────────────────────────────────
    st.subheader(f"📊 {report_type} Dashboard")

    try:
        if report_type == "Executive":
            fig = dashboard.executive_dashboard(start_str, end_str)
        elif report_type == "Product":
            fig = dashboard.product_dashboard(start_str, end_str)
        elif report_type == "Customer":
            fig = dashboard.customer_dashboard(start_str, end_str)
        else:
            fig = dashboard.sales_trend_dashboard(
                start_str, end_str,
                granularity=granularity.lower(),
            )

        st.pyplot(fig)
        plt.close(fig)
    except Exception as exc:
        st.error(f"Dashboard rendering failed: {exc}")

    st.markdown("---")

    # ── Data Tables Section ──────────────────────────────────────────
    st.subheader("📋 Query Results")

    table_choice = st.selectbox(
        "Select Data View",
        [
            "Revenue by Period",
            "Top Products",
            "Category Performance",
            "Channel Performance",
            "Customer Segments",
            "Geographic Revenue",
        ],
    )

    try:
        if table_choice == "Revenue by Period":
            df = query_lib.revenue_by_period(
                start_str, end_str,
                granularity.lower().rstrip("ly"),
            )
        elif table_choice == "Top Products":
            df = query_lib.top_products(start_str, end_str, limit=20)
        elif table_choice == "Category Performance":
            df = query_lib.category_performance(start_str, end_str)
        elif table_choice == "Channel Performance":
            df = query_lib.channel_performance(start_str, end_str)
        elif table_choice == "Customer Segments":
            df = query_lib.customer_segments()
        else:
            df = query_lib.geographic_revenue(start_str, end_str)

        st.dataframe(df, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"{table_choice.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )
    except Exception as exc:
        st.warning(f"Query failed: {exc}")

    # ── Footer ───────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "E-Commerce Analytics & Intelligence Platform v1.0 │ "
        "Built with Python, Pandas, Matplotlib, and Streamlit"
    )


if __name__ == "__main__":
    main()
