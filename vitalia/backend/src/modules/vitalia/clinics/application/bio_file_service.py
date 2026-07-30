# cap: clinics.lisa.doctores
"""BioFileService — application service for doctor bio material files (D3-B).

HIPAA-lite rules (vitalia/.claude/rules/hipaa-lite.md):
  - Audit log write SYNC (awaited) BEFORE response: doctor.bio_file_added /
    doctor.bio_file_deleted / doctor.bio_file_downloaded
  - Dual filter enforced by DoctorBioFileRepository (CompoundScopeRepositoryBase)
  - Cross-tenant access -> None/False + cross_tenant_attempt audit (404 at API,
    never 403 — no existence leak)

RN-D3B-1: deleting a bio file NEVER touches the doctor's generated bio/profile
snapshot — this service issues ZERO doctor mutations (doctor_repo is read-only
here, used solely for the existence/dual-filter check on register).

Download (D-1, impl-log): stream proxy via engine StorageStrategy.get_file_bytes
— the ONLY surface symmetric across local + R2 backends (presigned-GET does not
exist in luana-core-assets; F-1 brief finding). Engine consumed read-only.
Graceful degradation: storage failure -> BioFileStorageError (router maps 503).

Transaction boundary: caller (router) owns commit — this service only flushes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from uuid import UUID

import structlog

from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia.clinics.domain.bio_file import DoctorBioFile

if TYPE_CHECKING:
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_bio_file_repository import (
        DoctorBioFileRepository,
    )

logger = structlog.get_logger()


class BioFileStorageError(Exception):
    """Raised when the storage backend fails to serve a bio file (router -> 503)."""


class _DoctorLookupPort(Protocol):
    """Read-only doctor lookup (dual filter) — satisfied by DoctorRepository."""

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID, clinic_id: UUID) -> object | None:
        """Return the doctor or None (cross-tenant/clinic -> None)."""
        ...


def _resolve_storage_strategy() -> object:
    """Resolve the assets storage strategy (engine consume — read-only).

    Deferred import: avoids engine env validation at module load time
    (pattern from assets_proxy_router — PLC0415 accepted per codebase).
    Module-level indirection so tests can monkeypatch the strategy.
    """
    from luana_core_assets.infrastructure.storage import get_storage_strategy  # noqa: PLC0415

    return get_storage_strategy()


class BioFileService:
    """Application service for doctor bio file register/list/delete/download.

    Orchestrates: doctor existence check (dual filter) -> repo mutation ->
    audit log SYNC write pre-response. No business logic leaks to the router.
    """

    def __init__(
        self,
        bio_file_repo: "DoctorBioFileRepository",
        doctor_repo: _DoctorLookupPort,
        audit_repo: AuditLogRepository,
    ) -> None:
        """Initialize with injected dependencies.

        Args:
            bio_file_repo: DoctorBioFileRepository (dual filter + soft delete).
            doctor_repo: Read-only doctor lookup (DoctorRepository in production).
            audit_repo: AuditLogRepository for sync audit writes.
        """
        self._repo = bio_file_repo
        self._doctors = doctor_repo
        self._audit = audit_repo

    # ── Register (SC-D3B-1) ───────────────────────────────────────────────────

    async def register_file(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        user_id: UUID,
        storage_key: str,
        filename: str,
        size_bytes: int,
        content_type: str,
    ) -> DoctorBioFile | None:
        """Register an uploaded bio file for a doctor.

        Called AFTER /assets/upload (kind=bio_doc) returned the storage key.

        Returns:
            The persisted DoctorBioFile, or None when the doctor does not
            exist under tenant+clinic (router maps to 404 generic).

        Raises:
            ValueError: Invalid metadata (size/content_type/filename) -> 422.
        """
        doctor = await self._doctors.get_by_id(doctor_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if doctor is None:
            await self._write_cross_tenant_audit(
                tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id, resource_id=doctor_id
            )
            return None

        bio_file = DoctorBioFile(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            storage_key=storage_key,
            filename=filename,
            size_bytes=size_bytes,
            content_type=content_type,
        )
        saved = await self._repo.add(bio_file, tenant_id=tenant_id, clinic_id=clinic_id)

        # Audit SYNC pre-response (HIPAA-lite mandatory)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.bio_file_added",
                resource_type="doctor_bio_file",
                resource_id=saved.id,
            )
        )
        logger.info(
            "bio_file_registered",
            bio_file_id=str(saved.id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            size_bytes=size_bytes,
        )
        return saved

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_files(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
    ) -> list[DoctorBioFile]:
        """List active bio files for a doctor (dual filter, newest first)."""
        return await self._repo.list_for_doctor(tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)

    # ── Delete (SC-D3B-2 · RN-D3B-1) ──────────────────────────────────────────

    async def delete_file(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        file_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft-delete a bio file. RN-D3B-1: doctor bio snapshot untouched.

        Returns:
            True on delete; False when absent/cross-tenant/doctor mismatch
            (router maps to 404 generic).
        """
        existing = await self._repo.get_by_id(file_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if existing is None or existing.doctor_id != doctor_id:
            await self._write_cross_tenant_audit(
                tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id, resource_id=file_id
            )
            return False

        deleted = await self._repo.soft_delete(file_id, tenant_id=tenant_id, clinic_id=clinic_id, doctor_id=doctor_id)
        if not deleted:
            return False

        # Audit SYNC pre-response (HIPAA-lite mandatory)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.bio_file_deleted",
                resource_type="doctor_bio_file",
                resource_id=file_id,
            )
        )
        logger.info(
            "bio_file_deleted",
            bio_file_id=str(file_id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
        )
        return True

    # ── Download (SC-D3B-4 · D-1 stream proxy) ────────────────────────────────

    async def download_file(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        doctor_id: UUID,
        file_id: UUID,
        user_id: UUID,
    ) -> tuple[DoctorBioFile, bytes] | None:
        """Fetch bio file metadata + bytes from the storage backend.

        Works with BOTH backends (local/R2) via StorageStrategy.get_file_bytes.

        Returns:
            (bio_file, content) or None when absent/cross-tenant (router 404).

        Raises:
            BioFileStorageError: Storage backend failure (router maps 503).
        """
        existing = await self._repo.get_by_id(file_id, tenant_id=tenant_id, clinic_id=clinic_id)
        if existing is None or existing.doctor_id != doctor_id:
            await self._write_cross_tenant_audit(
                tenant_id=tenant_id, clinic_id=clinic_id, user_id=user_id, resource_id=file_id
            )
            return None

        strategy = _resolve_storage_strategy()
        try:
            content: bytes = strategy.get_file_bytes(existing.storage_key)  # type: ignore[attr-defined]
        except Exception as exc:
            logger.exception(
                "bio_file_storage_read_failed",
                bio_file_id=str(file_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            raise BioFileStorageError(str(exc)) from exc

        # Audit SYNC pre-response (HIPAA-lite mandatory — download is an access)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.bio_file_downloaded",
                resource_type="doctor_bio_file",
                resource_id=file_id,
            )
        )
        logger.info(
            "bio_file_downloaded",
            bio_file_id=str(file_id),
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            size_bytes=len(content),
        )
        return existing, content

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _write_cross_tenant_audit(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        resource_id: UUID,
    ) -> None:
        """Audit a not-found/cross-tenant access attempt (HIPAA-lite audit-on-404)."""
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="cross_tenant_attempt",
                resource_type="doctor_bio_file",
                resource_id=resource_id,
            )
        )
        logger.warning(
            "bio_file_not_found_or_cross_tenant",
            resource_id=str(resource_id),
            tenant_id=str(tenant_id),
        )
