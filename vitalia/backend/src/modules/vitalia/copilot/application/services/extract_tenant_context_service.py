# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""ExtractTenantContextService — extract clinic identity from website/documents.

Orchestrates LLM-based extraction of tenant context:
- Scrape clinic website URL
- Parse uploaded documents (PDFs, text)
- Merge extracted slot values into the OnboardingDraft

No PHI: wizard onboarding config only (clinic name, vertical, location).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog

from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
from src.modules.vitalia.copilot.domain.entities.wizard_slot import WizardSlot

logger = structlog.get_logger()


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class ExtractTenantContextService:
    """Application service for extracting tenant context into wizard slots.

    Calls website scraper and/or document extractor adapters, then
    merges extracted values into the OnboardingDraft slots.

    Dependencies injected — no direct DB or HTTP imports.
    """

    def __init__(
        self,
        draft_repo: "object",
        website_scraper: "object",
        document_extractor: "object",
    ) -> None:
        """Initialize with injected adapters."""
        self._draft_repo = draft_repo
        self._website_scraper = website_scraper
        self._document_extractor = document_extractor

    async def extract(
        self,
        *,
        draft_id: UUID,
        tenant_id: UUID,
        url: Optional[str],
        text_content: Optional[str],
    ) -> OnboardingDraft:
        """Extract tenant context from URL and/or text, merge into draft.

        Calls website_scraper when url is provided.
        Calls document_extractor when text_content is provided.
        Merges all extracted slot values (with confidence scores) into draft.

        Args:
            draft_id: OnboardingDraft to update.
            tenant_id: Tenant isolation identifier — always passed to adapters.
            url: Clinic website URL to scrape (optional).
            text_content: Freeform text or document content to parse (optional).

        Returns:
            Updated OnboardingDraft with extracted slot values filled in.
        """
        draft = await self._draft_repo.get_by_id(draft_id, tenant_id=tenant_id)

        # Collect all extractions: slot_id → (value, confidence)
        extracted: dict[str, tuple[str, float]] = {}

        if url:
            scraper_result = await self._website_scraper.extract(url=url, tenant_id=tenant_id)
            extracted.update(scraper_result)
            logger.info(
                "website_scraper_extracted",
                draft_id=str(draft_id),
                tenant_id=str(tenant_id),
                slots_found=list(scraper_result.keys()),
            )

        if text_content:
            doc_result = await self._document_extractor.extract(text=text_content, tenant_id=tenant_id)
            # Document extractor results override scraper results for same slot
            extracted.update(doc_result)
            logger.info(
                "document_extractor_extracted",
                draft_id=str(draft_id),
                tenant_id=str(tenant_id),
                slots_found=list(doc_result.keys()),
            )

        # Merge extracted values into draft slots
        for slot_id, (value, confidence) in extracted.items():
            new_slot = WizardSlot(
                slot_id=slot_id,
                value=value,
                confidence=confidence,
                confirmed_at=None,  # Not confirmed yet — requires user confirmation
                source="extracted",
            )
            draft.update_slot(slot_id, new_slot)

        draft.updated_at = _utc_now()
        saved = await self._draft_repo.save(draft)
        logger.info(
            "tenant_context_extracted",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            total_slots_updated=len(extracted),
        )
        return saved
