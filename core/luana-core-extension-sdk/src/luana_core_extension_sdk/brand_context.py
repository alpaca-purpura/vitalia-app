"""BrandContext — per-tenant frozen context passed to extension handlers.

Per checkpoint §7.5.2 D3 — 9 fields FROZEN at v0.1.0. Future optional fields
opcionales agregables sin breaking bump. Handler that uses only a subset of
fields MUST continue working when new optional fields are appended.

NO PII fields — safe to log. tenant_id + tenant_profile_id are opaque UUIDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class BrandContext:
    """Per-tenant context passed to extension handlers (CC-4 namespace + brand routing).

    Per checkpoint §7.5.2 D3 — 9 fields FROZEN at v0.1.0. Future optional fields
    opcionales agregables sin breaking bump. Handler that uses only a subset of
    fields MUST continue working when new optional fields are appended.

    NO PII fields — safe to log. tenant_id + tenant_profile_id are opaque UUIDs.
    """

    tenant_id: UUID
    brand_slug: Literal["nicolify", "vitalia", "comunify", "lupulo", "test-brand"]
    plan_tier: str  # tier_id from EP-17 brand-registered
    locale: str  # ISO 639-1 + region (es-AR / es-MX / es-CL / en-US)
    feature_flags: dict[str, bool]  # tenant-level flag map (brand-injected)
    tenant_profile_id: UUID
    vertical_kind: Literal["marketing", "medical", "creator-economy", "gastronomy"]
    compliance_flags: dict[str, bool]  # e.g. {"hipaa_required": True} per Vitalia
    pii_policy: Literal["standard", "medical", "creator", "gastronomy"]
