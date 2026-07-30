# cap: sales_agent.honor-mode-bridge
# voseo-allowed: sales_agent brand-voice output (tenant-configurable, respects regional tone)
"""``match_service_and_specialist`` — Adrián recommends the specialist for a service.

OLA-2 "recomienda" tool, NATIVE-SYNC ``(state, db) -> dict`` (the engine
``node_tool_executor`` ABI, ESC-17). Read-only over PUBLIC marketing data → no
PHI, no async bridge: a plain sync DB read via the platform sync engine.

Flow (03-arch-agentic § 2.2): ``service_intent`` → product (offer) by name ilike →
``offer_service_specialist_links`` (offer↔doctor) → doctors. Primary = the first
shareable doctor (``visible_en_landing`` + ``active`` + ``public_slug`` → public
URL ``/d/{clinic}/{doctor}``); callbacks = the remaining linked doctors (named;
URL only when shareable).

Args (LLM ``state["_pending_tool"]["args"]``): ``service_intent`` (free text).
``tenant_id`` is authoritative from ``state`` (never the LLM).

Availability filtering is a follow-up (the match recommends the specialist;
slot availability is `book_appointment`/`VitaliaSchedulerProvider`'s concern).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from luana_core_offer_studio.infrastructure.models.product_model import ProductModel
from luana_core_platform.core.config import get_settings
from luana_core_platform.core.database import get_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel
from src.modules.vitalia.clinics.infrastructure.models.doctor_model import VitaliaDoctorModel
from src.modules.vitalia.offer.infrastructure.models.offer_service_specialist_link_model import (
    OfferServiceSpecialistLinkModel,
)

logger = structlog.get_logger(__name__)


def _doctor_url(session: Session, doctor: VitaliaDoctorModel, base: str) -> str | None:
    """Public profile URL for a shareable doctor, else None."""
    if not (doctor.visible_en_landing and doctor.active and doctor.public_slug):
        return None
    clinic = session.get(ClinicModel, doctor.clinic_id)
    clinic_slug = getattr(clinic, "slug", None)
    if not clinic_slug:
        return None
    return f"{base}/d/{clinic_slug}/{doctor.public_slug}"


def _doctor_card(session: Session, doctor: VitaliaDoctorModel, base: str) -> dict[str, Any]:
    return {
        "name": f"{doctor.first_name} {doctor.last_name}".strip(),
        "specialty": doctor.specialty,
        "url": _doctor_url(session, doctor, base),
    }


def match_service_and_specialist(state: dict[str, Any], db: Any = None) -> dict[str, Any]:  # noqa: ANN401, ARG001
    """Recommend the service's specialist(s) (sync, engine ABI)."""
    tenant_raw = state.get("tenant_id")
    if not tenant_raw:
        return {"status": "error", "message": "Falta el contexto del tenant para buscar un especialista."}
    try:
        tenant_id = tenant_raw if isinstance(tenant_raw, UUID) else UUID(str(tenant_raw))
    except (ValueError, TypeError):
        return {"status": "error", "message": "Identificador de tenant inválido."}

    args = (state.get("_pending_tool") or {}).get("args") or {}
    service_intent = (args.get("service_intent") or args.get("service") or "").strip()
    if not service_intent:
        return {
            "status": "not_found",
            "message": "¿Qué servicio o tratamiento te interesa? Así te recomiendo al especialista indicado.",
        }

    base = (get_settings().FRONTEND_URL or "").rstrip("/")

    with Session(get_engine()) as session:
        product = session.execute(
            select(ProductModel)
            .where(
                ProductModel.tenant_id == tenant_id,
                ProductModel.name.ilike(f"%{service_intent}%"),
                ProductModel.status == "active",
                ProductModel.deleted_at.is_(None),
            )
            .order_by(ProductModel.name)
            .limit(1)
        ).scalar_one_or_none()
        if product is None:
            return {
                "status": "not_found",
                "message": (
                    f"No encontré un servicio que coincida con '{service_intent}'. "
                    "¿Querés que te muestre las opciones disponibles?"
                ),
            }

        doctor_ids = (
            session.execute(
                select(OfferServiceSpecialistLinkModel.doctor_id).where(
                    OfferServiceSpecialistLinkModel.tenant_id == tenant_id,
                    OfferServiceSpecialistLinkModel.offer_id == product.id,
                    OfferServiceSpecialistLinkModel.deleted_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        if not doctor_ids:
            return {
                "status": "not_found",
                "service": product.name,
                "message": (
                    f"Tenemos el servicio '{product.name}', pero todavía no hay un especialista asignado. "
                    "Un asesor puede ayudarte a coordinarlo."
                ),
            }

        doctors = (
            session.execute(
                select(VitaliaDoctorModel)
                .where(
                    VitaliaDoctorModel.tenant_id == tenant_id,
                    VitaliaDoctorModel.id.in_(doctor_ids),
                    VitaliaDoctorModel.deleted_at.is_(None),
                )
                .order_by(VitaliaDoctorModel.visible_en_landing.desc(), VitaliaDoctorModel.first_name)
            )
            .scalars()
            .all()
        )
        cards = [_doctor_card(session, d, base) for d in doctors]

    if not cards:
        return {
            "status": "not_found",
            "service": product.name,
            "message": f"Tenemos '{product.name}', pero el equipo no está disponible para mostrar ahora.",
        }

    # Primary = first shareable (has URL), else the first linked doctor.
    shareable = [c for c in cards if c["url"]]
    primary = shareable[0] if shareable else cards[0]
    callbacks = [c for c in cards if c is not primary]

    logger.info(
        "vitalia.sales_agent.match_service_and_specialist",
        tenant_id=str(tenant_id),
        service=product.name,
        primary=primary["name"],
        callbacks=len(callbacks),
    )
    return {
        "status": "success",
        "service": product.name,
        "primary": primary,
        "callbacks": callbacks,
        "message": (
            f"Para '{product.name}' te recomiendo a {primary['name']}"
            f"{f' ({primary["specialty"]})' if primary['specialty'] else ''}"
            f"{f': {primary["url"]}' if primary['url'] else ''}."
        ),
    }


__all__ = ["match_service_and_specialist"]
