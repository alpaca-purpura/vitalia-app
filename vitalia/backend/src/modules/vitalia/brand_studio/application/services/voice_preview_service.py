# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""VoicePreviewService — compile slot 5 BRAND_VOICE preview (deterministic, no LLM dispatch).

OQ-C resolution 2026-05-27:
  - BE endpoint /lisa/marca/voice-preview compiles slot 5 BRAND_VOICE server-side
  - In-process LRU cache + key=(tenant_id, profile_id, compiler_version, hash(blocks))
  - TTL: 1 hour (invalidated on PATCH personality)
  - Zero LLM calls — PersonalityCompiler.compile() is purely deterministic

Anti-creep: NO health_voice_validator.py, NO brand_voice_summary mirror.

downstream-regression-na: brand-local service vitalia
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()

_COMPILER_VERSION = "v2"
_SAMPLE_WHATSAPP_INTRO = "Hola, soy Valeria, tu asistente de "
_SAMPLE_EMAIL_INTRO = "Estimado paciente,\n\nNos complace acompañarte"

# In-process LRU cache — bounded 1000 entries (tenant scale moderate)
# Key: str (f"voice_preview:{tenant_id}:{profile_id}:{compiler_version}:{blocks_hash}")
# Value: tuple (sample_whatsapp, sample_email, compiled_at_isoformat)
_PREVIEW_CACHE: dict[str, tuple[str, str, str]] = {}
_MAX_CACHE_SIZE = 1000


def _build_cache_key(
    tenant_id: UUID,
    profile_id: UUID,
    compiler_version: str,
    blocks_hash: str,
) -> str:
    """Build cache key for voice preview."""
    return f"voice_preview:{tenant_id}:{profile_id}:{compiler_version}:{blocks_hash}"


def _hash_blocks(blocks: dict[str, Any]) -> str:
    """Deterministic hash of personality blocks for cache key."""
    serialized = json.dumps(blocks, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _extract_voice_excerpt(system_instruction: str) -> tuple[str, str]:
    """Extract two sample texts from compiled system_instruction.

    For WhatsApp: short greeting using first paragraph of system instruction.
    For email: longer reactivation using first two meaningful lines.

    Args:
        system_instruction: Full compiled system_instruction from PersonalityCompiler.

    Returns:
        Tuple of (whatsapp_sample, email_sample).
    """
    if not system_instruction:
        return (
            "Hola, soy tu asistente de salud. ¿Cómo puedo ayudarte hoy?",
            "Hola,\n\nQueríamos consultarte cómo te has sentido desde tu última visita.",
        )

    # Extract ASÍ HABLO block (Block 3) as basis for samples
    lines = [line.strip() for line in system_instruction.splitlines() if line.strip()]
    instruction_lines = [
        line
        for line in lines
        if not line.startswith("##") and not line.startswith("###") and not line.startswith("---") and len(line) > 20
    ]

    if instruction_lines:
        first_instruction = instruction_lines[0][:200]
        second_instruction = instruction_lines[1][:300] if len(instruction_lines) > 1 else ""
    else:
        first_instruction = "Acompaño con calidez y precisión clínica."
        second_instruction = "Mi objetivo es que te sientas en buenas manos."

    whatsapp_sample = f"Hola, soy tu asistente. {first_instruction[:100].rstrip('.')}. ¿En qué puedo ayudarte hoy?"
    email_sample = (
        f"Estimado paciente,\n\n"
        f"{first_instruction}\n\n"
        f"{second_instruction}\n\n"
        f"Si tienes alguna consulta, estamos a tu disposición."
    )
    return whatsapp_sample, email_sample


class VoicePreviewService:
    """Compile slot 5 BRAND_VOICE preview deterministic — NO LLM dispatch.

    OQ-C resolution: server-side cache (in-process LRU bounded 1000 entries).
    Compile pure-deterministic: PersonalityCompiler.compile() from engine.
    Cache key: f"voice_preview:{tenant_id}:{profile_id}:{compiler_version}:{hash(blocks)}"
    Cache invalidated by: MarcaService.patch_personality() post-commit.
    """

    def __init__(self) -> None:
        """Initialize VoicePreviewService."""

    async def get_preview(
        self,
        *,
        tenant_id: UUID,
        personality_profile_id: UUID,
        system_instruction: str,
        blocks: dict[str, Any],
    ) -> tuple[str, str, bool]:
        """Get voice preview for tenant.

        Args:
            tenant_id: Tenant UUID.
            personality_profile_id: Profile UUID.
            system_instruction: Compiled system instruction.
            blocks: Dict of personality blocks for cache key hashing.

        Returns:
            Tuple (sample_whatsapp, sample_email_reactivation, cache_hit).
        """
        blocks_hash = _hash_blocks(blocks)
        cache_key = _build_cache_key(tenant_id, personality_profile_id, _COMPILER_VERSION, blocks_hash)

        cached = _PREVIEW_CACHE.get(cache_key)
        if cached:
            logger.debug(
                "voice_preview_cache_hit",
                tenant_id=str(tenant_id),
                profile_id=str(personality_profile_id),
                cache_key=cache_key[:32],
            )
            return cached[0], cached[1], True

        # Cache miss — compile from system_instruction
        sample_whatsapp, sample_email = _extract_voice_excerpt(system_instruction)

        # Evict oldest if at capacity
        if len(_PREVIEW_CACHE) >= _MAX_CACHE_SIZE:
            oldest_key = next(iter(_PREVIEW_CACHE))
            del _PREVIEW_CACHE[oldest_key]

        now_iso = datetime.now(timezone.utc).isoformat()
        _PREVIEW_CACHE[cache_key] = (sample_whatsapp, sample_email, now_iso)

        logger.info(
            "voice_preview_compiled",
            tenant_id=str(tenant_id),
            profile_id=str(personality_profile_id),
            cache_size=len(_PREVIEW_CACHE),
        )
        return sample_whatsapp, sample_email, False

    async def invalidate(self, *, tenant_id: UUID) -> None:
        """Invalidate all voice preview cache entries for a tenant.

        Called by MarcaService.patch_personality() post-commit.

        Args:
            tenant_id: Tenant UUID — invalidate all matching entries.
        """
        prefix = f"voice_preview:{tenant_id}:"
        keys_to_delete = [k for k in _PREVIEW_CACHE if k.startswith(prefix)]
        for key in keys_to_delete:
            del _PREVIEW_CACHE[key]
        logger.info(
            "voice_preview_cache_invalidated",
            tenant_id=str(tenant_id),
            evicted_count=len(keys_to_delete),
        )
