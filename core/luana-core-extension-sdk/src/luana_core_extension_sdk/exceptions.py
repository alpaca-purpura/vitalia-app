"""SDK exception hierarchy — 3 exception types per §1.3 step 2."""

from __future__ import annotations


class ExtensionSDKError(Exception):
    """Base exception for all SDK errors."""


class NamespaceViolationError(ExtensionSDKError):
    """Raised when registration name lacks brand_slug prefix (CC-4)."""


class DuplicateRegistrationError(ExtensionSDKError):
    """Raised when same name registered twice within same EP (CC-4)."""


class RegistrationClosedError(ExtensionSDKError):
    """Raised when register_* called after FastAPI startup completes (CC-3)."""
