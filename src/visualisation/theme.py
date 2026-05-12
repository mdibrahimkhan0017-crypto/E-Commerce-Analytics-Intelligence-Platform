"""Chart theming for the E-Commerce Analytics Platform.

Provides a ChartTheme class that configures Matplotlib rcParams
for consistent, branded chart styling.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.colors import LinearSegmentedColormap, to_rgb

logger = logging.getLogger(__name__)


class ChartTheme:
    """Manages chart theming and colour palettes.

    Loads configuration from config.yaml and applies global
    Matplotlib styling for consistent branded charts.

    Attributes:
        primary_color: Hex colour for primary accents.
        font_family: Font family for chart text.
        palette: List of hex colour strings.
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        config: Optional[dict] = None,
    ) -> None:
        """Initialise the chart theme.

        Args:
            config_path: Path to the YAML config file.
            config: Pre-loaded config dict (overrides file loading).
        """
        if config is None:
            config = self._load_config(config_path)

        theme = config.get("theme", {})
        self.primary_color: str = theme.get("primary_color", "#2E86AB")
        self.font_family: str = theme.get("font_family", "DejaVu Sans")
        self.palette: list[str] = theme.get("palette", [
            "#2E86AB", "#A23B72", "#F18F01",
            "#C73E1D", "#3B1F2B", "#44BBA4",
        ])

        reports = config.get("reports", {})
        self.default_figsize: tuple = tuple(
            reports.get("figsize", [14, 8])
        )
        self.default_dpi: int = reports.get("dpi", 150)

    @staticmethod
    def _load_config(config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to the config file.

        Returns:
            Config dictionary.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except FileNotFoundError:
            logger.warning("Config not found at %s; using defaults.", config_path)
            return {}

    def apply(self) -> None:
        """Apply theme settings to global Matplotlib rcParams."""
        mpl.rcParams.update({
            "font.family": self.font_family,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "figure.facecolor": "#FAFAFA",
            "axes.facecolor": "#FFFFFF",
            "figure.figsize": self.default_figsize,
            "figure.dpi": self.default_dpi,
            "axes.prop_cycle": plt.cycler(color=self.palette),
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.framealpha": 0.8,
        })
        logger.debug("Chart theme applied.")

    # ── Colour helpers ───────────────────────────────────────────────────

    def get_palette(self, n: int) -> list[str]:
        """Return a list of n colours, interpolating if necessary.

        Args:
            n: Number of colours required.

        Returns:
            List of hex colour strings.
        """
        if n <= len(self.palette):
            return self.palette[:n]

        # Interpolate using a custom colormap
        cmap = LinearSegmentedColormap.from_list(
            "custom", self.palette, N=n
        )
        return [
            mpl.colors.rgb2hex(cmap(i / (n - 1)))
            for i in range(n)
        ]

    def get_sequential_cmap(
        self, base_color: Optional[str] = None,
    ) -> LinearSegmentedColormap:
        """Create a sequential colormap from white to base_color.

        Args:
            base_color: Hex colour for the dark end. Defaults to
                        primary_color.

        Returns:
            A LinearSegmentedColormap instance.
        """
        color = base_color or self.primary_color
        return LinearSegmentedColormap.from_list(
            "sequential", ["#FFFFFF", color], N=256,
        )

    def get_diverging_cmap(self) -> LinearSegmentedColormap:
        """Create a diverging colormap (red–white–blue).

        Returns:
            A LinearSegmentedColormap instance.
        """
        return LinearSegmentedColormap.from_list(
            "diverging",
            ["#C73E1D", "#FFFFFF", "#2E86AB"],
            N=256,
        )

    # ── Style properties ─────────────────────────────────────────────────

    @property
    def title_style(self) -> dict[str, Any]:
        """Font style dict for chart titles."""
        return {
            "fontsize": 18,
            "fontweight": "bold",
            "color": "#1a1a2e",
            "fontfamily": self.font_family,
        }

    @property
    def subtitle_style(self) -> dict[str, Any]:
        """Font style dict for chart subtitles."""
        return {
            "fontsize": 12,
            "fontweight": "normal",
            "color": "#555555",
            "fontfamily": self.font_family,
        }

    @property
    def annotation_style(self) -> dict[str, Any]:
        """Font style dict for data annotations."""
        return {
            "fontsize": 9,
            "color": "#333333",
            "fontfamily": self.font_family,
        }
