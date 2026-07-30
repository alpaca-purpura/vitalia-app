# cap: patients.nps-tracking
# story-origin: TBD
"""Repositorio de respuestas NPS — fidelización vitalia.

Hereda CompoundScopeRepositoryBase (engine) con scope_field="clinic_id".
Dual filter HIPAA-lite: tenant_id + clinic_id en TODA query.

PHI: comment BYTEA (pgcrypto — comentario libre del paciente).

Ver: core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py
     vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import (
    NPSBand,
)
from src.modules.vitalia.fidelizacion.infrastructure.models.nps_response_model import (
    NPSResponseModel,
)

logger = structlog.get_logger(__name__)


class NPSResponseRepository(CompoundScopeRepositoryBase[NPSResponseModel, UUID]):
    """Repositorio async para vitalia_nps_responses con dual-scope HIPAA-lite.

    scope_field="clinic_id" — filtro secundario obligatorio (HIPAA-lite).
    Todas las queries aplican tenant_id + clinic_id (sin excepción).
    Soft delete: excluye registros con deleted_at IS NOT NULL.
    """

    MODEL = NPSResponseModel

    def __init__(self, *, session: AsyncSession, scope_field: str = "clinic_id") -> None:
        """Inicializa el repositorio con scope_field='clinic_id' para HIPAA-lite."""
        super().__init__(session=session, scope_field=scope_field)

    async def save(self, model: NPSResponseModel) -> NPSResponseModel:
        """Persiste una respuesta NPS nueva o actualizada.

        Args:
            model: Instancia ORM a persistir.

        Returns:
            El modelo persistido.
        """
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "nps_response_saved",
            response_id=str(model.id),
            tenant_id=str(model.tenant_id),
            clinic_id=str(model.clinic_id),
            patient_id=str(model.patient_id),
            score=model.score,
            band=model.band,
        )
        return model

    async def list_for_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> list[NPSResponseModel]:
        """Lista respuestas NPS de un paciente en la clínica.

        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            patient_id: UUID del paciente.

        Returns:
            Lista de NPSResponseModel, ordenada por responded_at DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.patient_id == patient_id)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.responded_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_period(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: datetime,
        period_end: datetime,
        limit: int = 1000,
    ) -> list[NPSResponseModel]:
        """Lista respuestas NPS para un periodo de tiempo.

        Usada por NPSService.summary() para calcular estadísticas NPS.
        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            period_start: Inicio del periodo (UTC).
            period_end: Fin del periodo (UTC).
            limit: Máximo de respuestas a retornar (default 1000).

        Returns:
            Lista de NPSResponseModel en el periodo, respondidas_at DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.responded_at >= period_start)
            .where(self.MODEL.responded_at <= period_end)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.responded_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_detractors_untagged(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        limit: int = 200,
    ) -> list[NPSResponseModel]:
        """Lista detractores (score 0-6) aún no etiquetados en el inbox.

        Usada por copilot inbox classifier para priorizar atención.
        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant.
            clinic_id: UUID de la clínica.
            limit: Máximo de resultados (default 200 para procesamiento por lotes).

        Returns:
            Lista de NPSResponseModel detractores sin tag, respondidos_at DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.band == NPSBand.DETRACTOR.value)
            .where(self.MODEL.tagged_in_inbox.is_(False))
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.responded_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
