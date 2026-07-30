# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""Repositorio de planes de tratamiento — fidelización vitalia.

Hereda CompoundScopeRepositoryBase (engine) con scope_field="clinic_id".
Dual filter HIPAA-lite: tenant_id + clinic_id en TODA query.

Ver: core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py
     vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.fidelizacion.infrastructure.models.treatment_plan_model import (
    TreatmentPlanModel,
)

logger = structlog.get_logger(__name__)


class TreatmentPlanRepository(CompoundScopeRepositoryBase[TreatmentPlanModel, UUID]):
    """Repositorio async para vitalia_treatment_plans con dual-scope HIPAA-lite.

    scope_field="clinic_id" — filtro secundario obligatorio (HIPAA-lite).
    Todas las queries aplican tenant_id + clinic_id (sin excepción).
    Soft delete: excluye registros con deleted_at IS NOT NULL.
    """

    MODEL = TreatmentPlanModel

    def __init__(self, *, session: AsyncSession, scope_field: str = "clinic_id") -> None:
        """Inicializa el repositorio con scope_field='clinic_id' para HIPAA-lite."""
        super().__init__(session=session, scope_field=scope_field)

    async def save(self, model: TreatmentPlanModel) -> TreatmentPlanModel:
        """Persiste un plan de tratamiento nuevo o actualizado.

        Args:
            model: Instancia ORM a persistir.

        Returns:
            El modelo persistido (con id asignado si nuevo).
        """
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "treatment_plan_saved",
            plan_id=str(model.id),
            tenant_id=str(model.tenant_id),
            clinic_id=str(model.clinic_id),
            patient_id=str(model.patient_id),
            status=model.status,
        )
        return model

    async def list_for_patient(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        patient_id: UUID,
        include_completed: bool = True,
    ) -> list[TreatmentPlanModel]:
        """Lista los planes de tratamiento de un paciente en la clínica.

        HIPAA-lite: dual filter tenant_id + clinic_id SIEMPRE aplicado.

        Args:
            tenant_id: UUID del tenant (filtro raíz multitenant).
            clinic_id: UUID de la clínica (filtro secundario HIPAA-lite).
            patient_id: UUID del paciente.
            include_completed: Si True, incluye planes completados/abandonados.

        Returns:
            Lista de TreatmentPlanModel, vacía si no hay resultados.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.patient_id == patient_id)
            .where(self.MODEL.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
