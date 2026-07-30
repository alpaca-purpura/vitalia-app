"""Inbound mode-resolver + draft sink seam (GAP-2, additive · backward-compatible).

The inbound chat loop historically intercepts only ``handler_mode == 'human'``
(:meth:`ConversationPipeline.handle_human_mode`, pre-graph PAUSA). It has no
notion of a *consulta* / HITL mode where the agent should still **run** (consume
tokens, reason) but the reply is **drafted, not sent** — that concept is brand
(vitalia ``proposal_required``). This module is the hexagonal seam that lets a
brand inject:

  • a **mode resolver** ``(*, tenant_id, lead_id, checkpoint) -> InboundMode``
  • a **draft sink** ``async (*, tenant_id, lead_id, draft_text, result) -> None``

WITHOUT the engine importing anything brand. Default (no resolver registered) =
EXACT current behavior (every turn resolves to ``DECIDE`` → outbound sent).

Cache-safety (contract §Seam 1): the resolver + draft branch run **inside
``deliver_response``**, i.e. AFTER ``agent_app.ainvoke``. CONSULTA still runs the
graph (the prompt-cache slots + StateGraph are untouched); only the channel send
is suppressed. PAUSA stays pre-graph in ``handle_human_mode`` (engine default).

Graceful degradation: a raising resolver degrades to ``DECIDE`` (the turn never
breaks); a missing sink on CONSULTA still suppresses outbound (no crash).

# [SALES-AGENT-INBOUND-MODE-SEAM-GAP2] -> docs/promotion-protocol/proposals/
# 2026-06-23-sales-agent-inbound-mode-activity-seams.md
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

import structlog

if TYPE_CHECKING:
    from collections.abc import Awaitable

logger = structlog.get_logger()


class InboundMode(str, Enum):
    """Operating mode resolved for one inbound turn.

    DECIDE   — normal: graph runs + outbound SENT (engine default).
    CONSULTA — graph runs (tokens consumed) but outbound SUPPRESSED → draft.
    PAUSA    — agent does not respond (handled pre-graph by handle_human_mode;
               a resolver returning PAUSA is informational — the engine default
               path for PAUSA is the existing ``handler_mode == 'human'`` skip).
    """

    DECIDE = "decide"
    CONSULTA = "consulta"
    PAUSA = "pausa"


class _ModeResolver(Protocol):
    """A brand-injected resolver. Keyword-only, duck-typed, async, returns InboundMode.

    Async because the brand typically loads its own conversation state from the
    DB — and ``resolve_inbound_mode`` is awaited inside ``deliver_response`` (the
    main event loop that owns the shared async engine pool), so a brand AsyncSession
    runs natively without a cross-loop bridge.
    """

    def __call__(
        self, *, tenant_id: UUID, lead_id: UUID | None, checkpoint: Any
    ) -> "Awaitable[InboundMode]":
        """Resolve the inbound mode for this turn (awaitable)."""
        ...


class _DraftSink(Protocol):
    """A brand-injected draft writer. Called on CONSULTA. Best-effort, async."""

    def __call__(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID | None,
        draft_text: str,
        result: dict,
    ) -> "Awaitable[None]":
        """Persist the suppressed reply as a brand-side draft."""
        ...


# Module-level injectable hooks. Default None → engine default behavior.
_mode_resolver: _ModeResolver | None = None
_draft_sink: _DraftSink | None = None


def set_mode_resolver(resolver: _ModeResolver | None) -> None:
    """Register (or clear) the brand mode resolver. Called once at brand lifespan."""
    global _mode_resolver  # noqa: PLW0603 — module-level DI hook (mirrors tool resolver pattern)
    _mode_resolver = resolver


def set_draft_sink(sink: _DraftSink | None) -> None:
    """Register (or clear) the brand draft sink. Called once at brand lifespan."""
    global _draft_sink  # noqa: PLW0603 — module-level DI hook
    _draft_sink = sink


def get_draft_sink() -> _DraftSink | None:
    """Return the registered draft sink, or None when no brand opted in."""
    return _draft_sink


def reset_inbound_seam() -> None:
    """Clear both hooks — test isolation only."""
    global _mode_resolver, _draft_sink  # noqa: PLW0603 — test reset
    _mode_resolver = None
    _draft_sink = None


async def resolve_inbound_mode(
    *, tenant_id: UUID, lead_id: UUID | None, checkpoint: Any
) -> InboundMode:
    """Resolve the inbound mode for this turn (awaited inside deliver_response).

    No resolver registered → ``DECIDE`` (engine default = current behavior).
    A raising resolver degrades to ``DECIDE`` (graceful — never break the turn).
    """
    resolver = _mode_resolver
    if resolver is None:
        return InboundMode.DECIDE
    try:
        mode = await resolver(
            tenant_id=tenant_id, lead_id=lead_id, checkpoint=checkpoint
        )
    except Exception as exc:  # noqa: BLE001 — resolver failure must not break the turn
        logger.warning(
            "inbound_mode_resolver_failed",
            tenant_id=str(tenant_id),
            error=str(exc),
        )
        return InboundMode.DECIDE
    # Defensive: a brand that returns a non-InboundMode value degrades to DECIDE.
    if not isinstance(mode, InboundMode):
        logger.warning(
            "inbound_mode_resolver_bad_return",
            tenant_id=str(tenant_id),
            returned=type(mode).__name__,
        )
        return InboundMode.DECIDE
    return mode


__all__ = [
    "InboundMode",
    "get_draft_sink",
    "reset_inbound_seam",
    "resolve_inbound_mode",
    "set_draft_sink",
    "set_mode_resolver",
]
