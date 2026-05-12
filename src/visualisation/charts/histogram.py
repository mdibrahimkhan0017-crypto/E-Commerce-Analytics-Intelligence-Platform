"""Histogram chart with optional KDE overlay."""

import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class HistogramChart(BaseChart):
    """Distribution histogram with optional KDE overlay."""

    def render(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        title: str = "Distribution",
        bins: int = 30,
        kde: bool = True,
        **kwargs: Any,
    ) -> Figure:
        """Render a histogram chart.

        Args:
            data: DataFrame with the value column.
            value_col: Column to plot the distribution of.
            title: Chart title.
            bins: Number of histogram bins.
            kde: If True, overlay a KDE curve.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            values = data[value_col].dropna().values

            ax.hist(
                values, bins=bins,
                color=self.theme.primary_color, alpha=0.7,
                edgecolor="white", linewidth=0.5,
                density=kde,
            )

            if kde and len(values) > 2:
                from scipy import stats  # noqa: E402
                try:
                    kernel = stats.gaussian_kde(values)
                    x_range = np.linspace(values.min(), values.max(), 200)
                    ax.plot(
                        x_range, kernel(x_range),
                        color="#C73E1D", linewidth=2,
                        label="KDE",
                    )
                    ax.legend()
                except Exception:
                    # scipy might not be available; skip KDE silently
                    pass

            ax.set_title(title, **self.theme.title_style)
            ax.set_xlabel(value_col.replace("_", " ").title())
            ax.set_ylabel("Density" if kde else "Count")
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("HistogramChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
