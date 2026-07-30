# cap: lisa.servicios
"""RED-first unit tests for DocumentAutocompleteService (T-2 § 6, AC-11).

One-shot doc/URL → editable prefill (NOT RAG). The service:
  1. asks DocExtractPort for an ExtractionPrefill (graceful degrade → empty),
  2. records the upload as an engine KnowledgeSource row (so it is tracked /
     indexable later — Sub-phase A leaves the indexer a stub, status QUEUED),
  3. returns (prefill, knowledge_source_id) for the UI to pre-fill the form.

The KnowledgeSource write must NOT block the prefill: if recording fails the
service still returns the prefill (autocomplete UX degrades, never hard-errors).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.offer.application.ports.doc_extract_port import DocExtractPort, ExtractionPrefill
from src.modules.vitalia.offer.application.services.document_autocomplete_service import (
    DocumentAutocompleteService,
    KnowledgeSourceRef,
)

TENANT = UUID("11111111-1111-1111-1111-111111111111")
OFFER = UUID("44444444-4444-4444-4444-444444444444")


class _FakeExtract(DocExtractPort):
    def __init__(self, prefill: ExtractionPrefill) -> None:
        self._prefill = prefill

    async def extract_from_document(self, *, tenant_id, filename=None, url=None, content=None):
        return self._prefill


class _FakeKnowledgePort:
    def __init__(self, *, fail: bool = False) -> None:
        self.created: list[dict[str, object]] = []
        self._fail = fail

    async def record_source(self, *, tenant_id, offer_id, name, source_type, source_url=None, file_url=None):
        if self._fail:
            raise RuntimeError("engine knowledge write down")
        ref = KnowledgeSourceRef(id=uuid4(), status="queued")
        self.created.append({"name": name, "type": source_type, "url": source_url, "file": file_url})
        return ref


def _svc(prefill: ExtractionPrefill, *, knowledge_fail: bool = False):
    extract = _FakeExtract(prefill)
    knowledge = _FakeKnowledgePort(fail=knowledge_fail)
    return DocumentAutocompleteService(extractor=extract, knowledge=knowledge), knowledge


@pytest.mark.asyncio
async def test_extract_url_returns_prefill_and_records_source():
    prefill = ExtractionPrefill(description_long="Limpieza profesional", keywords=["limpieza"], source_label="art")
    svc, knowledge = _svc(prefill)
    result = await svc.autocomplete(tenant_id=TENANT, offer_id=OFFER, url="https://clinica/limpieza")
    assert result.prefill.description_long == "Limpieza profesional"
    assert result.knowledge_source_id is not None
    assert len(knowledge.created) == 1
    assert knowledge.created[0]["url"] == "https://clinica/limpieza"


@pytest.mark.asyncio
async def test_extract_file_records_source():
    prefill = ExtractionPrefill(source_label="ficha.pdf")
    svc, knowledge = _svc(prefill)
    result = await svc.autocomplete(
        tenant_id=TENANT,
        offer_id=OFFER,
        filename="ficha.pdf",
        content=b"%PDF-1.4",
    )
    assert result.knowledge_source_id is not None
    assert knowledge.created[0]["name"] == "ficha.pdf"


@pytest.mark.asyncio
async def test_degraded_extraction_still_returns_empty_prefill():
    svc, _ = _svc(ExtractionPrefill())  # extractor unavailable → empty prefill
    result = await svc.autocomplete(tenant_id=TENANT, offer_id=OFFER, url="https://x")
    assert result.prefill.description_long is None
    assert result.prefill.keywords == []


@pytest.mark.asyncio
async def test_knowledge_write_failure_does_not_block_prefill():
    prefill = ExtractionPrefill(description_long="ok")
    svc, _ = _svc(prefill, knowledge_fail=True)
    result = await svc.autocomplete(tenant_id=TENANT, offer_id=OFFER, url="https://x")
    assert result.prefill.description_long == "ok"
    assert result.knowledge_source_id is None  # recording failed, prefill survives


@pytest.mark.asyncio
async def test_requires_a_source():
    svc, _ = _svc(ExtractionPrefill())
    with pytest.raises(ValueError):
        await svc.autocomplete(tenant_id=TENANT, offer_id=OFFER)  # no url, no file
