"""BrandVoiceService — concrete adapter implementing BrandVoicePort.

Story 7 D-T3 introduction (per ADR-001 §2.4 + Session 3 ratificación).

This adapter wraps the engine internals:

- ``PersonalityCompiler`` (SSoT in ``brand_studio.domain.personality``)
- ``PersonalityProfileRepository`` (SQLA sync repo in
  ``brand_studio.infrastructure.repositories``)

and exposes the async ``BrandVoicePort`` interface for cross-package
consumers (notably ``luana-core-sales-agent`` slot 5 BRAND_VOICE prefix).

Cardinal invariants:

- Does NOT modify ``PersonalityCompiler.compile()`` signature (Story 5
  SSoT cement — arch fitness V-AG-7 enforces).
- Does NOT move ``PersonalityCompiler`` out of ``domain.personality``.
- Falls back to empty / default values when tenant has no active
  ``PersonalityProfile`` (consumer side handles default voice path).
- Best-effort design: errors during compile fall back to empty string +
  structlog warning, never propagate to the consumer's hot path.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from luana_core_brand_studio.domain.personality import (
    LinguisticPatterns,
    PersonalityCompiler,
    PersonalityDimensions,
    SampleExchange,
)

if TYPE_CHECKING:
    from luana_core_brand_studio.infrastructure.repositories.personality_repository import (
        PersonalityProfileRepository,
    )

logger = structlog.get_logger()


class BrandVoiceService:
    """Concrete adapter implementing :class:`BrandVoicePort`.

    Per ADR-001 §2.4 — engine lives in
    ``luana_core_brand_studio.domain.personality``. Consumer
    (``luana-core-sales-agent``) injects this adapter via DI factory
    pattern (FastAPI ``Depends`` in nicolify shell composition root).

    Structural conformance: ``BrandVoicePort`` is
    ``@runtime_checkable`` Protocol — ``BrandVoiceService`` satisfies
    by method signatures. ``isinstance(service, BrandVoicePort)`` returns
    True at runtime.

    Notes:
        - The underlying repository is sync (Session-based). Async
          methods here bridge to sync calls — acceptable because
          consumers wrap this in async cache layers (compose_prompt
          slot 5 cache prefix is computed at most once per tenant per
          5 min TTL).
        - When the cached ``system_instruction`` ORM column is
          populated, we return it directly (saves a recompile). When
          empty/stale, we recompile from JSONB pillars on the fly.
    """

    def __init__(
        self,
        repo: PersonalityProfileRepository,
        compiler: PersonalityCompiler | None = None,
    ) -> None:
        """Initialize adapter.

        Args:
            repo: Sync :class:`PersonalityProfileRepository` (Session-based).
            compiler: Optional ``PersonalityCompiler`` instance. The
                compiler's ``compile`` is a static method, so the
                argument exists for DI / test override only — default
                uses the static method directly.
        """
        self._repo = repo
        self._compiler = compiler or PersonalityCompiler

    async def compile_system_instruction(self, tenant_id: UUID) -> str:
        """Return the compiled 5-block system_instruction for the tenant.

        Resolution order:

        1. Active ``PersonalityProfile`` exists → return cached
           ``system_instruction`` ORM column if populated, else compile
           on the fly via ``PersonalityCompiler.compile()``.
        2. No active profile → return ``""`` (consumer falls back to
           specialist default voice).

        Errors during compile log a structlog warning and return ``""``
        so the consumer never breaks on a degraded brand-studio state.
        """
        try:
            model = self._repo.get_active(tenant_id=tenant_id)
        except Exception as exc:  # pragma: no cover — best-effort wrap
            logger.warning(
                "brand_voice_service.get_active_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return ""

        if model is None:
            logger.debug(
                "brand_voice_service.no_profile_fallback_empty",
                tenant_id=str(tenant_id),
            )
            return ""

        # Prefer cached compiled value if present.
        cached = getattr(model, "system_instruction", None)
        if cached:
            return cached

        # Fallback — compile from JSONB pillars on the fly.
        try:
            dimensions = PersonalityDimensions(**(model.dimensions or {}))
            patterns = LinguisticPatterns(**(model.linguistic_patterns or {}))
            exchanges_raw = model.sample_exchanges or []
            exchanges = [SampleExchange(**ex) for ex in exchanges_raw]
            return self._compiler.compile(dimensions, patterns, exchanges)
        except Exception as exc:  # pragma: no cover — best-effort wrap
            logger.warning(
                "brand_voice_service.compile_failed",
                tenant_id=str(tenant_id),
                profile_id=str(getattr(model, "id", "?")),
                error=str(exc),
            )
            return ""

    async def get_voice_metadata(self, tenant_id: UUID) -> dict:
        """Return voice metadata for prompt cache invalidation + routing.

        Schema (matches :class:`BrandVoicePort`):

        - ``personality_profile_version: int`` — bumps on profile
          update. ORM model currently has no explicit ``version``
          column; falls back to ``1`` when profile present, ``0`` when
          absent.
        - ``last_compiled_at: datetime | None`` — uses ORM
          ``updated_at`` when present, falls back to ``created_at``,
          else ``None``.
        - ``dimensions_summary: dict`` — JSONB dimensions dict copied
          out. Empty dict when no profile.
        """
        try:
            model = self._repo.get_active(tenant_id=tenant_id)
        except Exception as exc:  # pragma: no cover — best-effort wrap
            logger.warning(
                "brand_voice_service.get_active_failed_metadata",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            return self._empty_metadata()

        if model is None:
            return self._empty_metadata()

        last_compiled_at: datetime | None = getattr(model, "updated_at", None) or getattr(model, "created_at", None)
        dimensions_summary = dict(model.dimensions or {})

        return {
            "personality_profile_version": getattr(model, "version", 1),
            "last_compiled_at": last_compiled_at,
            "dimensions_summary": dimensions_summary,
        }

    @staticmethod
    def _empty_metadata() -> dict:
        return {
            "personality_profile_version": 0,
            "last_compiled_at": None,
            "dimensions_summary": {},
        }
