# cap: clinics.lisa.doctores
"""Tests for credential_validator.py — TDD RED-first.

Covers SC-2 (invalid credential → 422 per country).
Per 03-arch-be.md § 6: PE=CMP numeric, AR=matrícula nacional+provincial,
MX=cédula profesional 7-8 digits, CL=registro nacional numeric.
"""

from __future__ import annotations

import pytest

from src.modules.vitalia.clinics.application.credential_validator import (
    CredentialValidationError,
    validate_credential,
)

# ── PE (CMP) ─────────────────────────────────────────────────────────────────


def test_pe_valid_numeric() -> None:
    """CMP number: pure numeric string passes."""
    validate_credential("12345", "PE")  # must not raise


def test_pe_valid_long_numeric() -> None:
    """CMP can be 6 digits."""
    validate_credential("123456", "PE")  # must not raise


def test_pe_invalid_alpha() -> None:
    """CMP with alpha chars → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="CMP"):
        validate_credential("CMP123", "PE")


def test_pe_invalid_slash() -> None:
    """CMP with slash → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="CMP"):
        validate_credential("12/34", "PE")


# ── AR (matrícula nacional+provincial) ───────────────────────────────────────


def test_ar_valid_slash_format() -> None:
    """Matrícula format 'nacional/provincial' passes."""
    validate_credential("12345/67890", "AR")  # must not raise


def test_ar_valid_numbers_only() -> None:
    """Pure numeric matricula also passes (national only)."""
    validate_credential("123456", "AR")  # must not raise


def test_ar_invalid_alpha_prefix() -> None:
    """AR credential with alpha → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="matrícula"):
        validate_credential("MP12345", "AR")


def test_ar_invalid_double_slash() -> None:
    """AR credential with two slashes → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="matrícula"):
        validate_credential("12/34/56", "AR")


# ── MX (cédula profesional) ───────────────────────────────────────────────────


def test_mx_valid_7_digits() -> None:
    """Cédula profesional: 7 digits passes."""
    validate_credential("1234567", "MX")  # must not raise


def test_mx_valid_8_digits() -> None:
    """Cédula profesional: 8 digits passes."""
    validate_credential("12345678", "MX")  # must not raise


def test_mx_invalid_6_digits() -> None:
    """Cédula profesional: 6 digits → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="cédula"):
        validate_credential("123456", "MX")


def test_mx_invalid_alpha() -> None:
    """Cédula profesional: alpha → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="cédula"):
        validate_credential("ABCDEFG", "MX")


# ── CL (registro nacional) ────────────────────────────────────────────────────


def test_cl_valid_numeric() -> None:
    """Registro nacional: numeric passes."""
    validate_credential("9876543", "CL")  # must not raise


def test_cl_invalid_alpha() -> None:
    """Registro nacional: alpha → CredentialValidationError."""
    with pytest.raises(CredentialValidationError, match="registro"):
        validate_credential("REG123", "CL")


# ── Unknown country ───────────────────────────────────────────────────────────


def test_unknown_country_raises() -> None:
    """Unknown country code → CredentialValidationError."""
    with pytest.raises(CredentialValidationError):
        validate_credential("12345", "BR")


# ── Error field and message ───────────────────────────────────────────────────


def test_error_has_field_credential() -> None:
    """CredentialValidationError must have field='credential'."""
    with pytest.raises(CredentialValidationError) as exc_info:
        validate_credential("INVALID", "PE")
    assert exc_info.value.field == "credential"


def test_error_message_spanish_neutro() -> None:
    """Error message must be Spanish neutro (no voseo)."""
    with pytest.raises(CredentialValidationError) as exc_info:
        validate_credential("INVALID", "PE")
    # voseo-allowed: citations of voseo patterns as test assertions (not user-facing strings)
    # No voseo patterns: sos/tenés/podés/debés/mirá/dejá
    msg = exc_info.value.message.lower()
    assert "sos" not in msg
    assert "tenés" not in msg
    assert "debés" not in msg
