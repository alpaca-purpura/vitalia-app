"""RED tests — PHIRepository dual filter enforcement.

TDD: these tests MUST fail (RED) before implementation is written.
They verify that PhiRepositoryBase enforces dual filter (tenant_id + clinic_id).

T-infra-3: PHI compliance infrastructure.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# Import paths — will fail RED until implementation exists
# ---------------------------------------------------------------------------


def _import_phi_repository():
    from src.modules.vitalia._shared.repositories.phi_repository import (  # noqa: PLC0415
        MissingClinicFilterError,
        PhiRepositoryBase,
    )

    return PhiRepositoryBase, MissingClinicFilterError


# ---------------------------------------------------------------------------
# Test: PhiRepositoryBase is an ABC with required dual-filter methods
# ---------------------------------------------------------------------------


class TestPhiRepositoryBaseContract:
    """PhiRepositoryBase must enforce dual-filter contract via ABC."""

    def test_phi_repository_base_importable(self) -> None:
        """PhiRepositoryBase must be importable from _shared.repositories."""
        PhiRepositoryBase, _ = _import_phi_repository()
        assert PhiRepositoryBase is not None

    def test_phi_repository_base_is_abstract(self) -> None:
        """PhiRepositoryBase must be abstract — cannot instantiate directly."""
        PhiRepositoryBase, _ = _import_phi_repository()
        with pytest.raises(TypeError, match="abstract"):
            PhiRepositoryBase()  # type: ignore[call-arg]

    def test_phi_repository_base_has_get_by_id(self) -> None:
        """PhiRepositoryBase must declare abstract get_by_id requiring both ids."""
        PhiRepositoryBase, _ = _import_phi_repository()
        assert hasattr(PhiRepositoryBase, "get_by_id")

    def test_phi_repository_base_has_list_by_filter(self) -> None:
        """PhiRepositoryBase must declare abstract list_by_filter."""
        PhiRepositoryBase, _ = _import_phi_repository()
        assert hasattr(PhiRepositoryBase, "list_by_filter")

    def test_phi_repository_subclass_without_clinic_id_raises(self) -> None:
        """Concrete subclass that omits clinic_id in queries must raise MissingClinicFilterError."""
        PhiRepositoryBase, MissingClinicFilterError = _import_phi_repository()

        class BadRepo(PhiRepositoryBase):
            """Intentionally broken — no clinic_id filter."""

            async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID):
                # Violates contract: does not use clinic_id in the query
                self.validate_dual_filter(tenant_id=tenant_id, clinic_id=None)

            async def list_by_filter(self, *, tenant_id: UUID, clinic_id: UUID, **filters):
                self.validate_dual_filter(tenant_id=tenant_id, clinic_id=None)

        repo = BadRepo()
        import asyncio

        with pytest.raises(MissingClinicFilterError):
            asyncio.get_event_loop().run_until_complete(repo.get_by_id(uuid4(), tenant_id=uuid4(), clinic_id=uuid4()))

    def test_phi_repository_subclass_with_both_ids_valid(self) -> None:
        """Concrete subclass that passes both ids to validate_dual_filter must not raise."""
        PhiRepositoryBase, MissingClinicFilterError = _import_phi_repository()

        class GoodRepo(PhiRepositoryBase):
            """Correctly validates dual filter."""

            async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID):
                self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
                return None

            async def list_by_filter(self, *, tenant_id: UUID, clinic_id: UUID, **filters):
                self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)
                return []

        repo = GoodRepo()
        import asyncio

        # Must NOT raise
        asyncio.get_event_loop().run_until_complete(repo.get_by_id(uuid4(), tenant_id=uuid4(), clinic_id=uuid4()))
