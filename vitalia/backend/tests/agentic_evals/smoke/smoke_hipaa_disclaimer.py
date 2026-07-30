"""Agentic eval smoke — HIPAA-lite disclaimer insertion (V-AE-4).

5 conversation flows insert HIPAA disclaimer (spec § 15.4).

Per 04-validators.yaml V-AE-4:
  "5 conversation flows insert HIPAA disclaimer (spec § 15.4)"

Strategy — deterministic smoke, no LLM calls:
  Tests exercise the `medical_disclaimer_required` output guardrail with
  5 distinct medical conversation response types. Each verifies:
    1. Disclaimer inserted when medical topic detected
    2. DISCLAIMER_TEXT canonical phrase present in result
    3. Idempotency: second call on already-decorated response does NOT duplicate

Conversation flows tested (spec § 15.4):
  1. Dental procedure recommendation
  2. Medication topic (psychiatry)
  3. Surgical consultation
  4. Psychology therapy recommendation
  5. Medical condition explanation

Run:
    cd $WS/vitalia/backend && uv run pytest \
        tests/agentic_evals/smoke/smoke_hipaa_disclaimer.py -v
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from src.modules.vitalia.agentic.guardrails.medical_disclaimer_required import (
    DISCLAIMER_TEXT,
)
from src.modules.vitalia.agentic.guardrails.medical_disclaimer_required import (
    medical_disclaimer_required_check as apply_disclaimer_decorator,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


class _InMemoryAuditLog:
    """In-memory stand-in for medical_audit_log (best-effort writes)."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        self.entries.append(
            {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "event_type": event_type,
                "payload": payload,
            }
        )


_TENANT_ID = uuid.UUID("00000000-1111-2222-3333-000000000001")

# ── 5 conversation flows (spec § 15.4) ───────────────────────────────────────

# Flow 1: dental procedure recommendation (dental vertical)
_FLOW_1_DENTAL_PROCEDURE = (
    "Te recomiendo realizar una limpieza dental profunda y evaluar el implante "
    "para el molar derecho. El procedimiento incluye anestesia local y tiene una "
    "duración de aproximadamente 90 minutos."
)

# Flow 2: medication topic (psychiatry vertical — forced disclaimer for medication queries)
_FLOW_2_MEDICATION_PSYCHIATRY = (
    "En cuanto a la medicación que mencionás, es importante no modificar la dosis "
    "sin consultar con tu psiquiatra. Continuá tomando el antidepresivo según lo indicado."
)

# Flow 3: surgical consultation (surgical topic)
_FLOW_3_SURGICAL = (
    "La cirugía de extracción del tercer molar está indicada en tu caso. "
    "El postoperatorio habitualmente dura entre 3 y 7 días con reposo relativo."
)

# Flow 4: psychology therapy recommendation
_FLOW_4_THERAPY = (
    "Te sugiero continuar con la terapia cognitivo-conductual para trabajar "
    "los patrones de pensamiento que mencionaste. La frecuencia recomendada "
    "es una sesión semanal durante al menos 3 meses."
)

# Flow 5: medical condition explanation
_FLOW_5_CONDITION = (
    "El cuadro que describes puede estar relacionado con una condición de "
    "ansiedad generalizada, aunque solo el especialista puede evaluar tu caso "
    "en forma completa con el historial clínico."
)


@pytest.fixture
def audit_log() -> _InMemoryAuditLog:
    return _InMemoryAuditLog()


# ── Smoke flow 1: dental procedure ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_dental_procedure(audit_log: _InMemoryAuditLog) -> None:
    """Spec § 15.4 flow 1 — dental procedure: disclaimer must be inserted."""
    result = await apply_disclaimer_decorator(
        llm_response=_FLOW_1_DENTAL_PROCEDURE,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    # Canonical disclaimer phrase must be present
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    assert canonical_phrase in result, (
        f"Flow 1 (dental procedure): DISCLAIMER missing in output.\n"
        f"Expected substring: {canonical_phrase!r}\n"
        f"Got: {result!r}"
    )
    # Audit entry written
    assert len(audit_log.entries) == 1, f"Expected 1 audit entry, got {len(audit_log.entries)}"
    assert audit_log.entries[0]["event_type"] == "disclaimer_inserted"


# ── Smoke flow 2: medication psychiatry ──────────────────────────────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_medication_psychiatry(audit_log: _InMemoryAuditLog) -> None:
    """Spec § 15.4 flow 2 — medication topic (psychiatry): disclaimer must be inserted."""
    result = await apply_disclaimer_decorator(
        llm_response=_FLOW_2_MEDICATION_PSYCHIATRY,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    assert canonical_phrase in result, f"Flow 2 (medication psychiatry): DISCLAIMER missing in output.\nGot: {result!r}"
    assert len(audit_log.entries) == 1
    assert audit_log.entries[0]["event_type"] == "disclaimer_inserted"


# ── Smoke flow 3: surgical consultation ──────────────────────────────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_surgical_consultation(audit_log: _InMemoryAuditLog) -> None:
    """Spec § 15.4 flow 3 — surgical consultation: disclaimer must be inserted."""
    result = await apply_disclaimer_decorator(
        llm_response=_FLOW_3_SURGICAL,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    assert canonical_phrase in result, f"Flow 3 (surgical): DISCLAIMER missing in output.\nGot: {result!r}"
    assert len(audit_log.entries) == 1


# ── Smoke flow 4: psychology therapy ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_psychology_therapy(audit_log: _InMemoryAuditLog) -> None:
    """Spec § 15.4 flow 4 — psychology therapy: disclaimer must be inserted."""
    result = await apply_disclaimer_decorator(
        llm_response=_FLOW_4_THERAPY,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    assert canonical_phrase in result, f"Flow 4 (therapy): DISCLAIMER missing in output.\nGot: {result!r}"
    assert len(audit_log.entries) == 1


# ── Smoke flow 5: medical condition explanation ───────────────────────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_condition_explanation(audit_log: _InMemoryAuditLog) -> None:
    """Spec § 15.4 flow 5 — medical condition explanation: disclaimer must be inserted."""
    result = await apply_disclaimer_decorator(
        llm_response=_FLOW_5_CONDITION,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    assert canonical_phrase in result, f"Flow 5 (condition): DISCLAIMER missing in output.\nGot: {result!r}"
    assert len(audit_log.entries) == 1


# ── Idempotency smoke: second call does NOT duplicate disclaimer ──────────────


@pytest.mark.asyncio
async def test_smoke_hipaa_disclaimer_idempotent_no_duplicate(audit_log: _InMemoryAuditLog) -> None:
    """Idempotency invariant: applying disclaimer twice does NOT produce duplicates.

    Per medical_disclaimer_required module contract: second call on an already-
    decorated response returns the response unchanged + writes NO new audit entry.
    """
    first_result = await apply_disclaimer_decorator(
        llm_response=_FLOW_1_DENTAL_PROCEDURE,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    assert len(audit_log.entries) == 1  # First call wrote 1 entry

    # Second call on already-decorated response
    second_result = await apply_disclaimer_decorator(
        llm_response=first_result,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )

    # No new audit entry (idempotent)
    assert len(audit_log.entries) == 1, (
        f"Second call MUST NOT write a new audit entry. Got {len(audit_log.entries)} entries."
    )
    # Response string unchanged
    assert second_result == first_result, (
        "Second call on already-decorated response MUST return identity string. "
        f"First: {first_result!r}\nSecond: {second_result!r}"
    )
    # Canonical phrase appears exactly once
    canonical_phrase = "Esto no reemplaza consulta médica profesional"
    count = second_result.count(canonical_phrase)
    assert count == 1, f"Canonical phrase MUST appear exactly once after idempotent second call. Got {count}."


# ── Sanity: 5 flows covered ────────────────────────────────────────────────────


def test_five_disclaimer_flows_sanity() -> None:
    """Sanity: spec § 15.4 requires exactly 5 conversation flows."""
    flows = [
        _FLOW_1_DENTAL_PROCEDURE,
        _FLOW_2_MEDICATION_PSYCHIATRY,
        _FLOW_3_SURGICAL,
        _FLOW_4_THERAPY,
        _FLOW_5_CONDITION,
    ]
    assert len(flows) == 5, f"V-AE-4 requires exactly 5 disclaimer flows, got {len(flows)}"
    assert len(set(flows)) == 5, "All 5 flows must be distinct"


# ── DISCLAIMER_TEXT export sanity ─────────────────────────────────────────────


def test_disclaimer_text_constant_exported() -> None:
    """DISCLAIMER_TEXT constant must be exported and non-empty."""
    assert DISCLAIMER_TEXT, "DISCLAIMER_TEXT must be non-empty"
    assert "consulta médica" in DISCLAIMER_TEXT.lower(), (
        "DISCLAIMER_TEXT must reference 'consulta médica' per spec § 17.3"
    )
