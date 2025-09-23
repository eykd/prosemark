# Copyright (c) 2024 Prosemark Contributors
# This software is licensed under the MIT License

"""Adapters layer - External interface implementations.

This package contains concrete implementations of port interfaces,
handling all external I/O and third-party integrations.
"""

# Re-export main adapters for convenient importing
from prosemark.adapters.binder_repo_fs import BinderRepoFs
from prosemark.adapters.clock_system import ClockSystem
from prosemark.adapters.console_pretty import ConsolePretty
from prosemark.adapters.daily_repo_fs import DailyRepoFs
from prosemark.adapters.editor_launcher_system import EditorLauncherSystem
from prosemark.adapters.frontmatter_codec import FrontmatterCodec
from prosemark.adapters.id_generator_uuid7 import IdGeneratorUuid7
from prosemark.adapters.logger_stdout import LoggerStdout
from prosemark.adapters.markdown_binder_parser import MarkdownBinderParser
from prosemark.adapters.node_repo_fs import NodeRepoFs

__all__ = [
    'BinderRepoFs',
    'ClockSystem',
    'ConsolePretty',
    'DailyRepoFs',
    'EditorLauncherSystem',
    'FrontmatterCodec',
    'IdGeneratorUuid7',
    'LoggerStdout',
    'MarkdownBinderParser',
    'NodeRepoFs',
]
