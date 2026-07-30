# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Appointment origin registry (Vitalia agenda dispatch metadata).

Per `03-arch-be.md` § 6.3 — 4 origins Slice 1 mapped to
`vitalia_appointments.origin` enum column (per § 2.1):
`sales_agent | walk_in | phone_manual | proactive_outbound`.

Pure metadata — no callables. The agenda module reads this registry to render
UI labels (Spanish neutro), enforce capability gates (e.g. walk-in requires
on-site role), and route post-creation flows (e.g. proactive_outbound emits
`AppointmentCreated` with `origin=proactive_outbound` for downstream
attribution analytics in `AttributionMatrixWidget`).

Slice 2 candidates: kiosk_self_checkin, partner_referral, recurring_treatment.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppointmentOriginDef:
    """Metadata for a Vitalia appointment origin slot.

    Attributes:
        origin_id: canonical slug matching `vitalia_appointments.origin` enum value
        label_es: Spanish-neutro user-facing label (tuteo)
        description_es: short explanation for tooltip / docs
        is_default: True ONLY for `sales_agent` — the default when no origin is
                    explicitly provided (per arch § 2.1 DEFAULT 'sales_agent')
        requires_on_site_role: True for walk_in / phone_manual (require clinic
                               staff presence). Used for RBAC gating in the
                               agenda dispatch UI.
        attribution_kind: one of `sales_agent | manual | proactive` — drives the
                          AttributionMatrixWidget 4-origin tally in Marketing.
    """

    origin_id: str
    label_es: str
    description_es: str
    is_default: bool = False
    requires_on_site_role: bool = False
    attribution_kind: str = "manual"
    metadata: dict[str, Any] = field(default_factory=dict)


APPOINTMENT_ORIGIN_REGISTRY: dict[str, AppointmentOriginDef] = {
    "sales_agent": AppointmentOriginDef(
        origin_id="sales_agent",
        label_es="Agente comercial",
        description_es="Cita reservada por Adrián vía conversación entrante.",
        is_default=True,
        requires_on_site_role=False,
        attribution_kind="sales_agent",
    ),
    "walk_in": AppointmentOriginDef(
        origin_id="walk_in",
        label_es="Walk-in (paciente en mostrador)",
        description_es="Paciente llega sin cita previa; recepción registra el ingreso.",
        is_default=False,
        requires_on_site_role=True,
        attribution_kind="manual",
    ),
    "phone_manual": AppointmentOriginDef(
        origin_id="phone_manual",
        label_es="Llamada telefónica (recepción)",
        description_es="Recepción carga la cita después de una llamada del paciente.",
        is_default=False,
        requires_on_site_role=True,
        attribution_kind="manual",
    ),
    "proactive_outbound": AppointmentOriginDef(
        origin_id="proactive_outbound",
        label_es="Outbound proactivo",
        description_es=(
            "Cita generada por seguimiento proactivo (re-engagement, recordatorio "
            "de mantenimiento, NPS post-tratamiento)."
        ),
        is_default=False,
        requires_on_site_role=False,
        attribution_kind="proactive",
    ),
}


def get_appointment_origin(origin_id: str) -> AppointmentOriginDef | None:
    """Return the registered appointment origin def or None if unknown."""
    return APPOINTMENT_ORIGIN_REGISTRY.get(origin_id)


def list_appointment_origins() -> tuple[str, ...]:
    """Return the tuple of registered origin slugs (deterministic order)."""
    return tuple(APPOINTMENT_ORIGIN_REGISTRY.keys())


__all__: Iterable[str] = (
    "APPOINTMENT_ORIGIN_REGISTRY",
    "AppointmentOriginDef",
    "get_appointment_origin",
    "list_appointment_origins",
)
