"""Line chart for time-series data with optional trend line overlay."""

import logging
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


class LineChart(BaseChart):
    """Time-series line chart with optional trend line.

    Renders a line plot suitable for revenue trends, order counts,
    and other time-indexed metrics.
    """

    def render(
        self,
        data: pd.DataFrame,
        date_col: str = "period",
        value_col: str = "revenue",
        title: str = "Revenue Trend",
        trend: bool = False,
        **kwargs: Any,
    ) -> Figure:
        """Render a line chart.

        Args:
            data: DataFrame with date and value columns.
            date_col: Column name for the x-axis (dates/periods).
            value_col: Column name for the y-axis values.
            title: Chart title.
            trend: If True, overlay a linear trend line.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            x_vals = range(len(data))
            y_vals = data[value_col].values

            ax.plot(
                x_vals, y_vals,
                color=self.theme.primary_color,
                linewidth=2.5, marker="o", markersize=4,
                label=value_col.replace("_", " ").title(),
            )

            if trend and len(x_vals) > 1:
                z = np.polyfit(x_vals, y_vals.astype(float), 1)
                p = np.poly1d(z)
                ax.plot(
                    x_vals, p(x_vals),
                    linestyle="--", color="#C73E1D", alpha=0.7,
                    label="Trend",
                )

            ax.set_xticks(list(x_vals))
            ax.set_xticklabels(
                data[date_col].astype(str).values,
                rotation=45, ha="right",
            )
            ax.set_title(title, **self.theme.title_style)
            ax.set_xlabel(date_col.replace("_", " ").title())
            ax.set_ylabel(value_col.replace("_", " ").title())
            ax.legend()
            fig.tight_layout()

            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("LineChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
