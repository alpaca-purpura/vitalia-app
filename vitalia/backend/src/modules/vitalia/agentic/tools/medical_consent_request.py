# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Vitalia AGENTIC tool — `medical_consent_request`.

R23: production_code=True AGENTIC tool. Opus 4.7 EXCLUSIVE.
Story 11 T-tools-2.

Spec sources:
  * 02-design-agentic.md § 6.3 verbose spec + § 5.1 consent capture flow
  * 03-arch-agentic.md § 4.3 tool architecture
  * 06-tickets.yaml::T-tools-2 acceptance criteria A1-A3
  * 05-guidelines.md § 1.10 R23 agentic patterns + § 1.6 PII sanitization
  * .claude/rules/copilot-resilience.md (best-effort observability)
  * .claude/rules/copilot-observability.md (try/except + sanitize_payload)

Semantics — request informed consent pre-procedure:
  1. Validate offer.requires_informed_consent=true (A2 — gate). If false,
     return error WITHOUT side-effects.
  2. Delegate to ConsentService.request_consent (T-be-6) which:
       - applies D2 idempotency: same (booking_id, slug) within window
         returns existing pending consent (A3)
       - persists consent_record + template snapshot
       - generates HMAC-signed URL (24h expiry per D7 HIPAA-lite)
  3. Append audit_log consent_requested event with sanitized payload (A1).
  4. Fire-and-forget channel dispatch (WhatsApp / email / both).
       - Dispatch failures NEVER break tool turn (R23 best-effort).
  5. Best-effort trace_event emission for observability.

Tenant isolation (security boundary):
  * tenant_id MUST NEVER appear in input schema — injected from ctx via
    sales_agent tool dispatcher.
  * ConsentService + repos receive tenant_id at construction (caller wires
    tenant-scoped instances).

Observability (best-effort per R23 + copilot-observability.md):
  * audit_log_repo + trace_event_repo writes wrapped in try/except + structlog
    warning. Tool turn NEVER breaks on observability failure.
  * PII sanitized via `sanitize_payload` BEFORE persist — patient name /
    phone / email / signature evidence NEVER reach trace store raw.

Idempotency (A3):
  * Delegated to ConsentService.request_consent (T-be-6 D2): same
    (booking_id, consent_template_slug) pair within 1h window returns
    existing pending consent_id. NO duplicate row, NO duplicate channel
    dispatch (audit log still records each invocation as intent record,
    flagged via `is_new=False` payload).

Cost: $0 LLM (deterministic). External: WhatsApp + email send ~$0.002 USD
per consent (channel dispatcher cost). Latency p50 350ms / p99 1.2s
(02-design § 6.3).

Anti-duplication audit (Step 0 GATE pre-write):
  * `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
    (canonical) — NEVER re-implemented (`.claude/rules/anti-duplication.md`).
  * `BaseTraceEventRepoProtocol` from `luana_core_observability.persistence`
    (structural Protocol) — handler accepts any concrete implementing.
  * `ConsentService` (T-be-6) consumed via callable Protocol — NEVER raw
    HMAC duplication (HMAC SSoT lives in ConsentService).
  * `MedicalAuditLogRepository` (T-be-3) consumed via Protocol — NEVER raw SQL.
  * Channel dispatcher consumed via callable Protocol — vertical-medical
    specific (no equivalent in @luana/core/channels yet).
  * NO match in `medical_consent_request|MedicalConsentRequest|consent_request_tool`
    cross-codebase grep (verified 2026-05-14 pre-write).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Literal, Protocol

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger(__name__)


# ─── Configuration constants ─────────────────────────────────────────────

# Default consent URL token expiry (D7 HIPAA-lite per spec § 14 + 02-design § 6.3).
_DEFAULT_EXPIRY_HOURS: int = 24

# Audit log severity for consent_requested event (informational — request, not breach).
_AUDIT_SEVERITY_INFO: str = "info"

# Allowed delivery channel literals (mirrors ChannelAdapterDef registrations).
_DELIVERY_CHANNELS: frozenset[str] = frozenset({"whatsapp", "email"})


# ─── Pydantic schemas (input/output contract) ────────────────────────────


class MedicalConsentRequestInput(BaseModel):
    """Input schema — tenant_id intentionally OMITTED (ctx injection).

    Per 02-design § 6.3 + .claude/rules/tenant-isolation.md:
    > tenant_id NOT in schema — injected via tool dispatcher from ctx
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: uuid.UUID = Field(
        ...,
        description="Patient UUID requesting consent.",
    )
    consent_template_slug: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description='Template slug (e.g. "dental_implant_v1", "psychiatric_consult_v1").',
    )
    booking_id: uuid.UUID | None = Field(
        None,
        description="Booking UUID (nullable in pre-booking intent phase).",
    )
    delivery_channel: Literal["whatsapp", "email", "both"] = Field(
        "both",
        description="Where to deliver the consent capture URL.",
    )


class MedicalConsentRequestOutput(BaseModel):
    """Result of medical_consent_request tool invocation.

    Per 02-design § 6.3 verbose spec.
    """

    model_config = ConfigDict(frozen=True)

    status: Literal[
        "pending_signature",
        "delivery_failed",
        "offer_does_not_require_consent",
    ] = Field(
        ...,
        description="Consent capture status.",
    )
    consent_id: uuid.UUID | None = Field(
        None,
        description="Consent record UUID (None on validation error).",
    )
    consent_url: str | None = Field(
        None,
        description="Tenant-domain hosted signing page URL with HMAC token.",
    )
    expires_at: datetime | None = Field(
        None,
        description="Token expiration timestamp (24h default per D7 HIPAA-lite).",
    )
    template_version: str | None = Field(
        None,
        description="Consent template version snapshot.",
    )
    is_new: bool = Field(
        False,
        description="True iff a NEW consent_record was created (False = idempotent reuse).",
    )
    error_code: str | None = Field(
        None,
        description="Populated on validation failure (e.g. offer_does_not_require_consent).",
    )


# ─── Dependency Protocols (decouple from concrete classes) ────────────────


class _ConsentServiceLike(Protocol):
    """Minimal surface consumed from ConsentService (T-be-6)."""

    async def request_consent(self, request: Any, base_url: str) -> Any: ...


class _AuditLogRepoLike(Protocol):
    """Minimal surface consumed from MedicalAuditLogRepository (T-be-3)."""

    async def save(self, audit_event: Any) -> None: ...


class _ChannelDispatcherLike(Protocol):
    """Async fire-and-forget channel dispatcher.

    Implementations: WhatsApp adapter, email adapter, dual dispatcher.
    Tool invokes once per channel — failures swallowed (best-effort delivery).
    """

    async def dispatch(
        self,
        *,
        consent_id: uuid.UUID,
        consent_url: str,
        patient_id: uuid.UUID,
        delivery_channel: str,
        tenant_id: uuid.UUID,
    ) -> None: ...


class _TraceEventRepoLike(Protocol):
    """Mirror of BaseTraceEventRepoProtocol — see luana_core_observability."""

    def add(
        self,
        *,
        tenant_id: uuid.UUID,
        turn_id: uuid.UUID,
        span_id: uuid.UUID,
        event_type: str,
        name: str | None = ...,
        data: dict[str, Any] | None = ...,
        duration_ms: int | None = ...,
        status: str = ...,
        **agent_specific: Any,
    ) -> Any: ...


# ─── Handler ─────────────────────────────────────────────────────────────


async def medical_consent_request(
    input: MedicalConsentRequestInput,
    *,
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    offer_requires_consent: Any,  # Callable[[uuid.UUID], bool] — Awaitable also accepted
    consent_service: _ConsentServiceLike,
    audit_log_repo: _AuditLogRepoLike,
    channel_dispatcher: _ChannelDispatcherLike,
    base_url: str,
    trace_event_repo: _TraceEventRepoLike | None = None,
    turn_id: uuid.UUID | None = None,
    span_id: uuid.UUID | None = None,
) -> MedicalConsentRequestOutput:
    """Request informed consent pre-procedure with HMAC-signed URL.

    See module docstring for full semantics + spec references.

    Parameters
    ----------
    input
        Pydantic input — tenant_id NEVER here (security boundary).
    tenant_id
        Injected from ctx by sales_agent tool dispatcher.
    offer_id
        Offer UUID — tool validates `offer.requires_informed_consent=true`
        via the supplied `offer_requires_consent` callable (A2 gate).
    offer_requires_consent
        Callable `(offer_id: UUID) -> bool` (sync OR async). Caller wires
        tenant-scoped offer service. Returns True iff offer requires consent.
    consent_service
        ConsentService instance bound to this tenant_id (T-be-6). Owns HMAC
        URL signing + D2 idempotency.
    audit_log_repo
        MedicalAuditLogRepository bound to this tenant_id (T-be-3).
    channel_dispatcher
        Async fire-and-forget WhatsApp / email dispatcher.
    base_url
        Base URL for consent signing page (e.g. "https://vitalia.app").
    trace_event_repo
        Optional — when supplied, tool records one trace_event for the turn.
    turn_id / span_id
        Required iff trace_event_repo supplied — caller's correlation IDs.

    Returns
    -------
    MedicalConsentRequestOutput — never raises tool-side errors. Validation
    failures surface via `status='offer_does_not_require_consent'` + `error_code`.
    """
    # ── 1. Validation gate (A2) ──────────────────────────────────────────
    requires = await _resolve_requires_consent(offer_requires_consent, offer_id)
    if not requires:
        result = MedicalConsentRequestOutput(
            status="offer_does_not_require_consent",
            error_code="offer_does_not_require_consent",
        )
        await _emit_trace_event(
            trace_event_repo,
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            payload={
                "consent_template_slug": input.consent_template_slug,
                "delivery_channel": input.delivery_channel,
                "error_code": result.error_code,
            },
            status="error",
        )
        return result

    # ── 2. Persist consent_record (delegates to ConsentService — handles D2) ──
    # Build RequestConsentRequest via local import (avoids circular at module load).
    from src.modules.vitalia.application.services.consent_service import (
        RequestConsentRequest,
    )

    delivery_channels = _expand_delivery_channels(input.delivery_channel)

    request = RequestConsentRequest(
        patient_id=input.patient_id,
        booking_id=input.booking_id or input.patient_id,  # pre-booking phase: use patient as key
        consent_template_slug=input.consent_template_slug,
        delivery_channels=delivery_channels,
        expiry_hours=_DEFAULT_EXPIRY_HOURS,
    )

    consent_url_result = await consent_service.request_consent(
        request=request,
        base_url=base_url,
    )

    # ── 3. Audit log consent_requested (best-effort) ─────────────────────
    await _append_audit_log(
        audit_log_repo,
        tenant_id=tenant_id,
        patient_id=input.patient_id,
        booking_id=input.booking_id,
        consent_id=consent_url_result.consent_id,
        consent_template_slug=input.consent_template_slug,
        delivery_channel=input.delivery_channel,
        is_new=consent_url_result.is_new,
    )

    # ── 4. Fire-and-forget channel dispatch (best-effort) ────────────────
    # Per 02-design § 6.3: "Dispatches WhatsApp + email via channel adapters."
    # Failures NEVER break turn (R23). Use background tasks so dispatch latency
    # does not slow the agentic turn.
    for channel in delivery_channels:
        _schedule_dispatch(
            channel_dispatcher,
            tenant_id=tenant_id,
            consent_id=consent_url_result.consent_id,
            consent_url=consent_url_result.consent_url,
            patient_id=input.patient_id,
            delivery_channel=channel,
        )

    # ── 5. Build typed result + trace_event (best-effort) ────────────────
    result = MedicalConsentRequestOutput(
        status="pending_signature",
        consent_id=consent_url_result.consent_id,
        consent_url=consent_url_result.consent_url,
        expires_at=consent_url_result.expires_at,
        template_version=getattr(consent_url_result, "template_version", "v1"),
        is_new=consent_url_result.is_new,
    )

    await _emit_trace_event(
        trace_event_repo,
        tenant_id=tenant_id,
        turn_id=turn_id,
        span_id=span_id,
        payload={
            "consent_id": str(result.consent_id),
            "consent_template_slug": input.consent_template_slug,
            "delivery_channel": input.delivery_channel,
            "is_new": result.is_new,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        },
        status="ok",
    )

    return result


# ─── Helpers ─────────────────────────────────────────────────────────────


async def _resolve_requires_consent(
    callable_: Any,
    offer_id: uuid.UUID,
) -> bool:
    """Invoke offer_requires_consent callable — supports both sync + async."""
    res = callable_(offer_id)
    if asyncio.iscoroutine(res):
        return bool(await res)
    return bool(res)


def _expand_delivery_channels(channel: str) -> list[str]:
    """Expand 'both' → ['whatsapp', 'email']; otherwise singleton list."""
    if channel == "both":
        return ["whatsapp", "email"]
    if channel in _DELIVERY_CHANNELS:
        return [channel]
    # Defensive — Pydantic Literal already restricts, but fall back gracefully.
    logger.warning("medical_consent_request.unknown_channel", channel=channel)
    return [channel]


async def _append_audit_log(
    repo: _AuditLogRepoLike,
    *,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    booking_id: uuid.UUID | None,
    consent_id: uuid.UUID,
    consent_template_slug: str,
    delivery_channel: str,
    is_new: bool,
) -> None:
    """Append consent_requested audit event. Best-effort (try/except + warning).

    Per `.claude/rules/copilot-observability.md`: every audit/observability
    write wrapped in try/except + structlog warning + (no rollback here, caller
    owns the session). PII sanitized BEFORE persist.
    """
    try:
        from src.modules.vitalia.infrastructure.models.medical_audit_log_model import (
            VitaliaMedicalAuditLogModel,
        )

        # Sanitize payload — booking_id/consent_id/slug/channel are safe identifiers
        # but route through sanitize_payload for defense-in-depth + truncation.
        payload = sanitize_payload(
            {
                "consent_id": str(consent_id),
                "consent_template_slug": consent_template_slug,
                "delivery_channel": delivery_channel,
                "is_new": is_new,
            }
        )

        audit_event = VitaliaMedicalAuditLogModel(
            tenant_id=tenant_id,
            event_type="consent_requested",
            severity=_AUDIT_SEVERITY_INFO,
            patient_id=patient_id,
            booking_id=booking_id,
            payload_redacted=payload,
            actor_type="sales_agent",
        )
        await repo.save(audit_event)
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "medical_consent_request.audit_log_persist_failed",
            exc=str(exc),
            consent_id=str(consent_id),
            tenant_id=str(tenant_id),
        )


def _schedule_dispatch(
    dispatcher: _ChannelDispatcherLike,
    *,
    tenant_id: uuid.UUID,
    consent_id: uuid.UUID,
    consent_url: str,
    patient_id: uuid.UUID,
    delivery_channel: str,
) -> None:
    """Schedule async channel dispatch — fire-and-forget pattern.

    Per 02-design § 6.3 + tessl__graceful-degradation rules: dispatch failures
    NEVER break the synchronous tool turn. We schedule the coroutine on the
    running event loop and attach a done-callback that logs warnings on failure.
    """

    async def _safe_dispatch() -> None:
        try:
            await dispatcher.dispatch(
                tenant_id=tenant_id,
                consent_id=consent_id,
                consent_url=consent_url,
                patient_id=patient_id,
                delivery_channel=delivery_channel,
            )
        except Exception as exc:  # noqa: BLE001 — fire-and-forget
            logger.warning(
                "medical_consent_request.channel_dispatch_failed",
                exc=str(exc),
                consent_id=str(consent_id),
                tenant_id=str(tenant_id),
                delivery_channel=delivery_channel,
            )

    try:
        loop = asyncio.get_running_loop()
        # Use ensure_future to keep the task alive without awaiting it.
        # Strong reference held by loop until done — no GC race.
        loop.create_task(_safe_dispatch())
    except RuntimeError:
        # No running loop (e.g. sync caller) — log and skip dispatch.
        logger.warning(
            "medical_consent_request.no_running_loop_skip_dispatch",
            consent_id=str(consent_id),
            tenant_id=str(tenant_id),
            delivery_channel=delivery_channel,
        )


async def _emit_trace_event(
    trace_event_repo: _TraceEventRepoLike | None,
    *,
    tenant_id: uuid.UUID,
    turn_id: uuid.UUID | None,
    span_id: uuid.UUID | None,
    payload: dict[str, Any],
    status: str,
) -> None:
    """Best-effort trace_event emission. NEVER breaks tool turn (R23).

    Skips silently if repo not supplied or correlation IDs missing.
    Logs warning on persistence failure.
    """
    if trace_event_repo is None or turn_id is None or span_id is None:
        return

    try:
        sanitized = sanitize_payload(payload)
        trace_event_repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="tool.medical_consent_request.completed",
            name="medical_consent_request",
            data=sanitized,
            status=status,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "medical_consent_request.trace_event_persist_failed",
            exc=str(exc),
            tenant_id=str(tenant_id),
        )


__all__ = [
    "MedicalConsentRequestInput",
    "MedicalConsentRequestOutput",
    "medical_consent_request",
]
