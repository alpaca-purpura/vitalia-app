# cap: clinics.lisa.doctores
"""DoctorBioFileRepository — dual-filter repository for doctor bio files.

HIPAA-lite compliance:
  - Inherits CompoundScopeRepositoryBase (engine — post lift 2026-05-20)
    with scope_field="clinic_id" for cross-clinic isolation
    (ticket says "PhiRepositoryBase": that base was PROMOTED to the engine —
    arch gate test_compound_scope_repository_used.py mandates this class for
    new repos; the dual-filter contract is identical, incl. get_by_id)
  - All queries: deleted_at IS NULL + tenant_id + clinic_id
  - Soft deletes only (deleted_at)

Cross-tenant/cross-clinic reads return None/[] — API layer maps to 404
(never 403 — no existence leak, runtime-quality-checklist § tenant isolation).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile
from src.modules.vitalia.clinics.infrastructure.models.doctor_bio_file_model import (
    VitaliaDoctorBioFileModel,
)

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


class DoctorBioFileRepository(CompoundScopeRepositoryBase[VitaliaDoctorBioFileModel, UUID]):
    """Async repository for DoctorBioFile entities (dual filter, soft delete)."""

    MODEL = VitaliaDoctorBioFileModel

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async session (caller owns the commit boundary).

        Args:
            session: SQLAlchemy async session.
        """
        super().__init__(session=session, scope_field="clinic_id")

    def validate_dual_filter(
        self,
        *,
        tenant_id: UUID | None,
        clinic_id: UUID | None,
    ) -> None:
        """Validate dual filter (tenant_id + clinic_id) — DoctorRepository contract.

        Raises:
            ValueError: If tenant_id is None.
            MissingClinicFilterError: If clinic_id is None.
        """
        from src.modules.vitalia._shared.repositories.phi_repository import (  # noqa: PLC0415
            MissingClinicFilterError,
        )

        if tenant_id is None:
            raise ValueError("Repository requires tenant_id — never bypass root tenant isolation")
        if clinic_id is None:
            logger.warning(
                "dual_filter_violation",
                repository=self.__class__.__name__,
                reason="clinic_id missing from bio file query",
            )
            raise MissingClinicFilterError()

    # ── Reads ─────────────────────────────────────────────────────────────────

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> DoctorBioFile | None:
        """Get a bio file by ID with dual filter (None if cross-tenant/clinic)."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = select(VitaliaDoctorBioFileModel).where(
            VitaliaDoctorBioFileModel.id == entity_id,
            VitaliaDoctorBioFileModel.tenant_id == tenant_id,
            VitaliaDoctorBioFileModel.clinic_id == clinic_id,
            VitaliaDoctorBioFileModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model is not None else None

    async def list_for_doctor(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> list[DoctorBioFile]:
        """List active bio files for a doctor, newest first (dual filter)."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = (
            select(VitaliaDoctorBioFileModel)
            .where(
                VitaliaDoctorBioFileModel.tenant_id == tenant_id,
                VitaliaDoctorBioFileModel.clinic_id == clinic_id,
                VitaliaDoctorBioFileModel.doctor_id == doctor_id,
                VitaliaDoctorBioFileModel.deleted_at.is_(None),
            )
            .order_by(VitaliaDoctorBioFileModel.uploaded_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    # ── Writes ────────────────────────────────────────────────────────────────

    async def add(
        self,
        bio_file: DoctorBioFile,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> DoctorBioFile:
        """Persist a new bio file row (flush; caller commits)."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        self._session.add(_entity_to_model(bio_file))
        await self._session.flush()

        logger.info(
            "doctor_bio_file_added",
            bio_file_id=str(bio_file.id),
            doctor_id=str(bio_file.doctor_id),
            tenant_id=str(tenant_id),
            size_bytes=bio_file.size_bytes,
        )
        return bio_file

    async def soft_delete(
        self,
        file_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> bool:
        """Soft-delete a bio file (dual filter + doctor scope). Returns False if absent."""
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = (
            update(VitaliaDoctorBioFileModel)
            .where(
                VitaliaDoctorBioFileModel.id == file_id,
                VitaliaDoctorBioFileModel.tenant_id == tenant_id,
                VitaliaDoctorBioFileModel.clinic_id == clinic_id,
                VitaliaDoctorBioFileModel.doctor_id == doctor_id,
                VitaliaDoctorBioFileModel.deleted_at.is_(None),
            )
            .values(deleted_at=_utc_now())
        )
        result = await self._session.execute(stmt)
        await self._session.flush()

        deleted = (result.rowcount or 0) > 0
        if deleted:
            logger.info(
                "doctor_bio_file_soft_deleted",
                bio_file_id=str(file_id),
                doctor_id=str(doctor_id),
                tenant_id=str(tenant_id),
            )
        return deleted


# ── Domain ↔ Model mappers ────────────────────────────────────────────────────


def _model_to_entity(model: VitaliaDoctorBioFileModel) -> DoctorBioFile:
    """Map ORM model to domain entity."""
    return DoctorBioFile(
        id=model.id,
        tenant_id=model.tenant_id,
        clinic_id=model.clinic_id,
        doctor_id=model.doctor_id,
        storage_key=model.storage_key,
        filename=model.filename,
        size_bytes=model.size_bytes,
        content_type=model.content_type,
        uploaded_at=model.uploaded_at,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


def _entity_to_model(entity: DoctorBioFile) -> VitaliaDoctorBioFileModel:
    """Map domain entity to ORM model (for INSERT)."""
    return VitaliaDoctorBioFileModel(
        id=entity.id,
        tenant_id=entity.tenant_id,
        clinic_id=entity.clinic_id,
        doctor_id=entity.doctor_id,
        storage_key=entity.storage_key,
        filename=entity.filename,
        size_bytes=entity.size_bytes,
        content_type=entity.content_type,
        uploaded_at=entity.uploaded_at,
        created_at=entity.created_at,
        deleted_at=entity.deleted_at,
    )
