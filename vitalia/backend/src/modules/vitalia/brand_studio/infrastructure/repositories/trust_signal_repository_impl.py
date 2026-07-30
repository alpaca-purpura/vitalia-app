# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""TrustSignalRepositoryImpl — stores trust signals in tenant.config_json JSONB.

Tenant isolation: every operation scoped to tenant_id.
Soft deletes only (deleted_at set in JSONB entry).
Uses run_sync bridge to call sync engine BrandRepository from async context.

downstream-regression-na: brand-local repo impl vitalia
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.modules.vitalia.brand_studio.domain.trust_signal import TrustSignal
from src.modules.vitalia.brand_studio.infrastructure.repositories.trust_signal_repository import (
    TrustSignalRepository,
)

logger = structlog.get_logger()

_CONFIG_KEY = "vitalia_trust_signals"


def _entry_to_domain(entry: dict[str, Any]) -> TrustSignal:
    """Map JSONB entry to domain entity."""
    deleted_raw = entry.get("deleted_at")
    deleted_at = datetime.fromisoformat(deleted_raw) if deleted_raw else None
    created_raw = entry.get("created_at", datetime.now(timezone.utc).isoformat())
    return TrustSignal(
        id=UUID(entry["id"]),
        tenant_id=UUID(entry["tenant_id"]),
        label=entry.get("label", ""),
        catalog_code=entry.get("catalog_code"),
        logo_url=entry.get("logo_url"),
        issued_year=entry.get("issued_year"),
        deleted_at=deleted_at,
        created_at=datetime.fromisoformat(created_raw),
    )


def _domain_to_entry(signal: TrustSignal) -> dict[str, Any]:
    """Map domain entity to JSONB entry."""
    entry: dict[str, Any] = {
        "id": str(signal.id),
        "tenant_id": str(signal.tenant_id),
        "label": signal.label,
        "catalog_code": signal.catalog_code,
        "logo_url": signal.logo_url,
        "issued_year": signal.issued_year,
        "created_at": signal.created_at.isoformat(),
        "deleted_at": signal.deleted_at.isoformat() if signal.deleted_at else None,
    }
    return entry


class TrustSignalRepositoryImpl(TrustSignalRepository):
    """JSONB-backed trust signal repository.

    Stores signals in tenant.config_json['vitalia_trust_signals'] as list of dicts.
    Uses async SQLAlchemy (select + update directly on TenantModel).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with async SQLAlchemy session.

        Args:
            session: AsyncSession from FastAPI DI.
        """
        self._session = session

    async def _get_tenant_model(self, tenant_id: UUID) -> Any:
        """Load TenantModel for this tenant (raw access for config_json mutation)."""
        from luana_core_iam.infrastructure.models.tenant_model import TenantModel  # noqa: PLC0415

        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_for_tenant(self, *, tenant_id: UUID) -> list[TrustSignal]:
        """Return all active trust signals for a tenant."""
        tenant = await self._get_tenant_model(tenant_id)
        if not tenant:
            return []
        config = tenant.config_json or {}
        entries: list[dict[str, Any]] = config.get(_CONFIG_KEY, [])
        signals = [_entry_to_domain(e) for e in entries if not e.get("deleted_at")]
        logger.debug(
            "trust_signal_list",
            tenant_id=str(tenant_id),
            count=len(signals),
        )
        return signals

    async def create(self, signal: TrustSignal) -> TrustSignal:
        """Persist a new trust signal in tenant config JSONB."""
        tenant = await self._get_tenant_model(signal.tenant_id)
        if not tenant:
            msg = f"Tenant {signal.tenant_id} not found"
            raise ValueError(msg)

        config: dict[str, Any] = dict(tenant.config_json or {})
        entries: list[dict[str, Any]] = list(config.get(_CONFIG_KEY, []))

        now = datetime.now(timezone.utc)
        new_signal = TrustSignal(
            id=signal.id if signal.id else uuid4(),
            tenant_id=signal.tenant_id,
            label=signal.label,
            catalog_code=signal.catalog_code,
            logo_url=signal.logo_url,
            issued_year=signal.issued_year,
            created_at=now,
        )
        entries.append(_domain_to_entry(new_signal))
        config[_CONFIG_KEY] = entries
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        await self._session.flush()
        logger.info(
            "trust_signal_created",
            signal_id=str(new_signal.id),
            tenant_id=str(signal.tenant_id),
            catalog_code=signal.catalog_code,
        )
        return new_signal

    async def soft_delete(
        self,
        signal_id: UUID,
        *,
        tenant_id: UUID,
    ) -> None:
        """Soft-delete a trust signal (set deleted_at in JSONB entry)."""
        tenant = await self._get_tenant_model(tenant_id)
        if not tenant:
            return

        config: dict[str, Any] = dict(tenant.config_json or {})
        entries: list[dict[str, Any]] = list(config.get(_CONFIG_KEY, []))

        now = datetime.now(timezone.utc).isoformat()
        updated = False
        for entry in entries:
            if entry.get("id") == str(signal_id) and not entry.get("deleted_at"):
                entry["deleted_at"] = now
                updated = True
                break

        if updated:
            config[_CONFIG_KEY] = entries
            tenant.config_json = config
            flag_modified(tenant, "config_json")
            await self._session.flush()
            logger.info(
                "trust_signal_soft_deleted",
                signal_id=str(signal_id),
                tenant_id=str(tenant_id),
            )

    async def get_by_id(
        self,
        signal_id: UUID,
        *,
        tenant_id: UUID,
    ) -> TrustSignal | None:
        """Retrieve trust signal by ID and tenant."""
        signals = await self.list_for_tenant(tenant_id=tenant_id)
        for s in signals:
            if s.id == signal_id:
                return s
        return None
