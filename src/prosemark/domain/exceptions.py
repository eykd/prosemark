"""Domain exceptions for Prosemark."""


class ProsemarkDomainError(Exception):
    """Base exception for all domain errors."""


class NodeIdentityError(ProsemarkDomainError):
    """Exception raised for node ID validation issues."""


class BinderIntegrityError(ProsemarkDomainError):
    """Exception raised for binder validation failures."""
