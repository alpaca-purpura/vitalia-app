# cap: clinics.lisa.doctores
"""Public doctor serializer — explicit allow-list channel guard.

HIPAA-lite channel guard (hipaa-lite.md § Channel guards):
  - Constructs PublicDoctorDTO from Doctor domain entity using an
    EXPLICIT ALLOW-LIST of exactly 7 fields.
  - PHI fields (dni, email, phone, credential) are NEVER serialized.
  - Internal fields (tenant_id, clinic_id, active, visible_en_landing) are omitted.
  - The allow-list is the SECURITY BOUNDARY: adding PHI to the Doctor model
    does NOT leak it — only the 7 named fields are ever emitted.

Arch test: tests/architecture/test_public_doctors_allowlist.py (V-ARCH-7).
Functional test: tests/modules/vitalia/clinics/test_public_doctors_endpoint.py (V-FN-11).

Per 03-arch-be.md § 6:
  'Allow-list mapper (channel guard). Resolves avatar_url from avatar_key.
   credential_label optional ("CMP 12345" or "Colegiado/a" per clinic config).'
"""

from __future__ import annotations

from src.modules.vitalia.clinics.api.dtos import (
    BioPublicDTO,
    ExperienciaItemDTO,
    FormacionItemDTO,
    PublicDoctorDTO,
    PublicDoctorProfileDTO,
)
from src.modules.vitalia.clinics.domain.doctor import Doctor


def to_public_dto(
    doctor: Doctor,
    *,
    credential_label: str | None = None,
) -> PublicDoctorDTO:
    """Map a Doctor domain entity to a PublicDoctorDTO using the allow-list.

    This function is the ONLY sanctioned way to serialize a Doctor for public
    endpoints. It physically cannot emit PHI because it only reads the 7
    allow-listed fields — all other Doctor fields are ignored.

    Security invariant: even if PHI fields are added to Doctor in the future,
    this serializer will NOT include them (allow-list, not deny-list).

    Args:
        doctor: Domain entity with decrypted PII (used only for allow-listed fields).
        credential_label: Optional display label like "CMP 12345" or "Colegiado/a".
            Clinic admin decides whether to show the credential number publicly.
            Defaults to None (not shown).

    Returns:
        PublicDoctorDTO with exactly 7 allow-listed fields.
        PHI fields (dni, email, phone, credential) are NEVER included.

    Allowed fields (per 03-arch-be.md § 3 and 01-spec.md § Endpoint público):
        1. display_name       — derived from first_name + last_name (not PHI)
        2. specialty          — public specialty (not PHI)
        3. avatar_key         — R2 object key for public avatar (not PHI)
        4. years_experience   — signal of authority (not PHI)
        5. languages          — languages the doctor works in (not PHI)
        6. bio_public         — generated public bio in 3 sections (not PHI)
        7. credential_label   — optional display string (not the raw credential number)
    """
    # Build bio_public DTO from domain BioPublic dataclass
    bio_dto: BioPublicDTO | None = None
    if doctor.bio_public is not None and not doctor.bio_public.is_empty():
        bio_dto = BioPublicDTO(
            resumen=doctor.bio_public.resumen,
            formacion=doctor.bio_public.formacion,
            enfoque=doctor.bio_public.enfoque,
        )

    # Construct PublicDoctorDTO using ONLY the 7 allow-listed fields.
    # NEVER access doctor.dni, doctor.email, doctor.phone, doctor.credential here.
    # The constructor signature of PublicDoctorDTO enforces the allow-list at the
    # type level — Pydantic will reject any unknown fields.
    return PublicDoctorDTO(
        display_name=doctor.display_name,  # 1. derived property, not PHI
        specialty=doctor.specialty,  # 2. professional specialty
        avatar_key=doctor.avatar_key,  # 3. R2 key for public avatar
        years_experience=doctor.years_experience,  # 4. authority signal
        languages=doctor.languages,  # 5. languages list
        bio_public=bio_dto,  # 6. generated public bio
        credential_label=credential_label,  # 7. optional display string
    )


def to_public_profile_dto(
    doctor: Doctor,
    clinic_name: str | None = None,
) -> PublicDoctorProfileDTO:
    """Map a Doctor domain entity to a PublicDoctorProfileDTO (structured D3-D profile).

    CHANNEL GUARD (hipaa-lite.md): only allow-listed professional fields are serialized.
    PHI fields (dni, email, phone, credential) are NEVER accessed here.

    Business rules enforced:
      - RN-D3D-5: idiomas only exposed if len > 1 (single language omitted)
      - RN-D3D-6: all sections nullable — minimum identity = display_name
      - RN-D3D-7: OG-safe fields (display_name, specialty, sobre_mi, avatar_key)
        available for FE generateMetadata

    Args:
        doctor: Domain entity. Only non-PHI allow-listed fields are read.

    Returns:
        PublicDoctorProfileDTO with structured sections. Zero PHI fields.
    """
    profile = doctor.public_profile

    # Structured sections — None if no profile generated yet
    sobre_mi: str | None = None
    formacion: list[FormacionItemDTO] | None = None
    experiencia: list[ExperienciaItemDTO] | None = None
    tratamientos: list[str] | None = None
    certificaciones: list[str] | None = None

    if profile is not None and not profile.is_empty():
        sobre_mi = profile.sobre_mi or None

        if profile.formacion:
            formacion = [
                FormacionItemDTO(
                    titulo=item.get("titulo", ""),
                    institucion=item.get("institucion", ""),
                    anio=item.get("anio"),
                )
                for item in profile.formacion
                if isinstance(item, dict)
            ]

        if profile.experiencia:
            experiencia = [
                ExperienciaItemDTO(
                    puesto=item.get("puesto", ""),
                    lugar=item.get("lugar", ""),
                    anios=item.get("anios"),
                )
                for item in profile.experiencia
                if isinstance(item, dict)
            ]

        if profile.tratamientos:
            tratamientos = list(profile.tratamientos)

        if profile.certificaciones:
            certificaciones = list(profile.certificaciones)

    # RN-D3D-5: idiomas only if len > 1 — single language does NOT signal multilingual
    idiomas: list[str] | None = None
    languages_source = (profile.idiomas if profile is not None else None) or doctor.languages
    if len(languages_source) > 1:
        idiomas = list(languages_source)

    # Construct the channel-guarded DTO — NEVER access doctor.dni / email / phone.
    # credential_number/country = licencia PROFESIONAL pública (badge colegiatura,
    # mockup v3.2 firmado + RN-D3D) — no es PHI de paciente.
    credential_label = None
    cred_number = getattr(doctor, "credential", None)
    if cred_number:
        cc = getattr(doctor, "credential_country", None)
        credential_label = f"{cred_number}" + (f" ({cc})" if cc else "")

    return PublicDoctorProfileDTO(
        clinic_name=clinic_name,
        credential_label=credential_label,
        display_name=doctor.display_name,  # derived property, not PHI
        specialty=doctor.specialty,  # professional specialty, not PHI
        avatar_key=doctor.avatar_key,  # R2 key for public avatar, not PHI
        sobre_mi=sobre_mi,  # professional summary (OG-safe RN-D3D-7)
        formacion=formacion,  # academic background
        experiencia=experiencia,  # work experience
        tratamientos=tratamientos,  # treatment chips
        certificaciones=certificaciones,  # certifications
        idiomas=idiomas,  # languages (only if len>1)
    )
