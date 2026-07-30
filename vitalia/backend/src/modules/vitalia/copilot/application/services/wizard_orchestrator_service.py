# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""WizardOrchestratorService — composition root for the Valeria wizard graph.

High-level service consumed by the FastAPI route
``wizard_onboarding_routes.py::POST /api/v1/vitalia/onboarding/start`` and the
SSE stream route ``GET /stream/{draft_id}``. Exposes:

- ``start_wizard(draft_id, tenant_id, user_id, clinic_id)`` — builds initial
  state + invokes graph.
- ``stream_wizard(draft_id, tenant_id, ...)`` — async generator yielding
  LangGraph ``astream_events`` modes (``updates`` + ``messages``).

This file is the **only** layer that knows about both the graph factory AND
the per-tenant thread_id composition rule (tenant + draft → thread_id). Keeps
the route thin.

Anti-duplication audit:
  - Service composition — no shared abstraction lifted from engine. The
    wizard supervisor topology is brand-specific. NO mirror.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional
from uuid import UUID

import structlog
from langgraph.checkpoint.base import BaseCheckpointSaver
from luana_core_flows.checkpointer import build_flow_thread_id

from src.modules.vitalia.copilot.workflows.wizard_onboarding_graph import (
    build_wizard_onboarding_graph,
)
from src.modules.vitalia.copilot.workflows.wizard_onboarding_state import (
    WizardOnboardingState,
    build_initial_state,
)

logger = structlog.get_logger()


_WIZARD_FLOW_ID = "vitalia.wizard"


def _thread_id_for(tenant_id: str, draft_id: str) -> str:
    """Compose the durable thread_id from (tenant_id, draft_id).

    Delegates to the shared engine helper ``build_flow_thread_id`` (lifted from
    the per-site rules), keeping the tenant segment as the isolation cardinal —
    wizard sessions across tenants never collide on the durable thread surface.
    """
    return build_flow_thread_id(
        flow_id=_WIZARD_FLOW_ID,
        tenant_id=tenant_id,
        instance_id=draft_id,
    )


class WizardOrchestratorService:
    """High-level wizard orchestrator.

    Holds a compiled graph instance (single instance per process / FastAPI
    app lifespan). Caller provides the checkpointer at construction — the
    composition root chooses InMemorySaver (tests) vs AsyncPostgresSaver
    (production).
    """

    def __init__(
        self,
        *,
        checkpointer: BaseCheckpointSaver,
        supervisor_model: Optional[Any] = None,
    ) -> None:
        """Initialize the service with a compiled graph.

        Args:
            checkpointer: LangGraph-compatible checkpointer.
            supervisor_model: Optional LLM model identifier or BaseChatModel
                for the supervisor LLM binding. Slice 1 stub: passed through
                to the graph factory but the supervisor LLM binding lands at
                composition.
        """
        self._graph = build_wizard_onboarding_graph(
            checkpointer=checkpointer,
            supervisor_model=supervisor_model,
        )

    @property
    def graph(self) -> Any:
        """Compiled graph instance (exposed for stream-mode helpers)."""
        return self._graph

    async def start_wizard(
        self,
        *,
        draft_id: UUID | str,
        tenant_id: UUID | str,
        user_id: UUID | str,
        clinic_id: Optional[UUID | str] = None,
    ) -> WizardOnboardingState:
        """Start a new wizard session — seeds initial state + invokes once.

        Args:
            draft_id: Wizard draft identifier (created by
                OnboardingDraftService.create_draft prior to this call).
            tenant_id: Tenant isolation cardinal.
            user_id: Initiating admin user id.
            clinic_id: Optional clinic id (may be None pre-creation).

        Returns:
            Final state dict after one supervisor pass (typically waiting on
            the user's first message — mode is unset so ``decide_next_node``
            routes to slot_question).
        """
        tenant_id_str = str(tenant_id)
        draft_id_str = str(draft_id)
        user_id_str = str(user_id)
        clinic_id_str: Optional[str] = str(clinic_id) if clinic_id else None

        initial_state = build_initial_state(
            tenant_id=tenant_id_str,
            user_id=user_id_str,
            clinic_id=clinic_id_str,
        )
        thread_id = _thread_id_for(tenant_id_str, draft_id_str)
        config = {"configurable": {"thread_id": thread_id}}

        logger.info(
            "vitalia.copilot.workflows.wizard.start",
            tenant_id=tenant_id_str,
            draft_id=draft_id_str,
            thread_id=thread_id,
        )
        result = await self._graph.ainvoke(initial_state, config=config)
        return result

    async def stream_wizard(
        self,
        *,
        draft_id: UUID | str,
        tenant_id: UUID | str,
        state_update: Optional[dict] = None,
    ) -> AsyncIterator[dict]:
        """Stream wizard state updates (SSE v2 over LangGraph astream_events).

        Args:
            draft_id: Wizard draft id (must already exist in checkpoint).
            tenant_id: Tenant isolation cardinal.
            state_update: Optional partial state to inject before streaming
                (e.g., new user message, slot confirmation). ``None`` →
                stream resumes from the persisted state.

        Yields:
            ``{"event": "...", "data": ...}`` events shaped per SSE v2 spec
            (per copilot-expert::§SSE v2 protocol). Routes consume + emit to
            the HTTP EventSource.

        Stream modes used: ``updates`` (per-node deltas — production UI) and
        ``messages`` (token-by-token — chat UX). Both fire — caller filters
        as appropriate at the EventSource handler.
        """
        thread_id = _thread_id_for(str(tenant_id), str(draft_id))
        config = {"configurable": {"thread_id": thread_id}}

        logger.info(
            "vitalia.copilot.workflows.wizard.stream_open",
            tenant_id=str(tenant_id),
            draft_id=str(draft_id),
            thread_id=thread_id,
            has_state_update=state_update is not None,
        )

        # astream_events surface — LangGraph 2.0 emits per-node updates +
        # optional token streaming when an LLM is bound (which Slice 1 stub
        # nodes do not have yet — the events are still emitted as `updates`).
        astream = self._graph.astream_events(
            state_update or {},
            config=config,
            version="v2",
        )
        async for event in astream:
            yield event


async def build_production_wizard_orchestrator(
    *,
    supervisor_model: Optional[Any] = None,
) -> WizardOrchestratorService:
    """Production composition root — wizard orchestrator on the durable checkpointer.

    Constructs the ``WizardOrchestratorService`` with the brand-wide durable
    ``AsyncPostgresSaver`` (via the shared engine provider). This is the
    production swap surface that replaces the deleted brand factory mirror
    (``wizard_checkpoint_config``, now removed); the wizard graph then persists
    every supervisor step to Postgres and survives a process restart (resume),
    instead of the in-memory ``MemorySaver`` used by tests.
    """
    from src.modules.vitalia._shared.workers.durable_checkpointer import (
        get_vitalia_durable_checkpointer,
    )

    checkpointer = await get_vitalia_durable_checkpointer()
    return WizardOrchestratorService(
        checkpointer=checkpointer,
        supervisor_model=supervisor_model,
    )


__all__ = [
    "WizardOrchestratorService",
    "build_production_wizard_orchestrator",
]
