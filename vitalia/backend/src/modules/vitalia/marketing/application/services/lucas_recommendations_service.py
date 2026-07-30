# cap: marketing.lucas-stage-recommendations
# story-origin: TBD
"""LucasRecommendationsService — state machine for marketing recommendations.

Application layer — orchestrates:
  - Repository (LucasRecommendationRepository, dual-scope CompoundScopeRepositoryBase)
  - Audit log (AsyncAuditWriter — SYNC write BEFORE response, HIPAA mandate)
  - Domain events (outbox adapter_bus publish AFTER audit)

State machine:
  OPEN → APPROVED: approve() — sets undo_until = now + 5 min
  OPEN → REJECTED: reject() — records reason
  APPROVED → OPEN: undo() — only within 5-minute undo window
  OPEN → EXPIRED: expire() — cron-only

Validation:
  - action_payload_json.budget_amount_cents must be <= 100_000_00 (100k limit)
  - Idempotency: re-approving raises InvalidStateTransitionError

HIPAA-lite:
  - Dual filter: tenant_id + clinic_id on all queries.
  - Audit log written SYNC before returning (AsyncAuditWriter.write() awaited).
  - No PHI in audit log payloads (recommendation IDs only).

downstream-regression-na: brand-local marketing application service (vitalia-only)
"""

from __future__ import annotations

import uuid
from uuid import UUID

import structlog

from src.modules.vitalia.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)
from src.modules.vitalia.marketing.domain.entities.lucas_recommendation import LucasRecommendation
from src.modules.vitalia.marketing.domain.enums import BowtieStage, RecommendationStatus, RejectReason
from src.modules.vitalia.marketing.domain.events import (
    LucasRecommendationApproved,
    LucasRecommendationRejected,
    LucasRecommendationUndone,
)

# Outbox adapter_bus per anti-duplication.md — use core engine, never reimplement
try:
    from luana_core_events.outbox import adapter_bus  # type: ignore[import]
except ImportError:  # pragma: no cover — available in runtime
    import structlog as _structlog

    _fb_logger = _structlog.get_logger()

    class _FallbackBus:  # type: ignore[no-redef]
        """No-op fallback bus for dev environments without luana_core_events installed."""

        async def publish(self, event: object) -> None:  # noqa: D102
            _fb_logger.warning("adapter_bus.fallback_publish", event=repr(event))

    adapter_bus = _FallbackBus()

logger = structlog.get_logger()

# Maximum allowed budget amount in cents per SC-MK-04 range validation
_MAX_BUDGET_AMOUNT_CENTS = 100_000_00  # 100,000 USD in cents


class LucasRecommendationsService:
    """Application service for Lucas marketing recommendation lifecycle.

    Responsibilities:
      - list_open_by_stage(): surface OPEN recommendations for a bowtie stage
      - approve(): OPEN → APPROVED + audit + outbox
      - reject(): OPEN → REJECTED + audit + outbox
      - undo(): APPROVED → OPEN within 5-min window + audit + outbox

    All write operations enforce:
      1. Domain entity state machine (raises on invalid transitions)
      2. Action payload validation (range checks per SC-MK-04)
      3. Audit log write (SYNC, BEFORE returning — HIPAA-lite mandate)
      4. Outbox event publish (AFTER audit)
    """

    def __init__(
        self,
        *,
        repo: object,
        audit_writer: object,
    ) -> None:
        """Initialise with DI'd dependencies.

        Args:
            repo: LucasRecommendationRepository (CompoundScopeRepositoryBase subclass).
            audit_writer: AsyncAuditWriter instance (async .write() method).
        """
        self._repo = repo
        self._audit_writer = audit_writer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_open_by_stage(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: BowtieStage,
        limit: int = 3,
    ) -> list[LucasRecommendationModel]:
        """Return OPEN recommendations for a bowtie stage.

        Dual filter: tenant_id + clinic_id (HIPAA-lite mandate).

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (second scope filter).
            stage: BowtieStage enum value to filter by.
            limit: Maximum recommendations to return (default 3).

        Returns:
            List of LucasRecommendationModel ordered by priority DESC.
        """
        results = await self._repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=stage,
            limit=limit,
        )
        logger.info(
            "lucas_recommendations.list_open_by_stage",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            stage=stage.value,
            count=len(results),
        )
        return results

    async def approve(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> LucasRecommendationModel:
        """Approve an OPEN recommendation.

        Flow:
          1. Load recommendation (dual filter — raises 404 if not found or wrong scope).
          2. Validate action_payload range (SC-MK-04).
          3. Apply domain entity state machine (raises InvalidStateTransitionError if not OPEN).
          4. Save updated model.
          5. Write audit log SYNC (HIPAA-lite mandate — BEFORE returning).
          6. Publish LucasRecommendationApproved outbox event.
          7. Return updated model.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            recommendation_id: UUID of the recommendation to approve.
            user_id: UUID of the user performing the approval.

        Returns:
            Updated LucasRecommendationModel with status=APPROVED.

        Raises:
            ValueError: If action_payload budget_amount_cents exceeds limit (SC-MK-04).
            InvalidStateTransitionError: If recommendation is not in OPEN status.
            ExpiredRecommendationError: If recommendation has expired.
        """
        model = await self._repo.get_by_id(
            id=recommendation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )

        # SC-MK-04: validate action_payload range BEFORE state transition
        self._validate_action_payload(model)

        # Domain entity state machine (raises on invalid transition)
        entity = self._model_to_entity(model)
        entity.approve(user_id=user_id)

        # Persist changes back to model
        model = self._apply_entity_to_model(model, entity)
        model = await self._repo.save(model)

        # HIPAA-lite: audit log SYNC before returning (mandatory)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="lucas_recommendation.approve",
            resource_type="lucas_recommendation",
            resource_id=recommendation_id,
            payload={"recommendation_id": str(recommendation_id), "status": "approved"},
        )

        # Outbox event after audit
        event = LucasRecommendationApproved(
            tenant_id=tenant_id,
            recommendation_id=recommendation_id,
            approved_by_user_id=user_id,
        )
        await adapter_bus.publish(event)

        logger.info(
            "lucas_recommendation.approved",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            recommendation_id=str(recommendation_id),
            user_id=str(user_id),
        )

        return model

    async def reject(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        recommendation_id: UUID,
        user_id: UUID,
        reason: RejectReason,
    ) -> LucasRecommendationModel:
        """Reject an OPEN recommendation.

        Flow:
          1. Load recommendation (dual filter).
          2. Apply domain entity state machine (raises if not OPEN).
          3. Save updated model.
          4. Write audit log SYNC (HIPAA-lite mandate).
          5. Publish LucasRecommendationRejected outbox event.
          6. Return updated model.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            recommendation_id: UUID of the recommendation to reject.
            user_id: UUID of the user performing the rejection.
            reason: RejectReason enum value.

        Returns:
            Updated LucasRecommendationModel with status=REJECTED.

        Raises:
            InvalidStateTransitionError: If recommendation is not in OPEN status.
        """
        model = await self._repo.get_by_id(
            id=recommendation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )

        # Domain entity state machine
        entity = self._model_to_entity(model)
        entity.reject(user_id=user_id, reason=reason)

        # Persist changes
        model = self._apply_entity_to_model(model, entity)
        model = await self._repo.save(model)

        # HIPAA-lite: audit log SYNC before returning
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="lucas_recommendation.reject",
            resource_type="lucas_recommendation",
            resource_id=recommendation_id,
            payload={
                "recommendation_id": str(recommendation_id),
                "status": "rejected",
                "reason": reason.value,
            },
        )

        # Outbox event after audit
        event = LucasRecommendationRejected(
            tenant_id=tenant_id,
            recommendation_id=recommendation_id,
            rejected_by_user_id=user_id,
            reason=reason,
        )
        await adapter_bus.publish(event)

        logger.info(
            "lucas_recommendation.rejected",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            recommendation_id=str(recommendation_id),
            reason=reason.value,
        )

        return model

    async def undo(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        recommendation_id: UUID,
    ) -> LucasRecommendationModel:
        """Undo a recent approval — reverts APPROVED → OPEN within 5-min window.

        Flow:
          1. Load recommendation (dual filter).
          2. Apply domain entity undo() (raises if outside window or wrong status).
          3. Save updated model.
          4. Write audit log SYNC (HIPAA-lite mandate).
          5. Publish LucasRecommendationUndone outbox event.
          6. Return updated model.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            recommendation_id: UUID of the recommendation to undo.

        Returns:
            Updated LucasRecommendationModel with status=OPEN.

        Raises:
            UndoWindowExpiredError: If 5-minute undo window has passed.
            InvalidStateTransitionError: If recommendation is not in APPROVED status.
        """
        model = await self._repo.get_by_id(
            id=recommendation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )

        # Domain entity state machine (validates undo window)
        entity = self._model_to_entity(model)
        entity.undo()

        # Persist changes
        model = self._apply_entity_to_model(model, entity)
        model = await self._repo.save(model)

        # HIPAA-lite: audit log SYNC before returning
        # user_id not available for undo (anonymous undo) — use system sentinel
        system_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=system_user_id,
            action="lucas_recommendation.undo",
            resource_type="lucas_recommendation",
            resource_id=recommendation_id,
            payload={
                "recommendation_id": str(recommendation_id),
                "status": "open",
                "action": "undo_approval",
            },
        )

        # Outbox event after audit
        event = LucasRecommendationUndone(
            tenant_id=tenant_id,
            recommendation_id=recommendation_id,
        )
        await adapter_bus.publish(event)

        logger.info(
            "lucas_recommendation.undone",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            recommendation_id=str(recommendation_id),
        )

        return model

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_action_payload(model: LucasRecommendationModel) -> None:
        """Validate action_payload_json fields against business rules.

        SC-MK-04: budget_amount_cents must not exceed 100_000_00 (100k).

        Args:
            model: LucasRecommendationModel to validate.

        Raises:
            ValueError: If budget_amount_cents exceeds limit (Spanish message per spanish-text.md).
        """
        payload = model.action_payload_json or {}
        budget_cents = payload.get("budget_amount_cents")
        if budget_cents is not None and int(budget_cents) > _MAX_BUDGET_AMOUNT_CENTS:
            raise ValueError(
                f"El presupuesto solicitado excede el límite permitido de "
                f"{_MAX_BUDGET_AMOUNT_CENTS // 100:,} en su moneda local. "
                f"Revisa el monto e intenta de nuevo."
            )

    @staticmethod
    def _model_to_entity(model: LucasRecommendationModel) -> LucasRecommendation:
        """Map infrastructure model to domain entity for state machine operations.

        Handles enum value conversion (model stores strings, entity uses enums).
        """
        return LucasRecommendation(
            id=model.id,
            tenant_id=model.tenant_id,
            clinic_id=model.clinic_id,
            stage=BowtieStage(model.stage),
            recommendation_kind=model.recommendation_kind,
            title=model.title,
            body=model.body,
            rationale_json=model.rationale_json or {},
            priority=model.priority,
            status=RecommendationStatus(model.status),
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            action_payload_json=model.action_payload_json,
            confidence_pct=model.confidence_pct,
            projected_impact_text=model.projected_impact_text,
            approved_by_user_id=model.approved_by_user_id,
            approved_at=model.approved_at,
            undo_until=model.undo_until,
            rejected_by_user_id=model.rejected_by_user_id,
            rejected_at=model.rejected_at,
            reject_reason=(RejectReason(model.reject_reason) if model.reject_reason else None),
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _apply_entity_to_model(
        model: LucasRecommendationModel,
        entity: LucasRecommendation,
    ) -> LucasRecommendationModel:
        """Copy mutated entity fields back to the infrastructure model.

        Only updates mutable state fields — does not overwrite identity/meta.
        """
        model.status = entity.status.value
        model.approved_by_user_id = entity.approved_by_user_id
        model.approved_at = entity.approved_at
        model.undo_until = entity.undo_until
        model.rejected_by_user_id = entity.rejected_by_user_id
        model.rejected_at = entity.rejected_at
        model.reject_reason = entity.reject_reason.value if entity.reject_reason else None
        model.updated_at = entity.updated_at
        return model
