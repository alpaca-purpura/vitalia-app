# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""Vitalia Adrián sales_agent tool — ``reschedule_appointment``.

Story T-ag-tools-2 — R23 production_code=true. Opus 4.7 EXCLUSIVE.

Per 03-arch-agentic.md § 4.2 + 02-design-agentic.md § 2.3 + § 2.7.

Semantics:
  Fires the ``RescheduleAppointmentService.reschedule`` async pipeline:
    1. Delegate slot update to AppointmentService (existing vitalia scheduling)
    2. Emit ``appointment_rescheduled`` outbox event
    3. Operator notification (via downstream subscribers)
    4. Sync audit log row (HIPAA-lite mandate)

Tenant + clinic dual filter cardinal.

Cost: $0 LLM (pure DB + event emit).
Latency p95: ≤500ms (single DB UPDATE + event emit).

Constraint: rescheduling typically requires ≥24h anticipation per business
rules. Enforcement happens in ``AppointmentService.update_slot`` (vitalia
scheduling module) — tool surface trusts the downstream service.

Anti-duplication audit (Step 0 GATE):
  - ``RescheduleAppointmentService`` consumed via DI — NEVER instantiated in tool
  - Engine has no equivalent reschedule tool (each brand has its own
    scheduling adapter dependency).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from src.modules.vitalia.sales_agent.application.services.reschedule_appointment_service import (
        RescheduleAppointmentService,
    )

logger = structlog.get_logger(__name__)


# ── Pydantic schemas (Pydantic v2) ──────────────────────────────────────


class RescheduleAppointmentInput(BaseModel):
    """Input schema — tenant_id + clinic_id mandatory per HIPAA-lite cardinal."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    appointment_id: UUID = Field(
        ...,
        description="UUID of the appointment to reschedule.",
    )
    new_starts_at: datetime = Field(
        ...,
        description="New appointment datetime (timezone-aware UTC required).",
    )
    reason: str = Field(
        "",
        max_length=500,
        description="Reason for rescheduling (audit log only — not sent to patient).",
    )
    tenant_id: UUID = Field(
        ...,
        description="Tenant UUID (root isolation — dual filter).",
    )
    clinic_id: UUID = Field(
        ...,
        description="Clinic UUID (HIPAA-lite dual filter).",
    )
    user_id: UUID | None = Field(
        None,
        description="Operator UUID for audit log attribution. Defaults to appointment_id namespace when None.",
    )


# ── Service resolver (DI hook) ──────────────────────────────────────────

_service_resolver: Any = None  # callable returning RescheduleAppointmentService


def set_reschedule_service_resolver(resolver: Any) -> None:
    """Wire the service resolver at orchestrator init.

    Resolver signature: ``() -> RescheduleAppointmentService``. Called at
    tool invocation time so the service is built within the active request scope.
    """
    global _service_resolver  # noqa: PLW0603 — DI bootstrap hook
    _service_resolver = resolver


def _get_service() -> RescheduleAppointmentService:
    if _service_resolver is None:
        raise RuntimeError(
            "reschedule_appointment tool: service resolver not configured. "
            "Call set_reschedule_service_resolver(...) during orchestrator init."
        )
    return _service_resolver()


# ── Tool ────────────────────────────────────────────────────────────────


@tool("reschedule_appointment", args_schema=RescheduleAppointmentInput)
async def reschedule_appointment(
    appointment_id: UUID,
    new_starts_at: datetime,
    reason: str,
    tenant_id: UUID,
    clinic_id: UUID,
    user_id: UUID | None = None,
) -> str:
    """Reschedule an existing appointment to a new slot.

    Delegates slot update to the scheduling AppointmentService (validates
    professional availability + ≥24h anticipation rule + cross-clinic filter).

    Returns:
        Spanish summary string with new slot + audit timestamp.
        On failure, returns operator-handoff message.
    """
    service = _get_service()
    effective_user_id = user_id or appointment_id

    try:
        result = await service.reschedule(
            appointment_id=appointment_id,
            new_slot=new_starts_at,
            reason=reason,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=effective_user_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "vitalia.sales_agent.tools.reschedule_appointment.failed",
            error=str(exc),
            appointment_id=str(appointment_id),
            new_starts_at=new_starts_at.isoformat(),
        )
        return (
            "No pude reprogramar el turno automáticamente. "
            "El equipo te va a contactar en breve para coordinarlo manualmente."
        )

    return (
        f"Turno {result.appointment_id} reprogramado para "
        f"{result.new_slot.isoformat()}. Confirmación al lead pendiente."
    )


__all__ = [
    "RescheduleAppointmentInput",
    "reschedule_appointment",
    "set_reschedule_service_resolver",
]
