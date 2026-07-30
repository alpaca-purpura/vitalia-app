# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Sandbox tools available to the wizard extract_subagent.

Per 03-arch-agentic.md § 3.2 + § 4.1 + tessl__deepagents:
  - 3 sub-tools: ``scrape_website_tool`` + ``parse_document_tool`` +
    ``transcribe_audio_tool``.
  - Explicit sandbox — registered as the SubAgent's only tools, parent
    toolset is NOT inherited (per F2 deepagents pattern + copilot-expert).
  - All external calls wrap timeout + fallback per tessl__graceful-degradation.

These tools are intentionally **placeholders for Slice 1 production wiring**:
they return structured dicts shaped like the design § 1.3 contract but they
do not perform real HTTP / Whisper calls (the real adapter wiring lives in
``vitalia/backend/src/modules/vitalia/copilot/infrastructure/adapters/``).
The wizard sub-agent uses the structured shape; production replaces these
internals with `WebsiteScraperAdapter`, `DocumentExtractorAdapter`,
`WhisperSTTAdapter` calls via service factories.

Why placeholders here, not adapters? The deepagents subagent runs inside
LangGraph; its tools MUST be ``@tool`` decorated callables that the subagent
LLM invokes. The structured contract is what the LLM sees — the actual
network call inside the function body is the swappable part.
"""

from __future__ import annotations

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════════
# Input schemas
# ════════════════════════════════════════════════════════════════════════════


class ScrapeWebsiteInput(BaseModel):
    """Args schema for scrape_website_tool."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    url: str = Field(..., description="HTTPS URL of the clinic website to scrape.")
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=60,
        description="HTTP timeout in seconds (default 30, capped at 60).",
    )


class ParseDocumentInput(BaseModel):
    """Args schema for parse_document_tool."""

    model_config = ConfigDict(from_attributes=True)

    text_content: str = Field(..., description="Plain text content (presentation, brief, copied page).")


class TranscribeAudioInput(BaseModel):
    """Args schema for transcribe_audio_tool."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    audio_url: str = Field(..., description="Temporary signed URL of audio file.")
    duration_seconds: int = Field(
        default=0,
        ge=0,
        description="Duration in seconds (≤60 enforced by extractor_subagent.md).",
    )


# ════════════════════════════════════════════════════════════════════════════
# Sandbox tools — LangChain @tool decorated, async-friendly
# ════════════════════════════════════════════════════════════════════════════
#
# Note: these are sync stubs (no `async def`) on purpose for Slice 1 — the real
# adapter swap (T-be-services-1 produced) wraps the actual network call in
# asyncio.timeout per tessl__graceful-degradation. The subagent invokes via
# the LangChain ToolNode, which handles sync/async both.


@tool("scrape_website_tool", args_schema=ScrapeWebsiteInput)
def scrape_website_tool(url: str, timeout_seconds: int = 30) -> dict:
    """Scrape a clinic website (sandbox).

    Returns:
        ``{"text": "...", "sections": [...], "warnings": [...]}`` — structured
        shape matching what the subagent system prompt expects.

    Placeholder implementation: returns a warning indicator for Slice 1 — the
    real `WebsiteScraperAdapter` call lives in the service layer
    (`ExtractTenantContextService` consumed via the parent
    ``extract_tenant_context`` tool). When the subagent surface is wired to
    the real adapter, swap the body.
    """
    logger.info(
        "vitalia.copilot.workflows.extract_subagent.scrape_website_invoked",
        url_hash=hash(url),
        timeout_seconds=timeout_seconds,
    )
    return {
        "text": "",
        "sections": [],
        "warnings": ["scrape_website_placeholder_slice_1"],
        "elapsed_seconds": 0.0,
    }


@tool("parse_document_tool", args_schema=ParseDocumentInput)
def parse_document_tool(text_content: str) -> dict:
    """Parse pasted plain text (sandbox).

    Returns:
        ``{"sections": [{"title": "...", "text": "..."}], "warnings": [...]}``.

    Placeholder: minimal section detection by blank-line split — production
    replaces with `DocumentExtractorAdapter`.
    """
    logger.info(
        "vitalia.copilot.workflows.extract_subagent.parse_document_invoked",
        text_length=len(text_content),
    )
    sections: list[dict] = []
    for chunk in (s.strip() for s in text_content.split("\n\n")):
        if not chunk:
            continue
        lines = chunk.split("\n", 1)
        title = lines[0][:80] if lines else ""
        body = lines[1] if len(lines) > 1 else ""
        sections.append({"title": title, "text": body})
    return {
        "sections": sections,
        "warnings": [],
    }


@tool("transcribe_audio_tool", args_schema=TranscribeAudioInput)
def transcribe_audio_tool(audio_url: str, duration_seconds: int = 0) -> dict:
    """Transcribe a short audio (sandbox).

    Returns:
        ``{"transcript": "...", "warnings": [...]}``.

    Enforces the 60s cap from the subagent system prompt (extractor_subagent.md).
    Placeholder implementation: never returns a real transcript — production
    replaces with `WhisperSTTAdapter`.
    """
    logger.info(
        "vitalia.copilot.workflows.extract_subagent.transcribe_audio_invoked",
        audio_url_hash=hash(audio_url),
        duration_seconds=duration_seconds,
    )
    if duration_seconds > 60:
        return {
            "transcript": "",
            "warnings": ["audio_too_long"],
        }
    return {
        "transcript": "",
        "warnings": ["transcribe_audio_placeholder_slice_1"],
    }


# Convenience tuple — passed verbatim into the deepagents SubAgent ``tools``
# slot. NEVER include any other tool here (sandbox cardinal).
EXTRACT_SUBAGENT_TOOLS: tuple = (
    scrape_website_tool,
    parse_document_tool,
    transcribe_audio_tool,
)


__all__ = [
    "EXTRACT_SUBAGENT_TOOLS",
    "ParseDocumentInput",
    "ScrapeWebsiteInput",
    "TranscribeAudioInput",
    "parse_document_tool",
    "scrape_website_tool",
    "transcribe_audio_tool",
]
