"""Bar chart with value labels for categorical data."""

import logging
from typing import Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


class BarChart(BaseChart):
    """Vertical or horizontal bar chart with value labels."""

    def render(
        self,
        data: pd.DataFrame,
        x_col: str = "category",
        y_col: str = "value",
        title: str = "Bar Chart",
        orientation: str = "vertical",
        top_n: Optional[int] = None,
        **kwargs: Any,
    ) -> Figure:
        """Render a bar chart.

        Args:
            data: DataFrame with category and value columns.
            x_col: Column for categories.
            y_col: Column for values.
            title: Chart title.
            orientation: 'vertical' or 'horizontal'.
            top_n: If set, show only the top N bars.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            df = data.copy()
            if top_n:
                df = df.nlargest(top_n, y_col)

            fig, ax = plt.subplots(figsize=self.figsize)
            colors = self.theme.get_palette(len(df))

            if orientation == "horizontal":
                bars = ax.barh(
                    df[x_col].astype(str), df[y_col],
                    color=colors, edgecolor="white", linewidth=0.5,
                )
                for bar in bars:
                    width = bar.get_width()
                    ax.text(
                        width, bar.get_y() + bar.get_height() / 2,
                        f" {width:,.0f}", va="center", fontsize=9,
                    )
                ax.set_xlabel(y_col.replace("_", " ").title())
            else:
                bars = ax.bar(
                    df[x_col].astype(str), df[y_col],
                    color=colors, edgecolor="white", linewidth=0.5,
                )
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2, height,
                        f"{height:,.0f}", ha="center", va="bottom",
                        fontsize=9,
                    )
                ax.set_ylabel(y_col.replace("_", " ").title())
                plt.xticks(rotation=45, ha="right")

            ax.set_title(title, **self.theme.title_style)
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("BarChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
