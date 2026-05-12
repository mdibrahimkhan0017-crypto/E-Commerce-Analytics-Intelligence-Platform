"""Pie/donut chart with percentage labels."""

import logging
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class PieChart(BaseChart):
    """Pie or donut chart with percentage labels."""

    def render(
        self,
        data: pd.DataFrame,
        label_col: str = "category",
        value_col: str = "value",
        title: str = "Distribution",
        donut: bool = False,
        **kwargs: Any,
    ) -> Figure:
        """Render a pie or donut chart.

        Args:
            data: DataFrame with label and value columns.
            label_col: Column for slice labels.
            value_col: Column for slice values.
            title: Chart title.
            donut: If True, render as donut chart.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            colors = self.theme.get_palette(len(data))

            wedges, texts, autotexts = ax.pie(
                data[value_col],
                labels=data[label_col].astype(str),
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.85 if donut else 0.5,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            )

            for text in autotexts:
                text.set_fontsize(9)
                text.set_color("#333333")

            if donut:
                centre_circle = plt.Circle((0, 0), 0.70, fc="white")
                ax.add_artist(centre_circle)

            ax.set_title(title, **self.theme.title_style)
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("PieChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
