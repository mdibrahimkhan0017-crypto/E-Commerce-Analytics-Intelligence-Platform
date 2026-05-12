"""Stacked bar chart for part-whole relationships."""

import logging
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class StackedBarChart(BaseChart):
    """Stacked bar chart showing composition of categories."""

    def render(
        self,
        data: pd.DataFrame,
        x_col: str = "period",
        stack_col: str = "category",
        value_col: str = "value",
        title: str = "Stacked Bar Chart",
        **kwargs: Any,
    ) -> Figure:
        """Render a stacked bar chart.

        Args:
            data: DataFrame with x, stack, and value columns.
            x_col: Column for the x-axis groups.
            stack_col: Column whose unique values form stacks.
            value_col: Column for bar segment values.
            title: Chart title.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            pivot = data.pivot_table(
                index=x_col, columns=stack_col,
                values=value_col, aggfunc="sum", fill_value=0,
            )

            fig, ax = plt.subplots(figsize=self.figsize)
            colors = self.theme.get_palette(len(pivot.columns))

            bottom = np.zeros(len(pivot))
            for i, col in enumerate(pivot.columns):
                ax.bar(
                    pivot.index.astype(str),
                    pivot[col].values,
                    bottom=bottom,
                    label=str(col),
                    color=colors[i],
                    edgecolor="white", linewidth=0.5,
                )
                bottom += pivot[col].values

            ax.set_title(title, **self.theme.title_style)
            ax.set_xlabel(x_col.replace("_", " ").title())
            ax.set_ylabel(value_col.replace("_", " ").title())
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("StackedBarChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
