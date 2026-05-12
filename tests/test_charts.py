"""Tests for chart theme and chart rendering."""

import pytest
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import pandas as pd

from src.visualisation.theme import ChartTheme
from src.visualisation.chart_factory import ChartFactory


class TestChartTheme:
    """Test ChartTheme configuration."""

    def test_default_theme(self):
        """Default theme should have valid attributes."""
        theme = ChartTheme(config={})
        assert theme.primary_color == "#2E86AB"
        assert len(theme.palette) == 6

    def test_apply_rcparams(self):
        """Applying theme should set rcParams."""
        theme = ChartTheme(config={})
        theme.apply()
        assert plt.rcParams["axes.spines.top"] is False
        assert plt.rcParams["axes.grid"] is True

    def test_get_palette_small(self):
        """Should return exact palette for small n."""
        theme = ChartTheme(config={})
        colors = theme.get_palette(3)
        assert len(colors) == 3

    def test_get_palette_large(self):
        """Should interpolate for n > palette size."""
        theme = ChartTheme(config={})
        colors = theme.get_palette(12)
        assert len(colors) == 12

    def test_sequential_cmap(self):
        """Should return a valid colormap."""
        theme = ChartTheme(config={})
        cmap = theme.get_sequential_cmap()
        assert cmap is not None

    def test_diverging_cmap(self):
        """Should return a valid diverging colormap."""
        theme = ChartTheme(config={})
        cmap = theme.get_diverging_cmap()
        assert cmap is not None

    def test_title_style(self):
        """Title style should have fontsize and fontweight."""
        theme = ChartTheme(config={})
        style = theme.title_style
        assert "fontsize" in style
        assert "fontweight" in style


class TestCharts:
    """Test chart rendering."""

    @pytest.fixture
    def theme(self):
        """Create a default theme."""
        t = ChartTheme(config={})
        t.apply()
        return t

    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for charting."""
        return pd.DataFrame({
            "period": ["Jan", "Feb", "Mar", "Apr", "May"],
            "revenue": [1000, 1200, 1100, 1400, 1300],
            "category": ["A", "B", "C", "D", "E"],
            "value": [10, 20, 30, 40, 50],
            "group": ["X", "X", "Y", "Y", "X"],
        })

    def test_line_chart(self, theme, sample_data):
        """LineChart should render a Figure with axes."""
        chart = ChartFactory.create("line", theme)
        fig = chart.render(
            sample_data, date_col="period", value_col="revenue"
        )
        assert fig is not None
        assert len(fig.axes) >= 1
        plt.close(fig)

    def test_bar_chart(self, theme, sample_data):
        """BarChart should render a Figure."""
        chart = ChartFactory.create("bar", theme)
        fig = chart.render(
            sample_data, x_col="category", y_col="value"
        )
        assert fig is not None
        assert len(fig.axes) >= 1
        plt.close(fig)

    def test_pie_chart(self, theme, sample_data):
        """PieChart should render a Figure."""
        chart = ChartFactory.create("pie", theme)
        fig = chart.render(
            sample_data, label_col="category", value_col="value"
        )
        assert fig is not None
        plt.close(fig)

    def test_scatter_chart(self, theme, sample_data):
        """ScatterChart should render a Figure."""
        chart = ChartFactory.create("scatter", theme)
        fig = chart.render(
            sample_data, x_col="revenue", y_col="value"
        )
        assert fig is not None
        plt.close(fig)

    def test_histogram_chart(self, theme, sample_data):
        """HistogramChart should render a Figure."""
        chart = ChartFactory.create("histogram", theme)
        fig = chart.render(sample_data, value_col="value", kde=False)
        assert fig is not None
        plt.close(fig)

    def test_boxplot_chart(self, theme, sample_data):
        """BoxPlotChart should render a Figure."""
        chart = ChartFactory.create("boxplot", theme)
        fig = chart.render(
            sample_data, value_col="value", group_col="group"
        )
        assert fig is not None
        plt.close(fig)

    def test_stacked_bar_chart(self, theme, sample_data):
        """StackedBarChart should render a Figure."""
        chart = ChartFactory.create("stacked_bar", theme)
        data = pd.DataFrame({
            "period": ["Jan", "Jan", "Feb", "Feb"],
            "category": ["A", "B", "A", "B"],
            "value": [100, 200, 150, 250],
        })
        fig = chart.render(data)
        assert fig is not None
        plt.close(fig)

    def test_empty_data(self, theme):
        """Charts should handle empty DataFrames gracefully."""
        chart = ChartFactory.create("line", theme)
        fig = chart.render(pd.DataFrame())
        assert fig is not None
        plt.close(fig)

    def test_chart_factory_invalid(self, theme):
        """ChartFactory should raise for unknown types."""
        with pytest.raises(ValueError, match="Unknown"):
            ChartFactory.create("radar", theme)
