"""Tests for send_proactive_reengagement tool — TDD RED (T-9).

Story vitalia-slice-1-fidelizacion T-9 (R23 Opus production_code=true).

Per 03-arch-agentic.md § 2.1 + 06-tickets.yaml::T-9::gherkin_coverage:
- SC-01 happy: tool delegates to ProactiveOutboundService + Adrián WA template send
- SC-02 negative: tool refuses MARKETING send without opt_in
- SC-04 adversarial: throttle exceeded + opt_out + compliance block + unexpected exception
- input schema: tenant_id + clinic_id mandatory (HIPAA-lite dual filter)
- pattern enum: matches ReEngagementPattern values
- PII: patient_name + patient_phone NEVER leaked in tool surface return string
- resolver: DI hook contract (RuntimeError handled gracefully)

Anti-duplication §0:
- NO mirror of engine observability (engine SalesAgentObservabilityContext shipped)
- Tool delegates to ProactiveOutboundService (T-5 shipped) — does NOT
  call adapters/repos/outbox directly.

Tenant + clinic dual filter cardinal (hipaa-lite.md): tool input schema
requires tenant_id + clinic_id; service-level dual filter applied.

downstream-regression-na: brand-local vitalia sales_agent tool tests
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ProactiveReminderResponse,
)

# ── Fixtures (deterministic UUIDs for assertions) ──────────────────────────

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
PATIENT_ID = uuid4()
EVENT_ID = uuid4()
USER_ID = uuid4()


def _reset_resolver() -> None:
    """Clear the module-level service resolver between tests."""
    from src.modules.vitalia.sales_agent.tools import send_proactive_reengagement as mod

    mod._service_resolver = None  # noqa: SLF001 — test reset hook


def _make_sent_response(*, event_id=None) -> ProactiveReminderResponse:
    """Build a ProactiveReminderResponse for the happy 'sent' status."""
    return ProactiveReminderResponse(
        event_id=event_id or EVENT_ID,
        patient_id=PATIENT_ID,
        status="sent",
        sent_at=datetime.now(UTC),
        throttled=False,
        blocked_reason=None,
    )


def _make_blocked_response(*, blocked_reason: str) -> ProactiveReminderResponse:
    """Build a ProactiveReminderResponse for blocked outcomes (SC-02)."""
    return ProactiveReminderResponse(
        event_id=uuid4(),
        patient_id=PATIENT_ID,
        status="blocked",
        sent_at=None,
        throttled=False,
        blocked_reason=blocked_reason,
    )


def _make_throttled_response() -> ProactiveReminderResponse:
    """Build a ProactiveReminderResponse for throttled outcome (SC-04 adversarial)."""
    return ProactiveReminderResponse(
        event_id=uuid4(),
        patient_id=PATIENT_ID,
        status="throttled",
        sent_at=None,
        throttled=True,
        blocked_reason=None,
    )


# ──────────────────────────────────────────────────────────────────────────
# SC-01 Happy — multi_session send succeeds + event emitted
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delegates_to_service_and_emits_event() -> None:
    """SC-01: tool delegates to ProactiveOutboundService and reports event_id.

    Validates the tool fires the service.send_proactive_reminder kwargs flow,
    receives the sent response, and returns a Spanish-neutro summary suitable
    for LLM chain-of-thought continuation. NEVER leaks patient_name in return.
    """
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
        set_proactive_outbound_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    response = _make_sent_response()
    service.send_proactive_reminder = AsyncMock(return_value=response)
    set_proactive_outbound_service_resolver(lambda: service)

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "M. Rodríguez",
            "pattern": "multi_session",
            "template_id": "recordatorio_proxima_sesion",
            "marketing_opt_in": True,
            "opt_out": False,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "cron multi_session_gap_sweep",
            "triggered_by_user_id": USER_ID,
        }
    )

    # Tool returns Spanish neutro summary for LLM CoT
    assert "multi_session" in out or "recordatorio_proxima_sesion" in out
    assert "enviado" in out.lower()

    # PII MUST NOT leak in tool surface return string (HIPAA-lite)
    assert "M. Rodríguez" not in out
    assert "+5491145678900" not in out

    # Service called once with the expected dual filter + kwargs
    service.send_proactive_reminder.assert_awaited_once()
    call_kwargs = service.send_proactive_reminder.await_args.kwargs
    assert call_kwargs["tenant_id"] == TENANT_ID
    assert call_kwargs["clinic_id"] == CLINIC_ID
    assert call_kwargs["patient_id"] == PATIENT_ID
    assert call_kwargs["template_id"] == "recordatorio_proxima_sesion"
    assert call_kwargs["pattern"].value == "multi_session"
    assert call_kwargs["marketing_opt_in"] is True
    assert call_kwargs["opt_out"] is False
    assert call_kwargs["user_id"] == USER_ID
    # Idempotency key combines event_id (per service contract)
    assert str(EVENT_ID) in call_kwargs["idempotency_key"]


# ──────────────────────────────────────────────────────────────────────────
# SC-02 Negative — MARKETING template without opt_in → blocked
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refuses_marketing_no_optin() -> None:
    """SC-02: when marketing_opt_in=False, the service reports blocked outcome,
    and the tool surfaces it as a Spanish neutro 'no enviado' summary.

    The tool itself does NOT enforce opt-in (service layer does). The tool's
    responsibility is to faithfully report the blocked status back to the LLM.
    """
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
        set_proactive_outbound_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.send_proactive_reminder = AsyncMock(
        return_value=_make_blocked_response(blocked_reason="marketing_opt_in_required")
    )
    set_proactive_outbound_service_resolver(lambda: service)

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "M. Rodríguez",
            "pattern": "absence",
            "template_id": "re_engagement_ausencia",
            "marketing_opt_in": False,
            "opt_out": False,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "cron absence_sweep",
            "triggered_by_user_id": USER_ID,
        }
    )

    # Spanish neutro summary indicates the message was NOT sent
    out_lower = out.lower()
    assert "no enviado" in out_lower or "bloqueado" in out_lower
    assert "marketing_opt_in_required" in out or "opt-in" in out_lower or "consentimiento" in out_lower

    # PII NOT leaked
    assert "M. Rodríguez" not in out
    assert "+5491145678900" not in out

    # Service still invoked (the service is the SSoT for opt-in enforcement)
    service.send_proactive_reminder.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────────────
# SC-04 adversarial — opt_out cascade blocked
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refuses_opted_out_patient() -> None:
    """SC-04 adversarial: opted-out patient → service reports blocked → tool 'no enviado'."""
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
        set_proactive_outbound_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.send_proactive_reminder = AsyncMock(return_value=_make_blocked_response(blocked_reason="patient_opted_out"))
    set_proactive_outbound_service_resolver(lambda: service)

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "M. Rodríguez",
            "pattern": "follow_up",
            "template_id": "recordatorio_control_doctor",
            "marketing_opt_in": True,
            "opt_out": True,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "manual",
            "triggered_by_user_id": USER_ID,
        }
    )

    out_lower = out.lower()
    assert "no enviado" in out_lower or "bloqueado" in out_lower
    assert "opt" in out_lower or "consent" in out_lower or "baja" in out_lower


# ──────────────────────────────────────────────────────────────────────────
# SC-04 adversarial — throttle exceeded
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_throttle_exceeded_reports_throttled() -> None:
    """SC-04 adversarial: throttle window active → service reports throttled → tool 'throttle'."""
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
        set_proactive_outbound_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.send_proactive_reminder = AsyncMock(return_value=_make_throttled_response())
    set_proactive_outbound_service_resolver(lambda: service)

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "M. Rodríguez",
            "pattern": "maintenance",
            "template_id": "invitacion_mantenimiento",
            "marketing_opt_in": True,
            "opt_out": False,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "cron maintenance_due_sweep",
            "triggered_by_user_id": USER_ID,
        }
    )

    out_lower = out.lower()
    assert "throttle" in out_lower or "ventana" in out_lower or "espera" in out_lower


# ──────────────────────────────────────────────────────────────────────────
# Adversarial — unexpected exception (graceful degradation)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unexpected_exception_graceful() -> None:
    """Adversarial: service raises generic exception → tool never re-raises (graceful-degradation).

    PII MUST NOT leak in the user-facing return (audit log captures details,
    tool surface stays sanitized).
    """
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
        set_proactive_outbound_service_resolver,
    )

    _reset_resolver()

    service = AsyncMock()
    service.send_proactive_reminder = AsyncMock(side_effect=RuntimeError("WhatsApp Business API timeout"))
    set_proactive_outbound_service_resolver(lambda: service)

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "Paciente Juan Pérez",
            "pattern": "nps",
            "template_id": "nps_post_tratamiento",
            "marketing_opt_in": True,
            "opt_out": False,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "cron nps_post_treatment_sweep",
            "triggered_by_user_id": USER_ID,
        }
    )

    # Tool returned (did NOT raise) — graceful degradation
    assert isinstance(out, str)
    assert len(out) > 0

    # PII MUST NOT leak in the tool surface return string
    assert "Juan Pérez" not in out
    assert "+5491145678900" not in out

    # Spanish neutro fallback (LatAm)
    out_lower = out.lower()
    assert "problema" in out_lower or "técnico" in out_lower or "revisión" in out_lower


# ──────────────────────────────────────────────────────────────────────────
# Resolver guard — DI hook contract
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolver_not_configured_graceful() -> None:
    """Bootstrap contract: invoking the tool before set_proactive_outbound_service_resolver()
    runs returns Spanish fallback string (graceful-degradation envelope).
    """
    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
    )

    _reset_resolver()

    out = await send_proactive_reengagement.ainvoke(
        {
            "tenant_id": TENANT_ID,
            "clinic_id": CLINIC_ID,
            "patient_id": PATIENT_ID,
            "patient_phone": "+5491145678900",
            "patient_name": "M. Rodríguez",
            "pattern": "multi_session",
            "template_id": "recordatorio_proxima_sesion",
            "marketing_opt_in": True,
            "opt_out": False,
            "re_engagement_event_id": EVENT_ID,
            "trigger_source": "test bootstrap contract",
            "triggered_by_user_id": USER_ID,
        }
    )
    assert isinstance(out, str)
    assert len(out) > 0


# ──────────────────────────────────────────────────────────────────────────
# Input schema — tenant_id + clinic_id mandatory (HIPAA-lite cardinal)
# ──────────────────────────────────────────────────────────────────────────


def test_input_schema_requires_tenant_and_clinic() -> None:
    """Pydantic v2 input schema MUST require tenant_id + clinic_id per HIPAA-lite dual filter."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        SendProactiveReEngagementInput,
    )

    # Missing tenant_id
    with pytest.raises(ValidationError) as exc_info:
        SendProactiveReEngagementInput(
            clinic_id=CLINIC_ID,
            patient_id=PATIENT_ID,
            patient_phone="+5491145678900",
            patient_name="M. Rodríguez",
            pattern="multi_session",
            template_id="recordatorio_proxima_sesion",
            marketing_opt_in=True,
            opt_out=False,
            re_engagement_event_id=EVENT_ID,
            trigger_source="cron multi_session_gap_sweep",
            triggered_by_user_id=USER_ID,
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("tenant_id",) for e in errors)

    # Missing clinic_id
    with pytest.raises(ValidationError) as exc_info:
        SendProactiveReEngagementInput(
            tenant_id=TENANT_ID,
            patient_id=PATIENT_ID,
            patient_phone="+5491145678900",
            patient_name="M. Rodríguez",
            pattern="multi_session",
            template_id="recordatorio_proxima_sesion",
            marketing_opt_in=True,
            opt_out=False,
            re_engagement_event_id=EVENT_ID,
            trigger_source="cron multi_session_gap_sweep",
            triggered_by_user_id=USER_ID,
        )
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("clinic_id",) for e in errors)


def test_input_schema_pattern_enum() -> None:
    """Pattern field MUST accept exactly the 5 ReEngagementPattern values."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        SendProactiveReEngagementInput,
    )

    # All 5 valid patterns
    for valid in ["multi_session", "follow_up", "maintenance", "absence", "nps"]:
        SendProactiveReEngagementInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            patient_id=PATIENT_ID,
            patient_phone="+5491145678900",
            patient_name="M. Rodríguez",
            pattern=valid,
            template_id="recordatorio_proxima_sesion",
            marketing_opt_in=True,
            opt_out=False,
            re_engagement_event_id=EVENT_ID,
            trigger_source="cron",
            triggered_by_user_id=USER_ID,
        )

    # Invalid pattern rejected
    with pytest.raises(ValidationError):
        SendProactiveReEngagementInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            patient_id=PATIENT_ID,
            patient_phone="+5491145678900",
            patient_name="M. Rodríguez",
            pattern="invalid_pattern_value",
            template_id="recordatorio_proxima_sesion",
            marketing_opt_in=True,
            opt_out=False,
            re_engagement_event_id=EVENT_ID,
            trigger_source="cron",
            triggered_by_user_id=USER_ID,
        )


def test_input_schema_extra_forbid() -> None:
    """Pydantic v2 ConfigDict(extra='forbid') — reject unknown fields (anti-injection)."""
    from pydantic import ValidationError

    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        SendProactiveReEngagementInput,
    )

    with pytest.raises(ValidationError):
        SendProactiveReEngagementInput(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            patient_id=PATIENT_ID,
            patient_phone="+5491145678900",
            patient_name="M. Rodríguez",
            pattern="multi_session",
            template_id="recordatorio_proxima_sesion",
            marketing_opt_in=True,
            opt_out=False,
            re_engagement_event_id=EVENT_ID,
            trigger_source="cron",
            triggered_by_user_id=USER_ID,
            evil_field="prompt injection payload",  # type: ignore[call-arg]
        )


# ──────────────────────────────────────────────────────────────────────────
# Tool surface — LangChain @tool decorator + name + async
# ──────────────────────────────────────────────────────────────────────────


def test_tool_surface_metadata() -> None:
    """Tool is registered with name 'send_proactive_reengagement' and is an async coroutine."""
    import inspect

    from src.modules.vitalia.sales_agent.tools.send_proactive_reengagement import (
        send_proactive_reengagement,
    )

    # LangChain BaseTool subclass
    assert hasattr(send_proactive_reengagement, "name")
    assert send_proactive_reengagement.name == "send_proactive_reengagement"
    # args_schema reference points to Pydantic v2 input model
    assert hasattr(send_proactive_reengagement, "args_schema")
    # Tool function is async
    assert inspect.iscoroutinefunction(send_proactive_reengagement.coroutine) or hasattr(
        send_proactive_reengagement, "ainvoke"
    )


# ──────────────────────────────────────────────────────────────────────────
# Public exports — ensure module exposes the resolver setter + input class
# ──────────────────────────────────────────────────────────────────────────


def test_module_public_exports() -> None:
    """Module __all__ exposes tool + Input schema + resolver setter."""
    from src.modules.vitalia.sales_agent.tools import send_proactive_reengagement as mod

    public = set(mod.__all__)
    assert "send_proactive_reengagement" in public
    assert "SendProactiveReEngagementInput" in public
    assert "set_proactive_outbound_service_resolver" in public
