"""Unit tests — PiiScannerService (T-be-4 A3).

TDD RED → GREEN. Pure Python, no Postgres, no mocks needed (stateless scan).

Acceptance criteria (T-be-4):
  A3: PiiScannerService detects AR DNI / CL RUT / MX RFC / email / phone.

Also covers:
  V-F-14: PII scanner middleware — offer description + testimonial inputs.
  V-AE-2: 10 PII inputs detected (AR DNI / CL RUT / MX RFC / email / phone).
"""

from __future__ import annotations

import pytest

from src.modules.vitalia.application.services.pii_scanner_service import (
    BLOCKING_CATEGORIES,
    PiiScannerService,
)

# ── Fixture ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def scanner() -> PiiScannerService:
    return PiiScannerService()


# ── A3: Detects all required PII categories ──────────────────────────────────


def test_detects_all_pii_categories(scanner: PiiScannerService) -> None:
    """A3: Scanner detects AR DNI / CL RUT / MX RFC / email / phone in one text.

    This is the critical acceptance test per T-be-4 spec.
    """
    text = (
        "Hola, soy Juan Pérez, dni 12.345.678, "
        "mi RUT es 12.345.678-9, "
        "RFC AAAA900101AAA, "
        "email: juan@ejemplo.com, "
        "tel: +54 9 11 1234-5678"
    )
    result = scanner.scan(text)
    detected = set(result.detected)
    assert "email" in detected, f"email not detected. Found: {detected}"
    assert "phone" in detected, f"phone not detected. Found: {detected}"
    assert "dni_ar" in detected, f"AR DNI not detected. Found: {detected}"
    assert "rut_cl" in detected, f"CL RUT not detected. Found: {detected}"
    assert "rfc_mx" in detected, f"MX RFC not detected. Found: {detected}"


# ── Individual category tests ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected_category",
    [
        # AR DNI — formatted (12.345.678)
        ("Paciente con DNI 12.345.678 presente.", "dni_ar"),
        # CL RUT — formatted (12.345.678-9)
        ("RUT del paciente: 12.345.678-9.", "rut_cl"),
        # MX RFC — structural (12 chars uppercase alphanum)
        ("Factura a nombre de AAAA900101AAA.", "rfc_mx"),
        # Email
        ("Contacto: paciente@clinica.com para agendar.", "email"),
        # Phone international
        ("Llamar a +56 9 8765 4321 para confirmar.", "phone"),
        # MX CURP — structural
        ("CURP del paciente: JUPM800101HDFLRN02.", "curp_mx"),
    ],
)
def test_detects_individual_category(
    scanner: PiiScannerService,
    text: str,
    expected_category: str,
) -> None:
    """PiiScannerService detects each PII category individually."""
    result = scanner.scan(text)
    assert expected_category in result.detected, (
        f"Expected '{expected_category}' in detected={result.detected} for text: {text!r}"
    )


def test_clean_text_returns_empty_detected(scanner: PiiScannerService) -> None:
    """Clean clinical text with no PII returns empty detected list."""
    text = "El paciente presenta hipotiroidismo subclínico. Se recomienda control cada 6 meses."
    result = scanner.scan(text)
    # None of the PII categories should match
    assert result.detected == [], f"Unexpected PII detected in clean text: {result.detected}"
    assert result.blocked is False


# ── PiiScanResult model ───────────────────────────────────────────────────────


def test_pii_scan_result_blocked_when_blocking_category_detected(
    scanner: PiiScannerService,
) -> None:
    """result.blocked is True when at least one BLOCKING_CATEGORY is in detected."""
    # Email is typically blocking
    result = scanner.scan("contacto: user@example.com")
    if "email" in BLOCKING_CATEGORIES:
        assert result.blocked is True


def test_pii_scan_result_model_fields(scanner: PiiScannerService) -> None:
    """PiiScanResult has .detected (list[str]) and .blocked (bool)."""
    result = scanner.scan("texto sin PII")
    assert hasattr(result, "detected")
    assert hasattr(result, "blocked")
    assert isinstance(result.detected, list)
    assert isinstance(result.blocked, bool)


def test_scanner_scan_is_synchronous(scanner: PiiScannerService) -> None:
    """PiiScannerService.scan is a sync method (no await needed — hot path)."""
    import inspect

    assert not inspect.iscoroutinefunction(scanner.scan), (
        "PiiScannerService.scan must be synchronous (called pre-persist in hot path)"
    )


# ── Extended medical PII detection (V-AE-2 — 10 inputs) ──────────────────────


@pytest.mark.parametrize(
    "label,text,category",
    [
        ("ar_dni_1", "DNI 12.345.678 registrado", "dni_ar"),
        ("ar_dni_2", "documento 23.456.789 del paciente", "dni_ar"),
        ("cl_rut_1", "RUT 12.345.678-9 Aurora", "rut_cl"),
        ("mx_rfc_1", "RFC AAAA900101AAA factura", "rfc_mx"),
        ("mx_curp_1", "CURP JUPM800101HDFLRN02", "curp_mx"),
        ("email_1", "correo paciente@salud.com", "email"),
        ("email_2", "dra.juan@clinicaejemplo.org", "email"),
        ("phone_1", "+54 9 11 1234-5678", "phone"),
        ("phone_2", "+56 9 8765 4321 celular", "phone"),
        ("phone_3", "+52 55 1234 5678 whatsapp", "phone"),
    ],
)
def test_v_ae_2_ten_pii_inputs_detected(
    scanner: PiiScannerService,
    label: str,
    text: str,
    category: str,
) -> None:
    """V-AE-2: 10 PII input patterns detected (AR DNI / CL RUT / MX RFC / email / phone).

    Mirrors the agentic eval smoke test (smoke_pii_detection.py) at unit level.
    """
    result = scanner.scan(text)
    assert category in result.detected, f"[{label}] Expected '{category}' in detected={result.detected} for: {text!r}"


# ── Offer + testimonial integration (V-F-14) ─────────────────────────────────


def test_offer_description_scan_blocks_on_pii(scanner: PiiScannerService) -> None:
    """V-F-14: Offer description with PII is detected pre-persist."""
    offer_description = (
        "Tratamiento exclusivo para Juan Pérez (DNI 12.345.678). Contactar a juan@perez.com para más información."
    )
    result = scanner.scan(offer_description)
    assert len(result.detected) >= 2, f"Expected ≥2 PII categories in offer description, got: {result.detected}"


def test_testimonial_quote_scan_blocks_on_pii(scanner: PiiScannerService) -> None:
    """V-F-14: Testimonial quote with PII is detected pre-persist."""
    testimonial = "Me llamo María López, RUT 9.876.543-2, y puedo ser contactada al +56 9 1111 2222."
    result = scanner.scan(testimonial)
    assert "rut_cl" in result.detected, f"CL RUT not detected in testimonial: {result.detected}"
    assert "phone" in result.detected, f"phone not detected in testimonial: {result.detected}"


def test_clean_offer_description_not_blocked(scanner: PiiScannerService) -> None:
    """Clean offer description without PII passes scanner (not blocked)."""
    offer_description = (
        "Consulta de salud mental con profesionales certificados. "
        "Terapia cognitivo-conductual para adultos. "
        "Sesiones de 50 minutos, formato online o presencial en Santiago."
    )
    result = scanner.scan(offer_description)
    assert result.detected == [], f"False positives in clean offer: {result.detected}"
    assert result.blocked is False
