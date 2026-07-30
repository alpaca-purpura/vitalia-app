"""Tests unitarios — RBAC brand_owner para endpoints de mutación en marca_router.

Verifica:
  - role=patient → 403 BRAND_OWNER_RBAC_DENIED
  - role=marketing → 403
  - role=owner → pasa (200 o servicio llamado)
  - role=admin_clinic → pasa
  - Header ausente → 403 (default vacío)

Usa require_brand_owner_access() directamente (sin levantar FastAPI app completa).
Verifica el behavior del dependency function _dep.

T-3 — F2-S7 vitalia-fase2-lisa-marca (A2: RBAC role=patient→403, A6: rbac).
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.modules.vitalia._shared.auth.rbac import (
    ALLOWED_BRAND_OWNER_ROLES,
    require_brand_owner_access,
)

# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _call_dep(role: str) -> str:
    """Invoca el dependency function con un role dado."""
    dep_factory = require_brand_owner_access()
    return await dep_factory(user_role=role)


# ─── Tests ───────────────────────────────────────────────────────────────────


class TestBrandOwnerRBACAllowedRoles:
    """Roles permitidos: owner y admin_clinic."""

    @pytest.mark.asyncio
    async def test_owner_role_allowed(self) -> None:
        """role=owner debe pasar (sin excepción)."""
        result = await _call_dep("owner")
        assert result == "owner"

    @pytest.mark.asyncio
    async def test_admin_clinic_role_allowed(self) -> None:
        """role=admin_clinic debe pasar (sin excepción)."""
        result = await _call_dep("admin_clinic")
        assert result == "admin_clinic"

    def test_allowed_roles_frozenset_content(self) -> None:
        """ALLOWED_BRAND_OWNER_ROLES contiene exactamente owner y admin_clinic."""
        assert ALLOWED_BRAND_OWNER_ROLES == frozenset({"owner", "admin_clinic"})

    def test_allowed_roles_is_frozenset(self) -> None:
        """ALLOWED_BRAND_OWNER_ROLES es frozenset (inmutable)."""
        assert isinstance(ALLOWED_BRAND_OWNER_ROLES, frozenset)


class TestBrandOwnerRBACDeniedRoles:
    """Roles no permitidos deben recibir HTTP 403."""

    @pytest.mark.asyncio
    async def test_patient_role_denied(self) -> None:
        """role=patient → 403 BRAND_OWNER_RBAC_DENIED."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("patient")
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == {"error_code": "BRAND_OWNER_RBAC_DENIED"}

    @pytest.mark.asyncio
    async def test_marketing_role_denied(self) -> None:
        """role=marketing → 403 (no accede a brand config mutations)."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("marketing")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_doctor_role_denied(self) -> None:
        """role=doctor → 403 (doctor ve PHI, no brand config mutations)."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("doctor")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_nurse_role_denied(self) -> None:
        """role=nurse → 403."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("nurse")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sales_role_denied(self) -> None:
        """role=sales → 403."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("sales")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_role_denied(self) -> None:
        """role='' (header ausente/vacío) → 403."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_unknown_role_denied(self) -> None:
        """role desconocido → 403."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("superadmin_external")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_error_code_exact_value(self) -> None:
        """detail.error_code debe ser exactamente 'BRAND_OWNER_RBAC_DENIED'."""
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("patient")
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert detail.get("error_code") == "BRAND_OWNER_RBAC_DENIED"


class TestBrandOwnerRBACDependsFactory:
    """require_brand_owner_access() es Depends factory (invocable múltiples veces)."""

    def test_factory_returns_callable(self) -> None:
        """require_brand_owner_access() retorna callable (para Depends())."""
        dep = require_brand_owner_access()
        assert callable(dep)

    def test_factory_returns_new_callable_each_call(self) -> None:
        """Cada llamada a require_brand_owner_access() retorna callable nuevo."""
        dep1 = require_brand_owner_access()
        dep2 = require_brand_owner_access()
        assert dep1 is not dep2

    @pytest.mark.asyncio
    async def test_custom_roles_subset(self) -> None:
        """Se puede restringir roles a subset (solo owner)."""
        dep = require_brand_owner_access(roles=frozenset({"owner"}))
        # owner OK
        result = await dep(user_role="owner")
        assert result == "owner"

        # admin_clinic — NOT OK con subset custom
        with pytest.raises(HTTPException) as exc_info:
            await dep(user_role="admin_clinic")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_not_403_vs_401_for_wrong_role(self) -> None:
        """Rol incorrecto → 403 (Forbidden), NO 401 (Unauthorized).

        HIPAA-lite: el rol es conocido (autenticado via Clerk) pero no tiene
        permisos. Eso es Forbidden (403), no Unauthorized (401).
        """
        with pytest.raises(HTTPException) as exc_info:
            await _call_dep("patient")
        assert exc_info.value.status_code == 403
        assert exc_info.value.status_code != 401
