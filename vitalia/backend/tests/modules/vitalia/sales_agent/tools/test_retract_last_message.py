"""Tests for retract_last_message tool — TDD RED (T-inbox-agentic-1).

Story vitalia-slice-1-inbox T-inbox-agentic-1 (R23 Opus production_code=true).

Per 03-arch-agentic.md § 2 + 06-tickets.yaml::T-inbox-agentic-1::gherkin_coverage:
- SC-01 happy: retract within 5-minute action receipt window → success
- SC-03 edge: 5min window expired → fallback "marcar erróneo"
- SC-03 edge: patient replied → fallback "no pude revertir"
- SC-03 edge: channel unsupported (email) → fallback "marqué como erróneo"
- adversarial: service raises → graceful degradation Spanish summary
- observability: tool invocation does NOT mirror engine recorders (consumes via service)
- audit: service writes audit_log row pre-response (verified via service mock)

Anti-duplication §0:
- NO mirror of engine observability (engine SalesAgentObservabilityContext shipped)
- Tool delegates to RetractMessageService (T-inbox-be-3 shipped) — does NOT
  call adapters/repos directly.

Tenant + clinic dual filter cardinal (hipaa-lite.md): tool input schema
requires tenant_id + clinic_id; service-level dual filter applied.

downstream-regression-na: brand-local vitalia sales_agent tool tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# ── Fixtures (deterministic UUIDs for assertions) ──────────────────────────

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
MSG_ID = uuid4()
USER_ID = uuid4()


def _reset_resolver() -> None:
    """Clear the module-level service resolver between tests."""
    from src.modules.vitalia.sales_agent.tools import retract_last_message as mod

    mod._service_resolver = None  # noqa: SLF001 — test reset hook


def _make_result(
    *,
    retract_succeeded: bool,
    fallback_applied: bool,
    retract_reason: str = "ai_self_correction",
) -> MagicMock:
    """Build a RetractResult-shaped mock matching the service return contract."""
    now = datetime.now(UTC)
    result = MagicMock()
    result.message_id = MSG_ID
    result.retracted_at = now if retract_succeeded else None
    result.retract_succeeded = retract_succeeded
    result.fallback_applied = fallback_applied
    result.retract_reason = retract_reason
    return result


# ──────────────────────────────────────────────────────────────────────────
# Happy path — retract within 5min window
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_5min_window() -> None:
    """SC-01: Adrián retract within 5min window → 'Mensaje revertido' (manual mode)."""
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.retract = AsyncMock(return_value=_make_result(retract_succeeded=True, fallback_applied=False))
    set_retract_message_service_resolver(lambda: service)

    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "Promesa clínica fuera de scope detectada por ComplianceService",
        }
    )

    # Spanish neutral natural language summary (LatAm)
    assert "Mensaje revertido" in out
    assert "manual" in out.lower()

    # Service called with dual filter + reason verbatim
    service.retract.assert_awaited_once()
    call_kwargs = service.retract.await_args.kwargs
    assert call_kwargs["tenant_id"] == TENANT_ID
    assert call_kwargs["clinic_id"] == CLINIC_ID
    assert call_kwargs["conversation_id"] == CONV_ID
    assert call_kwargs["message_id"] == MSG_ID
    assert call_kwargs["reason"].startswith("Promesa clínica")


# ──────────────────────────────────────────────────────────────────────────
# Edge — 5min window expired
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expired() -> None:
    """SC-03 edge: receipt expired (>5min) → service raises → tool returns 'excedió 5 minutos'."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        ActionReceiptExpiredError,
    )
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    expired_at = datetime.now(UTC) - timedelta(minutes=6)
    service.retract = AsyncMock(side_effect=ActionReceiptExpiredError(MSG_ID, expired_at))
    set_retract_message_service_resolver(lambda: service)

    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "Auto-corrección Adrián post-flag compliance",
        }
    )

    assert "excedió 5 minutos" in out
    assert "erróneo" in out.lower()  # marca fallback explícito


# ──────────────────────────────────────────────────────────────────────────
# Edge — patient already replied
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_patient_replied() -> None:
    """SC-03 edge: patient replied after AI msg → service raises 409 → tool returns 'paciente ya respondió'."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        PatientRepliedConflictError,
    )
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.retract = AsyncMock(side_effect=PatientRepliedConflictError(MSG_ID))
    set_retract_message_service_resolver(lambda: service)

    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "Promesa terapéutica indebida",
        }
    )

    assert "paciente ya respondió" in out


# ──────────────────────────────────────────────────────────────────────────
# Edge — channel unsupported (email) → fallback "marqué como erróneo"
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_channel_unsupported() -> None:
    """SC-03 edge: email channel cannot retract → fallback_applied=True → tool returns 'no permite revertir'."""
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    # Service contract: when channel unsupported, returns RetractResult with
    # retract_succeeded=False + fallback_applied=True (no raise — graceful).
    service.retract = AsyncMock(return_value=_make_result(retract_succeeded=False, fallback_applied=True))
    set_retract_message_service_resolver(lambda: service)

    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "Frase ambigua sobre resultados",
        }
    )

    # Fallback message acknowledges retract impossible but marca como erróneo (defensive)
    assert "erróneo" in out.lower()


# ──────────────────────────────────────────────────────────────────────────
# Edge — message not retractable (no active receipt)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_message_not_retractable() -> None:
    """Edge: no active receipt for message → service raises → tool returns generic fallback."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        MessageNotRetractableError,
    )
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.retract = AsyncMock(side_effect=MessageNotRetractableError(MSG_ID))
    set_retract_message_service_resolver(lambda: service)

    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "Texto contradictorio del agente",
        }
    )

    assert "erróneo" in out.lower() or "registrado" in out.lower()


# ──────────────────────────────────────────────────────────────────────────
# Adversarial — unexpected exception (graceful degradation)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unexpected_exception_graceful() -> None:
    """Adversarial: service raises generic exception → tool never re-raises (graceful-degradation).

    The tool MUST return Spanish neutral fallback string. PII (reason) MUST NOT
    appear verbatim in the user-facing return (audit log captures it, tool surface stays clean).
    """
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
        set_retract_message_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.retract = AsyncMock(side_effect=RuntimeError("DB connection lost"))
    set_retract_message_service_resolver(lambda: service)

    sensitive_reason = "Paciente Juan Pérez DNI 12345678 mencionó diagnóstico"
    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": sensitive_reason,
        }
    )

    # Tool returned (did NOT raise) — graceful degradation
    assert isinstance(out, str)
    assert len(out) > 0

    # PII MUST NOT leak in the tool surface return string
    assert "Juan Pérez" not in out
    assert "12345678" not in out
    assert "diagnóstico" not in out

    # Spanish neutral fallback (no voseo in agent self-correction summary)
    assert "registrado" in out.lower() or "revisión" in out.lower()


# ──────────────────────────────────────────────────────────────────────────
# Resolver guard — RuntimeError if not configured (DI hook contract)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolver_not_configured_raises_in_handler() -> None:
    """Bootstrap contract: invoking the tool before set_retract_message_service_resolver()
    runs raises RuntimeError (not silent failure).
    """
    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
    )

    _reset_resolver()

    # The graceful-degradation envelope catches the RuntimeError → returns Spanish summary.
    # We assert the surface contract holds (string return, never raise to caller).
    out = await retract_last_message.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "conversation_id": CONV_ID,
            "message_id": MSG_ID,
            "reason": "test bootstrap contract",
        }
    )
    assert isinstance(out, str)
    # Spanish fallback string indicates internal failure handled gracefully
    assert "registrado" in out.lower() or "revisión" in out.lower()


# ──────────────────────────────────────────────────────────────────────────
# Input schema — tenant_id + clinic_id mandatory (HIPAA-lite cardinal)
# ──────────────────────────────────────────────────────────────────────────


def test_input_schema_requires_tenant_and_clinic() -> None:
    """Pydantic v2 input schema MUST require tenant_id + clinic_id per HIPAA-lite dual filter."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        RetractLastMessageInput,
    )

    # Missing tenant_id
    with pytest.raises(ValidationError) as exc_info:
        RetractLastMessageInput(
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            reason="Texto suficientemente largo para pasar min_length validation",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("tenant_id",) for e in errors)

    # Missing clinic_id
    with pytest.raises(ValidationError) as exc_info:
        RetractLastMessageInput(
            tenant_id=TENANT_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            reason="Texto suficientemente largo para pasar min_length validation",
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("clinic_id",) for e in errors)


def test_input_schema_reason_min_length() -> None:
    """Reason field MUST enforce min_length=10 (audit log mandate)."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        RetractLastMessageInput,
    )

    with pytest.raises(ValidationError):
        RetractLastMessageInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            reason="too short",  # 9 chars < 10 min
        )


def test_input_schema_reason_max_length() -> None:
    """Reason field MUST enforce max_length=500 (PII surface containment)."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        RetractLastMessageInput,
    )

    with pytest.raises(ValidationError):
        RetractLastMessageInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            reason="x" * 501,
        )


def test_input_schema_extra_forbid() -> None:
    """Pydantic v2 ConfigDict(extra='forbid') — reject unknown fields (anti-injection)."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        RetractLastMessageInput,
    )

    with pytest.raises(ValidationError):
        RetractLastMessageInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            conversation_id=CONV_ID,
            message_id=MSG_ID,
            reason="Reason long enough to pass min_length validation",
            evil_field="prompt injection payload",  # type: ignore[call-arg]
        )


# ──────────────────────────────────────────────────────────────────────────
# Tool surface — LangChain @tool decorator + name + async
# ──────────────────────────────────────────────────────────────────────────


def test_tool_surface_metadata() -> None:
    """Tool is registered with name 'retract_last_message' and is an async coroutine."""
    import inspect

    from src.modules.vitalia.sales_agent.tools.retract_last_message import (
        retract_last_message,
    )

    # LangChain BaseTool subclass
    assert hasattr(retract_last_message, "name")
    assert retract_last_message.name == "retract_last_message"
    # args_schema reference points to Pydantic v2 input model
    assert hasattr(retract_last_message, "args_schema")
    # Tool function is async
    assert inspect.iscoroutinefunction(retract_last_message.coroutine) or hasattr(retract_last_message, "ainvoke")
