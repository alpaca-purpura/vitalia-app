# cap: lisa.servicios
"""DocExtractPort — one-shot document → service field extraction (AC-11).

Consumes the engine copilot ``extract_from_doc`` capability. ONE-SHOT, NOT RAG
(no vector index). Sub-phase A: the infra impl may return an empty prefill when
the engine extractor is not wired — the autocomplete UX degrades to manual entry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class ExtractionPrefill:
    """Editable prefill suggested from an uploaded document/URL (all optional)."""

    description_long: str | None = None
    includes: str | None = None
    excludes: str | None = None
    procedure_steps: str | None = None
    aftercare: str | None = None
    risks: str | None = None
    keywords: list[str] = field(default_factory=list)
    source_label: str | None = None


class DocExtractPort(ABC):
    """Extract structured service fields from a document or URL."""

    @abstractmethod
    async def extract_from_document(
        self,
        *,
        tenant_id: UUID,
        filename: str | None = None,
        url: str | None = None,
        content: bytes | None = None,
    ) -> ExtractionPrefill:
        """Return an editable prefill. Empty prefill on unavailability (graceful degrade)."""
