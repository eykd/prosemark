"""Ports layer - Interface definitions and protocols.

This package defines the contracts (ports) for external interactions.
Port interfaces are defined using Python protocols or abstract base classes,
specifying the contracts that adapters must implement.
"""

from prosemark.ports.binder_repo import BinderRepo
from prosemark.ports.clock import Clock
from prosemark.ports.config_port import ConfigPort
from prosemark.ports.console_port import ConsolePort
from prosemark.ports.daily_repo import DailyRepo
from prosemark.ports.editor_port import EditorPort
from prosemark.ports.id_generator import IdGenerator
from prosemark.ports.logger import Logger
from prosemark.ports.node_repo import NodeRepo

__all__ = [
    'BinderRepo',
    'Clock',
    'ConfigPort',
    'ConsolePort',
    'DailyRepo',
    'EditorPort',
    'IdGenerator',
    'Logger',
    'NodeRepo',
]
