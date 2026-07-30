# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas cron integration package — smoke entrypoint for the LangGraph orchestrator.

Story: vitalia-copilot-tools-impl T-ag-workflows-2 (R23 Opus 4.7 production AGENTIC code).

Note on path naming: the production cron job (ARQ-driven weekly schedule) lives
at `vitalia/backend/src/modules/vitalia/_shared/workers/jobs/lucas_weekly_recommendations.py`
and was cemented by `vitalia-slice-1-infra-cross-cutting` T-infra-8. This package
provides the GRAPH-LAYER orchestrator entrypoint (`run_lucas_daily_analysis_job`)
that wraps the same 3 services through the new LangGraph topology + checkpointer.

Slice 1 wires this new entrypoint as a SMOKE-TEST-ONLY callable (validators target
the smoke runner at `tests/agentic_evals/agentic/lucas/test_lucas_smoke.py`). The
existing ARQ cron job continues to invoke services DIRECTLY — switching the cron
to invoke this orchestrator (gaining graph checkpoint resumability) is a Slice 2
follow-up that requires no contract change at the service layer.
"""

from src.modules.vitalia.agentic.lucas.cron.daily_analysis_job import (
    LucasDailyAnalysisJobInput,
    LucasDailyAnalysisJobResult,
    run_lucas_daily_analysis_job,
)

__all__ = [
    "LucasDailyAnalysisJobInput",
    "LucasDailyAnalysisJobResult",
    "run_lucas_daily_analysis_job",
]
