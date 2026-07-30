# cap: clinics.lisa.doctores
"""Cross-tenant access test for Doctor endpoints — SC-4.

Verifies: cross-tenant request → 404 generic (not 403 = no info leak).
Also verifies: audit log row written with action=cross_tenant_attempt on 404.

Note (config-cuenta T-2 follow-up): migrated from legacy
``asyncio.get_event_loop().run_until_complete()`` to native pytest-asyncio
(async def). The legacy pattern was order-dependent flaky: it broke whenever
a previous asyncio test closed the current loop (random test order).
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4


async def test_cross_tenant_get_doctor_returns_404() -> None:
    """SC-4: GET /doctors/{id} with doctor belonging to different tenant → 404."""
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService

    # Doctor exists for tenant_a, but request uses tenant_b + clinic_b
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None  # dual filter misses

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    result = await service.get_doctor(
        doctor_id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        user_id=uuid4(),
    )
    assert result is None


async def test_cross_tenant_writes_audit_log() -> None:
    """SC-4: cross-tenant attempt writes audit_log with cross_tenant_attempt action."""
    from src.modules.vitalia.clinics.application.doctor_service import DoctorService

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    audit_repo = AsyncMock()
    mock_emitter = AsyncMock()

    service = DoctorService(
        doctor_repo=mock_repo,
        audit_repo=audit_repo,
        emitter=mock_emitter,
    )

    await service.get_doctor(
        doctor_id=uuid4(),
        tenant_id=uuid4(),
        clinic_id=uuid4(),
        user_id=uuid4(),
    )
    # audit_repo.write should have been called with cross_tenant_attempt action
    assert audit_repo.write.called
    call_args = audit_repo.write.call_args[0][0]
    assert call_args.action == "cross_tenant_attempt"
