"""Tests for exceptions.py — 3 exception types per §1.3 step 2.

TDD: these tests written FIRST (RED phase before exceptions.py exists).
"""

from __future__ import annotations


def test_extension_sdk_error_exists():
    """ExtensionSDKError base exception must exist."""
    from luana_core_extension_sdk.exceptions import ExtensionSDKError

    assert issubclass(ExtensionSDKError, Exception)


def test_namespace_violation_error_inherits_base():
    """NamespaceViolationError must inherit ExtensionSDKError."""
    from luana_core_extension_sdk.exceptions import (
        ExtensionSDKError,
        NamespaceViolationError,
    )

    assert issubclass(NamespaceViolationError, ExtensionSDKError)


def test_duplicate_registration_error_inherits_base():
    """DuplicateRegistrationError must inherit ExtensionSDKError."""
    from luana_core_extension_sdk.exceptions import (
        DuplicateRegistrationError,
        ExtensionSDKError,
    )

    assert issubclass(DuplicateRegistrationError, ExtensionSDKError)


def test_registration_closed_error_inherits_base():
    """RegistrationClosedError must inherit ExtensionSDKError."""
    from luana_core_extension_sdk.exceptions import (
        ExtensionSDKError,
        RegistrationClosedError,
    )

    assert issubclass(RegistrationClosedError, ExtensionSDKError)


def test_exactly_3_exception_subtypes():
    """Exactly 3 subtypes of ExtensionSDKError must be defined."""
    from luana_core_extension_sdk.exceptions import (
        DuplicateRegistrationError,
        NamespaceViolationError,
        RegistrationClosedError,
    )

    subtypes = {NamespaceViolationError, DuplicateRegistrationError, RegistrationClosedError}
    assert len(subtypes) == 3


def test_exceptions_are_raiseable():
    """All 3 exception types must be raiseable and catchable as ExtensionSDKError."""
    import pytest
    from luana_core_extension_sdk.exceptions import (
        DuplicateRegistrationError,
        ExtensionSDKError,
        NamespaceViolationError,
        RegistrationClosedError,
    )

    for exc_cls in [NamespaceViolationError, DuplicateRegistrationError, RegistrationClosedError]:
        with pytest.raises(ExtensionSDKError):
            raise exc_cls("test message")
