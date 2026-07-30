# cap: sales_agent.honor-mode-bridge
"""``book_appointment`` — Adrián books a real appointment (OLA-2 "agenda").

EP-3 tool, sync ``(state, db) -> dict`` (the engine ``node_tool_executor`` ABI,
ESC-17). Unlike share/match (sync reads), this WRITES → it bridges to the async
``CreateAppointmentService`` via ``tool_bridge.run_async`` (which submits to the
app's main loop → the loop that owns the shared engine pool → no cross-loop trap).

Model facts (verified 2026-06-22):
- ``appointments.lead_id`` is ``ForeignKey("leads.id")`` → the inbound lead IS the
  appointment's subject. ``patient_id`` passed to ``create_appointment`` = the lead
  (``state["user_id"]``). No separate patient record / lead→patient CRM build.
- The engine ``appointments`` row has no clinic/doctor columns; the brand
  ``vitalia_appointment_clinic_map`` (written by ``create_clinic_map``) holds them.
  ``clinic_id`` is resolved from the doctor (a doctor belongs to a clinic).
- HIPAA-lite: ``CreateAppointmentService`` writes the audit-log row sync. ✓

Args (LLM ``state["_pending_tool"]["args"]``): ``doctor_id`` (or ``state[
"recommended_doctor_id"]``), ``start_time`` (ISO), ``service_label``,
``duration_minutes`` (opt, default 60). ``tenant_id`` + the lead (``user_id``) are
authoritative from ``state``. Idempotent per (lead, start_time, SCHEDULED).

Scope (MVP): creates the appointment + clinic_map + audit. Slot-hold marking
(``hold_service``/``vitalia_availability_slots``) + advisory-lock 409 race +
slot resolution by reasoning are documented follow-ups (lift doc § Tier 2.4b).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import structlog

from src.modules.vitalia.sales_agent.tool_bridge import run_async

logger = structlog.get_logger(__name__)

_DEFAULT_DURATION_MIN = 60


def _parse_dt(raw: Any) -> datetime | None:
    """Parse an ISO datetime (LLM-provided). Naive → assumed UTC."""
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def book_appointment(state: dict[str, Any], db: Any = None) -> dict[str, Any]:  # noqa: ANN401, ARG001
    """Book a real appointment (sync entry; async write via the main-loop bridge)."""
    tenant_raw = state.get("tenant_id")
    lead_raw = state.get("user_id")  # appointments.lead_id FK target (the inbound lead)
    if not tenant_raw:
        return {"status": "error", "message": "Falta el contexto del tenant para agendar."}
    if not lead_raw:
        return {"status": "error", "message": "Falta el contacto del lead para agendar."}

    args = (state.get("_pending_tool") or {}).get("args") or {}
    doctor_raw = args.get("doctor_id") or state.get("recommended_doctor_id")
    start_raw = args.get("start_time") or args.get("when")
    service_label = (args.get("service_label") or args.get("service") or "Consulta").strip()

    if not doctor_raw:
        return {"status": "need_info", "message": "¿Con qué especialista deseas agendar el turno?"}
    if not start_raw:
        return {"status": "need_info", "message": "¿Para qué día y horario te gustaría el turno?"}

    try:
        tenant_id = UUID(str(tenant_raw))
        lead_id = UUID(str(lead_raw))
        doctor_id = UUID(str(doctor_raw))
    except (ValueError, TypeError):
        return {"status": "error", "message": "Identificadores inválidos para agendar."}

    start_time = _parse_dt(start_raw)
    if start_time is None:
        return {"status": "error", "message": "No entendí la fecha y hora. ¿Me la pasás como AAAA-MM-DD HH:MM?"}
    try:
        duration = int(args.get("duration_minutes") or _DEFAULT_DURATION_MIN)
    except (ValueError, TypeError):
        duration = _DEFAULT_DURATION_MIN
    end_time = start_time + timedelta(minutes=duration)

    try:
        return run_async(
            _do_book(
                tenant_id=tenant_id,
                lead_id=lead_id,
                doctor_id=doctor_id,
                service_label=service_label,
                start_time=start_time,
                end_time=end_time,
            )
        )
    except Exception as exc:  # noqa: BLE001 — agent resilience (engine also catches)
        logger.warning("vitalia.sales_agent.book_appointment.error", error=str(exc), doctor_id=str(doctor_id))
        return {
            "status": "error",
            "message": "No pude crear el turno por un problema técnico. Un asesor te ayuda a coordinarlo.",
        }


async def _do_book(
    *,
    tenant_id: UUID,
    lead_id: UUID,
    doctor_id: UUID,
    service_label: str,
    start_time: datetime,
    end_time: datetime,
) -> dict[str, Any]:
    """Async write path — runs on the app main loop (shared pool safe)."""
    from luana_core_scheduling.infrastructure.models.appointment_model import AppointmentModel
    from sqlalchemy import select

    from src.db import get_async_session_committing
    from src.modules.vitalia._shared.telemetry.growth_studio_emitter import GrowthStudioEmitter
    from src.modules.vitalia.audit.audit_writer import AsyncAuditWriter
    from src.modules.vitalia.clinics.infrastructure.models.doctor_model import VitaliaDoctorModel
    from src.modules.vitalia.scheduling.application.services.create_appointment_service import (
        CreateAppointmentService,
    )
    from src.modules.vitalia.scheduling.infrastructure.repositories.agenda_grid_repository_impl import (
        AgendaGridRepositoryImpl,
    )

    result: dict[str, Any] = {"status": "error", "message": "No pude crear el turno."}

    # NOTE: no break/return inside the `async for` — let the committing generator
    # resume after the body so it COMMITS on success (an early return/break throws
    # GeneratorExit at the yield and skips the commit).
    async for session in get_async_session_committing():
        doctor = await session.get(VitaliaDoctorModel, doctor_id)
        if doctor is None or doctor.tenant_id != tenant_id or doctor.deleted_at is not None:
            result = {"status": "error", "message": "No encontré a ese especialista en la clínica."}
        else:
            clinic_id = doctor.clinic_id
            existing = (
                await session.execute(
                    select(AppointmentModel.id).where(
                        AppointmentModel.tenant_id == tenant_id,
                        AppointmentModel.lead_id == lead_id,
                        AppointmentModel.start_time == start_time,
                        AppointmentModel.status == "SCHEDULED",
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                result = {
                    "status": "already_booked",
                    "appointment_id": str(existing),
                    "message": "Ya tienes un turno reservado para ese horario.",
                }
            else:
                service = CreateAppointmentService(
                    repo=AgendaGridRepositoryImpl(session=session),
                    audit_writer=AsyncAuditWriter(session=session),
                    growth_emitter=GrowthStudioEmitter(session=session),
                )
                detail = await service.create_appointment(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=lead_id,  # agent-driven (origin marks it); the lead is the subject
                    origin="proactivo_adrian",
                    patient_id=lead_id,
                    doctor_id=doctor_id,
                    service_label=service_label,
                    start_time=start_time,
                    end_time=end_time,
                )
                appt_id = (detail or {}).get("id") or (detail or {}).get("appointment_id")
                doctor_name = f"{doctor.first_name} {doctor.last_name}".strip()
                result = {
                    "status": "success",
                    "appointment_id": str(appt_id) if appt_id else None,
                    "doctor_name": doctor_name,
                    "service": service_label,
                    "start_time": start_time.isoformat(),
                    "message": (
                        f"Turno reservado con {doctor_name} para "
                        f"{start_time.strftime('%d/%m/%Y %H:%M')} ({service_label})."
                    ),
                }
                logger.info(
                    "vitalia.sales_agent.book_appointment",
                    tenant_id=str(tenant_id),
                    appointment_id=result["appointment_id"],
                    doctor_id=str(doctor_id),
                    origin="proactivo_adrian",
                )

    return result


__all__ = ["book_appointment"]
