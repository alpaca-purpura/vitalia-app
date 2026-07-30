# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas agentic application services — factory helpers.

`make_orchestrator` provides a minimal no-deps wiring of
`LucasOrchestratorService` for callers (cron jobs) that do not own full
service-layer DI (e.g. the daily-sweep cron which runs outside FastAPI
request context).

The factory uses no-op async stubs for the three handler protocols so
that the cron can call `orchestrator.run_daily_analysis(...)` and receive
a real `AnalysisReport` containing whatever the LangGraph graph produces
with those stubs.  Production uses the real handlers wired with DB sessions
from within the cron DB context; this factory is intentionally minimal.

downstream-regression-na: brand-local factory; no cross-brand consumers.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from src.modules.vitalia.agentic.lucas.application.services.lucas_orchestrator_service import (
    AnalysisReport,
    LucasOrchestratorService,
    TenantLocaleProtocol,
)


async def _noop_stage_handler(
    *,
    tenant_id: UUID,  # noqa: ARG001
    clinic_id: UUID,  # noqa: ARG001
    stage: Any,  # noqa: ARG001
    period: str,  # noqa: ARG001
) -> dict[str, Any]:
    """No-op stage handler — graph node returns empty dict."""
    return {}


async def _noop_attribution_handler(
    *,
    tenant_id: UUID,  # noqa: ARG001
    clinic_id: UUID,  # noqa: ARG001
    period_start: dt.date,  # noqa: ARG001
    period_end: dt.date,  # noqa: ARG001
) -> dict[str, Any]:
    """No-op attribution handler — graph node returns empty dict."""
    return {}


async def _noop_referrals_handler(
    *,
    tenant_id: UUID,  # noqa: ARG001
    clinic_id: UUID,  # noqa: ARG001
    period_start: dt.date,  # noqa: ARG001
    period_end: dt.date,  # noqa: ARG001
    limit: int,  # noqa: ARG001
) -> dict[str, Any]:
    """No-op referrals handler — graph node returns empty dict."""
    return {}


async def make_orchestrator() -> LucasOrchestratorService:
    """Construct a `LucasOrchestratorService` with no-op handlers.

    Intended for callers (cron jobs) that run outside request-scoped DI.
    Uses the brand-wide DURABLE checkpointer (``AsyncPostgresSaver`` via the
    shared engine provider ``luana_core_flows.make_durable_checkpointer``) so
    the daily-analysis graph persists its checkpoints to Postgres — never the
    in-memory ``MemorySaver`` (tutorial-only; tests inject ``InMemorySaver``
    directly at ``LucasOrchestratorService`` construction).

    Async because the durable checkpointer opens a connection pool + runs
    ``.setup()`` once at construction.

    Returns:
        Fully wired `LucasOrchestratorService` ready for `run_daily_analysis`.
    """
    from src.modules.vitalia._shared.workers.durable_checkpointer import (
        get_vitalia_durable_checkpointer,
    )

    checkpointer = await get_vitalia_durable_checkpointer()
    return LucasOrchestratorService(
        stage_handler=_noop_stage_handler,
        attribution_handler=_noop_attribution_handler,
        referrals_handler=_noop_referrals_handler,
        checkpointer=checkpointer,
    )


__all__ = [
    "AnalysisReport",
    "LucasOrchestratorService",
    "TenantLocaleProtocol",
    "make_orchestrator",
]
