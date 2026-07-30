# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas growth setter tools — cron-invoked agentic tools.

Slice 1 cron-only per 02-design-agentic § 2.4 (Q2 default). Lucas runs
daily 06:00 LOCAL tenant TZ via APScheduler → invokes
`lucas_daily_analysis_graph` → each node calls one of these tools.

Tools (LangChain `@tool` decorated, async, Pydantic v2 input schemas):
- `compute_stage_recommendation` — LLM call (Kimi reasoning) per stage
- `compute_attribution_matrix` — pure DB analytics (no LLM)
- `compute_referrals_leaderboard` — pure DB analytics (no LLM)
- `compute_re_engagement_recommendation` — aggregate + cluster + LLM (T-10
  Slice 1 fidelización)

R23 production_code=True — agentic tools, Opus 4.7 exclusive.

Anti-duplication §0 audit (per .claude/rules/anti-duplication.md):
- `sanitize_payload` consumed from `luana_core_observability.recording.sanitization`
- `BaseTraceEventRepoProtocol` from `luana_core_observability.persistence.base_trace_event_repo`
- Lucas services + repos + adapters consumed (T-be-services-3) — NEVER re-implemented.
- No equivalent tool in `core/luana-core-*/` (vitalia growth setter is brand-specific
  vertical-medical analytics — Slice 2+ may lift to engine if cross-brand demand).
"""

from src.modules.vitalia.agentic.lucas.tools.compute_attribution_matrix import (
    ComputeAttributionMatrixInput,
    MatrixDTO,
    compute_attribution_matrix,
)
from src.modules.vitalia.agentic.lucas.tools.compute_re_engagement_recommendation import (
    ComputeReEngagementRecommendationInput,
    compute_re_engagement_recommendation,
)
from src.modules.vitalia.agentic.lucas.tools.compute_referrals_leaderboard import (
    ComputeReferralsLeaderboardInput,
    LeaderboardDTO,
    compute_referrals_leaderboard,
)
from src.modules.vitalia.agentic.lucas.tools.compute_stage_recommendation import (
    ComputeStageRecommendationInput,
    RecommendationDTO,
    compute_stage_recommendation,
)

__all__ = [
    "ComputeAttributionMatrixInput",
    "ComputeReEngagementRecommendationInput",
    "ComputeReferralsLeaderboardInput",
    "ComputeStageRecommendationInput",
    "LeaderboardDTO",
    "MatrixDTO",
    "RecommendationDTO",
    "compute_attribution_matrix",
    "compute_re_engagement_recommendation",
    "compute_referrals_leaderboard",
    "compute_stage_recommendation",
]
