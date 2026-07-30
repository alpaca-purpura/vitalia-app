"""RED tests — RBAC @require_phi_access decorator.

TDD: RED first per T-infra-3.
Verifies: blocks non-allowed roles with 403, logs audit event on both access + denial.
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


def _import_rbac():
    from src.modules.vitalia._shared.auth.rbac import (  # noqa: PLC0415
        PHIAccessDeniedError,
        require_phi_access,
    )

    return require_phi_access, PHIAccessDeniedError


class TestRequirePhiAccessDecorator:
    """@require_phi_access must block non-allowed roles and log audit events."""

    def test_rbac_importable(self) -> None:
        """require_phi_access must be importable from _shared.auth.rbac."""
        require_phi_access, _ = _import_rbac()
        assert require_phi_access is not None

    def test_phi_access_denied_error_importable(self) -> None:
        """PHIAccessDeniedError must be importable."""
        _, PHIAccessDeniedError = _import_rbac()
        assert PHIAccessDeniedError is not None

    @pytest.mark.asyncio
    async def test_allowed_role_doctor_passes(self) -> None:
        """Role 'doctor' must be in the default allowed list — no exception raised."""
        require_phi_access, _ = _import_rbac()

        mock_audit = AsyncMock()

        @require_phi_access(roles=["doctor", "nurse", "admin_clinic"], audit_repo=mock_audit)
        async def protected_endpoint(tenant_id, clinic_id, user_id, user_role):
            return "ok"

        result = await protected_endpoint(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="doctor",
        )
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_disallowed_role_marketing_raises_403(self) -> None:
        """Role 'marketing' must be blocked — PHIAccessDeniedError raised."""
        require_phi_access, PHIAccessDeniedError = _import_rbac()

        mock_audit = AsyncMock()

        @require_phi_access(roles=["doctor", "nurse", "admin_clinic"], audit_repo=mock_audit)
        async def protected_endpoint(tenant_id, clinic_id, user_id, user_role):
            return "ok"

        with pytest.raises(PHIAccessDeniedError):
            await protected_endpoint(
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="marketing",
            )

    @pytest.mark.asyncio
    async def test_audit_event_written_on_denial(self) -> None:
        """Audit event must be written when access is denied."""
        require_phi_access, PHIAccessDeniedError = _import_rbac()

        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()

        @require_phi_access(roles=["doctor"], audit_repo=mock_audit)
        async def protected_endpoint(tenant_id, clinic_id, user_id, user_role):
            return "ok"

        with pytest.raises(PHIAccessDeniedError):
            await protected_endpoint(
                tenant_id=uuid4(),
                clinic_id=uuid4(),
                user_id=uuid4(),
                user_role="sales",
            )

        # Audit write must have been called
        assert mock_audit.write.called

    @pytest.mark.asyncio
    async def test_audit_event_written_on_success(self) -> None:
        """Audit event must also be written on successful PHI access."""
        require_phi_access, _ = _import_rbac()

        mock_audit = AsyncMock()
        mock_audit.write = AsyncMock()

        @require_phi_access(roles=["doctor", "nurse", "admin_clinic"], audit_repo=mock_audit)
        async def protected_endpoint(tenant_id, clinic_id, user_id, user_role):
            return "data"

        result = await protected_endpoint(
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            user_id=uuid4(),
            user_role="nurse",
        )

        assert result == "data"
        assert mock_audit.write.called
