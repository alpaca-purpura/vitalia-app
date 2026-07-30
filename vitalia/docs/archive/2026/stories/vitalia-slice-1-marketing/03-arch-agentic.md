---
story_id: vitalia-slice-1-marketing
sub_arch: agentic
brand: vitalia
builder: builder-agentic (audit only — consumer-only surface)
auditor: auditor-agentic (Opus)
production_code: false
agentic_surface: consumer-only
---

# Agentic sub-arch — vitalia-slice-1-marketing

## TL;DR

**Agentic surface = consumer-only. NO new tools, NO new personas, NO new goldens, NO new prompt slots, NO new workflows.**

This story consumes the existing Lucas growth setter agentic stack already shipped in `vitalia/backend/src/modules/vitalia/agentic/lucas/` (story `vitalia-copilot-tools-impl` done 2026-05-18). The marketing module exposes a thin BE service layer (`MarketingService`, `LucasRecommendationsService`) that calls existing Lucas application services. **No agentic runtime change.**

## 1. Lucas stack (READ-ONLY — already shipped)

Verified via `ls /home/chalreme/Proyectos/luana-vitalia/vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/` on 2026-05-20:

| Asset | Path | Type | R23 production_code |
|---|---|---|---|
| Tool `compute_stage_recommendation` | `agentic/lucas/tools/compute_stage_recommendation.py` | LangChain tool (LLM-backed) | true (shipped) |
| Tool `compute_attribution_matrix` | `agentic/lucas/tools/compute_attribution_matrix.py` | Pure-DB tool (no LLM) | true (shipped) |
| Tool `compute_referrals_leaderboard` | `agentic/lucas/tools/compute_referrals_leaderboard.py` | Pure-DB tool (no LLM) | true (shipped) |
| Tool `compute_re_engagement_recommendation` | `agentic/lucas/tools/compute_re_engagement_recommendation.py` | LLM-backed | true (shipped, used by `/fidelizacion`) |
| Service `LucasStageRecommendationService` | `agentic/lucas/application/services/lucas_stage_recommendation_service.py` | App service · LLM-backed | true |
| Service `LucasAttributionService` | `agentic/lucas/application/services/lucas_attribution_service.py` | App service · pure DB | true |
| Service `LucasReferralsService` | `agentic/lucas/application/services/lucas_referrals_service.py` | App service · pure DB | true |
| Service `LucasOrchestratorService` | `agentic/lucas/application/services/lucas_orchestrator_service.py` | Coordinator (cron entrypoint) | true |
| Domain entity `AttributionMatrixSnapshot` | `agentic/lucas/domain/entities/attribution_matrix_snapshot.py` | Persisted snapshot | true |
| Domain entity `ReferralsLeaderboardSnapshot` | `agentic/lucas/domain/entities/referrals_leaderboard_snapshot.py` | Persisted snapshot | true |
| Infrastructure adapter `AnalyticsEngineQueryAdapter` | `agentic/lucas/infrastructure/adapters/analytics_engine_query_adapter.py` | Engine adapter (consumes `core/luana-core-analytics-engine/`) | true |

## 2. Consumption pattern (this story's BE service layer → existing Lucas services)

```python
# vitalia/backend/src/modules/vitalia/marketing/application/services/lucas_recommendations_service.py
class LucasRecommendationsService:
    """API-facing service for /marketing/recommendations endpoints.

    Reads from vitalia_lucas_recommendations table (persisted by cron).
    Does NOT call Lucas LLM tools at request time — those run in daily cron only.

    Approve/reject/undo flows: PURE state machine on the existing rec row.
    No LLM call. No agentic surface modified.
    """
    def __init__(
        self,
        *,
        lucas_recommendation_repo: LucasRecommendationRepository,
        audit_log_repo: AuditLogRepository,
        outbox_bus: OutboxBus,
    ) -> None:
        # NO LucasOrchestratorService injection here — that lives in the cron job
        ...
```

The cron `lucas_daily_analysis_sweep` (BE arch § 8.3) is the ONLY caller of Lucas LLM tools in this story. It invokes the existing `LucasOrchestratorService.run_daily_sweep(tenant_id, clinic_id)` once per tenant+clinic per day:

```python
# vitalia/backend/src/modules/vitalia/marketing/jobs/lucas_daily_analysis_sweep.py
from luana_core_platform.workers.cron_envelope import cron_envelope
from src.modules.vitalia.agentic.lucas.application.services.lucas_orchestrator_service import (
    LucasOrchestratorService,
)

@cron_envelope("vitalia.cron.lucas_daily_analysis_sweep", ttl=86400)
async def lucas_daily_analysis_sweep(ctx: dict) -> None:
    orchestrator: LucasOrchestratorService = ctx["lucas_orchestrator"]
    for tenant_id, clinic_id in await ctx["active_tenants_repo"].list_active():
        try:
            await orchestrator.run_daily_sweep(tenant_id=tenant_id, clinic_id=clinic_id)
        except Exception:
            logger.exception("lucas_daily_sweep_per_tenant_failed", tenant_id=str(tenant_id), clinic_id=str(clinic_id))
            # Soft-fail — next tenant continues
            continue
```

**Cost guard:** `BudgetGuard.check(agent_kind="sales_agent", estimated_cost_usd=...)` is already wired inside `LucasOrchestratorService` (verified per `sales-agent-expert::Budget + Outbound Gating` cement). This story does NOT modify that wiring.

## 3. Why no new agentic surface?

1. All Lucas growth setter recommendations for the 5 stages already implemented (5 stages × stage-specific prompt template inside `compute_stage_recommendation` tool).
2. AttributionMatrix is pure DB — no LLM call needed.
3. Referrals leaderboard is pure DB — no LLM call needed.
4. Approve/reject/undo flows are state transitions on persisted rec rows — no agentic runtime.
5. Channel sync (Meta/Google) is OAuth + REST API call — no agentic.
6. No new tools required by spec. No prompt slot architecture changes. No persona changes. No voice fidelity changes.

## 4. Anti-duplication audit (mandatory per `.claude/rules/anti-duplication.md`)

Cross-module audit executed:

```bash
WS=/home/chalreme/Proyectos/luana-vitalia
# Verify NO mirroring of Lucas pattern in marketing module
grep -rln "class.*GrowthSetter\|class.*LucasRecommendation.*Service\|create_supervisor.*lucas" \
  ${WS}/vitalia/backend/src/modules/vitalia/marketing/ 2>/dev/null
# Expected: empty result
```

Result: ZERO mirrors. Marketing module consumes existing Lucas services via Python imports, NEVER replicates Lucas agentic logic.

## 5. Observability (no new spans for agentic surface)

The 4 cron jobs emit OTel spans (per BE arch § 5) but those are infrastructure tracing, not agentic event recording. Existing Lucas services already write to:
- `sales_agent_trace_event` (Lucas growth setter trace events — invoked inside `LucasOrchestratorService.run_daily_sweep`)
- `sales_agent_llm_call` (Lucas LLM call costs — recorded per `compute_stage_recommendation` LLM invocation)

This story does NOT modify those write paths. Auditor verifies via `auditor-downstream-regression` rule that any modifications to `core/luana-core-observability/` or `core/luana-core-sales-agent/` are NOT introduced here.

## 6. Eval goldens (no changes)

`vitalia/backend/tests/agentic_evals/sales_agent/goldens/` for Lucas growth setter persona already cement 12 escenarios per parent story (3 dental + 3 estética + 3 psicología + 3 fertilidad). No new goldens needed for marketing story since no new prompt or tool surface introduced.

If `/dev-team` discovers during build that a new edge case requires golden (e.g., Lucas recommendation for adoption stage with zero data tenant) — escalate to `/pm-luana` for golden expansion ticket Slice 2. Slice 1 reuses existing.

## 7. Medical guardrails (no changes)

Lucas growth setter persona consumes existing guardrails per `vitalia/config/brand.yaml`:
- `medical_safety_no_diagnosis`
- `medical_safety_no_prescription`
- `medical_disclaimer_required`
- `prompt_injection_block`

Marketing surface NEVER processes PHI (no patient diagnoses, treatment plans, etc.). Lucas recommendations are aggregated marketing analytics — at most `referrer_patient_id_hash` (UUID hash, never patient name). Medical guardrails don't fire in marketing context but still active as safety net.

## 8. Spanish neutro vs sales_agent voice exception

Per `.claude/rules/sales-agent-brand-voice.md`, Lucas output respects tenant voice configuration (compiler v2 slot 5 `BRAND_VOICE`). Marketing UI chrome is Spanish neutro strict. Lucas-generated `title` + `body` in `vitalia_lucas_recommendations` rows MAY contain tenant voice features (voseo if tenant AR), but UI surrounding chrome stays neutro.

Implementation: Lucas recommendation rendering in `LucasStageRecommendationsCard` displays `rec.title` + `rec.body` verbatim (preserving tenant voice). All surrounding UI labels (buttons, modal headers, microcopy) come from `MARKETING_COPY` (neutro). Arch fitness `test_no_voseo_in_copy.test.ts` only scans `copy.ts`, NOT Lucas-generated content.

## 9. Test surfaces (BE only — FE tests covered in FE arch)

```
vitalia/backend/tests/modules/vitalia/marketing/application/services/
├── test_lucas_recommendations_service.py          ← Approve/reject/undo state machine, idempotency, audit log sync write, outbox events
└── test_marketing_service_uses_lucas_snapshots.py ← MarketingService reads attribution + referrals snapshots from existing Lucas services (no direct DB)
```

NO tests for Lucas internals (those live in `vitalia/backend/tests/modules/vitalia/agentic/lucas/` per `vitalia-copilot-tools-impl` archive, already GREEN).

## 10. References

- `vitalia/backend/src/modules/vitalia/agentic/lucas/` (Lucas stack shipped — READ-ONLY consumed)
- `vitalia/docs/archive/2026/stories/vitalia-copilot-tools-impl/` (parent story Lucas tools impl)
- `.claude/rules/sales-agent-brand-voice.md` (voice exception)
- `.claude/rules/anti-duplication.md` (mirror ban — Lucas patterns NEVER mirrored in marketing)
- `.claude/rules/auditor-downstream-regression.md` (auditor scope — verify no engine observability/agentic touch)
- `core/luana-core-{sales-agent,observability,llm,billing,analytics-engine}/` READ-ONLY consultation
