# cap: clinics.lisa.doctores
"""Credential validator — per-country validation rules for medical credentials.

Supported countries (ADR-vitalia-004 § D-6):
  PE — CMP (Colegio Médico del Perú): numeric string
  AR — Matrícula nacional/provincial: numeric or 'nacional/provincial' format
  MX — Cédula profesional: 7-8 digits
  CL — Registro nacional: numeric

Per 01-spec.md § Microcopy: error messages are Spanish neutro LatAm (no voseo).
"""

from __future__ import annotations

import re


class CredentialValidationError(ValueError):
    """Raised when a medical credential does not match country-specific rules.

    Maps to HTTP 422 Unprocessable Entity in the API layer.

    Attributes:
        field: Always "credential" (for DTO error mapping).
        message: Spanish neutro LatAm error message.
    """

    def __init__(self, message: str) -> None:
        """Initialize with a user-facing error message.

        Args:
            message: Spanish neutro message describing the validation failure.
        """
        self.field = "credential"
        self.message = message
        super().__init__(message)


# Country-specific validation patterns + labels
_PE_PATTERN = re.compile(r"^\d+$")
_AR_PATTERN = re.compile(r"^\d+(/\d+)?$")  # national or national/provincial
_MX_PATTERN = re.compile(r"^\d{7,8}$")
_CL_PATTERN = re.compile(r"^\d+$")

_COUNTRY_RULES: dict[str, tuple[re.Pattern[str], str, str]] = {
    "PE": (
        _PE_PATTERN,
        "CMP",
        "La credencial CMP debe ser numérica. Ejemplo: 123456",
    ),
    "AR": (
        _AR_PATTERN,
        "matrícula",
        "La matrícula debe ser numérica o en formato nacional/provincial. Ejemplo: 12345 o 12345/67890",
    ),
    "MX": (
        _MX_PATTERN,
        "cédula profesional",
        "La cédula profesional debe tener entre 7 y 8 dígitos. Ejemplo: 1234567",
    ),
    "CL": (
        _CL_PATTERN,
        "registro nacional",
        "El registro nacional debe ser numérico. Ejemplo: 9876543",
    ),
}


def validate_credential(credential: str, country: str) -> None:
    """Validate a medical credential for the given country code.

    Args:
        credential: Raw credential string from request (e.g. "12345").
        country: ISO 3166-1 alpha-2 code: PE, AR, MX, or CL.

    Raises:
        CredentialValidationError: If the credential does not match country rules.
            field="credential", message in Spanish neutro LatAm.
    """
    country_upper = country.upper()

    if country_upper not in _COUNTRY_RULES:
        raise CredentialValidationError(
            f"País '{country}' no tiene validación de credencial configurada. "
            f"Países soportados: {', '.join(sorted(_COUNTRY_RULES.keys()))}."
        )

    pattern, label, error_message = _COUNTRY_RULES[country_upper]

    if not pattern.match(credential.strip()):
        raise CredentialValidationError(error_message)
