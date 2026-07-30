"""Guardrail tests — `medical_disclaimer_required` (vitalia AGENTIC, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-guards-3 + 02-design § 17.3 + 03-arch § 10:
  A1: test_inserted_idempotent — disclaimer inserted on procedure mention +
      idempotent (regex check disclaimer absent before insert; second pass
      MUST NOT duplicate).
  Audit log: disclaimer_inserted (severity info) — best-effort, no break turn.

Covers (02-design § 17.3 spec):
  - Trigger patterns: response touches procedure / medication / condition
  - Action: INSERT disclaimer suffix
      "Esto no reemplaza consulta médica profesional"
  - Idempotency: if response already contains disclaimer text → NO duplicate
  - Severity: info (passive insertion)
  - Runtime layer: output decorator (post-LLM, pre-channel-send)

These are UNIT tests — guardrail check is pure (no LLM, no DB). Audit log is
mocked via in-memory fake. Best-effort observability invariant verified
(audit_log raising MUST NOT break decorator).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

# ── Imports under test (deferred until impl exists; module-level OK because
# T-guards-3 lands the impl together with this file) ────────────────────────
from src.modules.vitalia.agentic.guardrails.medical_disclaimer_required import (
    DISCLAIMER_TEXT,
    MEDICAL_TRIGGER_PATTERNS,
    apply_medical_disclaimer,
    medical_disclaimer_required_check,
    response_already_has_disclaimer,
    response_mentions_medical_topic,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


_TENANT_ID = uuid.uuid4()


class _FakeAuditLog:
    """In-memory stand-in for the medical audit_log (best-effort writes)."""

    def __init__(self, *, raise_on_log: bool = False) -> None:
        self._raise_on_log = raise_on_log
        self.entries: list[dict[str, Any]] = []

    async def log(
        self,
        *,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID | None = None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if self._raise_on_log:
            raise RuntimeError("audit_log unavailable — fake failure")
        self.entries.append(
            {
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "event_type": event_type,
                "payload": payload,
            }
        )


@pytest.fixture
def audit_log() -> _FakeAuditLog:
    return _FakeAuditLog()


@pytest.fixture
def audit_log_failing() -> _FakeAuditLog:
    return _FakeAuditLog(raise_on_log=True)


# ── A1 — Disclaimer constant present + spec-verbatim ────────────────────────


def test_disclaimer_constant_matches_spec() -> None:
    """A1: DISCLAIMER_TEXT MUST contain spec-mandated phrase verbatim.

    Per ticket description: 'Esto no reemplaza consulta médica profesional'
    — exact text required for grader rubric A5 (vertical-medical-fidelity).
    """
    assert "Esto no reemplaza consulta médica profesional" in DISCLAIMER_TEXT


def test_medical_trigger_patterns_non_empty() -> None:
    """A1: MEDICAL_TRIGGER_PATTERNS catalog covers procedure / medication / condition."""
    assert isinstance(MEDICAL_TRIGGER_PATTERNS, tuple)
    assert len(MEDICAL_TRIGGER_PATTERNS) > 0
    # Spec § 17.3 trigger patterns — implante / cirugía / terapia / medicación / dosis
    catalog_lower = " ".join(p.pattern for p in MEDICAL_TRIGGER_PATTERNS).lower()
    for keyword in ("implante", "cirug", "terap", "medic", "dosis", "procedimiento"):
        assert keyword in catalog_lower, (
            f"Missing medical trigger keyword '{keyword}' in MEDICAL_TRIGGER_PATTERNS — "
            f"spec § 17.3 requires procedure/medication/condition coverage."
        )


# ── A1 — Trigger detection (response_mentions_medical_topic) ───────────────


@pytest.mark.parametrize(
    "response_text",
    [
        "El implante dental se coloca en una sesión.",
        "Vamos a coordinar tu cirugía con el doctor.",
        "Esta terapia psicológica suele durar 8 semanas.",
        "Tu medicación actual debería continuarse según indicación del psiquiatra.",
        "Aumentar la dosis sin control puede ser peligroso.",
        "El procedimiento es ambulatorio.",
    ],
)
def test_detects_medical_topic(response_text: str) -> None:
    """A1: response touching procedure/medication/condition → trigger fires."""
    assert response_mentions_medical_topic(response_text) is True


@pytest.mark.parametrize(
    "response_text",
    [
        "Hola, ¿en qué puedo ayudarte?",
        "Te confirmo el horario de la cita.",
        "El consultorio queda en Av. Corrientes 1234.",
        "Aurora está abierta de lunes a viernes.",
    ],
)
def test_does_not_trigger_on_benign_text(response_text: str) -> None:
    """A1: greeting / scheduling / address → NO disclaimer trigger."""
    assert response_mentions_medical_topic(response_text) is False


# ── A1 — Idempotency (response_already_has_disclaimer) ─────────────────────


def test_idempotency_check_recognizes_full_disclaimer() -> None:
    """A1: response containing DISCLAIMER_TEXT verbatim → already has disclaimer."""
    response = f"El implante es ambulatorio. {DISCLAIMER_TEXT}"
    assert response_already_has_disclaimer(response) is True


def test_idempotency_check_recognizes_partial_match() -> None:
    """A1: response containing the spec-mandated phrase → already has disclaimer.

    Defensive: accepts variations that include the canonical phrase substring
    (e.g. response composed by LLM that already inserted it without the suffix
    formatting).
    """
    response = "Esto no reemplaza consulta médica profesional con tu doctor."
    assert response_already_has_disclaimer(response) is True


def test_idempotency_check_misses_when_disclaimer_absent() -> None:
    """A1: response without disclaimer phrase → idempotency check returns False."""
    response = "El implante es ambulatorio y dura 1 hora."
    assert response_already_has_disclaimer(response) is False


# ── A1 — Apply disclaimer (idempotent) ─────────────────────────────────────


def test_apply_inserts_when_missing() -> None:
    """A1: medical response without disclaimer → disclaimer appended."""
    response = "El implante dental se coloca en una sesión."
    result = apply_medical_disclaimer(response)
    assert DISCLAIMER_TEXT in result
    assert result.startswith(response), "original response MUST be preserved verbatim"
    assert result.endswith(DISCLAIMER_TEXT), "disclaimer MUST be suffix"


def test_apply_idempotent_no_double_insertion() -> None:
    """A1 (CRITICAL idempotency): second pass does NOT duplicate disclaimer.

    Acceptance criterion verbatim: "if disclaimer already present → NO
    duplicate insertion".
    """
    response = "El implante dental se coloca en una sesión."
    once = apply_medical_disclaimer(response)
    twice = apply_medical_disclaimer(once)
    # Hard invariant — disclaimer text MUST appear exactly once
    assert twice.count(DISCLAIMER_TEXT) == 1, (
        f"Idempotency violated — disclaimer present {twice.count(DISCLAIMER_TEXT)}x "
        f"after second apply pass. Spec § 17.3 requires NO duplicate insertion."
    )
    # And the second pass MUST be a no-op (string equality)
    assert twice == once


def test_apply_skips_on_benign_response() -> None:
    """A1: benign response (no medical trigger) → no disclaimer inserted.

    Disclaimer is reserved for responses that touch
    procedure/medication/condition. Inserting on greetings would dilute its
    safety signal.
    """
    response = "Hola, ¿cómo puedo ayudarte hoy?"
    result = apply_medical_disclaimer(response)
    assert DISCLAIMER_TEXT not in result
    assert result == response


def test_apply_idempotent_when_disclaimer_already_inline() -> None:
    """A1: LLM response already containing disclaimer mid-text → no duplicate."""
    response = "El implante es ambulatorio. Esto no reemplaza consulta médica profesional con tu odontólogo."
    result = apply_medical_disclaimer(response)
    # Canonical phrase appears once (already present in original)
    assert result.count("Esto no reemplaza consulta médica profesional") == 1
    assert result == response, "no append when canonical phrase already present"


# ── A1 — Combined check + audit_log integration ────────────────────────────


@pytest.mark.asyncio
async def test_check_records_audit_log_when_inserted(audit_log: _FakeAuditLog) -> None:
    """A1: when disclaimer inserted → audit_log records `disclaimer_inserted` (severity info).

    Audit log is best-effort but MUST be invoked when insertion happens.
    """
    response = "Tu medicación actual sigue según indicación del psiquiatra."
    result = await medical_disclaimer_required_check(
        response=response,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    assert DISCLAIMER_TEXT in result
    assert len(audit_log.entries) == 1
    entry = audit_log.entries[0]
    assert entry["event_type"] == "disclaimer_inserted"
    assert entry["tenant_id"] == _TENANT_ID
    assert entry["payload"]["severity"] == "info"


@pytest.mark.asyncio
async def test_check_does_not_record_when_already_present(
    audit_log: _FakeAuditLog,
) -> None:
    """A1: idempotent skip → no audit entry written (avoid noise)."""
    response = "El implante es ambulatorio. Esto no reemplaza consulta médica profesional con tu odontólogo."
    result = await medical_disclaimer_required_check(
        response=response,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    assert result == response, "no-op path returns original verbatim"
    assert audit_log.entries == [], "Idempotent path MUST NOT log — only fresh insertions are auditable events."


@pytest.mark.asyncio
async def test_check_does_not_record_when_benign(audit_log: _FakeAuditLog) -> None:
    """A1: benign response (no medical topic) → no audit entry."""
    response = "Hola, ¿cómo puedo ayudarte hoy?"
    result = await medical_disclaimer_required_check(
        response=response,
        tenant_id=_TENANT_ID,
        audit_log=audit_log,
    )
    assert result == response
    assert audit_log.entries == []


# ── A1 — Best-effort observability (R23 + tessl__graceful-degradation) ─────


@pytest.mark.asyncio
async def test_check_does_not_break_when_audit_log_raises(
    audit_log_failing: _FakeAuditLog,
) -> None:
    """A1: audit_log raising MUST NOT break the decorator (R23 best-effort).

    Per .claude/rules/copilot-observability.md + tessl__graceful-degradation:
    > "every external call needs a timeout" + "every timeout needs a fallback"
    > Audit log is observability — NEVER break the production path on failure.
    """
    response = "El implante dental se coloca en una sesión."
    # MUST NOT raise — disclaimer is still appended even though audit_log failed
    result = await medical_disclaimer_required_check(
        response=response,
        tenant_id=_TENANT_ID,
        audit_log=audit_log_failing,
    )
    assert DISCLAIMER_TEXT in result, (
        "Disclaimer insertion is the production-critical action — MUST succeed even if audit_log fails."
    )


@pytest.mark.asyncio
async def test_check_works_without_audit_log() -> None:
    """A1: audit_log optional — decorator works when omitted (graceful degradation)."""
    response = "Tu medicación actual sigue según indicación del psiquiatra."
    result = await medical_disclaimer_required_check(
        response=response,
        tenant_id=_TENANT_ID,
        audit_log=None,
    )
    assert DISCLAIMER_TEXT in result


# ── A1 — Idempotent end-to-end (regression bar for ticket spec) ────────────


@pytest.mark.asyncio
async def test_inserted_idempotent(audit_log: _FakeAuditLog) -> None:
    """A1 named verifier: ticket spec test_inserted_idempotent.

    Per 06-tickets.yaml::T-guards-3 acceptance:
      verifier: pytest path
      test_medical_disclaimer_required.py::test_inserted_idempotent

    Combines insertion + idempotency in one named test — first pass inserts
    + audits, second pass is a no-op + does not re-audit.
    """
    response = "Tu medicación actual sigue según indicación del psiquiatra."

    # First pass — fresh insertion
    once = await medical_disclaimer_required_check(response=response, tenant_id=_TENANT_ID, audit_log=audit_log)
    assert DISCLAIMER_TEXT in once
    assert len(audit_log.entries) == 1

    # Second pass — already present, no-op
    twice = await medical_disclaimer_required_check(response=once, tenant_id=_TENANT_ID, audit_log=audit_log)
    assert twice == once
    assert twice.count(DISCLAIMER_TEXT) == 1
    # No new audit entry on idempotent skip
    assert len(audit_log.entries) == 1
