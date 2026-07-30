"""Agentic eval smoke — PII detection (V-AE-2).

10 PII inputs (AR DNI / CL RUT / MX RFC / email / phone) must all be detected.
This mirrors the unit test coverage at smoke level — deterministic, no LLM calls.

Per 04-validators.yaml V-AE-2:
  "10 PII inputs (AR DNI / CL RUT / MX RFC / email / phone) detected (spec § 15.2)"

Run:
    cd $WS/vitalia/backend && .venv/bin/pytest \
        tests/agentic_evals/smoke/smoke_pii_detection.py -v
"""

from __future__ import annotations

import pytest

from src.modules.vitalia.application.services.pii_scanner_service import PiiScannerService

# ── Fixture ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def scanner() -> PiiScannerService:
    return PiiScannerService()


# ── 10 PII inputs (spec § 15.2) ──────────────────────────────────────────────

_PII_CASES = [
    # 1. AR DNI formatted
    ("ar_dni_formatted", "Paciente con DNI 12.345.678 presente.", "dni_ar"),
    # 2. AR DNI formatted variant
    ("ar_dni_formatted_2", "documento 23.456.789 del paciente confirmado", "dni_ar"),
    # 3. CL RUT formatted
    ("cl_rut_formatted", "RUT del paciente: 12.345.678-9.", "rut_cl"),
    # 4. CL RUT formatted variant
    ("cl_rut_formatted_2", "Rut 9.876.543-2 Aurora Mindful", "rut_cl"),
    # 5. MX RFC structural
    ("mx_rfc_structural", "Factura a nombre de AAAA900101AAA.", "rfc_mx"),
    # 6. MX CURP structural
    ("mx_curp_structural", "CURP del paciente: JUPM800101HDFLRN02.", "curp_mx"),
    # 7. Email
    ("email_clinic", "correo paciente@clinicaaurora.com para agendar.", "email"),
    # 8. Email variant
    ("email_personal", "dra.lopez@saludmindful.org es el contacto.", "email"),
    # 9. Phone +54 AR
    ("phone_ar_intl", "+54 9 11 1234-5678 para confirmar.", "phone"),
    # 10. Phone +56 CL
    ("phone_cl_intl", "Llamar a +56 9 8765 4321 urgente.", "phone"),
]


@pytest.mark.parametrize("label,text,expected_category", _PII_CASES, ids=[c[0] for c in _PII_CASES])
def test_pii_input_detected(
    scanner: PiiScannerService,
    label: str,
    text: str,
    expected_category: str,
) -> None:
    """V-AE-2: Each of the 10 PII input patterns must be detected by PiiScannerService."""
    result = scanner.scan(text)
    assert expected_category in result.detected, (
        f"[{label}] Expected '{expected_category}' in detected={result.detected} for: {text!r}"
    )
    assert result.blocked is True, f"[{label}] result.blocked must be True when PII detected. Got: {result.blocked}"


def test_all_ten_pii_cases_covered() -> None:
    """Sanity: confirm parametrize list has exactly 10 entries (spec § 15.2)."""
    assert len(_PII_CASES) == 10, f"V-AE-2 requires exactly 10 PII cases, got {len(_PII_CASES)}"
