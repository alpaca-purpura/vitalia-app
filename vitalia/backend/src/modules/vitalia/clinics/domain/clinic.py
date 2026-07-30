# cap: clinics.clinics-brand-extension
# story-origin: TBD
"""Vitalia Clinic domain entity — pure Python, zero framework imports.

DDD Inside-Out: domain layer is the innermost ring.
No sqlalchemy, no fastapi, no luana_core_iam imports.

A Clinic is the physical/legal healthcare entity (medical practice, dental
office, wellness center). Each Clinic maps to a tenant_id in the engine
IAM system. The dual-filter invariant (tenant_id + clinic_id) is enforced
at the repository and API layers.

HIPAA-lite: clinic data is PHI-adjacent (links to patient records).
Clinic identity fields (name, slug, country) are identity OK — not PHI.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Clinic(BaseModel):
    """Vitalia Clinic domain entity.

    A Clinic is the brand-specific extension that links a Luana tenant (from
    the engine IAM system) to a physical healthcare entity with location,
    plan tier, and onboarding status.

    Attributes:
        id: Unique identifier (UUID).
        tenant_id: FK to engine 'tenants' table — links clinic to IAM tenant.
        name: Human-readable clinic name (e.g. "Clínica Aurora Dental").
        slug: URL-safe identifier (unique per tenant, e.g. "aurora-dental-ar").
        country: ISO 3166-1 alpha-2 country code (AR, MX, CO, CL, PE, BR).
        timezone: IANA TZ string (e.g. "America/Argentina/Buenos_Aires").
        plan_tier: Subscription plan (starter, growth, scale).
        is_active: Whether clinic is currently active on the platform.
        onboarding_completed: Whether clinic has completed the onboarding wizard.
        created_at: UTC creation timestamp.
        updated_at: UTC last-update timestamp. None if never updated.
        deleted_at: UTC soft-delete timestamp. None if not deleted.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    country: str = Field(max_length=2, description="ISO 3166-1 alpha-2")
    timezone: str = Field(default="UTC", description="IANA timezone string")
    plan_tier: str = Field(default="starter", description="starter | growth | scale")
    is_active: bool = True
    onboarding_completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    # --- Account / fiscal identity fields (migration 039) ---
    # Non-PHI clinic identity: legal name, fiscal ID, address, contact info,
    # locale preferences. Added in vitalia-fase2-config-cuenta T-2.
    legal_name: str | None = Field(default=None, description="Razón social o nombre legal")
    fiscal_id: str | None = Field(default=None, description="ID fiscal (CUIT/RUC/RFC/NIT/RUT por país)")
    address: str | None = Field(default=None, description="Dirección fiscal o de atención")
    phone: str | None = Field(default=None, description="Teléfono de contacto")
    email: str | None = Field(default=None, description="Email de contacto clínica")
    language: str = Field(default="es-419", description="Locale preferido (IETF BCP 47)")
    currency: str | None = Field(default=None, description="Moneda preferida ISO 4217 (None = del país del tenant)")

    @field_validator("language", mode="before")
    @classmethod
    def _coerce_language_none(cls, v: object) -> object:
        """Back-compat: rows pre-039 (o fixtures) traen language=None — coerce al default.

        El server_default de la migración solo cubre INSERTs nuevos; objetos
        existentes hidratados via from_attributes pueden traer None explícito.
        """
        return "es-419" if v is None else v
