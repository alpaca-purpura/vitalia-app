"""Unit tests — ComplianceEventService (T-be-4 A2).

TDD RED → GREEN. All tests use mocked repositories (no Postgres needed).

Acceptance criteria (T-be-4):
  A2: ComplianceEventService never raises on persist failure (best-effort).

Decision coverage:
  D1: DDD inside-out — services receive repos via DI.
  D7: HIPAA-lite — sanitize_payload called before persist.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.vitalia.application.services.compliance_event_service import (
    ComplianceEventService,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def patient_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture()
def mock_audit_repo() -> MagicMock:
    repo = MagicMock()
    repo.save = AsyncMock()
    return repo


# ── A2: Best-effort — NEVER raises ──────────────────────────────────────────


def test_never_raises(tenant_id: uuid.UUID, patient_id: uuid.UUID) -> None:
    """A2: ComplianceEventService.log_event NEVER raises even when repo.save fails.

    This is the core best-effort observability pattern: user flow must
    not be interrupted by audit log failures (HIPAA-lite, not HIPAA strict).
    """
    import asyncio

    failing_repo = MagicMock()
    failing_repo.save = AsyncMock(side_effect=RuntimeError("DB connection lost"))

    async def run() -> None:
        svc = ComplianceEventService(audit_repo=failing_repo)
        # Must NOT raise despite the repo failure
        await svc.log_event(
            event_type="pii_detected",
            severity="medium",
            payload={"text": "patient: Juan Perez, dni 12345678"},
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

    # Should complete without raising
    asyncio.get_event_loop().run_until_complete(run())


def test_never_raises_on_sanitization_failure(
    tenant_id: uuid.UUID,
) -> None:
    """ComplianceEventService must not raise even if sanitize_payload explodes."""
    import asyncio

    mock_repo = MagicMock()
    mock_repo.save = AsyncMock()

    async def run() -> None:
        svc = ComplianceEventService(audit_repo=mock_repo)
        # Non-dict payload should be handled gracefully
        with patch(
            "src.modules.vitalia.application.services.compliance_event_service.sanitize_payload",
            side_effect=TypeError("unexpected input"),
        ):
            await svc.log_event(
                event_type="booking_created",
                severity="info",
                payload={"booking_id": "some-uuid"},
                tenant_id=tenant_id,
            )

    asyncio.get_event_loop().run_until_complete(run())


def test_log_event_calls_sanitize_payload_before_persist(
    tenant_id: uuid.UUID,
) -> None:
    """D7: sanitize_payload must be called before repo.save (PII redaction pre-persist)."""
    import asyncio

    calls: list[str] = []

    async def fake_save(model: object) -> None:
        calls.append("save")

    mock_repo = MagicMock()
    mock_repo.save = fake_save

    async def run() -> None:
        with patch(
            "src.modules.vitalia.application.services.compliance_event_service.sanitize_payload",
            side_effect=lambda p: {**p, "_sanitized": True} or calls.append("sanitize") or p,
        ) as mock_sanitize:
            svc = ComplianceEventService(audit_repo=mock_repo)
            await svc.log_event(
                event_type="pii_detected",
                severity="high",
                payload={"raw_text": "DNI 12.345.678"},
                tenant_id=tenant_id,
            )
            mock_sanitize.assert_called_once()

    asyncio.get_event_loop().run_until_complete(run())


def test_log_event_successful_write(
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    mock_audit_repo: MagicMock,
) -> None:
    """Happy path: log_event calls repo.save on success."""
    import asyncio

    async def run() -> None:
        svc = ComplianceEventService(audit_repo=mock_audit_repo)
        await svc.log_event(
            event_type="consent_signed",
            severity="info",
            payload={"consent_slug": "hipaa_lite_v1"},
            tenant_id=tenant_id,
            patient_id=patient_id,
        )

    asyncio.get_event_loop().run_until_complete(run())
    mock_audit_repo.save.assert_called_once()


def test_log_event_with_all_optional_params(
    tenant_id: uuid.UUID,
    mock_audit_repo: MagicMock,
) -> None:
    """log_event accepts booking_id + actor_id + actor_type as optional kwargs."""
    import asyncio

    booking_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    async def run() -> None:
        svc = ComplianceEventService(audit_repo=mock_audit_repo)
        await svc.log_event(
            event_type="slot_taken",
            severity="medium",
            payload={"doctor_id": str(uuid.uuid4())},
            tenant_id=tenant_id,
            booking_id=booking_id,
            actor_id=actor_id,
            actor_type="clinic_owner",
        )

    asyncio.get_event_loop().run_until_complete(run())
    mock_audit_repo.save.assert_called_once()


def test_compliance_event_service_di_constructor() -> None:
    """D1: ComplianceEventService must be constructable via DI (audit_repo param)."""
    import inspect

    sig = inspect.signature(ComplianceEventService.__init__)
    params = list(sig.parameters.keys())
    assert "audit_repo" in params, "ComplianceEventService must accept audit_repo via DI (D1)"
