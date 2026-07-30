# cap: lisa.servicios
"""BrandVoiceAdapter — read-only bridge to the tenant brand voice (lisa-marca).

RN-23: the voice is read-only with origin lisa-marca; this adapter NEVER mirrors
or fine-tunes it (``sales-agent-brand-voice`` rule). The voice SSoT is the
engine ``personality_profiles.system_instruction`` (SYNC repo, bridged via
``AsyncSession.run_sync``).

Sub-phase A degrade contract: when no active personality profile exists (or any
read fails), ``draft_description`` returns ``raw`` unchanged (identity
passthrough) — Lisa keeps the user's own copy. LLM rewriting in the tenant voice
is a later sub-phase; the seam is in place so it can swap in without touching
callers.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.modules.vitalia.offer.application.ports.brand_voice_port import BrandVoicePort

logger = structlog.get_logger()


class BrandVoiceAdapter(BrandVoicePort):
    """Drafts text in the tenant voice, degrading to passthrough on any failure."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def draft_description(self, *, tenant_id: UUID, raw: str) -> str:
        try:
            has_voice = await self._session.run_sync(_voice_available, tenant_id)
        except Exception as exc:  # noqa: BLE001 — graceful degrade, never break the write
            logger.warning("brand_voice_read_failed", tenant_id=str(tenant_id), error=str(exc))
            return raw
        if not has_voice:
            logger.info("brand_voice_unavailable_passthrough", tenant_id=str(tenant_id))
        # Sub-phase A: identity passthrough whether or not a voice exists.
        return raw


def _voice_available(sync_session: Session, tenant_id: UUID) -> bool:
    """Best-effort check that an active personality profile exists for the tenant."""
    from luana_core_brand_studio.infrastructure.repositories.personality_repository import (  # noqa: PLC0415
        PersonalityRepository,
    )

    repo = PersonalityRepository(sync_session)
    profile = repo.get_active(tenant_id=tenant_id)
    return profile is not None and bool(profile.system_instruction)
