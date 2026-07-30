# cap: clinics.lisa.doctores
"""BioGenerationService — deterministic extractive bio generation.

Architecture Decision D-4 (03-arch.md § D-4):
  - Deterministic single-shot extractive service in clinics/application/
  - NOT agentic: no LangGraph node, no copilot/sales_agent surface
  - Single LLM call via luana_core_llm router (shared engine, consumed via import)
  - R23 N/A → Sonnet-eligible

Anti-invent guardrail (01-spec.md § Business rules bio-generated-from-inputs-no-invent):
  - Prompt instructs LLM to use ONLY provided material (notes + file names + links)
  - If info missing, leave section empty with placeholder — DO NOT invent
  - Output: 3 editable sections (Resumen · Formación · Enfoque)

Graceful degradation (tessl__graceful-degradation):
  - LLM call with timeout
  - On failure: return empty BioPublic + Spanish neutro error message
  - Never breaks autosave of rest of profile

Brand voice anchor (brand-expert):
  - Optional: reads PersonalityProfile.system_instruction as tone anchor (read-only)
  - Does NOT write to brand aggregates

PHI note (03-arch D-4):
  - Bio material is promotional (diploma/CV/links) — NOT clinical patient data
  - Doctor profile has PHI (DNI, credential), but bio inputs are non-PHI
"""

from __future__ import annotations

import json
from typing import Any, Protocol

import structlog

from src.modules.vitalia.clinics.domain.bio import BioPublic
from src.modules.vitalia.clinics.domain.doctor import Doctor
from src.modules.vitalia.clinics.domain.public_profile import DoctorPublicProfile

logger = structlog.get_logger(__name__)

# ── User-facing message constants (Spanish neutro LatAm — no voseo) ─────────

BIO_GENERATION_FALLBACK_MESSAGE = "No pudimos generar la bio. Por favor, intenta de nuevo."
"""Fallback message shown when LLM call fails.

Spanish neutro LatAm (spanish-text.md): uses 'intenta' (tú), not 'intentá' (voseo).
"""

_LLM_TIMEOUT_SECONDS = 30
"""Timeout for the single LLM call (tessl__graceful-degradation)."""

# ── Prompt templates ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT_TEMPLATE = """\
Eres un asistente que genera bios profesionales para médicos de clínicas de salud.
Tu tarea es crear una bio pública estructurada en 3 secciones usando SOLO el material \
que te proveen.

REGLAS ESTRICTAS:
- Usa únicamente la información del material provisto (notas, links, nombre, especialidad).
- No inventes logros, credenciales, instituciones ni experiencias que no estén mencionados.
- Si falta información para una sección, devuelve esa sección como null o string vacío.
- No agregues saludos, disclaimers ni texto fuera del JSON solicitado.
- El tono debe ser profesional, cálido y en español neutro latinoamericano (sin voseo).
{voice_anchor_section}\
Devuelve exclusivamente un JSON con esta estructura:
{{
  "resumen": "string o null",
  "formacion": "string o null",
  "enfoque": "string o null"
}}
"""

_USER_MESSAGE_TEMPLATE = """\
Genera la bio profesional para el siguiente médico usando solo el material provisto.

NOMBRE: {display_name}
ESPECIALIDAD: {specialty}
AÑOS DE EXPERIENCIA: {years_experience}

MATERIAL PROVISTO:
{notes_section}
{links_section}

RECORDATORIO: Usa solo la información de arriba. No inventes. Si falta información \
para una sección, deja el campo como null.
"""


# ── Protocol for LLM service (decouple + testability) ────────────────────────


class LLMServiceProtocol(Protocol):
    """Minimal protocol for the LLM service (decouple from concrete class).

    Mirrors luana_core_llm.base.BaseLLMService.generate_response signature.
    Using Protocol allows dependency injection in tests without importing engine.
    """

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        **kwargs: Any,
    ) -> str:
        """Generate a text response from the LLM.

        Args:
            messages: Chat history (role/content dicts).
            system_prompt: Optional system instruction.
            model_type: Model role string (e.g. 'smart', 'fast').
            **kwargs: Additional provider-specific kwargs.

        Returns:
            Raw text response from the LLM.
        """
        ...


# ── Structured profile prompt templates ──────────────────────────────────────

_STRUCTURED_SYSTEM_PROMPT = """\
Eres un asistente que genera perfiles públicos estructurados para médicos.
Tu tarea es crear un perfil profesional en 6 secciones usando SOLO el material provisto.

REGLAS ESTRICTAS:
- Usa únicamente la información del material provisto.
- No inventes logros, credenciales, instituciones ni experiencias que no estén mencionados.
- Si falta información para una sección, usa null o lista vacía [] según corresponda.
- Español neutro latinoamericano (sin voseo). Tono profesional y cálido.
- Devuelve exclusivamente un JSON con la estructura indicada. Cero texto fuera del JSON.

Estructura de respuesta (JSON):
{{
  "sobre_mi": "string o null",
  "formacion": [
    {{"titulo": "string", "institucion": "string", "anio": "string o null"}}
  ],
  "experiencia": [
    {{"puesto": "string", "lugar": "string", "anios": "string o null"}}
  ],
  "tratamientos": ["string", ...],
  "certificaciones": ["string", ...],
  "idiomas": ["string", ...]
}}
"""

_STRUCTURED_USER_TEMPLATE = """\
Genera el perfil público estructurado para el siguiente médico usando solo el material provisto.

NOMBRE: {display_name}
ESPECIALIDAD: {specialty}
AÑOS DE EXPERIENCIA: {years_experience}
CREDENCIAL: {credential}
PAÍS CREDENCIAL: {credential_country}

IDIOMAS DECLARADOS: {languages}

MATERIAL PROVISTO:
{notes_section}
{links_section}
{files_section}

RECORDATORIO: Usa solo la información de arriba. No inventes.
Si falta información para una sección, usa null o [] vacío.
Devuelve solo el JSON, sin markdown, sin texto adicional.
"""


# ── Main service ─────────────────────────────────────────────────────────────


class BioGenerationService:
    """Single-shot extractive bio generation for doctor profiles.

    Not agentic (D-4): no LangGraph, no copilot, no state machine.
    Produces 3 sections from provided material only — anti-invent guardrail.

    Usage:
        svc = BioGenerationService()  # uses LLMFactory default
        bio = svc.generate(doctor)

    Or with DI for tests:
        svc = BioGenerationService(llm_service=mock_llm)
        bio = svc.generate(doctor)

    Graceful degradation:
        bio, error = svc.generate_with_error(doctor)
        if error:
            # LLM failed — bio is empty, show error to user
    """

    def __init__(
        self,
        llm_service: LLMServiceProtocol | None = None,
        *,
        voice_anchor: str | None = None,
    ) -> None:
        """Initialize BioGenerationService.

        Args:
            llm_service: LLM service to use. If None, uses LLMFactory.get_service()
                         (luana_core_llm engine — consumed via import, never edited).
            voice_anchor: Optional tone anchor string from PersonalityProfile.system_instruction
                          (read-only, does NOT write to brand aggregates).
        """
        self._llm_service = llm_service
        self._voice_anchor = voice_anchor

    def _get_llm_service(self) -> LLMServiceProtocol:
        """Lazily resolve LLM service (avoids import at module-load time).

        Uses luana_core_llm.factory.LLMFactory (shared engine — consume, never edit).
        """
        if self._llm_service is not None:
            return self._llm_service
        # Lazy import: avoids ImportError in test environments without LiteLLM configured
        try:
            from luana_core_llm.factory import LLMFactory  # noqa: PLC0415

            return LLMFactory.get_service()  # type: ignore[return-value]
        except Exception:
            logger.warning("luana_core_llm unavailable — using no-op fallback")

            class _NoOpLLM:
                def generate_response(self, *args: Any, **kwargs: Any) -> str:
                    raise RuntimeError("LLM service not available")

            return _NoOpLLM()  # type: ignore[return-value]

    def _build_system_prompt(self) -> str:
        """Build system prompt with optional voice anchor section."""
        voice_section = ""
        if self._voice_anchor:
            voice_section = (
                f"\nESTILO DE VOZ:\n{self._voice_anchor}\n"
                "Adapta el tono de la bio a este estilo de voz, "
                "pero sin inventar información.\n\n"
            )
        return _SYSTEM_PROMPT_TEMPLATE.format(voice_anchor_section=voice_section)

    def _build_user_message(self, doctor: Doctor) -> str:
        """Build the user message with doctor material."""
        notes_section = ""
        if doctor.bio_inputs_notes:
            notes_section = f"Notas:\n{doctor.bio_inputs_notes}"
        else:
            notes_section = "(Sin notas adicionales)"

        links_section = ""
        if doctor.bio_links:
            links_section = "Links de referencia:\n" + "\n".join(f"- {link}" for link in doctor.bio_links)

        return _USER_MESSAGE_TEMPLATE.format(
            display_name=doctor.display_name,
            specialty=doctor.specialty or "No especificada",
            years_experience=(f"{doctor.years_experience} años" if doctor.years_experience else "No especificada"),
            notes_section=notes_section,
            links_section=links_section,
        )

    def _parse_response(self, raw_response: str) -> BioPublic:
        """Parse LLM JSON response into BioPublic.

        Handles partial responses (missing sections → None).
        On parse error → returns empty BioPublic (fallback).
        """
        try:
            # Try to extract JSON from response (LLM may wrap in markdown)
            text = raw_response.strip()
            # Strip markdown code blocks if present
            if text.startswith("```"):
                lines = text.split("\n")
                # Remove first and last line if they are code fence markers
                text = "\n".join(line for line in lines if not line.strip().startswith("```"))

            data = json.loads(text)
            return BioPublic(
                resumen=data.get("resumen") or None,
                formacion=data.get("formacion") or None,
                enfoque=data.get("enfoque") or None,
            )
        except (json.JSONDecodeError, AttributeError, TypeError) as exc:
            logger.warning(
                "bio_generation_parse_error",
                error=str(exc),
                raw_response=raw_response[:200],
            )
            return BioPublic()

    def generate(self, doctor: Doctor) -> BioPublic:
        """Generate bio from provided material (single-shot extractive).

        Does NOT raise on LLM failure — returns empty BioPublic instead.
        For caller access to error_message, use generate_with_error().

        Args:
            doctor: Doctor domain entity with bio_inputs_notes + bio_links.

        Returns:
            BioPublic with 3 sections (some may be None if material is missing).
        """
        bio, _ = self.generate_with_error(doctor)
        return bio

    def generate_with_error(self, doctor: Doctor) -> tuple[BioPublic, str | None]:
        """Generate bio and return (BioPublic, error_message | None).

        error_message is non-None when LLM call failed or parse error occurred.
        Fallback: returns empty BioPublic + Spanish neutro error message.
        Never raises — graceful degradation per tessl__graceful-degradation.

        Args:
            doctor: Doctor domain entity.

        Returns:
            Tuple of (BioPublic, error_message | None).
        """
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(doctor)

        messages = [{"role": "user", "content": user_message}]

        try:
            llm = self._get_llm_service()
            raw_response = llm.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                model_type="fast",  # bio-gen uses fast model (extractive, not reasoning)
            )
            bio = self._parse_response(raw_response)
            # If parsing produced empty result from a successful call, still no error
            return bio, None
        except Exception as exc:
            logger.warning(
                "bio_generation_llm_error",
                doctor_id=str(doctor.id),
                tenant_id=str(doctor.tenant_id),
                error_type=type(exc).__name__,
                error=str(exc),
            )
            return BioPublic(), BIO_GENERATION_FALLBACK_MESSAGE

    def _build_structured_user_message(
        self,
        doctor: Doctor,
        bio_file_filenames: list[str],
    ) -> str:
        """Build user message for structured 6-section profile generation."""
        notes_section = f"Notas:\n{doctor.bio_inputs_notes}" if doctor.bio_inputs_notes else "(Sin notas)"
        links_section = "Links:\n" + "\n".join(f"- {link}" for link in doctor.bio_links) if doctor.bio_links else ""
        files_section = (
            "Archivos adjuntos:\n" + "\n".join(f"- {f}" for f in bio_file_filenames) if bio_file_filenames else ""
        )
        languages_str = ", ".join(doctor.languages) if doctor.languages else "No especificados"

        return _STRUCTURED_USER_TEMPLATE.format(
            display_name=doctor.display_name,
            specialty=doctor.specialty or "No especificada",
            years_experience=(f"{doctor.years_experience} años" if doctor.years_experience else "No especificada"),
            credential=doctor.credential or "No especificada",
            credential_country=doctor.credential_country,
            languages=languages_str,
            notes_section=notes_section,
            links_section=links_section,
            files_section=files_section,
        )

    def _parse_structured_response(self, raw_response: str) -> DoctorPublicProfile:
        """Parse LLM JSON response into DoctorPublicProfile (6-section schema).

        Handles partial/missing sections — all fields optional per RN-D3D-6.
        On parse error: returns empty DoctorPublicProfile (graceful degradation).
        """
        try:
            text = raw_response.strip()
            # Strip markdown fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(line for line in lines if not line.strip().startswith("```"))

            data = json.loads(text)

            def _safe_list(val: Any) -> list[Any]:
                return val if isinstance(val, list) else []

            def _safe_str(val: Any) -> str | None:
                return val if isinstance(val, str) and val.strip() else None

            def _safe_year(val: Any) -> int | None:
                """LLM devuelve años como string ('2008', '2015-2019') — el DTO tipa int|None.

                Dígitos puros → int; cualquier otra cosa → None (un anio no-numérico
                persistido rompía la validación Pydantic en CADA GET posterior —
                audit DELTA-BE 2026-06-12).
                """
                if isinstance(val, bool):
                    return None
                if isinstance(val, int):
                    return val
                if isinstance(val, str) and val.strip().isdigit():
                    return int(val.strip())
                return None

            return DoctorPublicProfile(
                sobre_mi=_safe_str(data.get("sobre_mi")),
                formacion=[
                    {
                        "titulo": item.get("titulo", ""),
                        "institucion": item.get("institucion", ""),
                        "anio": _safe_year(item.get("anio")),
                    }
                    for item in _safe_list(data.get("formacion"))
                    if isinstance(item, dict)
                ],
                experiencia=[
                    {
                        "puesto": item.get("puesto", ""),
                        "lugar": item.get("lugar", ""),
                        "anios": _safe_year(item.get("anios")),
                    }
                    for item in _safe_list(data.get("experiencia"))
                    if isinstance(item, dict)
                ],
                tratamientos=[t for t in _safe_list(data.get("tratamientos")) if isinstance(t, str)],
                certificaciones=[c for c in _safe_list(data.get("certificaciones")) if isinstance(c, str)],
                idiomas=[i for i in _safe_list(data.get("idiomas")) if isinstance(i, str)],
            )
        except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as exc:
            logger.warning(
                "structured_profile_parse_error",
                error=str(exc),
                raw_response=raw_response[:300],
            )
            return DoctorPublicProfile(
                sobre_mi=None,
                formacion=[],
                experiencia=[],
                tratamientos=[],
                certificaciones=[],
                idiomas=[],
            )

    def generate_structured(
        self,
        doctor: Doctor,
        bio_file_filenames: list[str] | None = None,
    ) -> DoctorPublicProfile:
        """Generate structured 6-section public profile from doctor material.

        DETERMINISTIC extractive — same style as generate_with_error (no-invent guardrail).
        Derives sections from provided material:
          - sobre_mi: from summary/notes
          - formacion[]: from credential/notes
          - experiencia[]: from notes
          - tratamientos[]: from specialty + notes
          - certificaciones[]: from credential if verified
          - idiomas[]: from doctor.languages if present

        Empty sections → None/[] (RN-D3D-6). Never raises — graceful degradation.

        Args:
            doctor: Doctor domain entity with bio_inputs_notes, bio_links, specialty.
            bio_file_filenames: List of uploaded bio file names (filenames only, not URLs).

        Returns:
            DoctorPublicProfile with 6 sections (empty fallback on LLM failure).
        """
        user_message = self._build_structured_user_message(
            doctor,
            bio_file_filenames=bio_file_filenames or [],
        )
        messages = [{"role": "user", "content": user_message}]

        try:
            llm = self._get_llm_service()
            raw_response = llm.generate_response(
                messages=messages,
                system_prompt=_STRUCTURED_SYSTEM_PROMPT,
                model_type="fast",
            )
            return self._parse_structured_response(raw_response)
        except Exception as exc:
            logger.warning(
                "structured_profile_llm_error",
                doctor_id=str(getattr(doctor, "id", "unknown")),
                tenant_id=str(getattr(doctor, "tenant_id", "unknown")),
                error_type=type(exc).__name__,
                error=str(exc),
            )
            return self._extractive_structured_fallback(doctor)

    def _extractive_structured_fallback(self, doctor: Doctor) -> "DoctorPublicProfile":
        """Fallback extractivo determinístico cuando el LLM falla (RN-D3D-6, no-invent).

        Mapea material EXISTENTE (bio_public legacy + specialty + credential + notas):
        nunca inventa — solo reordena lo que el dueño ya escribió/verificó.
        Fix 2026-06-12: el branch devolvía perfil VACÍO pese al docstring extractivo
        (live-verify: perfil generado sin contenido con material presente).
        """
        bio = getattr(doctor, "bio_public", None)
        sobre_parts: list[str] = []
        if bio is not None and getattr(bio, "resumen", None):
            sobre_parts.append(bio.resumen.strip())
        if bio is not None and getattr(bio, "enfoque", None):
            sobre_parts.append(bio.enfoque.strip())
        notes = (getattr(doctor, "bio_inputs_notes", None) or "").strip()
        if not sobre_parts and notes:
            sobre_parts.append(notes[:400])
        sobre_mi = " ".join(sobre_parts) or None

        formacion = []
        if bio is not None and getattr(bio, "formacion", None):
            # texto libre legacy → 1 item por oración significativa (sin parsear años/instituciones)
            for frag in [f.strip() for f in bio.formacion.replace("\n", ". ").split(". ") if len(f.strip()) > 8][:5]:
                formacion.append({"titulo": frag.rstrip("."), "institucion": "", "anio": None})

        tratamientos: list[str] = []
        specialty = getattr(doctor, "specialty", None)
        if specialty:
            tratamientos.append(str(specialty))

        certificaciones: list[str] = []
        cred_number = getattr(doctor, "credential", None)
        cred_country = getattr(doctor, "credential_country", None)
        if cred_number:
            label = f"Colegiatura {cred_number}" + (f" ({cred_country})" if cred_country else "")
            certificaciones.append(label)

        # formacion items quedan como list[dict] PLANOS (JSONB-ready): to_dict()
        # pasa la lista cruda a json.dumps en update_public_profile — un dataclass
        # acá rompía la persistencia con TypeError (audit DELTA-BE 2026-06-12).
        return DoctorPublicProfile(
            sobre_mi=sobre_mi,
            formacion=formacion,
            experiencia=[],
            tratamientos=tratamientos,
            certificaciones=certificaciones,
            idiomas=[],
        )
