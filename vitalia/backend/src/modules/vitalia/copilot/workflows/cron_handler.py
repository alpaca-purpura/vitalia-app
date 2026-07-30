# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""Cron handler — TreatmentFollowupWorkflow tick entry points.

Story 11 T-workflow-1 (R23 Opus 4.7 production AGENTIC code).

Per 02-design-agentic.md § 8.2 + 03-arch-agentic.md § 6.4.

Anti-duplication audit (per .claude/rules/anti-duplication.md):
  - Searched: `grep -rln "register_cron_handler|cron_worker"
    /home/chris/luana-platform/core/` → empty.
  - VERDICT: NO existing cron primitive exists in @luana/core/scheduling at
    Story 11 ratification time. The arch doc § 6.4 describes
    `from luana_core_scheduling.workers.cron_worker import register_cron_handler`
    as planned cement that has NOT yet been built.
  - DECISION (NO-NEW-LAYER + YAGNI): create vitalia-LOCAL handler module +
    registry. When a cross-brand cron primitive lands in @luana/core, this
    module's `register_cron_handler` decorator is the lift-shared candidate.
    A single-line wiring change replaces local registry with shared one.
    NOT a parallel layer to existing primitive — no primitive exists.
  - This LOCAL implementation is documented in T-workflow-1-impl-log.md as
    "scoped extension, lift-shared deferred".

Cron tick semantics:
  - External scheduler (APScheduler / cron / k8s CronJob — out of scope this
    ticket) computes next_scheduled_at per treatment via TreatmentFollowupService
    (T-be-6 cement) and invokes `handle_treatment_followup_tick` at the
    appropriate time.
  - Tick handler resumes the LangGraph workflow from saved checkpoint
    (RedisSaver in production per D10; MemorySaver for tests).
  - State key composite (tenant_id, treatment_id) per 02-design § 4.4.

Graceful degradation per `tessl__graceful-degradation` Rule 5:
  - Each tick wrapped in try/except + structlog warning. Single failed tick
    does NOT crash the worker; failure logged with full context for ops review.
  - Future: integrate with shared/domain_events/outbox for queued retry on
    transient failure (per 02-design § 8.2 fallback note).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any, Literal

import structlog

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════════
# Local cron handler registry (lift-shared candidate per anti-duplication.md)
# ════════════════════════════════════════════════════════════════════════════

CronHandler = Callable[..., Awaitable[Any]]

_VITALIA_CRON_HANDLERS: dict[str, CronHandler] = {}


def register_cron_handler(name: str) -> Callable[[CronHandler], CronHandler]:
    """Decorator to register a cron handler in vitalia local registry.

    Lift-shared deferred: when @luana/core/scheduling.cron_worker lands as
    cement primitive, replace this module-level decorator with the shared
    one — handler implementations stay identical, only the import changes.

    Args:
        name: handler identifier (e.g. "vitalia.treatment_followup.tick").

    Returns:
        Decorator preserving the wrapped async function.
    """

    def _decorator(fn: CronHandler) -> CronHandler:
        if name in _VITALIA_CRON_HANDLERS:
            logger.warning(
                "cron_handler_register_duplicate",
                name=name,
                prior_handler=_VITALIA_CRON_HANDLERS[name].__qualname__,
                new_handler=fn.__qualname__,
            )
        _VITALIA_CRON_HANDLERS[name] = fn
        logger.info("cron_handler_registered", name=name, handler=fn.__qualname__)
        return fn

    return _decorator


def get_registered_cron_handlers() -> dict[str, CronHandler]:
    """Return read-only view of registered handlers (for orchestrator
    integration tests + future shared-cron lift)."""
    return dict(_VITALIA_CRON_HANDLERS)


# ════════════════════════════════════════════════════════════════════════════
# TreatmentFollowupWorkflow cron tick handler
# ════════════════════════════════════════════════════════════════════════════


@register_cron_handler("vitalia.treatment_followup.tick")
async def handle_treatment_followup_tick(
    *,
    tenant_id: uuid.UUID,
    treatment_id: uuid.UUID,
    milestone: Literal["D5", "D14", "D90"],
    workflow_factory: Callable[[Any], Any],
    checkpointer: Any,
    state_loader: Callable[[uuid.UUID, uuid.UUID], Awaitable[dict[str, Any] | None]] | None = None,
) -> dict[str, Any] | None:
    """Cron tick entry point — resume TreatmentFollowupWorkflow at given milestone.

    Args:
        tenant_id: tenant scope (required, isolated state key).
        treatment_id: treatment workflow scope.
        milestone: which check the cron tick advances to.
        workflow_factory: callable returning compiled workflow given a checkpointer
            (typically `build_treatment_followup_workflow`).
        checkpointer: configured checkpointer instance (MemorySaver for tests,
            RedisSaver/AsyncPostgresSaver for production).
        state_loader: optional async callable returning the state dict for a
            (tenant_id, treatment_id) pair. If None, the workflow resumes from
            its existing checkpoint without seeding extra state.

    Returns:
        Final state dict from `workflow.ainvoke(...)`, or None if
        graceful-degradation caught a transient failure.

    Per `tessl__graceful-degradation` Rule 5 + Rule 6:
      - Wrap full tick in try/except (transient failure → None + warning).
      - Log structured context for ops debugging (dependency/error/fallback).
      - Future: integrate with outbox for retry-with-backoff (per 02-design
        § 8.2 fallback "cron job queued via Postgres outbox").
    """
    config = {"configurable": {"thread_id": f"{tenant_id}:{treatment_id}"}}
    milestone_to_step = {"D5": "D5_check", "D14": "D14_check", "D90": "D90_check"}
    target_step = milestone_to_step.get(milestone)
    if target_step is None:
        logger.warning(
            "cron_handler_invalid_milestone",
            tenant_id=str(tenant_id),
            treatment_id=str(treatment_id),
            milestone=milestone,
        )
        return None

    try:
        workflow = workflow_factory(checkpointer)

        # Compose tick input — workflow resumes from checkpoint, only step advance signaled
        tick_input: dict[str, Any] = {"current_step": target_step}

        if state_loader is not None:
            loaded = await state_loader(tenant_id, treatment_id)
            if loaded:
                tick_input.update(loaded)

        result = await workflow.ainvoke(tick_input, config=config)
        logger.info(
            "treatment_followup_tick_completed",
            tenant_id=str(tenant_id),
            treatment_id=str(treatment_id),
            milestone=milestone,
            current_step=result.get("current_step"),
        )
        return result
    except Exception as exc:  # noqa: BLE001 — graceful-degradation per Rule 5
        logger.warning(
            "cron_handler_tick_failed",
            dependency="vitalia.treatment_followup.tick",
            tenant_id=str(tenant_id),
            treatment_id=str(treatment_id),
            milestone=milestone,
            err=str(exc),
            err_type=type(exc).__name__,
            fallback="returning_none_for_outbox_retry",
        )
        return None
