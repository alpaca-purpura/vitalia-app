# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""ProhibitedPhrase domain entity — vitalia brand-local soft warning blocklist.

Anti-creep guards:
  - NO LLM validator — only soft warning UI hint (per .claude/rules/sales-agent-brand-voice.md)
  - NO brand_voice_summary mirror table
  - NO blocking behavior — UI shows warning + suggested_alternative + allows override with audit_log row

downstream-regression-na: brand-local domain entity vitalia
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class ProhibitedPhraseSeverity(StrEnum):
    """Severity bucket for soft warning UI hint."""

    LOW = "low"  # style (e.g., "rapidísimo")
    MEDIUM = "medium"  # potential regulatory (e.g., "tratamiento milagroso")
    HIGH = "high"  # clear regulation (e.g., "curamos", "garantizado")


@dataclass
class ProhibitedPhrase:
    """Vitalia-specific configurable phrase blocklist for soft warning UI.

    Brand-local. NO blocks persistence. UI shows warning + suggested_alternative +
    allows override with audit_log row voice_warning_overridden.

    Defense-in-depth per .claude/rules/sales-agent-brand-voice.md anti-creep:
      - NO crear LLM validator
      - NO crear brand_voice_summary mirror
    """

    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID | None = None  # NULL = seed default (cross-tenant); UUID = tenant override
    phrase: str = ""  # lowercase normalized
    suggested_alternative: str = ""  # microcopy de sugerencia
    severity: str = ProhibitedPhraseSeverity.MEDIUM.value
    country_scope: str | None = None  # ISO 3166-1 alpha-2 (PE/AR/CL/CO/MX/BR) — None = global
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None

    @property
    def is_seed(self) -> bool:
        """Return True if this is a seed default (cross-tenant, tenant_id IS NULL)."""
        return self.tenant_id is None
