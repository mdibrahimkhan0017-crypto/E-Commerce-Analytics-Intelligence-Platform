#!/usr/bin/env python3
"""Project scaffold generator for the E-Commerce Analytics Platform.

Creates the required directory tree and placeholder __init__.py files
for every Python sub-package under src/.

Usage:
    python setup_project.py
"""

import os
from pathlib import Path


# ── Directory tree specification ─────────────────────────────────────────────
# Each entry is a directory that will be created (relative to project root).
DIRECTORIES: list[str] = [
    "data",
    "db",
    "reports",
    "logs",
    "docs",
    "scripts",
    "src",
    "src/ingestion",
    "src/engine",
    "src/engine/queries",
    "src/analytics",
    "src/visualisation",
    "src/visualisation/charts",
    "src/utils",
    "src/db",
    "tests",
]

# Sub-packages that need an __init__.py (all directories under src/)
PACKAGES: list[str] = [
    "src",
    "src/ingestion",
    "src/engine",
    "src/analytics",
    "src/visualisation",
    "src/visualisation/charts",
    "src/utils",
    "src/db",
]


def _init_content(package_path: str) -> str:
    """Return a minimal __init__.py docstring for the given package.

    Args:
        package_path: Dotted or slash-separated package path.

    Returns:
        A string containing the __init__.py file content.
    """
    module_name = package_path.replace("/", ".")
    return f'"""Package: {module_name}."""\n'


def create_scaffold(root: Path | None = None) -> None:
    """Create the full project directory tree and placeholder files.

    Args:
        root: Project root directory.  Defaults to the current working
              directory.
    """
    root = root or Path.cwd()

    # Create directories
    for dir_path in DIRECTORIES:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Directory: {dir_path}/")

    # Create __init__.py files
    for pkg_path in PACKAGES:
        init_file = root / pkg_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(_init_content(pkg_path), encoding="utf-8")
            print(f"  ✓ Created:   {pkg_path}/__init__.py")
        else:
            print(f"  · Exists:    {pkg_path}/__init__.py")

    # Create .gitkeep in empty data directories
    for keep_dir in ("data", "db", "reports", "logs"):
        gitkeep = root / keep_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    print("\n✅ Project scaffold created successfully.")


if __name__ == "__main__":
    project_root = Path(os.path.dirname(os.path.abspath(__file__)))
    print(f"Setting up project at: {project_root}\n")
    create_scaffold(project_root)
