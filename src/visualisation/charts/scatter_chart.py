"""Scatter chart with optional regression line and group colouring."""

import logging
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class ScatterChart(BaseChart):
    """Scatter plot with optional regression and colour-coded groups."""

    def render(
        self,
        data: pd.DataFrame,
        x_col: str = "x",
        y_col: str = "y",
        title: str = "Scatter Plot",
        group_col: Optional[str] = None,
        regression: bool = False,
        **kwargs: Any,
    ) -> Figure:
        """Render a scatter chart.

        Args:
            data: DataFrame with x and y columns.
            x_col: Column for x-axis values.
            y_col: Column for y-axis values.
            title: Chart title.
            group_col: Optional column for colour grouping.
            regression: If True, overlay a regression line.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            if group_col and group_col in data.columns:
                groups = data[group_col].unique()
                colors = self.theme.get_palette(len(groups))
                for i, group in enumerate(groups):
                    mask = data[group_col] == group
                    ax.scatter(
                        data.loc[mask, x_col],
                        data.loc[mask, y_col],
                        color=colors[i], label=str(group),
                        alpha=0.7, s=60, edgecolors="white",
                    )
                ax.legend()
            else:
                ax.scatter(
                    data[x_col], data[y_col],
                    color=self.theme.primary_color,
                    alpha=0.7, s=60, edgecolors="white",
                )

            if regression and len(data) > 1:
                x = data[x_col].astype(float).values
                y = data[y_col].astype(float).values
                mask = ~(np.isnan(x) | np.isnan(y))
                if mask.sum() > 1:
                    z = np.polyfit(x[mask], y[mask], 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
                    ax.plot(
                        x_line, p(x_line),
                        color="#C73E1D", linestyle="--",
                        linewidth=2, alpha=0.7, label="Regression",
                    )
                    ax.legend()

            ax.set_title(title, **self.theme.title_style)
            ax.set_xlabel(x_col.replace("_", " ").title())
            ax.set_ylabel(y_col.replace("_", " ").title())
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("ScatterChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
