"""Custom exceptions for prosemark."""


class ProsemarkError(Exception):
    """Base exception for all prosemark errors."""


class NodeIdentityError(ProsemarkError):
    """Error raised when node identity validation fails."""
