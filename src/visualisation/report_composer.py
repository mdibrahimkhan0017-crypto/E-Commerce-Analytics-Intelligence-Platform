"""Report composer for generating full analytical report packages.

Orchestrates dashboard generation and export into a complete report
with PNG, PDF, and a summary index.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from visualisation.dashboard import DashboardComposer
from visualisation.exporter import ReportExporter

logger = logging.getLogger(__name__)


class ReportComposer:
    """Generates complete report packages from dashboards.

    Coordinates DashboardComposer and ReportExporter to produce
    all dashboards, save them in multiple formats, and create
    a summary index.
    """

    def __init__(
        self,
        dashboard: DashboardComposer,
        exporter: Optional[ReportExporter] = None,
    ) -> None:
        """Initialise the report composer.

        Args:
            dashboard: DashboardComposer instance.
            exporter: ReportExporter instance (created if None).
        """
        self.dashboard = dashboard
        self.exporter = exporter or ReportExporter()

    def generate_full_report(
        self,
        start_date: str,
        end_date: str,
        output_dir: str = "reports",
        formats: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Generate all dashboards and export them.

        Args:
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            output_dir: Output directory for reports.
            formats: Output formats (default: ['png', 'pdf']).

        Returns:
            Dict of saved file paths and summary index path.
        """
        if formats is None:
            formats = ["png", "pdf"]

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        results: dict[str, Any] = {}
        dashboards = {
            "executive_dashboard": self.dashboard.executive_dashboard,
            "product_dashboard": self.dashboard.product_dashboard,
            "customer_dashboard": self.dashboard.customer_dashboard,
            "sales_trend_dashboard": self.dashboard.sales_trend_dashboard,
        }

        index_entries = []

        for name, generator_fn in dashboards.items():
            try:
                fig = generator_fn(start_date, end_date)
                paths = self.exporter.export_figure(
                    fig, name, formats=formats,
                    output_dir=output_dir,
                )
                results[name] = paths

                index_entries.append({
                    "name": name,
                    "png_path": paths.get("png", ""),
                    "pdf_path": paths.get("pdf", ""),
                    "generated_at": datetime.utcnow().isoformat(),
                })

                logger.info("Generated dashboard: %s", name)
            except Exception as exc:
                logger.error(
                    "Failed to generate %s: %s", name, exc,
                )
                results[name] = {"error": str(exc)}

        # Create summary index
        index = {
            "report_date": datetime.utcnow().isoformat(),
            "period": f"{start_date} to {end_date}",
            "dashboards": index_entries,
        }

        index_path = out / "report_index.json"
        with open(index_path, "w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2, default=str)

        results["index_path"] = str(index_path)
        logger.info("Full report generated: %d dashboards", len(index_entries))
        return results
