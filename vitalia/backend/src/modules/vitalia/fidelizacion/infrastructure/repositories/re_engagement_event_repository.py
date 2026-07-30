# cap: fidelizacion.re-engagement
# story-origin: TBD
"""Repositorio de eventos de re-engagement — fidelización vitalia.

Hereda CompoundScopeRepositoryBase (engine) con scope_field="clinic_id".
Dual filter HIPAA-lite: tenant_id + clinic_id en TODA query.

PHI: payload_phi BYTEA (pgcrypto). Tabla particionada por trigger_at.

Ver: core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py
     vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.re_engagement_event_model import (
    ReEngagementEventModel,
)

logger = structlog.get_logger(__name__)


class ReEngagementEventRepository(CompoundScopeRepositoryBase[ReEngagementEventModel, UUID]):
    """Repositorio async para vitalia_re_engagement_events con dual-scope HIPAA-lite.

    scope_field="clinic_id" — filtro secundario obligatorio (HIPAA-lite).
    Tabla particionada RANGE(trigger_at) — queries de throttle usan trigger_at.
    Todas las queries aplican tenant_id + clinic_id (sin excepción).
    Soft delete: excluye registros con deleted_at IS NOT NULL.
    """

    MODEL = ReEngagementEventModel

    def __init__(self, *, session: AsyncSession, scope_field: str = "clinic_id") -> None:
        """Inicializa el repositorio con scope_field='clinic_id' para HIPAA-lite."""
        super().__init__(session=session, scope_field=scope_field)

    async def save(self, model: ReEngagementEventModel) -> ReEngagementEventModel:
        """Persiste un evento de re-engagement nuevo o actualizado.

        Args:
            model: Instancia ORM a persistir.

        Returns:
            El modelo persistido (con id asignado si nuevo).
        """
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "re_engagement_event_saved",
            event_id=str(model.id),
            tenant_id=str(model.tenant_id),
            clinic_id=str(model.clinic_id),
            patient_id=str(model.patient_id),
            pattern=model.pattern,
        )
        return model

    async def list_by_pattern(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        pattern: ReEngagementPattern,
        limit: int = 100,
    ) -> list[ReEngagementEventModel]:
        """Lista eventos de re-engagement por patrón en el tenant+clínica.

        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant (filtro raíz multitenant).
            clinic_id: UUID de la clínica (filtro secundario HIPAA-lite).
            pattern: Patrón de re-engagement a filtrar.
            limit: Máximo de resultados a retornar.

        Returns:
            Lista de ReEngagementEventModel, ordenada por trigger_at DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.pattern == pattern.value)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.trigger_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_for_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> list[ReEngagementEventModel]:
        """Lista eventos de re-engagement pendientes (sin sent_at) de un paciente.

        Usada por OptOutService para cascade cancel al darse de baja.
        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.

        Returns:
            Lista de ReEngagementEventModel sin sent_at (pendientes de envío).
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.patient_id == patient_id)
            .where(self.MODEL.sent_at.is_(None))
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.trigger_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_in_period(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_days: int,
    ) -> list[ReEngagementEventModel]:
        """Lista TODOS los eventos de re-engagement en el período (cualquier patrón).

        Usada por Lucas para agregar señales cross-pattern (T-10).
        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            period_days: Ventana hacia atrás desde now() (UTC) en días.

        Returns:
            Lista de ReEngagementEventModel triggered dentro del período,
            ordenada por trigger_at DESC.
        """
        cutoff = datetime.now(UTC) - timedelta(days=period_days)
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.trigger_at >= cutoff)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.trigger_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def check_throttle(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        pattern: ReEngagementPattern,
        throttle_days: int,
    ) -> bool:
        """Verifica si el paciente recibió un re-engagement reciente (throttle check).

        Retorna True si ya se envió un evento del patrón dado dentro del periodo
        throttle_days. Se usa para evitar spam de comunicaciones.

        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.
            pattern: Patrón de re-engagement a verificar.
            throttle_days: Número de días hacia atrás a verificar.

        Returns:
            True si se detecta un envío reciente (dentro de throttle_days).
            False si el paciente puede recibir el re-engagement.
        """
        cutoff = datetime.now(UTC) - timedelta(days=throttle_days)
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.patient_id == patient_id)
            .where(self.MODEL.pattern == pattern.value)
            .where(self.MODEL.sent_at.is_not(None))
            .where(self.MODEL.sent_at >= cutoff)
            .where(self.MODEL.deleted_at.is_(None))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
