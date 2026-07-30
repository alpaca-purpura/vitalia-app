# cap: lisa.servicios
"""DocumentAutocompleteService — one-shot doc/URL → editable prefill (T-2 § 6, AC-11).

Flow (NOT RAG, one-shot):
  1. :class:`DocExtractPort` returns an :class:`ExtractionPrefill` (graceful
     degrade → empty prefill when the engine extractor is not wired, Sub-phase A).
  2. The upload is recorded as an engine ``KnowledgeSource`` row through
     :class:`_KnowledgePort` so it is tracked / indexable later (indexer stub,
     status QUEUED in Sub-phase A).
  3. Returns the prefill + the knowledge-source id for the UI to pre-fill the form.

The KnowledgeSource write is best-effort: if it fails, the prefill still flows
back (autocomplete degrades, never hard-errors) and ``knowledge_source_id`` is
``None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import structlog

from src.modules.vitalia.offer.application.ports.doc_extract_port import DocExtractPort, ExtractionPrefill

logger = structlog.get_logger()


@dataclass(frozen=True)
class KnowledgeSourceRef:
    """Lightweight reference to a recorded engine KnowledgeSource."""

    id: UUID
    status: str


@dataclass(frozen=True)
class AutocompleteResult:
    """What the UI needs: the editable prefill + the tracked source (if recorded)."""

    prefill: ExtractionPrefill
    knowledge_source_id: UUID | None


class _KnowledgePort(Protocol):
    async def record_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        name: str,
        source_type: str,
        source_url: str | None = None,
        file_url: str | None = None,
    ) -> KnowledgeSourceRef: ...


class DocumentAutocompleteService:
    """One-shot document extraction → prefill, with the upload tracked as a source."""

    def __init__(self, *, extractor: DocExtractPort, knowledge: _KnowledgePort) -> None:
        self._extractor = extractor
        self._knowledge = knowledge

    async def autocomplete(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        filename: str | None = None,
        url: str | None = None,
        content: bytes | None = None,
    ) -> AutocompleteResult:
        if not url and not filename and content is None:
            raise ValueError("autocomplete requires a url or an uploaded file")

        prefill = await self._extractor.extract_from_document(
            tenant_id=tenant_id,
            filename=filename,
            url=url,
            content=content,
        )
        source_id = await self._record(
            tenant_id=tenant_id,
            offer_id=offer_id,
            filename=filename,
            url=url,
        )
        return AutocompleteResult(prefill=prefill, knowledge_source_id=source_id)

    async def _record(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        filename: str | None,
        url: str | None,
    ) -> UUID | None:
        source_type, name = _classify(filename=filename, url=url)
        try:
            ref = await self._knowledge.record_source(
                tenant_id=tenant_id,
                offer_id=offer_id,
                name=name,
                source_type=source_type,
                source_url=url,
                file_url=None,  # file storage wiring is Sub-phase A stub
            )
            return ref.id
        except Exception:  # noqa: BLE001 — recording is best-effort; prefill must survive
            logger.warning(
                "knowledge_source_record_degraded",
                tenant_id=str(tenant_id),
                offer_id=str(offer_id),
            )
            return None


def _classify(*, filename: str | None, url: str | None) -> tuple[str, str]:
    """Map an upload to (KnowledgeSourceType value, display name)."""
    if url:
        return "url_article", url
    name = filename or "documento"
    lower = name.lower()
    if lower.endswith(".pdf"):
        return "pdf", name
    if lower.endswith(".docx"):
        return "docx", name
    if lower.endswith((".txt",)):
        return "txt", name
    if lower.endswith((".md", ".markdown")):
        return "markdown", name
    return "pdf", name  # safe default for an uploaded doc
