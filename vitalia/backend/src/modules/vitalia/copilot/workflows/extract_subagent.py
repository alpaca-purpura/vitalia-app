# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""extract_subagent — deepagents-style SubAgent spec for the wizard extractor.

Per 03-arch-agentic.md § 3.2 + tessl__deepagents + copilot-expert::§Subagent
patterns:

- ``SubAgent`` TypedDict from `deepagents` carries name + description +
  system_prompt + tools list (explicit, NO inherit parent toolset).
- The subagent is wired into the supervisor via deepagents
  ``SubAgentMiddleware`` (caller's responsibility — see
  ``wizard_onboarding_graph``).
- ``allowed_keys_to_subagent`` / ``allowed_keys_from_subagent`` isolation
  semantics are enforced at the graph level by the supervisor node — the
  subagent only receives ``extraction_subagent_input`` + ``tenant_id``, and
  the supervisor accepts only ``extraction_subagent_output`` back.

Anti-duplication audit:
  - SubAgent TypedDict + create_deep_agent come from the `deepagents` package
    (~5k downloads/wk). We consume them as-is. NO mirror.
  - The 3 sandbox sub-tools live in ``extract_subagent_tools.py`` — also no
    mirror; they are brand-specific to the wizard extractor.
  - The prompt content comes from ``prompts/extractor_subagent.md`` (single
    source of truth for the subagent system prompt).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from deepagents import SubAgent

from src.modules.vitalia.copilot.workflows.extract_subagent_tools import (
    EXTRACT_SUBAGENT_TOOLS,
)

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════════
# Cement constants
# ════════════════════════════════════════════════════════════════════════════

EXTRACT_SUBAGENT_NAME: str = "vitalia_wizard_extractor"
"""Public subagent name — used by deepagents `task` tool dispatch."""

EXTRACT_SUBAGENT_DESCRIPTION: str = (
    "Extract clinic configuration (name, vertical, location) from a website URL, "
    "pasted text, or short audio. Read-only — never persists state, never "
    "calls parent tools. Returns a structured dict to the supervisor."
)


# ════════════════════════════════════════════════════════════════════════════
# System prompt loader
# ════════════════════════════════════════════════════════════════════════════


def _load_extractor_system_prompt() -> str:
    """Read extractor_subagent.md (single source of truth for the subagent prompt)."""
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    return (prompts_dir / "extractor_subagent.md").read_text(encoding="utf-8").strip()


# ════════════════════════════════════════════════════════════════════════════
# SubAgent spec builder
# ════════════════════════════════════════════════════════════════════════════


def build_extract_subagent_spec(*, model: Any | None = None) -> SubAgent:
    """Construct the deepagents SubAgent TypedDict for the wizard extractor.

    The returned dict is passed verbatim to ``SubAgentMiddleware(subagents=[...])``
    or to ``create_deep_agent(subagents=[...])`` at the composition root.

    Args:
        model: Optional LLM model identifier or BaseChatModel instance for the
            subagent. ``None`` → subagent inherits the supervisor's model
            (this is the production default — supervisor + extractor share the
            cached prompt prefix). Tests pass a stub to keep them offline.

    Returns:
        SubAgent TypedDict per deepagents API. ``tools`` is the explicit sandbox
        tuple — parent toolset NOT inherited (cardinal isolation).
    """
    spec: SubAgent = {
        "name": EXTRACT_SUBAGENT_NAME,
        "description": EXTRACT_SUBAGENT_DESCRIPTION,
        "system_prompt": _load_extractor_system_prompt(),
        "tools": list(EXTRACT_SUBAGENT_TOOLS),  # explicit sandbox
    }
    if model is not None:
        spec["model"] = model
    return spec


__all__ = [
    "EXTRACT_SUBAGENT_DESCRIPTION",
    "EXTRACT_SUBAGENT_NAME",
    "build_extract_subagent_spec",
]
