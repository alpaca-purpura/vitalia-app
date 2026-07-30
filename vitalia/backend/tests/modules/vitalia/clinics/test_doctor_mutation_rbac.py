# cap: clinics.lisa.doctores
"""Unit tests — RBAC policy for doctor (staff) mutations.

Policy decision (Chris, 2026-06-06): the clinic OWNER manages the staff roster,
so doctor mutations (create/edit/deactivate/bio/availability-blocks) allow
{owner, admin_clinic} — same as the marca (brand-config) module. Staff data is
business-roster data, not patient PHI; owner is a legitimate manager. This widens
the previous admin_clinic-only set (which left the only test user + clinic owner
unable to add staff, and created a bootstrap chicken-egg).

Source policy decision: vitalia-fase2-lisa-doctores chris-input #3b.
Mirrors brand_studio/test_rbac_brand_owner.py.

T-FIX-3 — vitalia-fase2-lisa-doctores.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.modules.vitalia._shared.auth.rbac import require_brand_owner_access
from src.modules.vitalia.clinics.api.doctors_router import _STAFF_MUTATION_ROLES


async def _call(role: str) -> str:
    dep = require_brand_owner_access(roles=_STAFF_MUTATION_ROLES)
    return await dep(user_role=role)


class TestStaffMutationRolesSet:
    def test_set_is_owner_plus_admin_clinic(self) -> None:
        """Doctor mutations allow exactly {owner, admin_clinic} (Chris #3b widen)."""
        assert _STAFF_MUTATION_ROLES == frozenset({"owner", "admin_clinic"})

    def test_is_frozenset(self) -> None:
        assert isinstance(_STAFF_MUTATION_ROLES, frozenset)


class TestStaffMutationAllowed:
    @pytest.mark.asyncio
    async def test_owner_allowed(self) -> None:
        """role=owner now passes (clinic owner manages staff)."""
        assert await _call("owner") == "owner"

    @pytest.mark.asyncio
    async def test_admin_clinic_allowed(self) -> None:
        assert await _call("admin_clinic") == "admin_clinic"


class TestStaffMutationDenied:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", ["marketing", "sales", "patient", "doctor", "nurse", ""])
    async def test_non_staff_roles_denied(self, role: str) -> None:
        """Roles outside {owner, admin_clinic} → 403. doctor/nurse read PHI but
        do NOT manage the staff roster (mutations). Empty header → 403."""
        with pytest.raises(HTTPException) as exc:
            await _call(role)
        assert exc.value.status_code == 403
