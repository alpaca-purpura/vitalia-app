# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""FunnelService — orchestrates the funnel domain operations.

Application layer — DDD Inside-Out (domain → infra → app → api).
No framework imports at this layer.

Responsibilities:
  - transition_stage(): validate machine + recompute score + optimistic lock
    + record transition audit + record activity + audit_log + telemetry + outbox event
  - get_board(): assemble BoardResponse with HOT_BOARD_STAGES columns + KPIs
  - get_frozen_list(): return congelados + decidio_no for Recuperar tab
  - get_lead_detail(): return LeadDetailResponse with score breakdown + autonomy
  - get_timeline(): return TimelineResponse (commercial, NON-PHI)
  - diagnose(): deterministic recommendation for frozen lead
  - reactivate(): clear frozen state + record activity
  - create_lead(): extend LeadService.create with funnel fields

Tenant isolation: every method requires tenant_id (no default, no bypass).
PHI firewall: Lead is non-PHI. No clinic_id dual filter. No clinical fields.

Event: lead_stage_overridden emitted via event_bus when triggered_by=manual_override
       and reason is not None. T-AG-1 (builder-agentic) subscribes to this event.

Shape of lead_stage_overridden outbox event:
  {
    "event_type": "lead_stage_overridden",
    "tenant_id": "<uuid>",
    "lead_id": "<uuid>",
    "from_stage": "<stage>",
    "to_stage": "<stage>",
    "reason": "<override context>",
    "actor_user_id": "<uuid>",
    "version_after": <int>,
  }
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import structlog

from src.modules.vitalia.crm.application.dto.board_dto import (
    BoardColumn,
    BoardKpis,
    BoardResponse,
    LeadCardDTO,
)
from src.modules.vitalia.crm.application.dto.frozen_dto import (
    DiagnoseResponse,
    FrozenLeadDTO,
    FrozenListResponse,
)
from src.modules.vitalia.crm.application.dto.lead_detail_dto import (
    AutonomyInfo,
    LeadDetailResponse,
    ScoreFactor,
)
from src.modules.vitalia.crm.application.dto.lead_dto import LeadResponse
from src.modules.vitalia.crm.application.dto.transition_dto import (
    StageTransitionResponse,
    TimelineEntry,
    TimelineResponse,
    TransitionDTO,
)
from src.modules.vitalia.crm.application.services.diagnose_service import DiagnoseService
from src.modules.vitalia.crm.application.services.lead_score_service import LeadScoreService
from src.modules.vitalia.crm.domain.exceptions import (
    InvalidTransitionError,
    ManualReservadoForbiddenError,
    ReasonRequiredError,
)
from src.modules.vitalia.crm.domain.funnel_machine import (
    HOT_BOARD_STAGES,
    STAGE_LABELS_ES,
    allowed_next_stages,
    compute_sla_state,
    is_manual_reservado_forbidden,
)
from src.modules.vitalia.crm.domain.lead import Lead

logger = structlog.get_logger()

# ── Autonomy tier constants (01-spec.md v3 § Resumen → Estado agente) ────────
_AGENT_CAN = [
    "Mover de etapa",
    "Agendar cita",
    "Enviar información del tratamiento",
    "Responder preguntas de precio",
]
_AGENT_NEEDS_OK = [
    "Aplicar descuentos",
    "Confirmar plan de pago",
    "Gestión de cobro",
    "Acceder a información clínica",
]


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _lead_to_response(lead: Lead) -> LeadResponse:
    """Map Lead domain entity to LeadResponse DTO."""
    return LeadResponse(
        id=lead.id,
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        status=lead.status,
        created_at=lead.created_at,
        stage=lead.stage,
        score=lead.score,
        temperature=lead.temperature,
        operated_by=lead.operated_by,
        channel=lead.channel,
        estimated_value=lead.estimated_value,
        currency=lead.currency,
        service_interest=lead.service_interest,
        assigned_doctor_id=lead.assigned_doctor_id,
        buying_signals=list(lead.buying_signals),
        stage_entered_at=lead.stage_entered_at,
        is_frozen=lead.is_frozen,
        frozen_reason=lead.frozen_reason,
        deposit_status=lead.deposit_status,
        version=lead.version,
    )


def _compute_days_since(dt: datetime | None) -> float:
    """Compute days since a datetime (returns 0 if None)."""
    if dt is None:
        return 0.0
    now = _utc_now()
    aware = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return max(0.0, (now - aware).total_seconds() / 86400)


class FunnelService:
    """Orchestrates funnel operations: transitions, board, frozen, diagnose, reactivate.

    Dependencies injected (no direct instantiation of repos):
      - lead_repo: LeadRepository
      - transition_repo: LeadStageTransitionRepository
      - activity_repo: LeadActivityRepository
      - emitter: GrowthStudioEmitter (fire-forget telemetry)
      - event_bus: OutboxEventBus (or AsyncMock in tests)

    All public methods require tenant_id as keyword argument.
    Raises ValueError if tenant_id is None (defense-in-depth).
    """

    def __init__(
        self,
        *,
        lead_repo: object,
        transition_repo: object,
        activity_repo: object,
        emitter: object,
        event_bus: object,
    ) -> None:
        """Initialize FunnelService with injected dependencies.

        Args:
            lead_repo: LeadRepository instance.
            transition_repo: LeadStageTransitionRepository instance.
            activity_repo: LeadActivityRepository instance.
            emitter: GrowthStudioEmitter for fire-forget telemetry.
            event_bus: Outbox event bus for domain events (lead_stage_overridden).
        """
        self._lead_repo = lead_repo
        self._transition_repo = transition_repo
        self._activity_repo = activity_repo
        self._emitter = emitter
        self._event_bus = event_bus
        self._scorer = LeadScoreService()
        self._diagnoser = DiagnoseService()

    # ── transition_stage ───────────────────────────────────────────────────

    async def transition_stage(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        to_stage: str,
        version: int,
        reason: str | None,
        triggered_by: str = "manual_override",
        actor_user_id: UUID | None = None,
    ) -> StageTransitionResponse:
        """Perform a funnel stage transition with all side-effects.

        Validates machine, recomputes score, writes audit+activity, emits
        telemetry and outbox event.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID — isolation mandatory.
            to_stage: Target stage slug.
            version: Expected version for optimistic lock.
            reason: Override context (required for backward/jump transitions, RN-4.1).
            triggered_by: Actor slug (default 'manual_override').
            actor_user_id: User performing the action (for manual overrides).

        Returns:
            StageTransitionResponse with updated lead + transition record.

        Raises:
            ValueError: If tenant_id is None or lead not found.
            InvalidTransitionError: If to_stage not in allowed_next.
            ManualReservadoForbiddenError: If trying to manually set reservado (RN-4).
            ReasonRequiredError: If backward/jump transition lacks reason.
            StaleStateError: If version mismatch (concurrent edit, SC-5).
        """
        if tenant_id is None:
            raise ValueError("FunnelService.transition_stage requires tenant_id")

        # 1. Load lead (tenant-scoped)
        lead = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if lead is None:
            # API layer maps None to 404 — no info leak
            return None  # type: ignore[return-value]

        from_stage = lead.stage

        # 2. Validate funnel machine
        allowed = allowed_next_stages(from_stage)
        if to_stage not in allowed:
            raise InvalidTransitionError(
                from_stage=from_stage,
                to_stage=to_stage,
                allowed_next=allowed,
            )

        # 3. Forbid manual reservado (RN-4)
        if is_manual_reservado_forbidden(to_stage):
            raise ManualReservadoForbiddenError()

        # 4. Require reason for backward/jump (non-adjacent) transitions
        # Adjacent = consecutive in STAGE_MACHINE order; decidio_no always OK without reason
        if to_stage != "decidio_no" and reason is None:
            # Determine if this is a backward transition
            stage_order = list(HOT_BOARD_STAGES)  # ordered forward progression
            try:
                from_idx = stage_order.index(from_stage)
                to_idx = stage_order.index(to_stage)
                is_backward = to_idx < from_idx
                is_jump = to_idx > from_idx + 1
            except ValueError:
                is_backward = False
                is_jump = False

            if is_backward or is_jump:
                raise ReasonRequiredError()

        # 5. Recompute score
        new_score, _breakdown = self._scorer.compute(lead)

        # 6. Update stage with optimistic lock (raises StaleStateError on conflict)
        updated_lead = await self._lead_repo.update_stage(
            lead_id,
            tenant_id=tenant_id,
            to_stage=to_stage,
            expected_version=version,
            score=new_score,
            actor_user_id=actor_user_id,
        )

        # 7. Record transition audit (sync pre-response)
        transition_record = await self._transition_repo.record(
            lead_id=lead_id,
            tenant_id=tenant_id,
            from_stage=from_stage,
            to_stage=to_stage,
            triggered_by=triggered_by,
            reason=reason,
            score_at_transition=new_score,
            actor_user_id=actor_user_id,
        )

        # 8. Record activity (commercial micro-log)
        stage_label = STAGE_LABELS_ES.get(to_stage, to_stage)
        actor_label = "manual" if triggered_by == "manual_override" else "el agente Adrián"
        description = f"Etapa cambiada a {stage_label} por {actor_label}."
        if reason:
            description += f" Motivo: {reason[:80]}."

        await self._activity_repo.record(
            lead_id=lead_id,
            tenant_id=tenant_id,
            actor="human" if triggered_by == "manual_override" else "agent",
            kind="stage_move",
            description_es=description,
        )

        # 9. Emit telemetry (fire-forget — never propagates)
        try:
            await self._emitter.emit_event(
                event_type="embudo_stage_changed",
                tenant_id=tenant_id,
                entity_id=lead_id,
                props={
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "trigger": triggered_by,
                    "score": new_score,
                },
            )
        except Exception:  # noqa: BLE001
            logger.warning("funnel_telemetry_emit_failed", lead_id=str(lead_id))

        # 10. Emit outbox event if manual override with reason (RN-4.1 → T-AG-1 wire)
        if triggered_by == "manual_override" and reason:
            try:
                await self._event_bus.publish(
                    {
                        "event_type": "lead_stage_overridden",
                        "tenant_id": str(tenant_id),
                        "lead_id": str(lead_id),
                        "from_stage": from_stage,
                        "to_stage": to_stage,
                        "reason": reason,
                        "actor_user_id": str(actor_user_id) if actor_user_id else None,
                        "version_after": updated_lead.version,
                    }
                )
            except Exception:  # noqa: BLE001
                logger.warning("funnel_outbox_event_failed", lead_id=str(lead_id))

        logger.info(
            "funnel_transition_complete",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            from_stage=from_stage,
            to_stage=to_stage,
            score=new_score,
        )

        return StageTransitionResponse(
            lead=_lead_to_response(updated_lead),
            transition=TransitionDTO(
                from_stage=transition_record.from_stage,
                to_stage=transition_record.to_stage,
                triggered_by=transition_record.triggered_by,
                reason=transition_record.reason,
                occurred_at=transition_record.occurred_at,
            ),
        )

    # ── get_board ──────────────────────────────────────────────────────────

    async def get_board(
        self,
        *,
        tenant_id: UUID,
        stage_filter: list[str] | None = None,
        sort: str = "stage_age_desc",
    ) -> BoardResponse:
        """Assemble the Kanban board with HOT_BOARD_STAGES columns + KPIs.

        Args:
            tenant_id: Tenant UUID.
            stage_filter: Optional subset of stages to include (default: all HOT_BOARD_STAGES).
            sort: Sort mode ('stage_age_desc' | 'score_desc' | 'value_desc' | 'activity_desc').

        Returns:
            BoardResponse with columns per stage + KPI strip.
        """
        if tenant_id is None:
            raise ValueError("FunnelService.get_board requires tenant_id")

        effective_stages = stage_filter or HOT_BOARD_STAGES
        leads = await self._lead_repo.list_for_board(
            tenant_id=tenant_id,
            stage_filter=effective_stages,
            is_frozen=False,
            sort=sort,
        )

        # Fetch last activity for each lead (micro-log + timestamp for board card)
        # T-FE2bis: store full LeadActivity to map both description + occurred_at to card
        from src.modules.vitalia.crm.domain.lead_activity import LeadActivity as _LeadActivity  # noqa: PLC0415

        last_activities: dict[UUID, _LeadActivity | None] = {}
        for lead in leads:
            activity = await self._activity_repo.last_for_lead(lead.id, tenant_id=tenant_id)
            last_activities[lead.id] = activity if activity else None

        # Group by stage
        by_stage: dict[str, list[Lead]] = {s: [] for s in effective_stages}
        for lead in leads:
            if lead.stage in by_stage:
                by_stage[lead.stage].append(lead)

        # Build columns
        columns: list[BoardColumn] = []
        for stage in effective_stages:
            stage_leads = by_stage[stage]
            cards: list[LeadCardDTO] = []
            for lead in stage_leads:
                days_in_stage = _compute_days_since(lead.stage_entered_at)
                sla_state = compute_sla_state(lead.stage, days_in_stage) or "green"
                # Resolve last activity for this lead
                last_act = last_activities.get(lead.id)
                last_act_description = last_act.description_es if last_act else None
                last_act_at = last_act.occurred_at.isoformat() if last_act else None

                cards.append(
                    LeadCardDTO(
                        id=lead.id,
                        tenant_id=lead.tenant_id,  # T-FE2bis
                        name=lead.name,
                        stage=lead.stage,
                        score=lead.score,
                        temperature=lead.temperature,
                        channel=lead.channel,
                        estimated_value=lead.estimated_value,
                        currency=lead.currency,
                        operated_by=lead.operated_by,
                        buying_signals=list(lead.buying_signals),
                        stage_entered_at=(lead.stage_entered_at.isoformat() if lead.stage_entered_at else None),
                        sla_state=sla_state,
                        deposit_status=lead.deposit_status,
                        # Freeze / terminal state (T-FE2bis)
                        is_frozen=lead.is_frozen,
                        frozen_reason=lead.frozen_reason,
                        closure_reason=lead.closure_reason,
                        reactivation_cohort_at=(
                            lead.reactivation_cohort_at.isoformat() if lead.reactivation_cohort_at else None
                        ),
                        # Commercial metadata (T-FE2bis)
                        service_interest=lead.service_interest,
                        assigned_doctor_id=lead.assigned_doctor_id,
                        is_blacklisted=lead.is_blacklisted,
                        # Optimistic lock (T-FE2bis — CRITICAL for drag mutation SC-5)
                        version=lead.version,
                        # Activity micro-log (T-FE2bis — renamed last_activity→last_activity_description)
                        last_activity_description=last_act_description,
                        last_activity_at=last_act_at,
                    )
                )

            sum_value = sum((lead.estimated_value or Decimal(0)) for lead in stage_leads)
            over_sla_count = sum(1 for c in cards if c.sla_state in {"amber", "red"})
            # Most common currency in column
            currencies = [c.currency for c in cards if c.currency]
            col_currency = max(set(currencies), key=currencies.count) if currencies else None

            columns.append(
                BoardColumn(
                    stage=stage,
                    label=STAGE_LABELS_ES.get(stage, stage),
                    count=len(stage_leads),
                    sum_value=sum_value,
                    currency=col_currency,
                    over_sla_count=over_sla_count,
                    leads=cards,
                )
            )

        # Compute KPIs
        all_cards = [card for col in columns for card in col.leads]
        active_total = len(all_cards)
        # Frozen count from a separate query (not in board scope)
        frozen_leads = await self._lead_repo.list_for_board(
            tenant_id=tenant_id,
            stage_filter=None,
            is_frozen=True,
            sort="stage_age_desc",
        )

        kpis = BoardKpis(
            active=active_total,
            agent_count=sum(1 for c in all_cards if c.operated_by == "agent"),
            human_count=sum(1 for c in all_cards if c.operated_by == "human"),
            hot=sum(1 for c in all_cards if c.temperature == "hot"),
            warm=sum(1 for c in all_cards if c.temperature == "warm"),
            cold=sum(1 for c in all_cards if c.temperature == "cold"),
            avg_score=int(sum(c.score for c in all_cards) / active_total) if active_total else 0,
            deposit_rate=(
                sum(1 for c in all_cards if c.deposit_status == "received") / active_total if active_total else 0.0
            ),
            frozen_count=len(frozen_leads),
        )

        return BoardResponse(columns=columns, kpis=kpis)

    # ── get_lead_detail ────────────────────────────────────────────────────

    async def get_lead_detail(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> LeadDetailResponse | None:
        """Return LeadDetailResponse with score breakdown + autonomy info.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID.

        Returns:
            LeadDetailResponse or None if not found for this tenant (→ 404 at API).
        """
        if tenant_id is None:
            raise ValueError("FunnelService.get_lead_detail requires tenant_id")

        lead = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if lead is None:
            return None

        score, factors = self._scorer.compute(lead)
        score_breakdown = [ScoreFactor(label=f.label, delta=f.delta) for f in factors]

        autonomy = AutonomyInfo(
            operated_by=lead.operated_by,
            can=_AGENT_CAN,
            needs_ok=_AGENT_NEEDS_OK,
        )

        # B2: override stored score with the freshly computed value so the detail
        # panel shows the glass-box score even for leads that have never transitioned
        # (stored score = 0 until first transition writes it back).
        lead_response = _lead_to_response(lead)
        lead_response = lead_response.model_copy(update={"score": score})

        return LeadDetailResponse(
            lead=lead_response,
            score_breakdown=score_breakdown,
            autonomy=autonomy,
        )

    # ── get_timeline ──────────────────────────────────────────────────────

    async def get_timeline(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> TimelineResponse | None:
        """Return commercial timeline for lead Historial tab.

        PHI firewall: only commercial activities (stage_move, note, info_sent).
        Clinical data stays in PHI-gated Inbox module (RN-2).

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID.

        Returns:
            TimelineResponse or None if lead not found for tenant.
        """
        if tenant_id is None:
            raise ValueError("FunnelService.get_timeline requires tenant_id")

        # Verify lead exists for this tenant
        lead = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if lead is None:
            return None

        activities = await self._activity_repo.list_for_lead(lead_id, tenant_id=tenant_id)
        transitions = await self._transition_repo.list_for_lead(lead_id, tenant_id=tenant_id)

        # Merge + sort by occurred_at DESC (newest first)
        events: list[TimelineEntry] = []

        for activity in activities:
            events.append(
                TimelineEntry(
                    actor=activity.actor,
                    kind=activity.kind,
                    description_es=activity.description_es,
                    occurred_at=activity.occurred_at,
                    signal=None,
                )
            )

        for transition in transitions:
            label = STAGE_LABELS_ES.get(transition.to_stage, transition.to_stage)
            events.append(
                TimelineEntry(
                    actor="system" if transition.triggered_by == "auto_freeze" else transition.triggered_by,
                    kind="stage_move",
                    description_es=f"Etapa cambiada a {label}."
                    + (f" Motivo: {transition.reason[:80]}." if transition.reason else ""),
                    occurred_at=transition.occurred_at,
                    signal=None,
                )
            )

        events.sort(key=lambda e: e.occurred_at, reverse=True)

        return TimelineResponse(events=events)

    # ── get_frozen_list ────────────────────────────────────────────────────

    async def get_frozen_list(
        self,
        *,
        tenant_id: UUID,
    ) -> FrozenListResponse:
        """Return frozen leads (is_frozen=True) + decidio_no leads for Recuperar tab.

        Args:
            tenant_id: Tenant UUID.

        Returns:
            FrozenListResponse with two lists.
        """
        if tenant_id is None:
            raise ValueError("FunnelService.get_frozen_list requires tenant_id")

        # Frozen leads (exclude decidio_no from frozen list — they go in their own section)
        frozen_leads = await self._lead_repo.list_for_board(
            tenant_id=tenant_id,
            stage_filter=["interesado", "calificando", "consulta_agendada", "plan_presentado"],
            is_frozen=True,
            sort="activity_desc",
        )

        # Leads that decided not (separate visual section in Recuperar)
        decidio_leads = await self._lead_repo.list_for_board(
            tenant_id=tenant_id,
            stage_filter=["decidio_no"],
            is_frozen=False,
            sort="activity_desc",
        )

        def _to_frozen_dto(lead: Lead, diagnosis: str | None = None) -> FrozenLeadDTO:
            return FrozenLeadDTO(
                id=lead.id,
                name=lead.name,
                channel=lead.channel,
                stage=lead.stage,
                frozen_reason=lead.frozen_reason,
                frozen_at=lead.frozen_at,
                diagnosis=diagnosis,
                closure_reason=lead.closure_reason,
            )

        return FrozenListResponse(
            recien_congelados=[_to_frozen_dto(lead) for lead in frozen_leads],
            decidio_no=[_to_frozen_dto(lead) for lead in decidio_leads],
        )

    # ── diagnose ──────────────────────────────────────────────────────────

    async def diagnose(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
    ) -> DiagnoseResponse | None:
        """Diagnose a frozen lead and return recommendation.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID.

        Returns:
            DiagnoseResponse or None if lead not found.
        """
        if tenant_id is None:
            raise ValueError("FunnelService.diagnose requires tenant_id")

        lead = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if lead is None:
            return None

        recommendation_es, suggested_action = self._diagnoser.diagnose(lead)

        return DiagnoseResponse(
            recommendation_es=recommendation_es,
            suggested_action=suggested_action,
        )

    # ── reactivate ────────────────────────────────────────────────────────

    async def reactivate(
        self,
        lead_id: UUID,
        *,
        tenant_id: UUID,
        objective: str | None = None,
    ) -> Lead | None:
        """Reactivate a frozen lead — clear frozen state + record activity.

        Args:
            lead_id: Lead UUID.
            tenant_id: Tenant UUID.
            objective: Optional context for reactivation (NON-PHI).

        Returns:
            Reactivated Lead entity or None if not found.
        """
        if tenant_id is None:
            raise ValueError("FunnelService.reactivate requires tenant_id")

        lead = await self._lead_repo.get_by_id(lead_id, tenant_id=tenant_id)
        if lead is None:
            return None

        reactivated = await self._lead_repo.reactivate(lead_id, tenant_id=tenant_id)

        description = "Prospecto reactivado manualmente."
        if objective:
            description += f" Objetivo: {objective[:80]}."

        await self._activity_repo.record(
            lead_id=lead_id,
            tenant_id=tenant_id,
            actor="human",
            kind="note",
            description_es=description,
        )

        # Fire-forget telemetry
        try:
            await self._emitter.emit_event(
                event_type="embudo_lead_reactivated",
                tenant_id=tenant_id,
                entity_id=lead_id,
                props={"previous_stage": lead.stage},
            )
        except Exception:  # noqa: BLE001
            logger.warning("funnel_reactivate_telemetry_failed", lead_id=str(lead_id))

        logger.info(
            "funnel_lead_reactivated",
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
        )

        return reactivated

    # ── create_lead (extend with funnel fields) ────────────────────────────

    async def create_lead(
        self,
        *,
        tenant_id: UUID,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        source: str | None = None,
        channel: str | None = None,
        service_interest: str | None = None,
        stage: str = "interesado",
        estimated_value: Decimal | None = None,
        currency: str | None = None,
        notes: str | None = None,
        marketing_opt_in: bool = False,
        actor_user_id: UUID | None = None,
    ) -> Lead:
        """Create a new lead with funnel fields + record initial activity.

        Args:
            tenant_id: Tenant UUID.
            name: Lead name (PII, pgcrypto-encrypted by repo).
            email: Optional email (PII, encrypted by repo).
            phone: Optional phone (PII, encrypted by repo).
            source: Acquisition source (e.g. 'instagram', 'referido').
            channel: Communication channel (wa|ig|meta|web|referido|tiktok).
            service_interest: Service the lead expressed interest in.
            stage: Initial funnel stage (default 'interesado').
            estimated_value: Estimated treatment value (NON-PHI).
            currency: Currency code — from tenant locale, NEVER hardcoded.
            notes: Optional notes (PII, encrypted by repo).
            marketing_opt_in: Marketing consent.
            actor_user_id: User creating the lead.

        Returns:
            Created Lead domain entity.
        """
        from uuid import uuid4  # noqa: PLC0415

        lead_id = uuid4()
        lead = await self._lead_repo.create(
            id=lead_id,
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            source=source,
            status="new",
            notes=notes,
            marketing_opt_in=marketing_opt_in,
            stage=stage,
            channel=channel,
            service_interest=service_interest,
            estimated_value=estimated_value,
            currency=currency,
        )

        # Record initial activity
        await self._activity_repo.record(
            lead_id=lead.id,
            tenant_id=tenant_id,
            actor="human" if actor_user_id else "system",
            kind="note",
            description_es=f"Prospecto registrado. Canal: {channel or 'sin especificar'}.",
        )

        # Fire-forget telemetry
        try:
            await self._emitter.emit_event(
                event_type="embudo_lead_created",
                tenant_id=tenant_id,
                entity_id=lead.id,
                props={
                    "stage": stage,
                    "channel": channel,
                    "has_value": estimated_value is not None,
                },
            )
        except Exception:  # noqa: BLE001
            logger.warning("funnel_create_telemetry_failed", lead_id=str(lead.id))

        return lead
