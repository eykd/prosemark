"""Configuration management for Prosemark.

This package provides a hierarchical, layered configuration system that integrates
with Click CLI options, supports automatic inheritance resolution, and validates
configuration using Pydantic models.
"""

from prosemark.config.manager import ConfigManager

__all__ = ['ConfigManager']
