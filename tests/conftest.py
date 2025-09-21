"""Test configuration for prosemark tests."""

import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables to prevent interactive editor launches."""
    # Override EDITOR to prevent interactive editors from opening during tests
    os.environ['EDITOR'] = 'echo'
    # Also set VISUAL as a fallback
    os.environ['VISUAL'] = 'echo'
