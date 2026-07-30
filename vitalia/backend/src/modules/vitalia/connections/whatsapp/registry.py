# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Vitalia WhatsApp HSM template registry — brand-local config (T-8).

5 Meta-approved templates for patient fidelización workflows:

  1. recordatorio_proxima_sesion   — UTILITY: appointment reminder
  2. recordatorio_control_doctor   — UTILITY: follow-up control reminder
  3. invitacion_mantenimiento       — MARKETING: maintenance session invite
  4. re_engagement_ausencia         — MARKETING: lapsed patient re-engagement
  5. nps_post_tratamiento           — UTILITY: post-treatment NPS survey

HIPAA-lite compliance (per vitalia/.claude/rules/hipaa-lite.md):
  - body_text uses ONLY {{N}} placeholders for patient_name, clinic_name,
    appointment_date. NO PHI embedded literally in template body.
  - MARKETING templates have requires_marketing_opt_in=True — the
    ProactiveOutboundService (T-5/T-9) enforces this at service layer:
    `if template.requires_marketing_opt_in and not patient.marketing_opt_in: raise 403`.

Spanish neutro LatAm per .claude/rules/spanish-text.md (tuteo, no voseo).

Anti-duplication: this registry is brand-specific vitalia config. NEVER mirror
to other brands (per .claude/rules/anti-duplication.md). Template configs
for other brands must live in their own brand connections module.

downstream-regression-na: brand-local vitalia whatsapp template registry (T-8)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "fidelizacion"


@dataclass(frozen=True)
class WhatsAppTemplateDef:
    """Brand-local WhatsApp Meta-approved HSM template definition.

    Attributes:
        slug: Brand-internal identifier (e.g. 'recordatorio_proxima_sesion').
        template_name: Meta template name as registered in WhatsApp Business API.
        category: 'UTILITY' or 'MARKETING'. MARKETING requires opt-in.
        language: ISO 639-1 language code ('es' for LatAm Spanish).
        body_text: Template body with {{N}} placeholders (no PHI).
        requires_marketing_opt_in: True for MARKETING templates.
            Enforced at ProactiveOutboundService layer (T-5/T-9).
        components_raw: Full JSON components as registered with Meta API.
        metadata: Extensible dict for future metadata (e.g. approval_id).
    """

    slug: str
    template_name: str
    category: str
    language: str
    body_text: str
    requires_marketing_opt_in: bool
    components_raw: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


def _load_template(filename: str) -> dict[str, Any]:
    """Load a JSON template file from the fidelizacion templates directory."""
    path = _TEMPLATES_DIR / filename
    with path.open(encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _extract_body_text(components: list[dict[str, Any]]) -> str:
    """Extract the BODY component text from a list of Meta template components."""
    for component in components:
        if component.get("type") == "BODY":
            return str(component.get("text", ""))
    return ""


def _build_registry() -> dict[str, WhatsAppTemplateDef]:
    """Build the WhatsApp template registry from JSON files.

    Loads 5 fidelización templates from the templates/fidelizacion/ directory.
    Called at module import time — fails fast if JSON files are missing or malformed.
    """
    templates: dict[str, WhatsAppTemplateDef] = {}

    # (slug, filename, category, requires_opt_in)
    _TEMPLATE_CONFIGS: list[tuple[str, str, str, bool]] = [
        ("recordatorio_proxima_sesion", "recordatorio_proxima_sesion.json", "UTILITY", False),
        ("recordatorio_control_doctor", "recordatorio_control_doctor.json", "UTILITY", False),
        ("invitacion_mantenimiento", "invitacion_mantenimiento.json", "MARKETING", True),
        ("re_engagement_ausencia", "re_engagement_ausencia.json", "MARKETING", True),
        ("nps_post_tratamiento", "nps_post_tratamiento.json", "UTILITY", False),
    ]

    for slug, filename, expected_category, requires_opt_in in _TEMPLATE_CONFIGS:
        raw = _load_template(filename)
        components = raw.get("components", [])
        body_text = _extract_body_text(components)

        # Validate category consistency between JSON file and registry config
        json_category = raw.get("category", "")
        if json_category != expected_category:
            raise ValueError(
                f"Template {slug!r}: JSON category={json_category!r} "
                f"does not match registry config category={expected_category!r}"
            )

        templates[slug] = WhatsAppTemplateDef(
            slug=slug,
            template_name=raw["name"],
            category=raw["category"],
            language=raw.get("language", "es"),
            body_text=body_text,
            requires_marketing_opt_in=requires_opt_in,
            components_raw=components,
            metadata={"source_file": filename},
        )

    return templates


# Module-level registry — loaded once at import time
WHATSAPP_TEMPLATE_REGISTRY: dict[str, WhatsAppTemplateDef] = _build_registry()


def get_whatsapp_template(slug: str) -> WhatsAppTemplateDef | None:
    """Look up a WhatsApp template by its brand-internal slug.

    Args:
        slug: Brand-internal slug (e.g. 'recordatorio_proxima_sesion').

    Returns:
        WhatsAppTemplateDef if found, None otherwise.
    """
    return WHATSAPP_TEMPLATE_REGISTRY.get(slug)


def list_whatsapp_templates() -> tuple[str, ...]:
    """Return all registered WhatsApp template slugs as a sorted tuple."""
    return tuple(sorted(WHATSAPP_TEMPLATE_REGISTRY.keys()))
