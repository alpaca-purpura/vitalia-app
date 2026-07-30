# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""FunnelMachine — deterministic 6-stage dental funnel SSoT.

Domain layer — pure Python constants + helpers. No ORM, no framework imports.

Dental vertical funnel (Vitalia Tier 1: odontología cosmética + medicina estética):
  interesado → calificando → consulta_agendada → plan_presentado → reservado (success)
                                                                 ↘ decidio_no (at any step)

Rules from 03-arch-be.md § 1 + 01-spec.md v3 RN-11/13/17/18:
  - reservado: NEVER set manually (webhook/payment only, RN-4/RN-5)
  - SLA per stage: time-in-stage triggers color badge (verde/ámbar/rojo)
  - FREEZE_RULES: 14d no response | 30d hard | 2×SLA multiplier (RN-13)
  - HOT_BOARD_STAGES: what shows on the Kanban board (excludes decidio_no, RN-18)
  - ORDER: stage_entered_at ASC = oldest first (most urgent at top, RN-17)

Lift candidate comment: stage machine pattern could be generalized to
core/luana-core-crm/ if a 2nd brand needs a funnel. Per anti-duplication.md:
do NOT lift proactively. Create PR if nicolify/comunify/lupulo request this.
"""

from __future__ import annotations

from typing import Literal

# ── Stage machine ────────────────────────────────────────────────────────────
# Maps each stage → list of allowed next stages.
# Empty list = terminal stage (no outgoing transitions).
# 'reservado' transition only via webhook, but listed here so service can
# validate the path; the manual-override guard is enforced at service layer.
STAGE_MACHINE: dict[str, list[str]] = {
    "interesado": ["calificando", "decidio_no"],
    "calificando": ["consulta_agendada", "decidio_no"],
    "consulta_agendada": ["plan_presentado", "decidio_no"],
    "plan_presentado": ["reservado", "decidio_no"],
    "reservado": [],  # success terminal
    "decidio_no": [],  # failure terminal
}

# ── SLA thresholds (days) per active stage (RN-11) ───────────────────────────
# green ≤ green days; amber > green; red > red days
SLA_DAYS: dict[str, dict[str, int]] = {
    "interesado": {"green": 7, "amber": 7, "red": 14},
    "calificando": {"green": 7, "amber": 7, "red": 14},
    "consulta_agendada": {"green": 5, "amber": 5, "red": 10},
    "plan_presentado": {"green": 14, "amber": 14, "red": 21},
    # reservado and decidio_no are terminal — no SLA
}

# ── Freeze rules (RN-13) ─────────────────────────────────────────────────────
FREEZE_RULES: dict[str, float] = {
    "no_response_days": 14,  # 14d without any response → auto-freeze
    "hard_days": 30,  # 30d hard cap → always freeze regardless of SLA
    "sla_multiplier": 2.0,  # >2× stage SLA → freeze
}

# ── Board scope (RN-18) ──────────────────────────────────────────────────────
# Hot board shows active stages + reservado (success). decidio_no → Recuperar tab.
HOT_BOARD_STAGES: list[str] = [
    "interesado",
    "calificando",
    "consulta_agendada",
    "plan_presentado",
    "reservado",
]

# ── Stage labels (Spanish neutro LatAm) ─────────────────────────────────────
STAGE_LABELS_ES: dict[str, str] = {
    "interesado": "Interesado",
    "calificando": "Calificando",
    "consulta_agendada": "Consulta",
    "plan_presentado": "Plan",
    "reservado": "Reservado",
    "decidio_no": "Decidió no",
}


# ── Pure helper functions ─────────────────────────────────────────────────────


def is_terminal_stage(stage: str) -> bool:
    """Return True if stage is a terminal (no outgoing transitions).

    Args:
        stage: Funnel stage slug.

    Returns:
        True if stage is terminal (reservado or decidio_no).
    """
    return len(STAGE_MACHINE.get(stage, [])) == 0


def allowed_next_stages(stage: str) -> list[str]:
    """Return allowed next stages from the given stage.

    Args:
        stage: Current funnel stage slug.

    Returns:
        List of allowed next stage slugs. Empty for terminal stages.
    """
    return list(STAGE_MACHINE.get(stage, []))


def is_manual_reservado_forbidden(to_stage: str) -> bool:
    """Return True if setting this stage manually is forbidden.

    reservado must ONLY be set via webhook (payment confirmation, RN-4).
    Manual drag/dropdown → 403 at service layer.

    Args:
        to_stage: Target stage slug.

    Returns:
        True if setting to_stage manually is forbidden.
    """
    return to_stage == "reservado"


def compute_sla_state(
    stage: str,
    days_in_stage: int | float,
) -> Literal["green", "amber", "red"] | None:
    """Compute the SLA state color badge for a lead in a given stage.

    Args:
        stage: Current funnel stage slug.
        days_in_stage: Number of days the lead has been in this stage.

    Returns:
        'green' | 'amber' | 'red' or None if stage has no SLA (terminal).
    """
    sla = SLA_DAYS.get(stage)
    if sla is None:
        # Terminal stage — no SLA
        return None

    if days_in_stage > sla["red"]:
        return "red"
    if days_in_stage > sla["amber"]:
        return "amber"
    return "green"


def should_freeze(
    stage: str,
    days_in_stage: int | float,
    days_since_last_response: int | float,
) -> tuple[bool, str | None]:
    """Check whether a lead should be auto-frozen per RN-13 rules.

    Three conditions (any triggers freeze):
      1. No response for 14d (no_response_days)
      2. 30d hard cap (hard_days)
      3. >2× stage SLA (sla_multiplier × amber threshold)

    Args:
        stage: Current funnel stage slug.
        days_in_stage: Days since stage_entered_at.
        days_since_last_response: Days since last lead response.

    Returns:
        Tuple of (should_freeze: bool, reason: str | None).
        reason is set when should_freeze is True.
    """
    # Rule 1: No response 14d
    if days_since_last_response >= FREEZE_RULES["no_response_days"]:
        return True, "inactividad_lead"

    # Rule 2: 30d hard cap
    if days_in_stage >= FREEZE_RULES["hard_days"]:
        return True, "sin_respuesta_presupuesto"

    # Rule 3: 2× SLA multiplier
    sla = SLA_DAYS.get(stage)
    if sla is not None:
        threshold = sla["amber"] * FREEZE_RULES["sla_multiplier"]
        if days_in_stage >= threshold:
            return True, "agente_trabado"

    return False, None
