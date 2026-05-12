"""Chart factory for creating chart instances by type name."""

import logging
from typing import Optional

from visualisation.base_chart import BaseChart
from visualisation.charts.bar_chart import BarChart
from visualisation.charts.boxplot_chart import BoxPlotChart
from visualisation.charts.heatmap_chart import HeatmapChart
from visualisation.charts.histogram import HistogramChart
from visualisation.charts.pie_chart import PieChart
from visualisation.charts.revenue_trend import LineChart
from visualisation.charts.scatter_chart import ScatterChart
from visualisation.charts.stacked_bar import StackedBarChart
from visualisation.theme import ChartTheme

logger = logging.getLogger(__name__)

# ── Chart type registry ──────────────────────────────────────────────────────
CHART_REGISTRY: dict[str, type[BaseChart]] = {
    "line": LineChart,
    "bar": BarChart,
    "pie": PieChart,
    "scatter": ScatterChart,
    "heatmap": HeatmapChart,
    "histogram": HistogramChart,
    "boxplot": BoxPlotChart,
    "stacked_bar": StackedBarChart,
}


class ChartFactory:
    """Factory for creating chart instances by type name.

    Centralises chart creation and provides a registry of available
    chart types.
    """

    @staticmethod
    def create(
        chart_type: str,
        theme: ChartTheme,
        figsize: Optional[tuple] = None,
    ) -> BaseChart:
        """Create a chart instance by type name.

        Args:
            chart_type: One of: line, bar, pie, scatter, heatmap,
                       histogram, boxplot, stacked_bar.
            theme: ChartTheme instance.
            figsize: Optional figure size override.

        Returns:
            A BaseChart subclass instance.

        Raises:
            ValueError: If chart_type is not registered.
        """
        chart_class = CHART_REGISTRY.get(chart_type.lower())
        if chart_class is None:
            raise ValueError(
                f"Unknown chart type: {chart_type!r}. "
                f"Available: {list(CHART_REGISTRY.keys())}"
            )
        return chart_class(theme=theme, figsize=figsize)

    @staticmethod
    def available_types() -> list[str]:
        """List all available chart type names.

        Returns:
            Sorted list of registered chart type names.
        """
        return sorted(CHART_REGISTRY.keys())
