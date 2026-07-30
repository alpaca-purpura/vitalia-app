# cap: clinics.lisa.doctores
"""Doctor domain entity — pure Python dataclass.

DDD Inside-Out: zero framework/infrastructure imports allowed here.
All PHI fields (dni, email, phone, credential) are plain strings at domain level;
encryption/decryption happens in the infrastructure layer (doctor_repository.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


@dataclass
class Doctor:
    """Staff doctor profile for a Vitalia clinic.

    PHI fields: dni, email, phone, credential.
    These are stored encrypted (BYTEA via pgcrypto) in the DB;
    the domain entity holds plain-text values after decryption.
    """

    tenant_id: UUID
    clinic_id: UUID
    first_name: str
    last_name: str
    dni: str
    """DNI / passport number — PHI, encrypted at rest."""

    email: str
    """Professional contact email — PHI, encrypted at rest."""

    credential: str
    """Credential number (CMP / matrícula / cédula / registro) — PHI, encrypted at rest."""

    credential_country: str
    """ISO-2 country code for credential validation: PE|AR|MX|CL."""

    id: UUID = field(default_factory=uuid4)
    phone: str | None = None
    """Mobile phone — PHI, encrypted at rest."""

    specialty: str | None = None
    years_experience: int | None = None
    languages: list[str] = field(default_factory=list)
    bio_inputs_notes: str | None = None
    """Raw notes/text provided by clinic admin for bio generation."""

    bio_links: list[str] = field(default_factory=list)
    """URLs to publications, profiles, or attachments (PDFs, images)."""

    bio_public: BioPublic | None = None
    """Generated/edited public bio (3 sections: resumen/formacion/enfoque). Legacy — kept for compat."""

    public_profile: DoctorPublicProfile | None = None
    """Structured public profile — supersedes bio_public. 6-section schema (D3-D)."""

    bio_generated_at: datetime | None = None
    """Timestamp of last bio/profile generation. Used for RN-D3D-4 material_new detection."""

    public_slug: str | None = None
    """URL-safe slug for public doctor profile. Unique per (tenant_id, clinic_id)."""

    avatar_key: str | None = None
    """Cloudflare R2 object key for doctor avatar."""

    visible_en_landing: bool = False
    """Whether this doctor appears on the public landing page."""

    active: bool = True
    """False = soft-deactivated (excluded from scheduling)."""

    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    @property
    def display_name(self) -> str:
        """Formatted display name: 'Dr(a). Nombre Apellido'.

        Uses 'Dra.' prefix for names typically female in LatAm medical context
        (simple heuristic: names ending in 'a'). Clinics can override via bio.
        """
        # Simple heuristic: feminine names common in LatAm ending in 'a'
        first_lower = self.first_name.strip().lower()
        title = "Dra." if first_lower.endswith("a") else "Dr."
        return f"{title} {self.first_name.strip()} {self.last_name.strip()}"

    @property
    def is_active(self) -> bool:
        """Alias for active — used by scheduling integration."""
        return self.active
