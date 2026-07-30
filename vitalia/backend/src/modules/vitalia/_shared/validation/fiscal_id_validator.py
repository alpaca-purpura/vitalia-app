# cap: configuracion.cuenta
"""Fiscal ID validator for LatAm countries — pure Python, no framework imports.

Supports:
  - AR: CUIT (11 digits + mod-11 checksum)
  - PE: RUC (11 numeric digits)
  - MX: RFC (12-13 alphanumeric)
  - UY: RUT (12 numeric digits)
  - CL: NIT (freetext — any non-empty value accepted)
  - CO: NIT (freetext — any non-empty value accepted)
  - Other countries: freetext degradation — validated as non-empty only.

Freetext degradation (Q1 resolution): unsupported countries accept any
non-empty value without format checks. This is intentional to avoid blocking
tenants in countries with complex or variable fiscal ID formats.
"""

from __future__ import annotations

import re


class FiscalIdValidationError(ValueError):
    """Raised when a fiscal ID fails format or checksum validation.

    Attributes:
        field: Always "fiscal_id" (for DTO error mapping).
        message: Human-readable error message in Spanish neutro LatAm.
    """

    def __init__(self, field: str = "fiscal_id", message: str = "") -> None:
        """Initialize with field name and message."""
        self.field = field
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# AR CUIT — 11 digits, mod-11 checksum
# ---------------------------------------------------------------------------

_AR_CUIT_WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def _validate_ar_cuit(value: str) -> None:
    """Validate Argentina CUIT using mod-11 algorithm.

    Strips hyphens before validation.
    Valid CUIT format: XX-XXXXXXXX-X (11 digits total).
    """
    digits = value.replace("-", "")
    if not digits.isdigit() or len(digits) != 11:
        raise FiscalIdValidationError(message=f"CUIT inválido: debe tener 11 dígitos numéricos (recibido: {value!r})")

    total = sum(w * int(d) for w, d in zip(_AR_CUIT_WEIGHTS, digits))
    remainder = total % 11
    if remainder == 0:
        expected = 0
    elif remainder == 1:
        expected = 9
    else:
        expected = 11 - remainder

    if int(digits[-1]) != expected:
        raise FiscalIdValidationError(message=f"CUIT inválido: dígito verificador incorrecto (esperado {expected})")


# ---------------------------------------------------------------------------
# PE RUC — 11 numeric digits
# ---------------------------------------------------------------------------


def _validate_pe_ruc(value: str) -> None:
    """Validate Peru RUC (11 numeric digits)."""
    if not value.isdigit() or len(value) != 11:
        raise FiscalIdValidationError(message=f"RUC inválido: debe tener 11 dígitos numéricos (recibido: {value!r})")


# ---------------------------------------------------------------------------
# MX RFC — 12-13 alphanumeric
# RFC pattern: 3-4 letters + 6-digit date + 3-char homoclave
# Accepts: letters, digits only (no spaces/special chars)
# ---------------------------------------------------------------------------

_MX_RFC_PATTERN = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z\d]{2,3}$", re.IGNORECASE)


def _validate_mx_rfc(value: str) -> None:
    """Validate Mexico RFC (12-13 alphanumeric)."""
    cleaned = value.strip().upper()
    if len(cleaned) not in (12, 13):
        raise FiscalIdValidationError(message=f"RFC inválido: debe tener 12 o 13 caracteres (recibido: {value!r})")
    if not _MX_RFC_PATTERN.match(cleaned):
        raise FiscalIdValidationError(message=f"RFC inválido: formato incorrecto (recibido: {value!r})")


# ---------------------------------------------------------------------------
# UY RUT — 12 numeric digits
# ---------------------------------------------------------------------------


def _validate_uy_rut(value: str) -> None:
    """Validate Uruguay RUT (12 numeric digits)."""
    if not value.isdigit() or len(value) != 12:
        raise FiscalIdValidationError(message=f"RUT inválido: debe tener 12 dígitos numéricos (recibido: {value!r})")


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_VALIDATORS: dict[str, callable] = {
    "AR": _validate_ar_cuit,
    "PE": _validate_pe_ruc,
    "MX": _validate_mx_rfc,
    "UY": _validate_uy_rut,
    # CL, CO: freetext (no strict format — any non-empty value)
    # Other: freetext degradation
}


def validate_fiscal_id(value: str, country: str) -> None:
    """Validate a fiscal ID for the given country.

    Args:
        value: The fiscal ID string to validate.
        country: ISO 3166-1 alpha-2 country code (case-insensitive).

    Returns:
        None if valid.

    Raises:
        FiscalIdValidationError: If the value fails format/checksum validation.
            - Empty or whitespace-only values always raise.
            - Unsupported countries accept any non-empty value (freetext degradation).
    """
    stripped = value.strip() if value else ""
    if not stripped:
        raise FiscalIdValidationError(message="El identificador fiscal no puede estar vacío")

    country_upper = country.upper() if country else ""
    validator = _VALIDATORS.get(country_upper)

    if validator is not None:
        validator(stripped)
    # Else: freetext degradation — CL, CO, and all unsupported countries
    # accept any non-empty value without format checks.

    return None
