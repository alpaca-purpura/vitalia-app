# luana-core-campaigns v0.0.8-alpha

Campaigns engine — lifted verbatim from `AISALESHT/backend/src/modules/campaigns/`.

## Origin

Lift source: `backend/src/modules/campaigns/` (AISALESHT monorepo).
Lift mode: mechanical copy per outcome §7.3 — verbatim file names, class names, function signatures.

## DDD Layers

```
luana_core_campaigns/
├── domain/           # Campaign, Segment, AuditLog entities + repositories interfaces + enums + events
├── infrastructure/   # SQLA models + repository impls + channels + resilience + links + external adapters
├── application/      # DTOs + ports + services + segment_filter_evaluator + observability
├── api/              # FastAPI routers + dependencies + service factories
└── workers/          # arq workers (execution_task, scheduler_tick, audit_retention, segment_refresh)
```

## Key Exports

- `CampaignService`, `SegmentService`, `AuditLogService`, `CampaignTemplateService`
- `CampaignOrchestrator` — main campaign execution orchestrator with idempotency
- `SegmentFilterEvaluator` — DSL-based segment filter evaluation
- FastAPI routers: `campaigns_router`, `segments_router`, `templates_router`
- Workers: `execution_task`, `scheduler_tick`, `audit_retention_task`, `segment_refresh_tick`

## Import Path

```python
from luana_core_campaigns.domain.campaign import Campaign
from luana_core_campaigns.application.services.campaign_service import CampaignService
```
