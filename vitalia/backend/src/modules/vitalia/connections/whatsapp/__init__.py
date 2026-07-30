# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""WhatsApp Cloud API connection adapter + HSM template registry — vitalia connections module.

Provides:
  - retract_message_id via Meta Graph API DELETE with graceful degradation (T-inbox-be-4)
  - WHATSAPP_TEMPLATE_REGISTRY: 5 Meta-approved HSM templates for fidelización (T-8)

T-8 fidelización templates:
  recordatorio_proxima_sesion   (UTILITY)
  recordatorio_control_doctor   (UTILITY)
  invitacion_mantenimiento       (MARKETING — requires opt-in)
  re_engagement_ausencia         (MARKETING — requires opt-in)
  nps_post_tratamiento           (UTILITY)

Per hipaa-lite.md: MARKETING templates enforce requires_marketing_opt_in=True.
Per spanish-text.md: all template bodies in Spanish neutro LatAm (tuteo).
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections whatsapp module
from src.modules.vitalia.connections.whatsapp.adapter import (
    RetractResult,
    WhatsAppAdapter,
)
from src.modules.vitalia.connections.whatsapp.registry import (
    WHATSAPP_TEMPLATE_REGISTRY,
    WhatsAppTemplateDef,
    get_whatsapp_template,
    list_whatsapp_templates,
)

__all__ = [
    "WhatsAppAdapter",
    "RetractResult",
    "WHATSAPP_TEMPLATE_REGISTRY",
    "WhatsAppTemplateDef",
    "get_whatsapp_template",
    "list_whatsapp_templates",
]
