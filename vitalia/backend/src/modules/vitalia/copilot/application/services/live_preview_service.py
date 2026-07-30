# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""LivePreviewService — orchestrates WhatsApp + landing live preview generation.

Combines SimulatePersonalityService (sample brand voice message) and a
server-side HTML renderer from BrandStudioDraft data. Used during the
onboarding wizard to give tenants a real-time preview of their brand
voice and landing page copy before committing.

No PHI involved: brand voice samples + landing copy only (clinic name,
tagline, vertical — not patient data).
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from src.modules.vitalia.copilot.application.services.simulate_personality_service import (
        SimulatePersonalityService,
    )
    from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
        BrandStudioDraftRepository,
    )

logger = structlog.get_logger()


def _render_landing_html(payload: dict) -> str:
    """Render a minimal landing snippet HTML from draft payload dict.

    Server-side only — produces a static HTML preview of brand identity
    fields for display in the wizard's LiveLandingSnippetPreview component.

    Args:
        payload: Draft payload dict (slot_id → extracted_value) from BrandStudioDraft.

    Returns:
        HTML string with available brand identity sections.
    """
    brand_name = html.escape(str(payload.get("brand_name", "")))
    tagline = html.escape(str(payload.get("tagline", "")))
    vertical = html.escape(str(payload.get("vertical", "")))
    location = html.escape(str(payload.get("location", "")))
    description = html.escape(str(payload.get("description", "")))

    parts: list[str] = ['<section class="landing-preview">']

    if brand_name:
        parts.append(f'  <h1 class="brand-name">{brand_name}</h1>')

    if tagline:
        parts.append(f'  <p class="tagline">{tagline}</p>')

    if vertical:
        parts.append(f'  <span class="vertical-badge">{vertical}</span>')

    if description:
        parts.append(f'  <p class="description">{description}</p>')

    if location:
        parts.append(f'  <address class="location">{location}</address>')

    parts.append("</section>")
    return "\n".join(parts)


class LivePreviewService:
    """Orchestrates Live WhatsApp Preview and Live Landing Snippet Preview.

    WhatsApp preview: delegates to SimulatePersonalityService (which owns
    throttle 5/min + 10-min cache TTL) to generate a sample brand-voice
    message for the given wizard draft.

    Landing preview: renders a server-side HTML snippet from the current
    BrandStudioDraft payload (brand identity, hero copy).

    Cache integration: simulate_personality_service handles throttle 5/min
    + cache 10-min TTL. LivePreviewService does not add its own cache layer.

    No PHI: brand voice samples + landing copy — not patient data.
    """

    def __init__(
        self,
        simulate_service: "SimulatePersonalityService",
        draft_repo: "BrandStudioDraftRepository",
    ) -> None:
        """Initialize with injected services.

        Args:
            simulate_service: Personality simulation service (owns throttle + cache).
            draft_repo: BrandStudioDraft repository for fetching draft state.
        """
        self._simulate = simulate_service
        self._drafts = draft_repo

    async def generate_whatsapp_preview(
        self,
        *,
        tenant_id: UUID,
        draft_id: UUID,
        scenario: str = "appointment_inquiry",
    ) -> dict:
        """Generate a sample WhatsApp-style message from the brand voice profile.

        Fetches the draft (with tenant isolation), extracts the partial voice
        profile, and delegates to SimulatePersonalityService.

        Args:
            tenant_id: Tenant isolation identifier.
            draft_id: BrandStudioDraft UUID to use for voice profile.
            scenario: Scenario context for the simulation (default: appointment_inquiry).

        Returns:
            Dict with keys:
              - sample_text (str): Generated brand-voice message sample.
              - cached (bool): True if simulate_service returned a cached result.
              - throttled (bool): Always False (ThrottleExceededError raised on throttle).

        Raises:
            ValueError: If draft not found for the given tenant_id + draft_id.
            ThrottleExceededError: If simulate_personality rate limit exceeded (from service).
        """
        draft = await self._drafts.get_by_id_tenant(tenant_id=tenant_id, draft_id=draft_id)
        if draft is None:
            raise ValueError(f"Draft {draft_id} not found for tenant {tenant_id}")

        profile_partial = draft.voice_profile_partial_json or {}

        simulate_response = await self._simulate.simulate(
            tenant_id=tenant_id,
            profile_partial=profile_partial,
            scenario=scenario,
        )

        logger.info(
            "live_preview_whatsapp_generated",
            tenant_id=str(tenant_id),
            draft_id=str(draft_id),
            scenario=scenario,
            cached=simulate_response.cache_hit,
        )

        return {
            "sample_text": simulate_response.sample_text,
            "cached": simulate_response.cache_hit,
            "throttled": False,
        }

    async def generate_landing_snippet(
        self,
        *,
        tenant_id: UUID,
        draft_id: UUID,
    ) -> dict:
        """Generate a server-side HTML landing snippet from draft brand identity.

        Fetches the draft (with tenant isolation) and renders its draft_payload
        into a minimal HTML section representing the landing page hero area.

        Args:
            tenant_id: Tenant isolation identifier.
            draft_id: BrandStudioDraft UUID to render.

        Returns:
            Dict with keys:
              - html (str): Server-rendered HTML snippet.
              - sections_included (list[str]): Keys from draft_payload that were rendered.

        Raises:
            ValueError: If draft not found for the given tenant_id + draft_id.
        """
        draft = await self._drafts.get_by_id_tenant(tenant_id=tenant_id, draft_id=draft_id)
        if draft is None:
            raise ValueError(f"Draft {draft_id} not found for tenant {tenant_id}")

        payload = draft.draft_payload or {}
        rendered_html = _render_landing_html(payload)

        logger.info(
            "live_preview_landing_generated",
            tenant_id=str(tenant_id),
            draft_id=str(draft_id),
            sections_count=len(payload),
        )

        return {
            "html": rendered_html,
            "sections_included": list(payload.keys()),
        }
