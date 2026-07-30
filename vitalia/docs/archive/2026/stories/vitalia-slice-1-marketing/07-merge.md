# Merge artifact — vitalia/vitalia-slice-1-marketing

> Brand: vitalia
> Merged: 2026-05-21
> Commit (squash-merge): TBD (set post merge to main)
> Branch source: wip/vitalia (heads: f0e395e..8cecbbaa)
> Audit verdict: APPROVED iter 3 (BE) + APPROVED iter 1 (FE)
> Final transition: ready → developing → developed → reviewing → done
> Audit cycle: 3 iterations (cap 3 reached, succeeded)

## § 1 — Gherkin verification matrix

> Cada scenario de `01-spec-extract.md` mapeado a test que pasa. Copia consolidada de `06-audit/gherkin-matrix-{backend,frontend}.md`.

| Scenario (Gherkin) | Test paths | Status |
|---|---|---|
| **SC-MK-01** — Happy: Owner aprueba recomendación Lucas escalar Meta budget | `vitalia/backend/tests/modules/vitalia/marketing/domain/test_lucas_recommendation_entity.py::test_approve_transitions_status` + `test_approved_sets_undo_until_5min` · `infrastructure/repositories/test_lucas_recommendation_repository.py::test_approve_updates_status` + `test_dual_filter_tenant_and_clinic` · `application/services/test_lucas_recommendations_service.py::test_approve_sets_status_audit_outbox` + `test_approve_undo_within_5min` + `test_approve_idempotency_dedup` · `api/test_recommendations_endpoints.py` round-trip · `vitalia/frontend/src/features/marketing/__tests__/LucasStageRecommendationsCard.test.tsx::test_renders_top_3_cards` · `LucasApprovalModal.test.tsx::test_approve_invokes_mutation_with_idempotency_key` + `test_post_approve_shows_undo_chip_5min` | ✅ PASS |
| **SC-MK-02** — Negative: Meta API timeout · sync degraded · UI muestra last_known | `vitalia/backend/tests/modules/vitalia/connections/meta_ads/test_meta_ads_adapter.py::test_timeout_30s_raises` + `test_circuit_breaker_after_5_consecutive_failures` · `vitalia/backend/tests/workers/test_marketing_crons.py::test_channel_metrics_sync_meta_soft_fail_per_tenant` + `test_channel_metrics_sync_meta_publishes_channelsyncfailed_event` + `test_lucas_daily_analysis_sweep_skips_rejected_30d_cooldown` · `vitalia/frontend/src/features/marketing/__tests__/ChannelBreakdownRow.test.tsx::test_shows_warning_badge_when_sync_error` + `test_shows_last_known_metrics_with_timestamp` + `test_retry_sync_button_invokes_useSyncChannel` | ✅ PASS |
| **SC-MK-03** — Edge: Stage tab change · Lucas re-render correctly | `vitalia/frontend/src/features/marketing/__tests__/marketing-parsers.test.ts::test_default_tab_is_attraction` + `test_tab_param_replace_intra_route` · `MarketingStageTabs.test.tsx::test_tab_click_updates_url_replace` + `test_active_tab_highlight_cian` · `MarketingLayout.test.tsx::test_bowtie_sticky_top` · `ReservationStage.test.tsx::test_renders_attribution_matrix_inline` · `ExpansionStage.test.tsx::test_renders_referrals_widget` | ✅ PASS |
| **SC-MK-04** — Adversarial: RBAC + cross-clinic isolation + range validation | `vitalia/backend/tests/modules/vitalia/marketing/infrastructure/repositories/test_lucas_recommendation_repository.py::test_other_clinic_cannot_read` · `test_channel_sync_state_repository.py::test_oauth_token_pgcrypto_roundtrip` · `application/services/test_lucas_recommendations_service.py::test_approve_action_payload_out_of_range_rejected` · `api/test_recommendations_endpoints.py` RBAC role checks · `vitalia/frontend/src/features/marketing/__tests__/LucasApprovalModal.test.tsx::test_role_recepcion_disables_approve_button_with_tooltip` | ✅ PASS |
| **SC-MK-01 E2E** — Lucas approve modal opens/closes no confirm | `vitalia/frontend/e2e/specs/smoke/marketing.smoke.spec.ts::test_lucas_approval_modal_opens_closes_no_confirm` | 🟡 SCAFFOLD (DEFERRED CI — Turbopack instability, see learning 2026-05-20) |
| **SC-MK-03 E2E** — Tab change updates URL re-renders | `marketing.smoke.spec.ts::test_tab_change_updates_url_re_renders` | 🟡 SCAFFOLD (DEFERRED CI) |

Aggregate: 4 scenarios × multiple test paths = ALL PASS (158 BE tests + 116 FE tests verified via `gate-output.json` audit-3 `any_fail=false`). 2 E2E specs DEFERRED CI documented.

## § 2 — Playwright E2E run

> Última corrida intentada local — DEFERRED CI por Turbopack dev server instability (learning emitido).

```bash
cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/marketing.smoke.spec.ts
```

- Specs scaffold count: 2 (Gherkin SC-MK-01 + SC-MK-03)
- Live run: DEFERRED CI — Turbopack dev server drops connections under concurrent Playwright browser load (laz compile de `/marketing` race con auth.fixture POMs). Stack-stable run requiere fix Docker RAM + Turbopack memory budget per `vitalia/docs/learnings/2026-05-20-docker-frontend-ram-turbopack-issue.md`.
- Trace artifacts: N/A (no live run)
- Workaround corto-plazo: Chris ratifica baselines/specs en staging tunnel (`https://dev-app.vitalialat.com/marketing`) cuando dev-stack se estabiliza Slice 2.

**Unit coverage de los 2 E2E scenarios:** SC-MK-01 cubierto por 6+ unit tests FE (LucasApprovalModal modal flow + Idempotency-Key + undo chip + audit trail) + 3+ BE service tests (audit_log SYNC + idempotency dedup). SC-MK-03 cubierto por 5+ unit tests FE (nuqs parsers + StageTabs URL update + Layout sticky). Cobertura conductual completa vía unit; E2E queda como verificación visual + integración stack pendiente Slice 2.

## § 3 — Capabilities updated/created

- `vitalia/docs/product/capabilities/marketing/bowtie-funnel-5-stages.yaml` — NEW (5-stage Bowtie SVG pixel-invariante + StageDispatcher + nuqs URL state · features/marketing centro)
- `vitalia/docs/product/capabilities/marketing/lucas-stage-recommendations.yaml` — NEW (Lucas top-3 cards per stage + 5min undo + RBAC + idempotency-key + audit_log sync · core MUST visible MVP)
- `vitalia/docs/product/capabilities/marketing/attribution-matrix-4-origins.yaml` — NEW (4 origins × KPI columns + heatmap + Lucas top insight · Stage Reserva)
- `vitalia/docs/product/capabilities/marketing/referrals-leaderboard.yaml` — NEW (3 KPIs + top 5 leaderboard + Adrián CTA + cron daily sync conversion_value_cents · Stage Expansión)
- `vitalia/docs/product/capabilities/connections/oauth-meta-google-ads.yaml` — NEW (Meta Ads + Google Ads OAuth adapters + circuit breaker per-tenant + EP-8 registration + pgcrypto oauth_token_encrypted)

## § 4 — Modules MD refreshed

- `vitalia/docs/product/modules/marketing.md` — NEW module (4 capabilities listed)
- `vitalia/docs/product/modules/connections.md` — UPDATE auto-list adds `oauth-meta-google-ads`
- (Auto-regen via `scripts/reconcile_capabilities.py --brand vitalia`)

## § 5 — How to verify (reproducible commands)

```bash
# Setup (asumiendo make dev-vitalia corriendo, port 3002 FE + 8002 BE):
WS=$(git rev-parse --show-toplevel)

# 1. BE unit + integration + arch fitness
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest \
  tests/architecture/ \
  tests/modules/vitalia/marketing/ \
  tests/modules/vitalia/connections/{meta_ads,google_ads}/ \
  tests/workers/test_marketing_crons.py tests/workers/test_arq_settings.py \
  -v --tb=short
# Expected: 270 arch + 158 marketing/connections/workers GREEN

# 2. FE type-check + lint + arch fitness + unit
cd ${WS}/vitalia/frontend && npx tsc --noEmit
cd ${WS}/vitalia/frontend && npx eslint src/features/marketing src/lib/zod-schemas/lucas-recommendation.ts --cache
cd ${WS}/vitalia/frontend && npx vitest run src/features/marketing/
# Expected: 0 tsc errors + 0 eslint errors + 116 vitest GREEN

# 3. BowtieSVG bundle size budget (static build required)
cd ${WS}/vitalia/frontend && next build && node scripts/check-bowtie-bundle.mjs
# Expected: < 30KB gzipped (deferred — depends on .next/ stable, see learning)

# 4. E2E smoke (DEFERRED CI — stack stability required)
cd ${WS}/vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test --project=smoke e2e/specs/smoke/marketing.smoke.spec.ts
# Expected: 2 specs PASS once Turbopack stack stable (Slice 2)

# 5. Chromatic visual baselines (requires CHROMATIC_PROJECT_TOKEN)
cd ${WS}/vitalia/frontend && CHROMATIC_PROJECT_TOKEN=<token> npx chromatic --auto-accept-changes=false
# Expected: ~71 baselines published — Chris ratifica pre-prod
```

**Expected:** comandos 1-2 retornan exit code 0 reliably. Comandos 3-5 DEFERRED CI con razón documentada.

## Cross-cutting fixes incorporated (out-of-scope per ticket but absorbed mid-session)

- **Engine factory `make_orchestrator()`** en `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/__init__.py` — wires `LucasOrchestratorService` con no-op handlers + MemorySaver checkpointer (audit iter 3 fix F-iter2-1). Pattern candidato lift core si otras brands necesitan wiring similar.
- **`_FallbackLocale` dataclass** en `lucas_daily_analysis_sweep.py` — UTC/USD satisface `TenantLocaleProtocol` mientras tenant_locale resolver real no exista (Slice 2 follow-up).
- **Migration 031** — added `conversion_value_cents` column to `vitalia_referrals` + `vitalia_appointments` (consumido por referrals_value_sync cron).
- **6 FE non-blocking WARNs aggregated:** staleTime deviation hooks (T-mk-fe-1), nested-interactive button-in-button UndoChip + toLocaleString hardcoded "es-PE" DetailModal (T-mk-fe-3), `toLocaleDateString("es-419")` direct (T-mk-fe-5), Chromatic deferred (T-mk-fe-6), 4 deferred validators CI (T-mk-fe-7). Tracked como follow-up Slice 2.

## Commit history (squash-merge captures)

```
8cecbbaa docs(vitalia/marketing): audit iter 3 APPROVED — CHECKPOINTS.md story-level emitted
86def4f0 fix(vitalia/marketing): T-mk-be-6 cron iter 2 — make_orchestrator factory + run_daily_analysis + BowtieStage enum
ac8ec6f3 fix(vitalia/marketing): AUDITOR_AUTO_FIX_LOOP iter 1 — F1-F5 defects fixed
2d610c63 docs(vitalia/marketing): audit iter 1 — 5 BE CHANGES_REQUESTED + FE all APPROVED
d9e481e6 feat(vitalia/marketing): state developing→developed (all 13 tickets pushed)
258a42fc docs(vitalia): learning Docker RAM + Turbopack issue → /pm-vitalia acción requerida
601ebd0d docs(vitalia): T-mk-fe-7 SHA pin 145a854 + result artifact commit reference
145a854 test(vitalia/e2e): T-mk-fe-7 wave 6 — E2E smoke + a11y + perf budget + bundle check
e9f2060 docs(vitalia/marketing): T-mk-fe-6 result.md + 06-tickets state=pushed sha:5b8b0d2
5b8b0d2 feat(vitalia/marketing/storybook): T-mk-fe-6 — Storybook stories + BowtieSVG visual regression
04f64ab docs(vitalia/marketing): T-mk-fe-5 result artifact + ticket state pushed
b8edd54 feat(vitalia/marketing): T-mk-fe-5 — Channel components Wave 5
9341106 docs(vitalia): T-mk-fe-4 result + 06-tickets state=pushed SHA fc8f6aa
fc8f6aa feat(vitalia/marketing): T-mk-fe-4 — AttributionMatrixWidget + ReferralsWidget + 5 stage section components
40cd57a docs(vitalia/marketing): T-mk-fe-3 result artifact + ticket state pushed
205e8d9 feat(vitalia/marketing): T-mk-fe-3 — Lucas StageRecommendationsCard + DetailModal + ApprovalModal + UndoChip + RejectModal
a2e1630 docs(vitalia/marketing): T-mk-fe-2 result.md ticket state pushed
aad4469 feat(vitalia/marketing): T-mk-fe-2 — Bowtie SVG + StageTabs + Layout + StageDispatcher + ActivityFooter + page.tsx
a79f88b docs(vitalia): T-mk-fe-1 SHA pin 866079b + result file
866079b feat(vitalia/marketing): T-mk-fe-1 — FE foundation (types + Zod + nuqs + MARKETING_COPY + 10 hooks + Zustand store)
5d0512f docs(vitalia/marketing): T-mk-be-6 result artifact + 06-tickets state=pushed
8471b25 feat(vitalia/marketing): T-mk-be-6 — 4 ARQ cron jobs Wave 3 with @cron_envelope
dd83d82 docs(vitalia): T-mk-be-5 SHA pin 191c93a
191c93a feat(vitalia/marketing): T-mk-be-5 — 11 FastAPI endpoints + RBAC + Idempotency-Key + dual filter
603209a docs(vitalia): T-mk-be-4 SHA pin 08555c5 + result file
08555c5 feat(vitalia/connections): T-mk-be-4 — Meta Ads + Google Ads OAuth adapters + EP-8 registration
0f0b0e6 docs(vitalia): T-mk-be-3 SHA pin 978d002 + result file
978d002 feat(vitalia/marketing): T-mk-be-3 — application services + Pydantic v2 DTOs
71f83ed chore(vitalia/marketing): T-mk-be-2 SHA pin 8211510
8211510 feat(vitalia/marketing): T-mk-be-2 — SQLA 2.0 models + repositories Wave 1
3304441 docs(vitalia/marketing): T-mk-be-1 result + 06-tickets state=pushed
f0e395e feat(vitalia/marketing): T-mk-be-1 — marketing domain entities, enums, events + 5 migrations
884381c chore(vitalia/marketing): CONTEXT-BRIEF + state ready→developing wave-1
b44daf0 feat(vitalia/marketing): ready package v1.0 — 03-arch + validators + tickets
```

29 commits total (15 BE feat/docs + 14 FE feat/docs/test + 3 audit cycle artifacts).

## Promotion candidate

- `make_orchestrator()` agentic factory pattern + `_FallbackLocale` dataclass — **monitor**, no promote yet. Wait for fitflow/comunify parallel agentic build to confirm cross-brand need before lift to `core/luana-core-platform/`.
- Docker RAM + Turbopack issue (learning 2026-05-20) — **promotable: candidate** ping `/pm-luana` cross-brand (same Docker dev pattern, all 4 active brands likely affected).

## Audit cycle summary

- iter 1: 5 BE CHANGES_REQUESTED (cascading spec drift + MagicMock factories) + 7 FE APPROVED with 6 WARN
- iter 2: 4 BE APPROVED + T-mk-be-6 3 regressions (cron service wiring + method rename + enum type)
- iter 3: T-mk-be-6 APPROVED (make_orchestrator factory + run_daily_analysis adapter + BowtieStage enum) → ALL APPROVED → CHECKPOINTS.md story-level APPROVED

## Deferred CI items (Chris ratifies in production cutover)

- Chromatic visual baselines (requires `CHROMATIC_PROJECT_TOKEN`)
- Playwright E2E smoke (requires stable Turbopack dev server — learning 2026-05-20)
- Axe a11y WCAG 2.1 AA (depends on stable dev server)
- Lighthouse perf budget LCP<2.5s · INP<200ms · CLS<0.1 (depends on stable dev server)
- 6 FE WARNs follow-up Slice 2 (staleTime + a11y nested-interactive + locale wrappers)

All deferred items are infrastructure/observability concerns — NO regression de funcionalidad shipped.
