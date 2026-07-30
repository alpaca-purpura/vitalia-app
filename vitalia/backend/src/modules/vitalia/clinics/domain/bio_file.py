# cap: clinics.lisa.doctores
"""DoctorBioFile domain entity — private bio material uploaded for a doctor.

Delta v3 D3-B (03-arch-delta § 3.1): bio docs are PRIVATE input material
(CV, diplomas, certificates) consumed by bio/profile generation — never
published directly. Distinct from credential_doc (credential verification).

Pure Python dataclass — zero framework imports (DDD domain layer).

SSoT shared with the API layer (api imports domain, never the reverse):
  - BIO_DOC_ALLOWED_CONTENT_TYPES: PDF/JPG/PNG/DOCX allow-list for kind=bio_doc
    (consumed by assets_proxy_router + register validation — no mirror).
  - MAX_BIO_FILE_SIZE_BYTES: 10MB cap (same as assets proxy).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

#: Content types accepted for kind=bio_doc — same allow-list as credential_doc
#: (PDF/JPG/PNG/DOCX) per 03-arch-delta § 3.1.
BIO_DOC_ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

#: 10 MB max — mirrors assets proxy MAX_FILE_SIZE_BYTES (spec § Business rules).
MAX_BIO_FILE_SIZE_BYTES: int = 10 * 1024 * 1024


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


@dataclass
class DoctorBioFile:
    """A bio material file registered for a doctor (R2/local object + metadata).

    The binary lives in the assets storage backend (R2 in prod, local in
    dev/test) under ``storage_key``; this entity is the tenant-scoped registry
    row that drives listing, deletion, download and material-new detection
    (RN-D3D-4 reads ``uploaded_at``).

    RN-D3B-1: deleting a bio file NEVER touches the doctor's generated
    bio/profile snapshot — this entity has no reference to bio_public.
    """

    tenant_id: UUID
    clinic_id: UUID
    doctor_id: UUID
    storage_key: str
    filename: str
    size_bytes: int
    content_type: str
    id: UUID = field(default_factory=uuid4)
    uploaded_at: datetime = field(default_factory=_utc_now)
    created_at: datetime = field(default_factory=_utc_now)
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants (defense in depth behind the assets proxy).

        Raises:
            ValueError: On empty filename/storage_key, size out of 1..10MB
                bounds, or content_type outside the bio_doc allow-list.
        """
        if not self.filename or not self.filename.strip():
            raise ValueError("filename no puede estar vacío.")
        if not self.storage_key or not self.storage_key.strip():
            raise ValueError("storage_key no puede estar vacío.")
        if self.size_bytes < 1:
            raise ValueError("size_bytes debe ser mayor o igual a 1.")
        if self.size_bytes > MAX_BIO_FILE_SIZE_BYTES:
            raise ValueError(f"size_bytes supera el límite de 10 MB ({MAX_BIO_FILE_SIZE_BYTES} bytes).")
        normalized = (self.content_type or "").lower().split(";")[0].strip()
        if normalized not in BIO_DOC_ALLOWED_CONTENT_TYPES:
            allowed = ", ".join(sorted(BIO_DOC_ALLOWED_CONTENT_TYPES))
            raise ValueError(f"content_type no permitido para material de bio. Se aceptan: {allowed}.")
        self.content_type = normalized
