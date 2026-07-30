---
module: marketing
brand: vitalia
last_updated: 2026-05-21
---

# marketing — Bowtie funnel 5-stage + Lucas recommendations + Attribution + Referrals

Marketing module brand-local for vitalia health clinics. Implements Bowtie funnel visualization (5 stages: Atracción · Calificación · Reserva · Adopción · Expansión), Lucas StageRecommendations consumer flow, AttributionMatrix widget (4 origins × KPI), ReferralsWidget + leaderboard, and channels viewport read-only (Meta/Google Ads sync degraded UX). Built NEW from scratch per Chris ratificación 2026-05-20 — NO reuse de growth-studio Nicolify (arch diferente).

## Boundary

- Surface: Bowtie SVG pixel-invariante + 5 stage section components + 3 widget components (Lucas/Attribution/Referrals) + Channel viewport (read-only) + UTM tracking lead→origin
- Reuso: consumes shipped Lucas tools from `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/` (shipped 2026-05-18 vitalia-copilot-tools-impl) — `LucasOrchestratorService`, `LucasAttributionService`, `LucasReferralsService` via factory `make_orchestrator()`
- Engine consumed: `core/luana-core-platform.workers.cron_envelope` (v0.4.0) + `core/luana-core-platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` (v0.4.0) — migrated 2026-05-20
- HIPAA-lite: dual filter `tenant_id + clinic_id` enforced; UTM payload sin PHI; OAuth tokens pgcrypto-encrypted at rest; audit_log SYNC write antes response on mutations

## Structure (DDD)

```
vitalia/backend/src/modules/vitalia/marketing/
├── domain/                    # entities, enums, events, exceptions (pure)
├── persistence/
│   ├── models/                # SQLA 2.0 mapped_column models
│   └── migrations/            # Alembic 026-031 idempotent
├── infrastructure/
│   └── repositories/          # 4 repos subclass CompoundScopeRepositoryBase
├── application/
│   └── services/              # MarketingService · AttributionService · ReferralsService · LucasRecommendationsService
├── api/
│   ├── schemas/               # Pydantic v2 DTOs
│   ├── deps.py                # FastAPI Depends factories (DI real services)
│   └── routes.py              # 11 endpoints + Idempotency-Key + RBAC
└── jobs/                      # ARQ cron jobs decorated @cron_envelope

vitalia/frontend/src/features/marketing/
├── types/                     # TS mirrors of Pydantic DTOs (camelCase)
├── store/marketing-store.ts   # Zustand ephemeral UI state
├── copy.ts                    # MARKETING_COPY namespace (Spanish neutro)
├── api/                       # 10 React Query hooks
└── components/                # 17 components + Storybook stories

vitalia/frontend/src/app/marketing/page.tsx  # Server Component reading nuqs SSR
```

## Capabilities

<!-- auto-list:start -->
- `vitalia-marketing-bowtie-funnel-5-stages` (live)
- `vitalia-marketing-lucas-stage-recommendations` (live)
- `vitalia-marketing-attribution-matrix-4-origins` (live)
- `vitalia-marketing-referrals-leaderboard` (live)
<!-- auto-list:end -->

## Deferred CI items

- Chromatic visual baselines (requires `CHROMATIC_PROJECT_TOKEN`) — Chris ratifies on production cutover
- Playwright E2E smoke (`/marketing.smoke.spec.ts`) — Turbopack dev server instability, see `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md`
- Axe a11y E2E (WCAG 2.1 AA) — depends on stable dev server
- Lighthouse perf budget LCP<2.5s / INP<200ms / CLS<0.1 — depends on stable dev server
- BowtieSVG bundle size budget < 30KB gzipped — requires stable `next build` (Docker `.next/` EACCES issue documented)

## Story origin

`vitalia/docs/archive/2026/stories/vitalia-slice-1-marketing/` — 13 tickets shipped (T-mk-be-1..6 + T-mk-fe-1..7) · ~5K LOC implementation · audit cycle 3 iter APPROVED.
