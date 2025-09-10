"""Port protocols for Prosemark hexagonal architecture.

This module defines the protocol interfaces that serve as contracts
between the application layer and the adapters, enabling dependency
inversion and testability.
"""

from .io_ports import ConsolePort, EditorPort
from .repository_ports import BinderRepo, DailyRepo, NodeRepo
from .system_ports import Clock, IdGenerator, Logger

__all__ = [
    'BinderRepo',
    'Clock',
    'ConsolePort',
    'DailyRepo',
    'EditorPort',
    'IdGenerator',
    'Logger',
    'NodeRepo',
]
