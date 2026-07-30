# cap: lisa.servicios
"""Social-proof aggregates — Case (PHI · before/after photo) + Testimonial.

Pure domain. Case is PHI (patient photo) → gated by consent_signed (RN-33):
a Case with consent_signed=False MUST NOT be persisted (enforced at repo layer
via PhiRepositoryBase). Testimonial is NOT PHI (manual marketing copy).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Case:
    """Before/after patient case — PHI. consent_signed is the persist gate (RN-33)."""

    tenant_id: UUID
    offer_id: UUID
    before_asset_url: str
    after_asset_url: str
    consent_signed: bool  # gate RN-33 (False → never persisted)
    consent_ref: str | None = None
    clinic_id: UUID | None = None  # HIPAA-lite dual-filter (second filter)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass
class Testimonial:
    """Manually-loaded testimonial (RN-33). Not PHI."""

    tenant_id: UUID
    offer_id: UUID
    rating: int
    text: str
    author: str
    source: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    deleted_at: datetime | None = None
