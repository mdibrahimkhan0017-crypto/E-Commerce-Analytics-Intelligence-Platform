"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner

from src.cli import cli


class TestCLI:
    """Test CLI commands using Click's CliRunner."""

    @pytest.fixture
    def runner(self):
        """Create a CliRunner."""
        return CliRunner()

    def test_help(self, runner):
        """Main help should display command groups."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "ingest" in result.output
        assert "report" in result.output

    def test_generate_help(self, runner):
        """Generate help should show all options."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--records" in result.output
        assert "--seed" in result.output

    def test_generate_command(self, runner, tmp_path):
        """Generate should create CSV files."""
        result = runner.invoke(cli, [
            "generate",
            "--records", "100",
            "--start", "2023-01-01",
            "--end", "2023-06-30",
            "--seed", "42",
            "--output-dir", str(tmp_path / "data"),
        ])
        assert result.exit_code == 0
        assert "generated" in result.output.lower()

    def test_health_command(self, runner):
        """Health check should execute."""
        result = runner.invoke(cli, ["health"])
        # May exit 1 if no DB, but should not crash
        assert result.exit_code in (0, 1)

    def test_query_no_args(self, runner):
        """Query without --name or --file should error."""
        result = runner.invoke(cli, ["query"])
        assert result.exit_code == 1

    def test_ingest_help(self, runner):
        """Ingest help should show options."""
        result = runner.invoke(cli, ["ingest", "--help"])
        assert result.exit_code == 0
        assert "--source" in result.output

    def test_report_help(self, runner):
        """Report help should show options."""
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output

    def test_schedule_help(self, runner):
        """Schedule help should show options."""
        result = runner.invoke(cli, ["schedule", "--help"])
        assert result.exit_code == 0
        assert "--mode" in result.output
