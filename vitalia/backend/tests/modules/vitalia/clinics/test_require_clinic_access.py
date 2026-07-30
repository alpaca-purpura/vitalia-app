"""Unit tests for @require_clinic_access decorator — HIPAA access control.

TDD: RED tests defined per vitalia-adopt-luana-core-iam story.

downstream-regression-na: brand-local clinics decorator tests
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException, status

from src.modules.vitalia.clinics.api.decorators import require_clinic_access


class TestRequireClinicAccessDefaultRoles:
    """Default roles: doctor, nurse, admin_clinic."""

    @pytest.mark.anyio
    async def test_doctor_role_allowed(self) -> None:
        """doctor role passes through."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "doctor") -> str:
            return "ok"

        result = await dummy_route(requesting_role="doctor")
        assert result == "ok"

    @pytest.mark.anyio
    async def test_nurse_role_allowed(self) -> None:
        """nurse role passes through."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "nurse") -> str:
            return "ok"

        result = await dummy_route(requesting_role="nurse")
        assert result == "ok"

    @pytest.mark.anyio
    async def test_admin_clinic_role_allowed(self) -> None:
        """admin_clinic role passes through."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "admin_clinic") -> str:
            return "ok"

        result = await dummy_route(requesting_role="admin_clinic")
        assert result == "ok"

    @pytest.mark.anyio
    async def test_marketing_role_denied(self) -> None:
        """marketing role raises 403 — PHI access forbidden."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "marketing") -> str:
            return "ok"

        with pytest.raises(HTTPException) as exc_info:
            await dummy_route(requesting_role="marketing")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail["error"] == "access_denied"

    @pytest.mark.anyio
    async def test_missing_role_denied(self) -> None:
        """Empty role string raises 403."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "") -> str:
            return "ok"

        with pytest.raises(HTTPException) as exc_info:
            await dummy_route(requesting_role="")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.anyio
    async def test_sales_role_denied(self) -> None:
        """sales role raises 403 — PHI access forbidden per HIPAA-lite."""

        @require_clinic_access()
        async def dummy_route(requesting_role: str = "sales") -> str:
            return "ok"

        with pytest.raises(HTTPException) as exc_info:
            await dummy_route(requesting_role="sales")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "required_roles" in exc_info.value.detail


class TestRequireClinicAccessCustomRoles:
    """Custom roles override default list."""

    @pytest.mark.anyio
    async def test_custom_roles_allow_specified(self) -> None:
        """Custom roles=['admin'] allows admin role."""

        @require_clinic_access(roles=["admin"])
        async def dummy_route(requesting_role: str = "admin") -> str:
            return "ok"

        result = await dummy_route(requesting_role="admin")
        assert result == "ok"

    @pytest.mark.anyio
    async def test_custom_roles_deny_doctor_when_not_in_list(self) -> None:
        """Custom roles=['admin'] denies doctor even though doctor is default."""

        @require_clinic_access(roles=["admin"])
        async def dummy_route(requesting_role: str = "doctor") -> str:
            return "ok"

        with pytest.raises(HTTPException) as exc_info:
            await dummy_route(requesting_role="doctor")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
