# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""HSM Template definitions — vitalia inbox proactive outbound.

5 Meta-approved templates hardcoded for Slice 1 per 03-arch-be.md § 6.6.
Templates are immutable SSoT for this slice — no DB configuration.

Template categories:
- UTILITY: no marketing_opt_in required (appointment reminders, service comms)
- MARKETING: requires patient.marketing_opt_in = True (re-engagement, NPS)

Per hipaa-lite.md: NO PHI fields (diagnosis, treatment_plan, etc.) may appear
in template bodies. Variables use generic identifiers only.

downstream-regression-na: brand-local vitalia inbox templates
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TemplateCategory = Literal["UTILITY", "MARKETING"]


@dataclass(frozen=True)
class HsmTemplate:
    """Immutable HSM template descriptor.

    Attributes:
        template_id: Unique identifier matching Meta-approved template name.
        category: UTILITY (no opt-in) or MARKETING (requires opt-in).
        display_name_es: Human-readable name in Spanish neutro LatAm.
        required_variables: Ordered list of variable names ({{1}}, {{2}}, ...).
        description_es: Brief description for operator UI.
    """

    template_id: str
    category: TemplateCategory
    display_name_es: str
    required_variables: tuple[str, ...]
    description_es: str


# ---------------------------------------------------------------------------
# 5 Meta-approved HSM templates — Slice 1 SSoT
# ---------------------------------------------------------------------------

TEMPLATE_REGISTRY: dict[str, HsmTemplate] = {
    "recordatorio_proxima_sesion": HsmTemplate(
        template_id="recordatorio_proxima_sesion",
        category="UTILITY",
        display_name_es="Recordatorio próxima sesión",
        required_variables=("fecha",),
        description_es="Recuerda al paciente su próxima cita. Ejemplo: 'miércoles 21 de mayo'.",
    ),
    "recordatorio_control_doctor": HsmTemplate(
        template_id="recordatorio_control_doctor",
        category="UTILITY",
        display_name_es="Recordatorio control con el doctor",
        required_variables=("fecha", "hora"),
        description_es="Recuerda control post-tratamiento. No mencionar diagnóstico.",
    ),
    "invitacion_mantenimiento": HsmTemplate(
        template_id="invitacion_mantenimiento",
        category="UTILITY",
        display_name_es="Invitación mantenimiento",
        required_variables=("nombre_servicio",),
        description_es="Invita al paciente a su sesión de mantenimiento programada.",
    ),
    "re_engagement_ausencia": HsmTemplate(
        template_id="re_engagement_ausencia",
        category="MARKETING",
        display_name_es="Re-engagement por ausencia",
        required_variables=("meses_ausencia",),
        description_es=(
            "Contacto a pacientes inactivos. Requiere marketing_opt_in=True. "
            "Solo para WhatsApp Business (ventana activa)."
        ),
    ),
    "nps_post_tratamiento": HsmTemplate(
        template_id="nps_post_tratamiento",
        category="MARKETING",
        display_name_es="NPS post-tratamiento",
        required_variables=("nombre_tratamiento",),
        description_es=("Solicita valoración del servicio recibido. Requiere marketing_opt_in=True."),
    ),
}


def get_template(template_id: str) -> HsmTemplate | None:
    """Return template descriptor or None if not found."""
    return TEMPLATE_REGISTRY.get(template_id)


def is_marketing_template(template_id: str) -> bool:
    """Return True if template requires marketing_opt_in."""
    tpl = get_template(template_id)
    if tpl is None:
        return False
    return tpl.category == "MARKETING"


def all_template_ids() -> list[str]:
    """Return list of all registered template IDs."""
    return list(TEMPLATE_REGISTRY.keys())
