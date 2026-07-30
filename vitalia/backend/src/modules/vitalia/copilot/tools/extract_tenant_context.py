# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""LangChain @tool — extract_tenant_context (Valeria wizard).

Wraps :class:`ExtractTenantContextService` (T-be-services-1 produced).
Orchestrates 3 adapters: website_scraper, document_extractor, whisper_stt
(adapter layer applies tessl__graceful-degradation timeout + fallback).

Output: short summary string (LangGraph supervisor consumes the message via
the agent state, not the return value verbatim). Detail lives in the draft's
slot extractions persisted by the service.

Per 03-arch-agentic.md § 4.1 + 05-guidelines.md § 1.13:
  - ``@tool`` decorator with Pydantic v2 ``args_schema`` required
  - ``async def`` required
  - Calls SERVICE (never raw repos)
  - ``tenant_id: UUID`` mandatory
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()


class ExtractTenantContextInput(BaseModel):
    """Args schema for ``extract_tenant_context`` tool.

    Per design § 1.5: extracts only tenant configuration data (clinic name,
    vertical, location). NEVER PHI. The deepagents extract_subagent sandbox
    rejects PHI documents at the source.
    """

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    draft_id: UUID = Field(..., description="OnboardingDraft to update.")
    tenant_id: UUID = Field(..., description="Tenant isolation identifier.")
    url: str | None = Field(
        default=None,
        description="Clinic website URL (https). Optional. Scraped via website_scraper adapter.",
    )
    text_content: str | None = Field(
        default=None,
        description=(
            "Free-form text pasted by the user (clinic brief, social-media copy). "
            "Optional. Parsed via document_extractor adapter."
        ),
    )


# Module-level service factory hook — injected by composition root at startup.
# Tests override via monkeypatch.
_service_factory: Any = None


def set_extract_tenant_context_service_factory(factory: Any) -> None:  # noqa: ANN401
    """Wire the service factory (called by FastAPI lifespan)."""
    global _service_factory  # noqa: PLW0603 — DI hook by design
    _service_factory = factory


def get_extract_tenant_context_service() -> Any:  # noqa: ANN401
    """Resolve the service factory. Raises if not wired."""
    if _service_factory is None:
        raise RuntimeError(
            "extract_tenant_context_service factory not wired — "
            "call set_extract_tenant_context_service_factory at FastAPI lifespan startup.",
        )
    return _service_factory()


@tool("extract_tenant_context", args_schema=ExtractTenantContextInput)
async def extract_tenant_context(
    draft_id: UUID,
    tenant_id: UUID,
    url: str | None = None,
    text_content: str | None = None,
) -> str:
    """Extract clinic configuration (name, vertical, location) from URL or text.

    Calls :class:`ExtractTenantContextService` which orchestrates the website
    scraper + document extractor adapters. The service applies sanitization
    (engine ``sanitize_payload``) before persistence.

    Returns:
        Short summary string ("Extracted N slots from <sources>").
    """
    service = get_extract_tenant_context_service()
    try:
        draft = await service.extract(
            draft_id=draft_id,
            tenant_id=tenant_id,
            url=url,
            text_content=text_content,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort, surface to LLM as error string
        logger.warning(
            "vitalia.copilot.tools.extract_tenant_context_failed",
            draft_id=str(draft_id),
            tenant_id=str(tenant_id),
            error=str(exc),
        )
        return f"Error extracting tenant context: {type(exc).__name__}"

    sources: list[str] = []
    if url:
        sources.append("url")
    if text_content:
        sources.append("text")
    sources_str = " + ".join(sources) if sources else "none"

    # Count extracted slots (those with confidence > 0 + source=='extracted').
    extracted_count = 0
    for slot_map in (getattr(draft, "slots_required", {}), getattr(draft, "slots_optional", {})):
        for slot in slot_map.values():
            confidence = getattr(slot, "confidence", 0.0)
            source = getattr(slot, "source", "")
            if confidence > 0.0 and source == "extracted":
                extracted_count += 1

    return f"Extracted {extracted_count} slot(s) from {sources_str}. Draft: {draft_id}"


__all__ = [
    "ExtractTenantContextInput",
    "extract_tenant_context",
    "get_extract_tenant_context_service",
    "set_extract_tenant_context_service_factory",
]
