"""Box plot chart by group with outlier dots."""

import logging
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class BoxPlotChart(BaseChart):
    """Box-and-whisker chart by group with outlier indicators."""

    def render(
        self,
        data: pd.DataFrame,
        value_col: str = "value",
        group_col: str = "group",
        title: str = "Box Plot",
        **kwargs: Any,
    ) -> Figure:
        """Render a box plot chart.

        Args:
            data: DataFrame with value and group columns.
            value_col: Column for the numeric values.
            group_col: Column for grouping.
            title: Chart title.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            fig, ax = plt.subplots(figsize=self.figsize)

            groups = data[group_col].unique()
            box_data = [
                data[data[group_col] == g][value_col].dropna().values
                for g in groups
            ]

            bp = ax.boxplot(
                box_data,
                labels=[str(g) for g in groups],
                patch_artist=True,
                flierprops={"marker": "o", "markersize": 4,
                            "alpha": 0.5},
            )

            colors = self.theme.get_palette(len(groups))
            for patch, color in zip(bp["boxes"], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax.set_title(title, **self.theme.title_style)
            ax.set_ylabel(value_col.replace("_", " ").title())
            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("BoxPlotChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
