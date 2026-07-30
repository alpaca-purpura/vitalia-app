# cap: configuracion.cuenta
"""ClinicAccountService — orchestrates account read/write for the config-cuenta surface.

Responsibilities:
  - RBAC enforcement (admin_clinic only for PATCH)
  - Fiscal ID validation per clinic's country
  - Atomic update: clinic fields + config_json specialties in same transaction
  - SYNC audit log write pre-response
  - Best-effort domain event dispatch (ClinicSpecialtiesChanged)
  - GET aggregation: clinic + config_json(specialties) + catalog

DDD Inside-Out: application layer. No FastAPI / HTTP imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

import structlog

from src.modules.vitalia._shared.catalogs.specialty_catalog import (
    SpecialtyEntry,
    get_specialties_for_country,
    validate_specialties,
)
from src.modules.vitalia._shared.validation.fiscal_id_validator import validate_fiscal_id
from src.modules.vitalia.clinics.api.dtos import (
    ClinicAccountPatchRequest,
    ClinicAccountResponse,
)
from src.modules.vitalia.clinics.domain.exceptions import ClinicNotFoundError
from src.modules.vitalia.clinics.infrastructure.repositories.clinic_config_repository import (
    ClinicConfigRepository,
)
from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
    ClinicRepository,
)

logger = structlog.get_logger()

# Roles permitted to modify account data — aligned to platform canonical
# ALLOWED_BRAND_OWNER_ROLES (_shared/auth/rbac.py): tenant account data is
# owner-level non-PHI config (same set that manages staff + marca). RN-1
# "solo admin de la clínica edita" = {owner, admin_clinic} per vitalia role
# model (real tenant owners — e.g. dr.demo — carry role="owner").
_WRITE_ROLES = frozenset(["owner", "admin_clinic"])


@dataclass
class ClinicAccountData:
    """Aggregated account view (clinic + config_json clinic_config).

    This is the domain-level aggregate used internally before serialization.
    The API layer maps this to ClinicAccountResponse.
    """

    clinic_id: UUID
    tenant_id: UUID
    name: str
    slug: str
    country: str
    timezone: str
    plan_tier: str
    is_active: bool
    legal_name: str | None = None
    fiscal_id: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    language: str = "es-419"
    currency: str | None = None
    primary_specialties: list[str] = field(default_factory=list)


class ClinicAccountService:
    """Service for clinic account read/write operations.

    Wires ClinicRepository + ClinicConfigRepository + AsyncAuditWriter.
    All writes are RBAC-gated (admin_clinic only).
    """

    def __init__(
        self,
        clinic_repo: ClinicRepository,
        config_repo: ClinicConfigRepository,
        audit_writer: object,  # AsyncAuditWriter — typed loosely to avoid circular import
    ) -> None:
        """Initialize service with injected dependencies."""
        self.clinic_repo = clinic_repo
        self.config_repo = config_repo
        self.audit_writer = audit_writer

    async def get_account(self, tenant_id: UUID) -> ClinicAccountResponse:
        """Read clinic account data for the tenant.

        Aggregates clinic identity + primary_specialties from config_json.

        Args:
            tenant_id: Tenant whose account to fetch.

        Returns:
            ClinicAccountResponse (aggregated view).

        Raises:
            ClinicNotFoundError: If no active clinic found for tenant.
        """
        clinic = await self.clinic_repo.get_active_for_tenant(tenant_id)
        if clinic is None:
            raise ClinicNotFoundError(tenant_id=tenant_id)

        config = await self.config_repo.get_config(tenant_id)
        specialties = config.get("primary_specialties", [])

        return ClinicAccountResponse(
            clinic_id=clinic.id,
            tenant_id=clinic.tenant_id,
            name=clinic.name,
            slug=clinic.slug,
            country=clinic.country,
            timezone=clinic.timezone,
            plan_tier=clinic.plan_tier,
            is_active=clinic.is_active,
            legal_name=clinic.legal_name,
            fiscal_id=clinic.fiscal_id,
            address=clinic.address,
            phone=clinic.phone,
            email=clinic.email,
            language=getattr(clinic, "language", "es-419") or "es-419",
            currency=clinic.currency,
            primary_specialties=specialties,
        )

    async def patch_account(
        self,
        tenant_id: UUID,
        user_id: UUID,
        patch: ClinicAccountPatchRequest,
        user_role: str,
        from_ip: str | None = None,
    ) -> ClinicAccountResponse:
        """Partially update clinic account data.

        RBAC: requires admin_clinic role.
        Fiscal validation: validates fiscal_id if provided + country known.
        Atomicity: clinic fields + specialties committed in same unit.
        Audit: SYNC write pre-response.

        Args:
            tenant_id: Tenant context.
            user_id: User performing the update.
            patch: Partial update fields.
            user_role: Role from X-User-Role header.
            from_ip: Request IP for audit log.

        Returns:
            Updated ClinicAccountResponse.

        Raises:
            PermissionError: If user_role not in admin_clinic.
            ClinicNotFoundError: If no active clinic found.
            FiscalIdValidationError: If fiscal_id fails country format check.
        """
        if user_role not in _WRITE_ROLES:
            raise PermissionError(f"Acceso denegado: se requiere rol admin_clinic (rol recibido: {user_role!r})")

        clinic = await self.clinic_repo.get_active_for_tenant(tenant_id)
        if clinic is None:
            raise ClinicNotFoundError(tenant_id=tenant_id)

        # Validate fiscal_id format if provided
        if patch.fiscal_id is not None:
            validate_fiscal_id(patch.fiscal_id, clinic.country)

        # Build update dict (only provided non-None fields — partial update)
        clinic_fields: dict[str, object] = {}
        for attr in ("name", "legal_name", "fiscal_id", "address", "phone", "email", "language", "currency"):
            value = getattr(patch, attr)
            if value is not None:
                clinic_fields[attr] = value

        # Capture previous specialties for event
        previous_config = await self.config_repo.get_config(tenant_id)
        previous_specialties = previous_config.get("primary_specialties", [])
        new_specialties = patch.primary_specialties

        # RN-3 / AC-4b: specialties fuera del catálogo del país → 422 (pre-persist)
        if new_specialties is not None:
            validate_specialties(new_specialties, clinic.country)

        # Update clinic fields (if any changed)
        if clinic_fields:
            clinic = await self.clinic_repo.update_account(
                tenant_id=tenant_id,
                clinic_id=clinic.id,
                **clinic_fields,
            )

        # Update specialties in config_json (if provided)
        if new_specialties is not None:
            await self.config_repo.update_specialties(
                tenant_id=tenant_id,
                specialties=new_specialties,
            )

        # SYNC audit log write — MUST complete before response (hipaa-lite)
        await self.audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic.id,
            user_id=user_id,
            action="clinic_account_patch",
            resource_type="clinic_account",
            resource_id=clinic.id,
            payload={
                "updated_fields": list(clinic_fields.keys())
                + (["primary_specialties"] if new_specialties is not None else [])
            },
            from_ip=from_ip,
        )

        # Best-effort domain event dispatch (ClinicSpecialtiesChanged)
        if new_specialties is not None and set(new_specialties) != set(previous_specialties):
            try:
                from src.modules.vitalia.clinics.domain.events import (  # noqa: PLC0415
                    ClinicSpecialtiesChanged,
                )

                event = ClinicSpecialtiesChanged(
                    tenant_id=tenant_id,
                    clinic_id=clinic.id,
                    previous_specialties=tuple(previous_specialties),
                    new_specialties=tuple(new_specialties),
                    changed_by=user_id,
                )
                logger.info(
                    "clinic_specialties_changed",
                    tenant_id=str(tenant_id),
                    clinic_id=str(clinic.id),
                    previous=previous_specialties,
                    new=new_specialties,
                )
                # Future: dispatch via EventBus
                _ = event  # consumed by logger above; bus dispatch TBD
            except Exception:  # noqa: BLE001
                logger.warning(
                    "clinic_specialties_event_dispatch_failed",
                    tenant_id=str(tenant_id),
                )

        # Build and return updated view
        final_specialties = new_specialties if new_specialties is not None else previous_specialties
        return ClinicAccountResponse(
            clinic_id=clinic.id,
            tenant_id=clinic.tenant_id,
            name=clinic.name,
            slug=clinic.slug,
            country=clinic.country,
            timezone=clinic.timezone,
            plan_tier=clinic.plan_tier,
            is_active=clinic.is_active,
            legal_name=clinic.legal_name,
            fiscal_id=clinic.fiscal_id,
            address=clinic.address,
            phone=clinic.phone,
            email=clinic.email,
            language=getattr(clinic, "language", "es-419") or "es-419",
            currency=clinic.currency,
            primary_specialties=final_specialties,
        )

    async def get_specialties_catalog(self, tenant_id: UUID) -> tuple[str | None, list[SpecialtyEntry]]:
        """Return (country, specialties) for the clinic's country.

        Returns a tuple so the router can populate SpecialtyCatalogResponse.country
        without a second get_active_for_tenant query (C9-4 fix).

        Args:
            tenant_id: Tenant whose clinic determines the country.

        Returns:
            Tuple of (country code or None, list of SpecialtyEntry).

        Raises:
            ClinicNotFoundError: If no active clinic found for tenant.
        """
        clinic = await self.clinic_repo.get_active_for_tenant(tenant_id)
        if clinic is None:
            raise ClinicNotFoundError(tenant_id=tenant_id)
        return clinic.country, get_specialties_for_country(clinic.country)

    async def get_dpo(self, tenant_id: UUID) -> dict | None:
        """Return DPO (Responsable de tratamiento) info for the tenant.

        Args:
            tenant_id: Tenant to read DPO config from.

        Returns:
            DPO dict or None if not configured.
        """
        return await self.config_repo.get_dpo(tenant_id)
