"""Abstract base chart class for the E-Commerce Analytics Platform.

All chart types inherit from BaseChart, which provides common
save, watermark, subtitle, and data label functionality.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)


class BaseChart(ABC):
    """Abstract base class for all chart types.

    Provides common methods for saving, watermarking, and annotating
    charts. Subclasses must implement the render() method.
    """

    def __init__(
        self,
        theme: ChartTheme,
        figsize: Optional[tuple] = None,
    ) -> None:
        """Initialise the base chart.

        Args:
            theme: ChartTheme instance for styling.
            figsize: Optional figure size override (width, height).
        """
        self.theme = theme
        self.figsize = figsize or theme.default_figsize

    @abstractmethod
    def render(
        self, data: pd.DataFrame, **kwargs: Any,
    ) -> Figure:
        """Render the chart with the given data.

        Args:
            data: DataFrame containing the chart data.
            **kwargs: Chart-specific keyword arguments.

        Returns:
            A matplotlib Figure object.
        """

    def save(
        self,
        fig: Figure,
        filename: str,
        output_dir: str = "reports",
        dpi: int = 150,
        formats: Optional[list[str]] = None,
    ) -> dict[str, str]:
        """Save a figure to disk in one or more formats.

        Args:
            fig: The Figure to save.
            filename: Base filename (without extension).
            output_dir: Output directory.
            dpi: Resolution in dots per inch.
            formats: List of formats ('png', 'pdf', 'svg').

        Returns:
            Dict mapping format to saved file path.
        """
        if formats is None:
            formats = ["png"]

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths: dict[str, str] = {}

        for fmt in formats:
            filepath = out / f"{filename}.{fmt}"
            fig.savefig(
                str(filepath), dpi=dpi, format=fmt,
                bbox_inches="tight", facecolor=fig.get_facecolor(),
            )
            paths[fmt] = str(filepath)
            logger.debug("Saved chart to %s", filepath)

        return paths

    @staticmethod
    def add_watermark(
        fig: Figure,
        text: str = "E-Commerce Analytics Platform",
    ) -> None:
        """Add a semi-transparent watermark to the figure.

        Args:
            fig: The Figure to watermark.
            text: Watermark text.
        """
        fig.text(
            0.5, 0.5, text,
            fontsize=40, color="gray", alpha=0.05,
            ha="center", va="center", rotation=30,
            transform=fig.transFigure,
        )

    @staticmethod
    def add_subtitle(ax: plt.Axes, text: str) -> None:
        """Add a subtitle below the axis title.

        Args:
            ax: The Axes to add the subtitle to.
            text: Subtitle text.
        """
        ax.text(
            0.5, 1.02, text,
            transform=ax.transAxes,
            fontsize=10, color="#666666",
            ha="center", va="bottom",
        )

    @staticmethod
    def add_data_label(
        ax: plt.Axes, x: Any, y: Any, label: str,
    ) -> None:
        """Add a data label at the specified coordinates.

        Args:
            ax: The Axes to annotate.
            x: X-coordinate.
            y: Y-coordinate.
            label: Text label to display.
        """
        ax.annotate(
            label, (x, y),
            textcoords="offset points", xytext=(0, 8),
            ha="center", fontsize=8, color="#333333",
        )

    def _empty_figure(self, message: str = "No Data") -> Figure:
        """Create a blank figure with a centered message.

        Used when the input DataFrame is empty.

        Args:
            message: Message to display.

        Returns:
            A Figure with the message.
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.text(
            0.5, 0.5, message,
            transform=ax.transAxes,
            fontsize=20, color="#999999",
            ha="center", va="center",
        )
        ax.set_axis_off()
        return fig
