# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""BrandStudioDraft — domain entity for onboarding extraction staging area.

Stores intermediate extracted brand/personality data during onboarding wizard
before commitment to the canonical brand_settings on the tenants table.
Supports resumable extraction sessions with TTL via expires_at.

Not PHI: brand identity data only (clinic name, vertical, tone, voice samples).
Tenant-level isolation — single tenant_id filter (no clinic_id required).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class BrandStudioDraft:
    """Mutable entity representing an in-progress brand studio extraction session.

    Attributes:
        id: Unique draft identifier.
        tenant_id: Cardinal tenant isolation field. Every query MUST filter by this.
        user_id: Initiating user ID (admin starting onboarding).
        draft_kind: Type of draft — "onboarding_extraction" (Slice 1), extensible.
        draft_payload: Accumulated extraction results (slot_id → extracted_value dict).
        voice_profile_partial_json: Partial PersonalityProfile compilation in progress.
        committed_at: UTC timestamp when draft was committed to brand_settings. None = draft.
        expires_at: TTL for uncommitted drafts. None allowed for committed drafts.
        created_at: UTC timestamp of draft creation.
        updated_at: UTC timestamp of last modification.
    """

    id: UUID
    tenant_id: UUID
    user_id: UUID
    draft_kind: str
    draft_payload: dict
    voice_profile_partial_json: dict | None
    committed_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def merge_payload_patch(self, patch: dict) -> None:
        """Apply a shallow merge of patch into draft_payload.

        Existing keys are preserved if not overwritten by patch.
        New keys from patch are added.

        Args:
            patch: Dict of updates to merge into draft_payload.
        """
        self.draft_payload = {**self.draft_payload, **patch}
