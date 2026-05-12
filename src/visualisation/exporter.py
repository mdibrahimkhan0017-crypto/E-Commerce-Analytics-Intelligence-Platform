"""Report exporter for figures and DataFrames.

Exports matplotlib Figures and pandas DataFrames to multiple formats
with metadata and manifest generation.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class ReportExporter:
    """Exports figures and DataFrames to various file formats.

    Supports PNG, PDF, SVG for figures and CSV, JSON, XLSX for
    DataFrames, with batch export and manifest generation.
    """

    def export_figure(
        self,
        fig: Figure,
        name: str,
        formats: Optional[list[str]] = None,
        dpi: int = 150,
        output_dir: Optional[str] = None,
    ) -> dict[str, str]:
        """Save a figure in one or more formats.

        Args:
            fig: The matplotlib Figure to export.
            name: Base filename (without extension).
            formats: List of formats ('png', 'pdf', 'svg').
            dpi: Resolution (must be >= 72).
            output_dir: Output directory (defaults to 'reports/').

        Returns:
            Dict mapping format to the saved file path.

        Raises:
            ValueError: If DPI is less than 72.
        """
        if dpi < 72:
            raise ValueError(f"DPI must be >= 72, got {dpi}")

        if formats is None:
            formats = ["png"]

        out = Path(output_dir or "reports")
        out.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        paths: dict[str, str] = {}

        for fmt in formats:
            filename = f"{name}_{timestamp}.{fmt}"
            filepath = out / filename
            fig.savefig(
                str(filepath), dpi=dpi, format=fmt,
                bbox_inches="tight",
                facecolor=fig.get_facecolor(),
            )
            paths[fmt] = str(filepath)
            logger.info("Exported figure to %s", filepath)

        # Close figure to free memory
        import matplotlib.pyplot as plt
        plt.close(fig)

        return paths

    def export_dataframe(
        self,
        df: pd.DataFrame,
        name: str,
        formats: Optional[list[str]] = None,
        output_dir: Optional[str] = None,
    ) -> dict[str, str]:
        """Export a DataFrame to one or more formats.

        Args:
            df: The DataFrame to export.
            name: Base filename (without extension).
            formats: List of formats ('csv', 'json', 'xlsx').
            output_dir: Output directory.

        Returns:
            Dict mapping format to saved file path.
        """
        if formats is None:
            formats = ["csv"]

        out = Path(output_dir or "reports")
        out.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        paths: dict[str, str] = {}

        for fmt in formats:
            filename = f"{name}_{timestamp}.{fmt}"
            filepath = out / filename

            if fmt == "csv":
                df.to_csv(filepath, index=False)
            elif fmt == "json":
                df.to_json(
                    filepath, orient="records", indent=2, default_handler=str,
                )
            elif fmt == "xlsx":
                try:
                    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                        # Metadata sheet
                        meta = pd.DataFrame({
                            "Field": ["Report Name", "Generated", "Rows"],
                            "Value": [name, timestamp, len(df)],
                        })
                        meta.to_excel(
                            writer, sheet_name="Metadata", index=False,
                        )
                        df.to_excel(
                            writer, sheet_name="Data", index=False,
                        )
                except ImportError:
                    logger.warning("openpyxl not installed; skipping xlsx.")
                    continue
            else:
                logger.warning("Unsupported format: %s", fmt)
                continue

            paths[fmt] = str(filepath)
            logger.info("Exported DataFrame to %s", filepath)

        return paths

    def batch_export(
        self,
        figures: dict[str, Figure],
        formats: list[str],
        output_dir: str,
    ) -> dict[str, dict[str, str]]:
        """Export multiple named figures.

        Args:
            figures: Dict mapping figure names to Figure objects.
            formats: List of output formats.
            output_dir: Output directory.

        Returns:
            Nested dict: {figure_name: {format: path}}.
        """
        results: dict[str, dict[str, str]] = {}
        for name, fig in figures.items():
            results[name] = self.export_figure(
                fig, name, formats=formats, output_dir=output_dir,
            )
        return results

    def create_export_manifest(
        self,
        export_results: dict[str, Any],
        output_dir: str,
    ) -> str:
        """Create a JSON manifest of all exported files.

        Args:
            export_results: Dict of export results from batch_export.
            output_dir: Directory to save the manifest.

        Returns:
            Path to the manifest file.
        """
        manifest_entries = []

        for name, format_paths in export_results.items():
            if isinstance(format_paths, dict):
                for fmt, path in format_paths.items():
                    size_kb = 0
                    try:
                        size_kb = round(
                            os.path.getsize(path) / 1024, 2
                        )
                    except OSError:
                        pass

                    manifest_entries.append({
                        "name": name,
                        "format": fmt,
                        "path": path,
                        "size_kb": size_kb,
                        "created_at": datetime.utcnow().isoformat(),
                    })

        manifest_path = Path(output_dir) / "export_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest_entries, fh, indent=2, default=str)

        logger.info("Export manifest saved to %s", manifest_path)
        return str(manifest_path)
