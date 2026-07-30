# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""LeadScoreService — deterministic glass-box scoring (0-100, no ML).

Application layer — pure business logic, no DB access.

Score formula (from 03-arch-be.md § 7 + 01-spec.md § glass-box research):
  Base by stage (escalating):
    interesado         → 10
    calificando        → 25
    consulta_agendada  → 50
    plan_presentado    → 70
    reservado          → 100
    decidio_no         → 0

  Buying signals (additive, capped at max 100):
    pregunto_precio      +25
    presupuesto_ok       +20
    respondio_rapido     +15
    campana_pagada       +10
    urgencia             +10
    consulto_fecha       +8
    manda_referencias    +5

  Recency penalty (stage age, for non-terminal stages):
    sin_agendar: -2 per day over SLA green threshold, capped at -20

  Temperature derivation:
    score ≥ 70  → hot
    score ≥ 40  → warm
    else        → cold

Lift candidate: this scoring pattern is vertical-specific (dental SLA),
but the structure is generic enough for a 2nd brand. Per anti-duplication.md:
do NOT lift proactively — only if nicolify/comunify needs it.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from src.modules.vitalia.crm.domain.funnel_machine import SLA_DAYS
from src.modules.vitalia.crm.domain.lead import Lead

logger = structlog.get_logger()

# ── Signal weights ───────────────────────────────────────────────────────────
_SIGNAL_WEIGHTS: dict[str, int] = {
    "pregunto_precio": 25,
    "presupuesto_ok": 20,
    "respondio_rapido": 15,
    "campana_pagada": 10,
    "urgencia": 10,
    "consulto_fecha": 8,
    "manda_referencias": 5,
}

# ── Base score by stage ──────────────────────────────────────────────────────
_STAGE_BASE: dict[str, int] = {
    "interesado": 10,
    "calificando": 25,
    "consulta_agendada": 50,
    "plan_presentado": 70,
    "reservado": 100,
    "decidio_no": 0,
}

_RECENCY_PENALTY_PER_DAY = 2
_RECENCY_PENALTY_CAP = 20


class ScoreFactor:
    """One score component — label + signed delta."""

    def __init__(self, label: str, delta: int) -> None:
        """Initialize ScoreFactor.

        Args:
            label: Human-readable description (Spanish neutro).
            delta: Points added (+) or subtracted (-).
        """
        self.label = label
        self.delta = delta


class LeadScoreService:
    """Glass-box deterministic lead scorer.

    No external dependencies — pure computation.
    Used by FunnelService.transition_stage() to recompute score on each transition.
    """

    def compute(
        self,
        lead: Lead,
    ) -> tuple[int, list[ScoreFactor]]:
        """Compute glass-box score for a lead.

        Args:
            lead: Lead domain entity with current stage + buying_signals.

        Returns:
            Tuple of (score 0-100, breakdown list of ScoreFactor).
        """
        factors: list[ScoreFactor] = []

        # 1. Base by stage
        base = _STAGE_BASE.get(lead.stage, 10)
        factors.append(ScoreFactor(label=f"Etapa: {lead.stage}", delta=base))
        running = base

        # 2. Buying signals
        for signal in set(lead.buying_signals):
            weight = _SIGNAL_WEIGHTS.get(signal, 0)
            if weight > 0:
                factors.append(ScoreFactor(label=f"Señal: {signal}", delta=weight))
                running += weight

        # 3. Recency penalty (only for non-terminal active stages)
        sla_config = SLA_DAYS.get(lead.stage)
        if sla_config is not None and lead.stage_entered_at is not None:
            now = datetime.now(tz=timezone.utc)
            stage_entered = lead.stage_entered_at
            # Make timezone-aware if naive
            if stage_entered.tzinfo is None:
                stage_entered = stage_entered.replace(tzinfo=timezone.utc)
            days_in_stage = (now - stage_entered).days
            green_threshold = sla_config["green"]
            if days_in_stage > green_threshold:
                over_days = days_in_stage - green_threshold
                penalty = min(over_days * _RECENCY_PENALTY_PER_DAY, _RECENCY_PENALTY_CAP)
                factors.append(ScoreFactor(label="Días sin avance", delta=-penalty))
                running -= penalty

        # 4. Clamp to [0, 100]
        final_score = max(0, min(100, running))

        logger.debug(
            "lead_score_computed",
            lead_id=str(lead.id),
            stage=lead.stage,
            score=final_score,
            signals=list(lead.buying_signals),
        )

        return final_score, factors

    @staticmethod
    def derive_temperature(score: int) -> str:
        """Derive temperature label from score.

        Args:
            score: Score 0-100.

        Returns:
            'hot' | 'warm' | 'cold'
        """
        if score >= 70:
            return "hot"
        if score >= 40:
            return "warm"
        return "cold"
