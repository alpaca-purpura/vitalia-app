"""Tool tests — `medical_consent_request` (vitalia AGENTIC tool, R23 Opus 4.7).

TDD: RED first per `.claude/rules/tdd-mandatory.md`.

Acceptance per 06-tickets.yaml::T-tools-2 + 02-design § 6.3 + 03-arch-agentic § 4.3:

  A1: test_persists_audit_logs — Tool persists consent_record + audit_log
      consent_requested entry on first invocation.
  A2: test_offer_validation — Tool returns error status when
      offer.requires_informed_consent=false (validation gate).
  A3: test_idempotency — Same (booking_id, consent_template_slug) within 1h
      window returns existing consent_id (D2 idempotency, no duplicate row).

Plus defensive coverage (per copilot-resilience.md + R23):

  - test_tenant_id_not_in_schema — security boundary (ctx-injected)
  - test_dispatches_channels — WhatsApp + email channel dispatch invoked async
  - test_dispatch_failure_does_not_break_turn — fire-and-forget pattern
  - test_trace_event_recorded — best-effort observability
  - test_trace_event_failure_does_not_break_turn — observability never breaks turn
  - test_pii_sanitized_in_trace — patient name / phone NEVER in trace payload raw
  - test_signed_url_format — HMAC URL contains consent_id + token query params
  - test_expiry_24h_default — expires_at = now + 24h (D7 HIPAA-lite)

These are UNIT tests — ConsentService + repos + dispatcher mocked via in-memory fakes.
Integration tests (real Postgres + actual WhatsApp/email send) land in
tests/integration/ + smoke E2E suite (separate scope).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

# ───────────────────────────────────────────────────────────────────────────
# A3 — Tenant ID NOT in input schema (security boundary; sync test)
# ───────────────────────────────────────────────────────────────────────────


def test_tenant_id_not_in_schema() -> None:
    """tenant_id MUST NEVER appear in client-provided input.

    Security boundary per `.claude/rules/tenant-isolation.md` + 02-design § 6.3.
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
    )

    fields = MedicalConsentRequestInput.model_fields
    assert "tenant_id" not in fields, (
        "tenant_id MUST NOT be in MedicalConsentRequestInput — "
        "security boundary per tenant-isolation.md + 02-design § 6.3"
    )
    # patient_id + consent_template_slug required; booking_id + delivery_channel optional
    assert "patient_id" in fields
    assert "consent_template_slug" in fields
    assert "booking_id" in fields
    assert "delivery_channel" in fields


# ───────────────────────────────────────────────────────────────────────────
# Fixtures — in-memory fakes
# ───────────────────────────────────────────────────────────────────────────


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


class _FakeConsentRecord:
    """Mirror minimal surface of VitaliaConsentRecordModel."""

    def __init__(
        self,
        *,
        consent_id: uuid.UUID,
        tenant_id: uuid.UUID,
        patient_id: uuid.UUID,
        booking_id: uuid.UUID | None,
        consent_template_slug: str,
        status: str = "pending_signature",
        expires_at: datetime | None = None,
        template_version: str = "v1",
    ) -> None:
        self.id = consent_id
        self.tenant_id = tenant_id
        self.patient_id = patient_id
        self.booking_id = booking_id
        self.consent_template_slug = consent_template_slug
        self.status = status
        self.expires_at = expires_at or (_utc_now() + timedelta(hours=24))
        self.template_version = template_version


class _FakeConsentService:
    """In-memory ConsentService stand-in.

    Mirrors the relevant T-be-6 surface (`request_consent` + `build_consent_url`).
    Stores pending consents in-memory and applies D2 idempotency per
    `(booking_id, consent_template_slug)` key.
    """

    def __init__(self, tenant_id: uuid.UUID) -> None:
        self._tenant_id = tenant_id
        self._records: list[_FakeConsentRecord] = []
        self._url_secret = "test-secret"
        self.request_calls: list[dict[str, Any]] = []

    async def request_consent(
        self,
        request: Any,  # RequestConsentRequest
        base_url: str,
    ) -> Any:
        """Idempotent — returns existing pending consent for same (booking_id, slug)."""
        self.request_calls.append(
            {
                "patient_id": request.patient_id,
                "booking_id": request.booking_id,
                "consent_template_slug": request.consent_template_slug,
                "delivery_channels": request.delivery_channels,
                "expiry_hours": request.expiry_hours,
            }
        )

        # D2 idempotency: pending consent for same (booking, slug) → return existing
        for rec in self._records:
            if (
                rec.booking_id == request.booking_id
                and rec.consent_template_slug == request.consent_template_slug
                and rec.status == "pending_signature"
            ):
                from src.modules.vitalia.application.services.consent_service import (
                    ConsentUrlResult,
                )

                return ConsentUrlResult(
                    consent_id=rec.id,
                    consent_url=f"{base_url}/consent/sign?consent_id={rec.id}&token=t",
                    expires_at=rec.expires_at,
                    is_new=False,
                )

        # Create new
        consent_id = uuid.uuid4()
        expires_at = _utc_now() + timedelta(hours=request.expiry_hours)
        rec = _FakeConsentRecord(
            consent_id=consent_id,
            tenant_id=self._tenant_id,
            patient_id=request.patient_id,
            booking_id=request.booking_id,
            consent_template_slug=request.consent_template_slug,
            expires_at=expires_at,
        )
        self._records.append(rec)

        from src.modules.vitalia.application.services.consent_service import (
            ConsentUrlResult,
        )

        return ConsentUrlResult(
            consent_id=consent_id,
            consent_url=f"{base_url}/consent/sign?consent_id={consent_id}&token=hmacXYZ",
            expires_at=expires_at,
            is_new=True,
        )


class _CapturingAuditRepo:
    """Captures audit_log save calls."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    async def save(self, audit_event: Any) -> None:
        self.events.append(audit_event)


class _RaisingAuditRepo:
    """Audit log raises — confirms tool turn does NOT break."""

    async def save(self, audit_event: Any) -> None:
        raise RuntimeError("audit log down — must not break turn")


class _CapturingChannelDispatcher:
    """Captures async channel dispatch calls."""

    def __init__(self) -> None:
        self.dispatches: list[dict[str, Any]] = []

    async def dispatch(
        self,
        *,
        consent_id: uuid.UUID,
        consent_url: str,
        patient_id: uuid.UUID,
        delivery_channel: str,
        tenant_id: uuid.UUID,
    ) -> None:
        self.dispatches.append(
            {
                "consent_id": consent_id,
                "consent_url": consent_url,
                "patient_id": patient_id,
                "delivery_channel": delivery_channel,
                "tenant_id": tenant_id,
            }
        )


class _RaisingChannelDispatcher:
    """Always raises — confirms fire-and-forget pattern (no break turn)."""

    async def dispatch(self, **kwargs: Any) -> None:
        raise RuntimeError("channel dispatch down — must not break turn")


class _CapturingTraceRepo:
    """Captures trace_event.add() calls (sync surface per BaseTraceEventRepoProtocol)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return None


class _RaisingTraceRepo:
    def add(self, **kwargs: Any) -> Any:
        raise RuntimeError("trace repo down — must NOT break turn")


def _offer_requires_consent_true(offer_id: uuid.UUID) -> bool:
    return True


def _offer_requires_consent_false(offer_id: uuid.UUID) -> bool:
    return False


# ───────────────────────────────────────────────────────────────────────────
# A1 — Persists consent_record + audit_log consent_requested
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_persists_audit_logs() -> None:
    """A1 acceptance: tool persists consent_record (via ConsentService) AND
    appends audit_log consent_requested event with sanitized payload.
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    offer_id = uuid.uuid4()

    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=patient_id,
            booking_id=booking_id,
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=offer_id,
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    # Result populated
    assert result.status == "pending_signature"
    assert result.consent_id is not None
    assert "consent/sign" in result.consent_url
    assert result.expires_at > _utc_now()
    assert result.template_version == "v1"

    # ConsentService.request_consent called once
    assert len(consent_service.request_calls) == 1
    call = consent_service.request_calls[0]
    assert call["patient_id"] == patient_id
    assert call["booking_id"] == booking_id
    assert call["consent_template_slug"] == "dental_implant_v1"

    # Audit log saved with consent_requested event
    assert len(audit_repo.events) == 1
    audit = audit_repo.events[0]
    assert audit.tenant_id == tenant_id
    assert audit.event_type == "consent_requested"
    assert audit.severity == "info"
    assert audit.patient_id == patient_id
    assert audit.booking_id == booking_id
    assert audit.actor_type == "sales_agent"
    # Payload sanitized — slug + channel + consent_id present, NO patient_name/phone/email
    payload = audit.payload_redacted
    assert payload["consent_template_slug"] == "dental_implant_v1"
    assert payload["delivery_channel"] == "both"
    assert payload["consent_id"] == str(result.consent_id)
    assert payload["is_new"] is True


# ───────────────────────────────────────────────────────────────────────────
# A2 — Tool returns error when offer.requires_informed_consent=false
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_offer_validation_returns_error_when_not_required() -> None:
    """A2 acceptance: offer.requires_informed_consent=false → tool returns
    status='offer_does_not_require_consent' WITHOUT persisting consent_record.

    Per 02-design § 6.3 error mode: "Tool MUST NOT request consent if
    offer.requires_informed_consent=false (tool validates against offers table)".
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    offer_id = uuid.uuid4()

    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=patient_id,
            booking_id=booking_id,
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=offer_id,
        offer_requires_consent=_offer_requires_consent_false,  # ← validation gate
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    # Tool returns offer_validation error
    assert result.status == "offer_does_not_require_consent"
    assert result.consent_id is None
    assert result.consent_url is None
    assert result.error_code == "offer_does_not_require_consent"

    # NO consent created
    assert len(consent_service.request_calls) == 0
    # NO channel dispatched
    assert len(dispatcher.dispatches) == 0


# ───────────────────────────────────────────────────────────────────────────
# A3 — Idempotency 1h window same (booking_id, slug) returns existing consent_id
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_idempotency_returns_existing_consent_id() -> None:
    """A3 acceptance: invoking twice with same (booking_id, consent_template_slug)
    within 1h returns the SAME consent_id and does NOT create a new row.

    Idempotency delegates to ConsentService.request_consent (T-be-6 D2) which
    returns existing pending consent for same (booking_id, slug) pair.
    Tool surfaces this via `is_new=False` in the underlying ConsentUrlResult.
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    offer_id = uuid.uuid4()

    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    inp = MedicalConsentRequestInput(
        patient_id=patient_id,
        booking_id=booking_id,
        consent_template_slug="dental_implant_v1",
        delivery_channel="both",
    )

    first = await medical_consent_request(
        inp,
        tenant_id=tenant_id,
        offer_id=offer_id,
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    second = await medical_consent_request(
        inp,
        tenant_id=tenant_id,
        offer_id=offer_id,
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    # Same consent_id returned both times (D2 idempotency)
    assert first.consent_id == second.consent_id
    assert first.status == "pending_signature"
    assert second.status == "pending_signature"

    # ConsentService called twice, but only ONE record materialized
    assert len(consent_service.request_calls) == 2
    assert len(consent_service._records) == 1

    # Both invocations recorded as audit log entries (audit log captures intent)
    assert len(audit_repo.events) == 2
    # Second event flagged as is_new=False (idempotent reuse)
    assert audit_repo.events[1].payload_redacted["is_new"] is False


# ───────────────────────────────────────────────────────────────────────────
# Defensive: dispatches channels async + fire-and-forget
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatches_channels_for_both() -> None:
    """delivery_channel='both' → dispatcher invoked once per channel (whatsapp + email)."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    # Allow background tasks to settle
    await asyncio.sleep(0.05)

    channels = sorted(d["delivery_channel"] for d in dispatcher.dispatches)
    assert channels == ["email", "whatsapp"]


@pytest.mark.asyncio
async def test_dispatches_channel_whatsapp_only() -> None:
    """delivery_channel='whatsapp' → dispatcher invoked once for whatsapp only."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="whatsapp",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    await asyncio.sleep(0.05)

    assert len(dispatcher.dispatches) == 1
    assert dispatcher.dispatches[0]["delivery_channel"] == "whatsapp"


@pytest.mark.asyncio
async def test_dispatch_failure_does_not_break_turn() -> None:
    """Channel dispatch raising MUST NOT break turn (fire-and-forget pattern)."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _RaisingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    # Allow background tasks (which raise) to settle
    await asyncio.sleep(0.05)

    # Tool succeeded — consent persisted, status reflects best-effort dispatch attempt
    assert result.status == "pending_signature"
    assert result.consent_id is not None
    # Audit log still appended
    assert len(audit_repo.events) == 1


# ───────────────────────────────────────────────────────────────────────────
# Defensive: trace_event observability + sanitization
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trace_event_recorded_when_repo_supplied() -> None:
    """Best-effort observability: trace_event recorded on tool completion."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()
    trace_repo = _CapturingTraceRepo()
    turn_id = uuid.uuid4()
    span_id = uuid.uuid4()

    await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
        trace_event_repo=trace_repo,
        turn_id=turn_id,
        span_id=span_id,
    )

    assert len(trace_repo.calls) == 1
    call = trace_repo.calls[0]
    assert call["tenant_id"] == tenant_id
    assert call["turn_id"] == turn_id
    assert call["span_id"] == span_id
    assert call["event_type"] == "tool.medical_consent_request.completed"
    assert call["status"] == "ok"
    assert call["data"]["consent_template_slug"] == "dental_implant_v1"


@pytest.mark.asyncio
async def test_trace_event_failure_does_not_break_turn() -> None:
    """Trace repo raising MUST NOT break tool turn (R23 best-effort observability)."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
        trace_event_repo=_RaisingTraceRepo(),
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    assert result.status == "pending_signature"
    assert result.consent_id is not None


@pytest.mark.asyncio
async def test_audit_log_failure_does_not_break_turn() -> None:
    """audit_log raising MUST NOT break tool turn (best-effort persist).

    Per copilot-observability.md: any audit/observability failure → log warning,
    swallow exception, return successful tool result.
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _RaisingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    assert result.status == "pending_signature"
    assert result.consent_id is not None


# ───────────────────────────────────────────────────────────────────────────
# Defensive: PII never raw in trace payload
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_patient_pii_in_trace_payload() -> None:
    """Trace payload MUST NOT contain raw patient PII (name / phone / email).

    Per `.tessl/RULES.md` PII sanitisation + sales-agent-brand-voice.md.
    Audit log payload + trace payload are both sanitized via sanitize_payload.
    """
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()
    trace_repo = _CapturingTraceRepo()

    await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
        trace_event_repo=trace_repo,
        turn_id=uuid.uuid4(),
        span_id=uuid.uuid4(),
    )

    # Trace payload only contains safe identifiers + slug + status — NO patient_name / phone / email
    payload = trace_repo.calls[0]["data"]
    forbidden_keys = ("patient_name", "patient_phone", "patient_email", "signed_name")
    for key in forbidden_keys:
        assert key not in payload, f"PII key {key!r} leaked into trace payload"


# ───────────────────────────────────────────────────────────────────────────
# Defensive: signed URL format + 24h default expiry (D7 HIPAA-lite)
# ───────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_signed_url_contains_consent_id_and_token() -> None:
    """Generated consent URL contains consent_id + HMAC token query params."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )

    assert result.consent_url is not None
    assert "consent_id=" in result.consent_url
    assert "token=" in result.consent_url
    # consent_id must match returned ID (HMAC token bound to that consent)
    assert str(result.consent_id) in result.consent_url


@pytest.mark.asyncio
async def test_expiry_24h_default_per_d7_hipaa_lite() -> None:
    """expires_at = now + 24h default per D7 HIPAA-lite + 02-design § 6.3."""
    from src.modules.vitalia.agentic.tools.medical_consent_request import (
        MedicalConsentRequestInput,
        medical_consent_request,
    )

    tenant_id = uuid.uuid4()
    consent_service = _FakeConsentService(tenant_id)
    audit_repo = _CapturingAuditRepo()
    dispatcher = _CapturingChannelDispatcher()

    before = _utc_now()
    result = await medical_consent_request(
        MedicalConsentRequestInput(
            patient_id=uuid.uuid4(),
            booking_id=uuid.uuid4(),
            consent_template_slug="dental_implant_v1",
            delivery_channel="both",
        ),
        tenant_id=tenant_id,
        offer_id=uuid.uuid4(),
        offer_requires_consent=_offer_requires_consent_true,
        consent_service=consent_service,
        audit_log_repo=audit_repo,
        channel_dispatcher=dispatcher,
        base_url="https://vitalia.app",
    )
    after = _utc_now()

    # 24h default ± a few seconds for processing
    assert result.expires_at >= before + timedelta(hours=23, minutes=59)
    assert result.expires_at <= after + timedelta(hours=24, minutes=1)
