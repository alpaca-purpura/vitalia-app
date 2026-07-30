# cap: clinics.lisa.doctores
"""CredentialCountry enum — supported credential validation countries.

Pure Python StrEnum — no framework imports.
Extensible: add new country codes as Vitalia expands.
"""

from __future__ import annotations

from enum import StrEnum


class CredentialCountry(StrEnum):
    """ISO 3166-1 alpha-2 country codes with supported credential validation."""

    PE = "PE"
    """Peru — Colegio Médico del Perú (CMP), numeric."""

    AR = "AR"
    """Argentina — Matrícula nacional/provincial, slash-delimited."""

    MX = "MX"
    """Mexico — Cédula profesional, 7-8 digits."""

    CL = "CL"
    """Chile — Registro nacional, numeric."""
