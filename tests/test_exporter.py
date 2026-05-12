"""Tests for the report exporter module."""

import json
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.visualisation.exporter import ReportExporter


class TestReportExporter:
    """Test ReportExporter functionality."""

    @pytest.fixture
    def exporter(self):
        """Create a ReportExporter instance."""
        return ReportExporter()

    @pytest.fixture
    def sample_fig(self):
        """Create a sample figure."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        return fig

    def test_export_figure_png(self, exporter, sample_fig, tmp_path):
        """Should export figure as PNG."""
        paths = exporter.export_figure(
            sample_fig, "test", formats=["png"],
            output_dir=str(tmp_path),
        )
        assert "png" in paths
        from pathlib import Path
        assert Path(paths["png"]).exists()

    def test_export_figure_pdf(self, exporter, tmp_path):
        """Should export figure as PDF."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        paths = exporter.export_figure(
            fig, "test", formats=["pdf"],
            output_dir=str(tmp_path),
        )
        assert "pdf" in paths

    def test_export_figure_low_dpi_raises(self, exporter, tmp_path):
        """Should raise ValueError for DPI < 72."""
        fig, ax = plt.subplots()
        with pytest.raises(ValueError, match="DPI"):
            exporter.export_figure(
                fig, "test", dpi=50, output_dir=str(tmp_path),
            )
        plt.close(fig)

    def test_export_dataframe_csv(self, exporter, tmp_path):
        """Should export DataFrame as CSV."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        paths = exporter.export_dataframe(
            df, "test", formats=["csv"],
            output_dir=str(tmp_path),
        )
        assert "csv" in paths

    def test_export_dataframe_json(self, exporter, tmp_path):
        """Should export DataFrame as JSON."""
        df = pd.DataFrame({"a": [1, 2]})
        paths = exporter.export_dataframe(
            df, "test", formats=["json"],
            output_dir=str(tmp_path),
        )
        assert "json" in paths

    def test_batch_export(self, exporter, tmp_path):
        """Should batch export multiple figures."""
        figures = {}
        for name in ["fig1", "fig2"]:
            fig, ax = plt.subplots()
            ax.plot([1, 2])
            figures[name] = fig

        results = exporter.batch_export(
            figures, ["png"], str(tmp_path),
        )
        assert "fig1" in results
        assert "fig2" in results

    def test_create_manifest(self, exporter, tmp_path):
        """Should create a valid JSON manifest."""
        fig, ax = plt.subplots()
        ax.plot([1, 2])
        paths = exporter.export_figure(
            fig, "test", formats=["png"],
            output_dir=str(tmp_path),
        )

        manifest_path = exporter.create_export_manifest(
            {"test": paths}, str(tmp_path),
        )
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert isinstance(manifest, list)
        assert len(manifest) >= 1
