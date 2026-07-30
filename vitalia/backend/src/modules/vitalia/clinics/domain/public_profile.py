# cap: clinics.lisa.doctores
"""DoctorPublicProfile — structured public profile domain entity.

Supersedes the legacy BioPublic (3-blob resumen/formacion/enfoque) with a
structured 6-section schema: sobre_mi, formacion[], experiencia[],
tratamientos[], certificaciones[], idiomas[].

DDD Inside-Out — pure Python dataclass, zero framework imports.
BioPublic is kept read-only for backward compatibility (T-BE-bio-docs).

Per 03-arch-delta.md § 6.1:
  sobre_mi: str | None
  formacion: list[dict]    — [{titulo, institucion, anio}]
  experiencia: list[dict]  — [{puesto, lugar, anios}]
  tratamientos: list[str]  — chips
  certificaciones: list[str]
  idiomas: list[str]       — RN-D3D-5: only exposed publicly if len > 1

RN-D3D-6: all sections nullable (minimum identity = display_name + specialty).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FormacionItem:
    """Formación académica — título, institución, año."""

    titulo: str
    institucion: str
    anio: int | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSONB persistence."""
        return {
            "titulo": self.titulo,
            "institucion": self.institucion,
            "anio": self.anio,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormacionItem":
        """Deserialize from JSONB dict."""
        return cls(
            titulo=data.get("titulo", ""),
            institucion=data.get("institucion", ""),
            anio=data.get("anio"),
        )


@dataclass(frozen=True)
class ExperienciaItem:
    """Experiencia profesional — puesto, lugar, años."""

    puesto: str
    lugar: str
    anios: int | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSONB persistence."""
        return {
            "puesto": self.puesto,
            "lugar": self.lugar,
            "anios": self.anios,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExperienciaItem":
        """Deserialize from JSONB dict."""
        return cls(
            puesto=data.get("puesto", ""),
            lugar=data.get("lugar", ""),
            anios=data.get("anios"),
        )


@dataclass(frozen=True)
class DoctorPublicProfile:
    """Structured public doctor profile — 6-section schema.

    All sections nullable (RN-D3D-6).
    Supersedes BioPublic legacy 3-blob (kept read-only for compat).

    Fields:
        sobre_mi:        Free-text professional summary.
        formacion:       Academic background items [{titulo, institucion, anio}].
        experiencia:     Work experience items [{puesto, lugar, anios}].
        tratamientos:    Treatment/procedure chips (public display strings).
        certificaciones: Professional certifications (tick list).
        idiomas:         Languages spoken — stored structured, exposed publicly
                         only if len > 1 (RN-D3D-5, enforced by serializer).
    """

    sobre_mi: str | None = None
    formacion: list[dict] = field(default_factory=list)
    experiencia: list[dict] = field(default_factory=list)
    tratamientos: list[str] = field(default_factory=list)
    certificaciones: list[str] = field(default_factory=list)
    idiomas: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Return True if all sections are empty/None."""
        return (
            not self.sobre_mi
            and not self.formacion
            and not self.experiencia
            and not self.tratamientos
            and not self.certificaciones
            and not self.idiomas
        )

    def to_dict(self) -> dict:
        """Serialize to dict for JSONB persistence in vitalia_doctors.public_profile."""
        return {
            "sobre_mi": self.sobre_mi,
            "formacion": self.formacion,
            "experiencia": self.experiencia,
            "tratamientos": self.tratamientos,
            "certificaciones": self.certificaciones,
            "idiomas": self.idiomas,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "DoctorPublicProfile | None":
        """Deserialize from JSONB dict. Returns None if data is None or empty dict.

        Legacy compat (audit DELTA-BE 2026-06-12 · 03-arch-delta § 6.1): la
        migración 041 backfillea ``public_profile = bio_public`` verbatim — shape
        legacy 3-blob ``{resumen, formacion: str, enfoque}``. Ese shape se
        normaliza acá al contrato ratificado:
          - ``sobre_mi ← resumen``
          - ``formacion ← [{titulo: <blob>, institucion: '', anio: None}]``
        (institucion '' y no None: FormacionItemDTO.institucion tipa str requerido.)

        Type-hardening: secciones con tipo inesperado (str/int/dict donde va una
        lista) colapsan a ``[]`` — nunca un str tipado como list[dict] (el router
        iteraría sus caracteres → items basura).
        """
        if not data:
            return None

        # Legacy 3-blob shape (post-041 backfill): sin claves estructuradas.
        if "sobre_mi" not in data and ("resumen" in data or "enfoque" in data):
            formacion_blob = data.get("formacion")
            formacion_items: list[dict] = (
                [{"titulo": formacion_blob.strip(), "institucion": "", "anio": None}]
                if isinstance(formacion_blob, str) and formacion_blob.strip()
                else []
            )
            resumen = data.get("resumen")
            return cls(
                sobre_mi=resumen if isinstance(resumen, str) and resumen.strip() else None,
                formacion=formacion_items,
            )

        def _as_list(value: object) -> list:
            return value if isinstance(value, list) else []

        sobre_mi_raw = data.get("sobre_mi")
        return cls(
            sobre_mi=sobre_mi_raw if isinstance(sobre_mi_raw, str) and sobre_mi_raw.strip() else None,
            formacion=_as_list(data.get("formacion")),
            experiencia=_as_list(data.get("experiencia")),
            tratamientos=_as_list(data.get("tratamientos")),
            certificaciones=_as_list(data.get("certificaciones")),
            idiomas=_as_list(data.get("idiomas")),
        )
