"""Test configuration for prosemark tests."""

import os

import pytest

# Import custom fixtures from the fixtures module
from .fixtures.binder_with_placeholders import (
    binder_with_invalid_placeholder_names,
    binder_with_large_number_of_placeholders,
    binder_with_mixed_nodes,
    binder_with_no_placeholders,
    binder_with_placeholders,
    empty_binder,
    no_binder,
)

__all__ = [
    'binder_with_invalid_placeholder_names',
    'binder_with_large_number_of_placeholders',
    'binder_with_mixed_nodes',
    'binder_with_no_placeholders',
    'binder_with_placeholders',
    'empty_binder',
    'no_binder',
]


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables to prevent interactive editor launches."""
    # Override EDITOR to prevent interactive editors from opening during tests
    os.environ['EDITOR'] = 'echo'
    # Also set VISUAL as a fallback
    os.environ['VISUAL'] = 'echo'
