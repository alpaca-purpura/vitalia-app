# cap: configuracion.cuenta
"""ClinicConfigRepository — reads/writes clinic_config JSONB in the engine tenant model.

Pattern: read-modify-write on `tenant.config_json["clinic_config"]`.
Imports TenantModel from luana_core_iam (engine, read-only pattern).
NEVER adds new columns to the engine — only modifies the JSONB dict.

Architecture note: This repo operates on the engine TenantModel's config_json
JSONB column, same pattern used in brand_studio/marca_service.py.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ClinicConfigRepository:
    """Read/write clinic configuration stored in tenant.config_json JSONB.

    Provides:
      - get_config: Returns clinic_config dict for a tenant
      - update_specialties: RMW primary_specialties list
      - get_dpo: Returns compliance.dpo dict (read-only)
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with async session."""
        self.db = db

    async def _get_tenant_model(self, tenant_id: UUID):  # type: ignore[return]
        """Fetch TenantModel by tenant_id. Returns None if not found."""
        # Lazy import to avoid cross-package import at module load time
        from luana_core_iam.infrastructure.models.tenant_model import (  # noqa: PLC0415
            TenantModel,
        )

        result = await self.db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        return result.scalars().first()

    async def get_config(self, tenant_id: UUID) -> dict:
        """Return clinic_config sub-dict from tenant.config_json.

        Args:
            tenant_id: Tenant to read config from.

        Returns:
            clinic_config dict, or empty dict if absent/null.
        """
        tenant = await self._get_tenant_model(tenant_id)
        if tenant is None or not tenant.config_json:
            return {}
        return tenant.config_json.get("clinic_config", {})

    async def update_specialties(self, tenant_id: UUID, specialties: list[str]) -> None:
        """RMW primary_specialties in tenant.config_json["clinic_config"].

        Reads current config_json, sets clinic_config.primary_specialties,
        and writes back via UPDATE (JSONB merge pattern).

        Args:
            tenant_id: Tenant whose specialties to update.
            specialties: New list of specialty IDs.
        """
        from luana_core_iam.infrastructure.models.tenant_model import (  # noqa: PLC0415
            TenantModel,
        )

        tenant = await self._get_tenant_model(tenant_id)
        if tenant is None:
            logger.warning("update_specialties_tenant_not_found", tenant_id=str(tenant_id))
            return

        # Read-modify-write
        existing = dict(tenant.config_json) if tenant.config_json else {}
        clinic_config = dict(existing.get("clinic_config", {}))
        clinic_config["primary_specialties"] = specialties
        existing["clinic_config"] = clinic_config

        await self.db.execute(update(TenantModel).where(TenantModel.id == tenant_id).values(config_json=existing))
        # NOTE: commit() removed — caller owns the unit-of-work (Option A fix C9-1).
        # When called from account_router (get_async_session_committing), the commit
        # happens once on clean return, atomically with update_account + audit row.
        logger.info(
            "clinic_specialties_updated",
            tenant_id=str(tenant_id),
            count=len(specialties),
        )

    async def get_dpo(self, tenant_id: UUID) -> dict | None:
        """Return compliance.dpo dict from tenant.config_json.

        Args:
            tenant_id: Tenant to read DPO config from.

        Returns:
            DPO dict (name, email, phone) or None if not configured.
        """
        tenant = await self._get_tenant_model(tenant_id)
        if tenant is None or not tenant.config_json:
            return None
        compliance = tenant.config_json.get("compliance", {})
        return compliance.get("dpo") or None
