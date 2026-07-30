# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Lead detail DTOs — workspace page (Resumen tab).

API layer Pydantic v2 models.
ScoreFactor: glass-box score breakdown (what contributed + delta).
AutonomyInfo: what Adrián can do vs. needs human OK.
Lead detail: NON-PHI only (RN-2 firewall — no clinical fields).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.modules.vitalia.crm.application.dto.lead_dto import LeadResponse


class ScoreFactor(BaseModel):
    """One component of the glass-box score breakdown."""

    model_config = ConfigDict(from_attributes=True)

    label: str  # Spanish neutro description of the factor
    delta: int  # points added or subtracted (signed integer)


class AutonomyInfo(BaseModel):
    """What Adrián (agent) can do vs. needs human approval.

    Per 03-arch-be.md § 7 + 01-spec.md v3 Resumen tab.
    can: actions Adrián performs autonomously (e.g. "mover etapa", "agendar cita")
    needs_ok: actions requiring human approval (e.g. "aplicar descuento", "gestión de cobro")
    """

    model_config = ConfigDict(from_attributes=True)

    operated_by: str  # agent | human
    can: list[str]  # autonomy tier actions (Spanish neutro)
    needs_ok: list[str]  # human-gated actions


class LeadDetailResponse(BaseModel):
    """Full lead detail for Resumen tab in workspace (opción C).

    Combines the lead record + score breakdown + autonomy info.
    PHI firewall: no clinical fields here. Historial tab links to PHI-gated Inbox.
    """

    model_config = ConfigDict(from_attributes=True)

    lead: LeadResponse
    score_breakdown: list[ScoreFactor]
    autonomy: AutonomyInfo
