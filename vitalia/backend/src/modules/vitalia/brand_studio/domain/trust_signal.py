# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""TrustSignal domain entity — certifications/authority tenant-specific.

Hybrid catalog per country (OQ-D resolution 2026-05-27):
  - Closed catalog (catalog_code not None) for known authorities per country
  - Free-text "Otra" for custom trust signals (catalog_code=None)

downstream-regression-na: brand-local domain entity vitalia
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class TrustSignal:
    """Certification/authority listed by tenant for their public presence.

    Resolution OQ-D: hybrid catalog per country + free-text "Otra".
    Stored as JSONB in tenant.config_json['trust_signals'] via brand config.
    """

    id: UUID = field(default_factory=uuid4)
    tenant_id: UUID | None = None
    label: str = ""  # "DIGESA" or free-text "Otra: Centro Premium..."
    catalog_code: str | None = None  # None if free-text
    logo_url: str | None = None
    issued_year: int | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_seed(self) -> bool:
        """Return True if this is a seed/catalog default (catalog_code not None)."""
        return self.catalog_code is not None
