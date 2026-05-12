"""Heatmap chart with annotated cell values."""

import logging
from typing import Any, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from visualisation.base_chart import BaseChart

logger = logging.getLogger(__name__)


class HeatmapChart(BaseChart):
    """Correlation or pivot heatmap with cell annotations."""

    def render(
        self,
        data: pd.DataFrame,
        pivot_index: Optional[str] = None,
        pivot_columns: Optional[str] = None,
        pivot_values: Optional[str] = None,
        title: str = "Heatmap",
        annotate: bool = True,
        **kwargs: Any,
    ) -> Figure:
        """Render a heatmap chart.

        Args:
            data: DataFrame (or pre-pivoted matrix).
            pivot_index: Column to use as row index for pivot.
            pivot_columns: Column to use as columns for pivot.
            pivot_values: Column for cell values.
            title: Chart title.
            annotate: If True, show values in cells.
            **kwargs: Additional keyword arguments.

        Returns:
            A matplotlib Figure.
        """
        if data.empty:
            return self._empty_figure("No Data Available")

        try:
            # Pivot if column names are provided
            if pivot_index and pivot_columns and pivot_values:
                matrix = data.pivot_table(
                    index=pivot_index,
                    columns=pivot_columns,
                    values=pivot_values,
                    aggfunc="mean",
                )
            else:
                # Assume data is already a matrix
                matrix = data.select_dtypes(include=[np.number])

            fig, ax = plt.subplots(figsize=self.figsize)
            cmap = self.theme.get_sequential_cmap()

            im = ax.imshow(matrix.values, cmap=cmap, aspect="auto")

            ax.set_xticks(range(len(matrix.columns)))
            ax.set_xticklabels(
                matrix.columns.astype(str), rotation=45, ha="right",
            )
            ax.set_yticks(range(len(matrix.index)))
            ax.set_yticklabels(matrix.index.astype(str))

            if annotate:
                for i in range(len(matrix.index)):
                    for j in range(len(matrix.columns)):
                        val = matrix.iloc[i, j]
                        if pd.notna(val):
                            ax.text(
                                j, i, f"{val:.1f}",
                                ha="center", va="center",
                                fontsize=8,
                                color="white" if val > matrix.values.max() * 0.6
                                else "black",
                            )

            fig.colorbar(im, ax=ax, shrink=0.8)
            ax.set_title(title, **self.theme.title_style)
            fig.tight_layout()
            self.add_watermark(fig)
            return fig
        except Exception as exc:
            logger.error("HeatmapChart render failed: %s", exc)
            plt.close("all")
            return self._empty_figure(f"Render Error: {exc}")
