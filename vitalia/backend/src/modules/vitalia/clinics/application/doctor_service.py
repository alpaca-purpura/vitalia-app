# cap: clinics.lisa.doctores
"""DoctorService — application service orchestrating Doctor CRUD.

HIPAA-lite rules (vitalia/.claude/rules/hipaa-lite.md):
  - Audit log write SYNC (awaited) BEFORE response on every mutation
  - cross_tenant_attempt audit on get_by_id returning None
  - Dual filter enforced by DoctorRepository (PhiRepositoryBase)
  - Telemetry FIRE-FORGET (post-commit, best-effort via GrowthStudioEmitter)

Error classes:
  - DniConflictError → HTTP 409 (SC-5 race)
  - CredentialValidationError → HTTP 422 (SC-2, re-raised from validator)
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia._shared.repositories.audit_log_repository import (
    AuditLogEntry,
    AuditLogRepository,
)
from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
from src.modules.vitalia.clinics.application.credential_validator import (
    validate_credential,
)
from src.modules.vitalia.clinics.application.ports.doctor_repo_port import DoctorRepoPort
from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile
from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (
    compute_dni_hash,
)

logger = structlog.get_logger()


class DniConflictError(Exception):
    """Raised when a Doctor with the same DNI already exists in the tenant.

    Maps to HTTP 409 Conflict (SC-5 duplicate DNI race condition).

    Attributes:
        message: Spanish neutro LatAm user message.
    """

    def __init__(self, message: str = "Ya existe un médico con ese DNI en esta clínica.") -> None:
        self.message = message
        super().__init__(message)


class DoctorNotFoundError(Exception):
    """Raised when a Doctor is not found (dual-filter miss)."""


class DoctorService:
    """Application service for Doctor CRUD operations.

    Orchestrates: validate → persist → audit (sync) → telemetry (fire-forget).
    Transaction boundary: one session per request; audit + mutation in same session.
    """

    def __init__(
        self,
        doctor_repo: DoctorRepoPort,
        audit_repo: AuditLogRepository,
        emitter: GrowthStudioEmitter | None = None,
    ) -> None:
        """Initialize DoctorService with injected dependencies.

        Args:
            doctor_repo: Doctor repository (DoctorRepository in production).
            audit_repo: AuditLogRepository for sync audit writes.
            emitter: GrowthStudioEmitter for fire-forget telemetry (optional).
        """
        self._repo = doctor_repo
        self._audit = audit_repo
        self._emitter = emitter

    async def create_doctor(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        first_name: str,
        last_name: str,
        dni: str,
        email: str,
        phone: str | None,
        specialty: str | None,
        credential: str,
        credential_country: str,
        years_experience: int | None = None,
        languages: list[str] | None = None,
    ) -> Doctor:
        """Create a new Doctor, validate credential, check DNI uniqueness.

        Steps:
        1. Validate credential (CredentialValidationError → 422)
        2. Check DNI hash uniqueness (DniConflictError → 409)
        3. Persist Doctor via repo (PII encrypted by repo)
        4. Write audit log SYNC (doctor.created)
        5. Emit telemetry FIRE-FORGET (lisa_staff_doctor_created)

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: Actor user UUID (for audit log).
            first_name: Doctor first name.
            last_name: Doctor last name.
            dni: Raw DNI (encrypted by repo).
            email: Professional email (encrypted by repo).
            phone: Mobile phone (optional, encrypted by repo).
            specialty: Medical specialty string.
            credential: Credential number.
            credential_country: ISO-2: PE, AR, MX, CL.
            years_experience: Optional years of experience.
            languages: List of ISO-639-1 language codes.

        Returns:
            Persisted Doctor entity.

        Raises:
            CredentialValidationError: Invalid credential format.
            DniConflictError: DNI already registered in this tenant.
        """
        # 1. Validate credential (raises CredentialValidationError → 422)
        validate_credential(credential, credential_country)

        # 2. Check DNI uniqueness via hash (no plaintext comparison)
        # We need the KEK to compute the hash — get from repo's KEK client
        # Use repo's validate_dual_filter to get KEK through repo method
        # The hash is computed in the repository layer; here we delegate to
        # get_by_dni_hash which internally uses repo's KEK
        # To avoid exposing KEK here, we call repo.get_by_dni_hash
        # (repo handles encryption internally)
        existing = await self._repo.get_by_dni_hash(
            _compute_local_hash(dni, self._repo),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        if existing is not None:
            raise DniConflictError()

        # 3. Build domain entity
        doctor = Doctor(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            first_name=first_name,
            last_name=last_name,
            dni=dni,
            email=email,
            phone=phone,
            specialty=specialty,
            credential=credential,
            credential_country=credential_country,
            years_experience=years_experience,
            languages=languages or [],
        )

        # 4. Persist (pgcrypto encryption happens in repo)
        saved = await self._repo.create(doctor, tenant_id=tenant_id, clinic_id=clinic_id)

        # 5. Audit log SYNC (mandatory — HIPAA-lite § Audit log)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.created",
                resource_type="doctor",
                resource_id=saved.id,
            )
        )

        # 6. Telemetry FIRE-FORGET (post-commit, best-effort)
        if self._emitter is not None:
            try:
                await self._emitter.emit_event(
                    event_type="lisa_staff_doctor_created",
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=user_id,
                    entity_id=saved.id,
                    props={"specialty": specialty, "country": credential_country},
                )
            except Exception:  # noqa: BLE001
                pass  # fire-forget

        logger.info(
            "doctor_created",
            doctor_id=str(saved.id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )
        return saved

    async def get_doctor(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> Doctor | None:
        """Retrieve a Doctor by ID with dual filter.

        Returns None (404) if not found OR if belongs to different tenant/clinic.
        Cross-tenant access returns None + writes audit cross_tenant_attempt.

        Args:
            doctor_id: Doctor UUID.
            tenant_id: Requesting tenant UUID.
            clinic_id: Requesting clinic UUID.
            user_id: Actor user UUID (for audit log).

        Returns:
            Doctor entity or None.
        """
        doctor = await self._repo.get_by_id(
            doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        if doctor is None:
            # Write cross_tenant_attempt audit (HIPAA-lite requires audit on 404)
            await self._audit.write(
                AuditLogEntry(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=user_id,
                    action="cross_tenant_attempt",
                    resource_type="doctor",
                    resource_id=doctor_id,
                )
            )
            logger.warning(
                "doctor_not_found_or_cross_tenant",
                doctor_id=str(doctor_id),
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )

        return doctor

    async def list_doctors(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        q: str | None = None,
        specialty: str | None = None,
        active: bool | None = None,
        page: int = 1,
        page_size: int = 24,
    ) -> tuple[list[Doctor], int]:
        """List doctors with filtering and pagination.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            q: Optional free-text search over first/last name + specialty.
            specialty: Filter by specialty.
            active: Filter by active status.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Tuple of (list[Doctor], total_count).
        """
        doctors = await self._repo.list_by_filter(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            q=q,
            specialty=specialty,
            active=active,
            page=page,
            page_size=page_size,
        )
        total = await self._repo.count_by_filter(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            q=q,
            active=active,
            specialty=specialty,
        )
        return doctors, total

    async def update_doctor(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        # Patchable fields
        phone: str | None = None,
        bio_inputs_notes: str | None = None,
        bio_links: list[str] | None = None,
        bio_public: BioPublic | None = None,
        avatar_key: str | None = None,
        visible_en_landing: bool | None = None,
        active: bool | None = None,
        specialty: str | None = None,
        years_experience: int | None = None,
        languages: list[str] | None = None,
    ) -> Doctor | None:
        """Patch a Doctor's mutable fields.

        Writes audit `doctor.updated` or `doctor.deactivated` sync pre-response.

        Returns:
            Updated Doctor or None if not found.
        """
        existing = await self._repo.get_by_id(
            doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        if existing is None:
            return None

        # Build updated entity (patch style — keep existing if not provided)
        import dataclasses  # noqa: PLC0415

        updated = dataclasses.replace(
            existing,
            phone=phone if phone is not None else existing.phone,
            bio_inputs_notes=bio_inputs_notes if bio_inputs_notes is not None else existing.bio_inputs_notes,
            bio_links=bio_links if bio_links is not None else existing.bio_links,
            bio_public=bio_public if bio_public is not None else existing.bio_public,
            avatar_key=avatar_key if avatar_key is not None else existing.avatar_key,
            visible_en_landing=(visible_en_landing if visible_en_landing is not None else existing.visible_en_landing),
            active=active if active is not None else existing.active,
            specialty=specialty if specialty is not None else existing.specialty,
            years_experience=(years_experience if years_experience is not None else existing.years_experience),
            languages=languages if languages is not None else existing.languages,
        )

        saved = await self._repo.update(updated, tenant_id=tenant_id, clinic_id=clinic_id)

        # Determine action label for audit
        action = "doctor.deactivated" if (active is False and existing.active) else "doctor.updated"

        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action=action,
                resource_type="doctor",
                resource_id=doctor_id,
            )
        )

        return saved

    async def deactivate_doctor(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Soft-deactivate a Doctor (active=False).

        Writes audit `doctor.deactivated` sync.

        Returns:
            True if deactivated, False if not found.
        """
        existing = await self._repo.get_by_id(
            doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        if existing is None:
            return False

        await self._repo.soft_deactivate(
            doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )

        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.deactivated",
                resource_type="doctor",
                resource_id=doctor_id,
            )
        )
        return True

    async def generate_public_profile(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        profile: DoctorPublicProfile,
        public_slug: str | None = None,
    ) -> Doctor | None:
        """Persist generated public profile for a doctor.

        Writes bio_generated_at = utc_now() + public_profile + public_slug.
        Writes audit `doctor.profile_generated` SYNC (hipaa-lite.md § Audit log).

        bio_generated_at ONLY updated here (RN-D3B-4 — not in update_doctor).

        Args:
            doctor_id: Doctor UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: Actor user UUID (for audit log).
            profile: Structured DoctorPublicProfile to persist.
            public_slug: Optional URL-safe slug. If None, uses doctor's existing slug or None.

        Returns:
            Updated Doctor entity or None if not found.
        """
        bio_generated_at = datetime.now(tz=timezone.utc)

        updated = await self._repo.update_public_profile(
            doctor_id=doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            public_profile=profile,
            bio_generated_at=bio_generated_at,
            public_slug=public_slug,
        )

        # Audit log SYNC (mandatory — HIPAA-lite § Audit log + shell-feature-arch constraint 6)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.profile_generated",
                resource_type="doctor",
                resource_id=doctor_id,
            )
        )

        logger.info(
            "doctor_profile_generated",
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )
        return updated

    async def patch_public_profile(
        self,
        *,
        doctor_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        profile: DoctorPublicProfile,
    ) -> Doctor | None:
        """Persist manually-edited public profile sections WITHOUT touching bio_generated_at.

        RN-D3B-4: bio_generated_at is ONLY set by generate-profile, NEVER here.
        Writes audit `doctor.public_profile_updated` SYNC (hipaa-lite.md § Audit log).

        Args:
            doctor_id: Doctor UUID.
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID.
            user_id: Actor user UUID (for audit log).
            profile: Updated DoctorPublicProfile sections to persist.

        Returns:
            Updated Doctor entity or None if not found (dual filter miss).
        """
        updated = await self._repo.update_public_profile_sections(
            doctor_id=doctor_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            public_profile=profile,
        )

        # Audit log SYNC (mandatory — HIPAA-lite § Audit log + shell-feature-arch constraint 6)
        await self._audit.write(
            AuditLogEntry(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                user_id=user_id,
                action="doctor.public_profile_updated",
                resource_type="doctor",
                resource_id=doctor_id,
            )
        )

        logger.info(
            "doctor_public_profile_updated",
            doctor_id=str(doctor_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
        )
        return updated


def _slugify(text: str) -> str:
    """Convert display_name to URL-safe slug.

    Example: 'Dra. María González' → 'dra-maria-gonzalez'.
    """
    # Normalize unicode (decompose accents)
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    lower = ascii_text.lower()
    # Replace non-alphanumeric with hyphen
    slug = re.sub(r"[^a-z0-9]+", "-", lower)
    # Strip leading/trailing hyphens
    return slug.strip("-")


def _compute_local_hash(dni: str, repo: DoctorRepoPort) -> str:
    """Compute DNI hash using repo's KEK.

    Accesses _kek attribute only if repo is a DoctorRepository concrete instance.
    This avoids exposing KEK through the port interface.
    """
    from src.modules.vitalia.clinics.infrastructure.repositories.doctor_repository import (  # noqa: PLC0415
        DoctorRepository,
    )

    if isinstance(repo, DoctorRepository):
        kek_val = repo._kek.get_key()
        return compute_dni_hash(dni, kek_val)

    # For mock repos in tests, return a placeholder hash
    # (test should mock get_by_dni_hash to return the expected result)
    return compute_dni_hash(dni, "0" * 64)
