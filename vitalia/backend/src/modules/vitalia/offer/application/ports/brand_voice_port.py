# cap: lisa.servicios
"""BrandVoicePort — read-only access to the tenant brand voice (lisa-marca).

Used to draft service descriptions in the tenant voice. NEVER mirrors or
fine-tunes voice (sales-agent-brand-voice rule). Degrades gracefully to an
identity passthrough when the voice source is unavailable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class BrandVoicePort(ABC):
    """Draft text in the tenant brand voice (RN-23 read-only with origin)."""

    @abstractmethod
    async def draft_description(self, *, tenant_id: UUID, raw: str) -> str:
        """Return ``raw`` rewritten in the tenant voice (or ``raw`` unchanged on degrade)."""
