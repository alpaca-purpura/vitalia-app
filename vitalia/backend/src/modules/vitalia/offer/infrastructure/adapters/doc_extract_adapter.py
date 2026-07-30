# cap: lisa.servicios
"""DocExtractAdapter — one-shot document → service-field extraction (AC-11).

Wraps the engine copilot ``extract_from_doc`` capability. ONE-SHOT, NOT RAG
(no vector index). Sub-phase A degrade contract: the extractor is not wired yet,
so this returns an empty :class:`ExtractionPrefill` (with a ``source_label`` so
the UI can show provenance) and the autocomplete UX falls back to manual entry.
The seam is in place so the real extractor can swap in without touching callers.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from src.modules.vitalia.offer.application.ports.doc_extract_port import DocExtractPort, ExtractionPrefill

logger = structlog.get_logger()


class DocExtractAdapter(DocExtractPort):
    """One-shot doc extraction; degrades to an empty prefill on unavailability."""

    async def extract_from_document(
        self,
        *,
        tenant_id: UUID,
        filename: str | None = None,
        url: str | None = None,
        content: bytes | None = None,
    ) -> ExtractionPrefill:
        source_label = filename or url
        logger.info(
            "doc_extract_degraded_passthrough",
            tenant_id=str(tenant_id),
            source_label=source_label,
            has_content=content is not None,
        )
        # Sub-phase A: no engine extractor wired → empty editable prefill.
        return ExtractionPrefill(source_label=source_label)
