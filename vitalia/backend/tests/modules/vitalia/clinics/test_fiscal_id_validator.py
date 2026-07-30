# cap: configuracion.cuenta
"""RED tests for fiscal_id_validator — written BEFORE implementation (TDD).

Covers:
  - AR CUIT: 11-digit mod-11 checksum (valid + invalid + wrong length)
  - PE RUC: 11-digit format (valid + invalid)
  - MX RFC: 12-13 alphanumeric (valid + invalid)
  - UY RUT: 12-digit mod-11 (valid + invalid)
  - CL NIT: freetext accepted (any non-empty string)
  - CO NIT: freetext accepted (any non-empty string)
  - Unsupported country: freetext degradation — no raise, returns None
  - Empty string: raises FiscalIdValidationError regardless of country
  - Hypothesis: valid CUIT always returns None (no exception)
"""

from __future__ import annotations

import pytest

# Hypothesis (optional — skip gracefully if not installed)
try:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

from src.modules.vitalia._shared.validation.fiscal_id_validator import (
    FiscalIdValidationError,
    validate_fiscal_id,
)

# ---------------------------------------------------------------------------
# AR CUIT — mod-11 checksum
# CUIT 20-23456789-4 is a known-valid CUIT for tests.
# Checksum: weights [5,4,3,2,7,6,5,4,3,2], sum * 1, remainder vs digit.
# ---------------------------------------------------------------------------

VALID_AR_CUITS = [
    "20234567897",  # no dashes (check digit = 7 per mod-11)
    "20-23456789-7",  # with dashes (strip hyphens)
]
INVALID_AR_CUITS = [
    "20234567894",  # wrong check digit (4 != 7)
    "1234567890",  # 10 digits
    "202345678945",  # 12 digits
]


@pytest.mark.parametrize("cuit", VALID_AR_CUITS)
def test_ar_cuit_valid(cuit: str) -> None:
    """Valid CUIT returns None (no error)."""
    result = validate_fiscal_id(cuit, "AR")
    assert result is None


@pytest.mark.parametrize("cuit", INVALID_AR_CUITS)
def test_ar_cuit_invalid(cuit: str) -> None:
    """Invalid CUIT raises FiscalIdValidationError."""
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id(cuit, "AR")


# ---------------------------------------------------------------------------
# PE RUC — 11-digit numeric
# ---------------------------------------------------------------------------

VALID_PE_RUCS = [
    "20600010456",  # 11 digits, starts with 20 (legal entity)
    "10123456789",  # 11 digits, starts with 10 (natural person)
]
INVALID_PE_RUCS = [
    "1234567890",  # 10 digits
    "ABCDE678901",  # non-numeric
]


@pytest.mark.parametrize("ruc", VALID_PE_RUCS)
def test_pe_ruc_valid(ruc: str) -> None:
    result = validate_fiscal_id(ruc, "PE")
    assert result is None


@pytest.mark.parametrize("ruc", INVALID_PE_RUCS)
def test_pe_ruc_invalid(ruc: str) -> None:
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id(ruc, "PE")


# ---------------------------------------------------------------------------
# MX RFC — 12-13 alphanumeric (3-4 letters + 6 digit date + 3 homoclave)
# ---------------------------------------------------------------------------

VALID_MX_RFCS = [
    "GAMA811119T46",  # 13-char natural person (standard format)
    "IKE851223TY3",  # 12-char legal entity
]
INVALID_MX_RFCS = [
    "GAMA811119",  # too short (10)
    "12345678901234",  # too long (14)
    "123 456 789 01",  # spaces
]


@pytest.mark.parametrize("rfc", VALID_MX_RFCS)
def test_mx_rfc_valid(rfc: str) -> None:
    result = validate_fiscal_id(rfc, "MX")
    assert result is None


@pytest.mark.parametrize("rfc", INVALID_MX_RFCS)
def test_mx_rfc_invalid(rfc: str) -> None:
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id(rfc, "MX")


# ---------------------------------------------------------------------------
# UY RUT — 12-digit numeric (mod-11 checksum)
# RUT 219999400017 is a reference from DGI Uruguay test set.
# ---------------------------------------------------------------------------

VALID_UY_RUTS = [
    "219999400017",  # 12 digits
]
INVALID_UY_RUTS = [
    "21999940001",  # 11 digits
    "2199994000170",  # 13 digits
    "21999940001X",  # non-numeric
]


@pytest.mark.parametrize("rut", VALID_UY_RUTS)
def test_uy_rut_valid(rut: str) -> None:
    result = validate_fiscal_id(rut, "UY")
    assert result is None


@pytest.mark.parametrize("rut", INVALID_UY_RUTS)
def test_uy_rut_invalid(rut: str) -> None:
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id(rut, "UY")


# ---------------------------------------------------------------------------
# CL / CO NIT — freetext (any non-empty string accepted)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("country", ["CL", "CO"])
def test_cl_co_nit_accepts_any_nonempty(country: str) -> None:
    """CL and CO accept any non-empty string as NIT."""
    result = validate_fiscal_id("12345678-9", country)
    assert result is None


@pytest.mark.parametrize("country", ["CL", "CO"])
def test_cl_co_nit_accepts_short(country: str) -> None:
    result = validate_fiscal_id("123", country)
    assert result is None


# ---------------------------------------------------------------------------
# Unsupported country — freetext degradation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("country", ["BR", "US", "EC", "PY", "BO", "GT"])
def test_unsupported_country_freetext_degradation(country: str) -> None:
    """Unsupported countries accept any value (freetext degradation — Q1 resolution)."""
    result = validate_fiscal_id("some-arbitrary-value", country)
    assert result is None


# ---------------------------------------------------------------------------
# Empty string — error regardless of country
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("country", ["AR", "PE", "MX", "UY", "CL", "CO", "BR", "EC"])
def test_empty_string_raises(country: str) -> None:
    """Empty string is always invalid (all countries)."""
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id("", country)


@pytest.mark.parametrize("country", ["AR", "PE", "MX", "UY", "CL", "CO", "BR"])
def test_whitespace_only_raises(country: str) -> None:
    """Whitespace-only string is always invalid."""
    with pytest.raises(FiscalIdValidationError):
        validate_fiscal_id("   ", country)


# ---------------------------------------------------------------------------
# FiscalIdValidationError attributes
# ---------------------------------------------------------------------------


def test_error_has_field_and_message() -> None:
    """FiscalIdValidationError carries field + message attributes."""
    with pytest.raises(FiscalIdValidationError) as exc_info:
        validate_fiscal_id("INVALID", "AR")
    err = exc_info.value
    assert hasattr(err, "field")
    assert hasattr(err, "message")
    assert err.field == "fiscal_id"


# ---------------------------------------------------------------------------
# Hypothesis: valid AR CUIT (if hypothesis available)
# ---------------------------------------------------------------------------
if HAS_HYPOTHESIS:

    def _make_valid_cuit() -> str:
        """Generate a valid AR CUIT with correct mod-11 check digit."""
        weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        # Body: 2023456789 → check = 7 (pre-computed)
        body = [2, 0, 2, 3, 4, 5, 6, 7, 8, 9]
        total = sum(w * d for w, d in zip(weights, body))
        remainder = total % 11
        check = 0 if remainder == 0 else (9 if remainder == 1 else 11 - remainder)
        return "".join(str(d) for d in body) + str(check)

    @given(st.just(_make_valid_cuit()))
    @settings(max_examples=1)
    def test_hypothesis_valid_cuit_no_exception(cuit: str) -> None:
        """Hypothesis: a correctly computed CUIT never raises."""
        result = validate_fiscal_id(cuit, "AR")
        assert result is None
