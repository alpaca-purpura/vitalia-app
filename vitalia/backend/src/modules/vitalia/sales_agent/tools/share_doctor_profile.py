# cap: sales_agent.honor-mode-bridge
"""``share_doctor_profile`` — Adrián shares a doctor's PUBLIC profile URL.

OLA-2 "comparte" tool, written NATIVE-SYNC ``(state, db) -> dict`` (the engine
``node_tool_executor`` ABI, ESC-17). It reads only PUBLIC marketing data
(``visible_en_landing`` doctors) → no PHI, no HIPAA dual-filter mandate, no async
service → a plain sync DB read via the platform sync engine, bypassing the
async→sync bridge entirely (the cleanest possible adapter, and the ESC-17 pilot).

URL contract (vitalia-fase2-lisa-doctores § D3-D): ``/d/{clinic_slug}/{public_slug}``
on ``settings.FRONTEND_URL``. Only doctors with ``visible_en_landing=True`` AND
``active=True`` AND a ``public_slug`` are shareable (RN: visible-en-landing gate).

Args (from the LLM ``[TOOL_REQUEST]`` ``state["_pending_tool"]["args"]``, optional):
  ``doctor_id`` — share a specific doctor; else
  ``specialty`` / ``service_intent`` — match by specialty (ilike); else
  first shareable doctor for the tenant.
``tenant_id`` is authoritative from ``state`` (never the LLM).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from luana_core_platform.core.config import get_settings
from luana_core_platform.core.database import get_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel
from src.modules.vitalia.clinics.infrastructure.models.doctor_model import VitaliaDoctorModel

logger = structlog.get_logger(__name__)


def share_doctor_profile(state: dict[str, Any], db: Any = None) -> dict[str, Any]:  # noqa: ANN401, ARG001
    """Return the public profile URL of a shareable doctor (sync, engine ABI)."""
    tenant_raw = state.get("tenant_id")
    if not tenant_raw:
        return {"status": "error", "message": "Falta el contexto del tenant para compartir un perfil."}
    try:
        tenant_id = tenant_raw if isinstance(tenant_raw, UUID) else UUID(str(tenant_raw))
    except (ValueError, TypeError):
        return {"status": "error", "message": "Identificador de tenant inválido."}

    args = (state.get("_pending_tool") or {}).get("args") or {}
    doctor_id = args.get("doctor_id")
    specialty = args.get("specialty") or args.get("service_intent")

    stmt = select(VitaliaDoctorModel).where(
        VitaliaDoctorModel.tenant_id == tenant_id,
        VitaliaDoctorModel.visible_en_landing.is_(True),
        VitaliaDoctorModel.active.is_(True),
        VitaliaDoctorModel.public_slug.isnot(None),
        VitaliaDoctorModel.deleted_at.is_(None),
    )
    if doctor_id:
        try:
            stmt = stmt.where(VitaliaDoctorModel.id == UUID(str(doctor_id)))
        except (ValueError, TypeError):
            return {"status": "error", "message": "Identificador de doctor inválido."}
    elif specialty:
        stmt = stmt.where(VitaliaDoctorModel.specialty.ilike(f"%{specialty}%"))

    with Session(get_engine()) as session:
        doctor = session.execute(stmt.limit(1)).scalar_one_or_none()
        if doctor is None:
            return {
                "status": "not_found",
                "message": "Todavía no hay un perfil de doctor público disponible para compartir.",
            }
        clinic = session.get(ClinicModel, doctor.clinic_id)
        clinic_slug = getattr(clinic, "slug", None)
        full_name = f"{doctor.first_name} {doctor.last_name}".strip()
        specialty_label = doctor.specialty
        public_slug = doctor.public_slug

    if not clinic_slug:
        return {"status": "error", "message": "La sede del doctor no tiene una página pública configurada."}

    base = (get_settings().FRONTEND_URL or "").rstrip("/")
    url = f"{base}/d/{clinic_slug}/{public_slug}"
    logger.info(
        "vitalia.sales_agent.share_doctor_profile",
        tenant_id=str(tenant_id),
        doctor_slug=public_slug,
        clinic_slug=clinic_slug,
        url=url,
    )
    return {
        "status": "success",
        "doctor_name": full_name,
        "specialty": specialty_label,
        "url": url,
        "message": (f"Perfil de {full_name}{f' ({specialty_label})' if specialty_label else ''}: {url}"),
    }


__all__ = ["share_doctor_profile"]
