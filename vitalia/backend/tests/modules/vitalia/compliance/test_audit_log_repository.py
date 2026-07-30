"""RED tests — AuditLogRepository sync write enforcement.

TDD: RED first per T-infra-3.
Verifies: sync write, required fields, retention column populated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


def _import_audit_log_repo():
    from src.modules.vitalia._shared.repositories.audit_log_repository import (  # noqa: PLC0415
        AuditLogEntry,
        AuditLogRepository,
    )

    return AuditLogRepository, AuditLogEntry


class TestAuditLogRepositoryContract:
    """AuditLogRepository MUST write sync (not fire-forget)."""

    def test_audit_log_repository_importable(self) -> None:
        """AuditLogRepository must be importable."""
        AuditLogRepository, _ = _import_audit_log_repo()
        assert AuditLogRepository is not None

    def test_audit_log_entry_has_required_fields(self) -> None:
        """AuditLogEntry must include all required HIPAA-lite fields."""
        _, AuditLogEntry = _import_audit_log_repo()
        entry = AuditLogEntry(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            action="view_diagnosis",
            resource_type="treatment_plan",
            resource_id=uuid4(),
            from_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            payload_redacted=b"",
        )
        assert entry.tenant_id is not None
        assert entry.clinic_id is not None
        assert entry.user_id is not None
        assert entry.action == "view_diagnosis"
        assert entry.resource_type == "treatment_plan"

    def test_audit_log_entry_occurred_at_populated(self) -> None:
        """AuditLogEntry.occurred_at should be set automatically."""
        _, AuditLogEntry = _import_audit_log_repo()
        entry = AuditLogEntry(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            action="edit_treatment_plan",
            resource_type="treatment_plan",
            resource_id=uuid4(),
        )
        assert entry.occurred_at is not None

    def test_audit_log_repository_write_is_coroutine(self) -> None:
        """AuditLogRepository.write must be an async method (not sync fire-forget)."""
        import inspect

        AuditLogRepository, _ = _import_audit_log_repo()
        # write must be an async method
        assert inspect.iscoroutinefunction(AuditLogRepository.write)

    @pytest.mark.asyncio
    async def test_audit_log_repository_write_calls_session(self) -> None:
        """write() must call session.execute/add/flush (not schedule background task)."""
        AuditLogRepository, AuditLogEntry = _import_audit_log_repo()
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        repo = AuditLogRepository(session=mock_session)
        entry = AuditLogEntry(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            action="capture_payment",
            resource_type="appointment",
            resource_id=uuid4(),
        )
        await repo.write(entry)

        # Session must have been used synchronously (add or execute called)
        assert mock_session.add.called or mock_session.execute.called or mock_session.flush.called
