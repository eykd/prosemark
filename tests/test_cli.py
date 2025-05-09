from __future__ import annotations

import pytest
from click.testing import CliRunner

from prosemark import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


def test_cli_main(runner: CliRunner) -> None:
    """Test that the CLI runs without error."""
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
