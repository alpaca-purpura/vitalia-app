# delta-arch-refresh.md — vitalia-slice-1-onboarding-wizard

> Refresh validation del paquete inherited (parent `vitalia-ux-discovery/`) contra realidad shipped post merges 2026-05-18:
> - `vitalia-slice-1-infra-cross-cutting` → main (squash 50143d57 + cc4fcd68)
> - `vitalia-copilot-tools-impl` → wip/vitalia (chain 3331151..427b0f3, pending squash a main)
>
> Date: 2026-05-18
> Refreshed-by: `/architect` (architect-orchestrator skill, brand=vitalia)
> Worktree: `~/Proyectos/luana-vitalia/` on `wip/vitalia` (CANÓNICO vitalia)
> Knowledge cutoff Opus 4.7 = Jan 2026; multimarca reorg cementado 2026-05-15. No state-of-the-art research nuevo necesario (refresh validation, not novel design).

## TL;DR

**Verdict: MINOR_DRIFT.**

Inherited package es ~85% válido as-is. La realidad shipped supera lo prometido en varias dimensiones (4 tools Valeria ya completos, wizard supervisor + state + prompt compiler + 7 API routes ya construidos, migraciones 002-021 todas aplicadas, checkpoint table 020 añadida más allá de spec). Esto **reduce el scope** de los tickets T-onboarding-1..7, no lo expande.

**Next action:** producir `06-tickets-refresh.yaml` override acotado a los tickets con SCOPE_REDUCED y spawn `/dev-team` consumiendo parent T-onboarding-1..7 + refresh overrides. Cinco tickets se vuelven WIRE-UP/QA only; dos quedan UNCHANGED (FE wizard + goldens).

## Check 1 — DB schema drift

**Status: MATCH (caller hint sobre `location_lat`/`location_lng` era inexacto).**

| Surface | Inherited spec (03-arch-be.md § 2.10/2.11/2.13) | Shipped reality (vitalia/backend/alembic/versions/) | Verdict |
|---|---|---|---|
| `vitalia_onboarding_progress` | CREATE TABLE (id, tenant_id, user_id, step, slots_confirmed JSONB, slots_pending JSONB, mode, draft_id, attachments JSONB, status, completed_at, created_at, updated_at) + UNIQUE INDEX (tenant_id, user_id) | `011_vitalia_onboarding_progress.py` — todas las columnas presentes ✅ + extra `CREATE INDEX ix_vitalia_onboarding_progress_tenant_status` (mejora, no rompe spec) | **MATCH** |
| `vitalia_brand_studio_drafts` | CREATE TABLE (id, tenant_id, user_id, draft_kind, draft_payload JSONB, voice_profile_partial_json JSONB, committed_at, expires_at, created_at, updated_at) + INDEX (tenant_id, user_id, committed_at) | `012_vitalia_brand_studio_drafts.py` — todas las columnas presentes ✅ + extra partial INDEX `WHERE committed_at IS NULL` para sweep eficiente | **MATCH** |
| `tenants` columnas | ALTER ADD `is_onboarded BOOLEAN` + `location_country CHAR(2)` + `location_city VARCHAR(128)` + `timezone VARCHAR(64)` | `014_vitalia_tenants_columns.py` — 4 columnas ✅ (VARCHAR(2) y VARCHAR(255) en lugar de CHAR(2) y VARCHAR(128), diff cosmético tolerable per `core/luana-core-platform` promotion proposal `2026-05-17-platform-tenants-location-columns.md` state=migrated). | **MATCH** (cosmetic widening of varchar bounds OK; no functional impact) |
| Wizard LangGraph checkpoint table | Spec mencionaba "AsyncPostgresSaver" + table name `vitalia_wizard_onboarding_checkpoints` (03-arch-agentic § 6) | `020_vitalia_langgraph_checkpoint_tables.py` — table `vitalia_wizard_onboarding_checkpoints` ya creada ✅ con schema LangGraph AsyncPostgresSaver canónico | **MATCH + EXCEEDS** (table fue declarada y migrated por copilot-tools-impl story, no por esta sub-story) |

**Caller-supplied hint inexacto:** la prompt mencionaba columnas `location_lat`, `location_lng` en spec. Lectura directa de `03-arch-be.md` § 2.13 confirma spec NUNCA pidió lat/lng — pidió `timezone` (lo que efectivamente shipped). Sin drift, sin trabajo extra.

**Detalles:**
- No hay drift en schema PHI: `pgcrypto` BYTEA en `vitalia_treatment_plans.notes` + `vitalia_re_engagement_events.payload_phi` shipped por sister story (infra-cross-cutting). Wizard tables (`vitalia_onboarding_progress` + `vitalia_brand_studio_drafts`) NO contienen PHI (tenant-config + brand voice samples), por lo que no requieren columnas BYTEA pgcrypto.

## Check 2 — Valeria agentic tools contract drift

**Status: MATCH (signatures + decorator pattern) con SCOPE-SLIM en input schemas vs spec.**

| Tool | Inherited spec (03-arch-agentic § 4.1) | Shipped reality (`vitalia/backend/src/modules/vitalia/copilot/tools/`) | Verdict |
|---|---|---|---|
| `extract_tenant_context` | `ExtractInput(urls, doc_uploads, audio_uploads, tenant_id, user_id) → ExtractResponse` | `ExtractTenantContextInput(draft_id, tenant_id, url, text_content)` → `str` summary. **Adapter orchestration vive en `ExtractTenantContextService`**, no en el tool (correcta separación tool=thin, service=fat per LangChain idioms + arch-agentic § 4.1 último bullet "All tools `@tool` decorated, async, call SERVICES (never raw repos)") | **MATCH (architectural) + SLIM (input shape)** — tool input es más conciso que spec; service orquesta `website_scraper`, `document_extractor`, `whisper_stt` (audio path TBD post Slice 1 si Whisper se cablea, ver Check 5 T-onboarding-2 nota) |
| `confirm_slot` | `ConfirmSlotInput(slot_id, value, tenant_id, user_id) → ConfirmSlotResponse` | `ConfirmSlotInput(draft_id, tenant_id, slot_id, value, source: Literal["user_text","user_correction"])` → `str` summary | **MATCH** + EXCEEDS (adds `draft_id` y `source` discriminator para distinguir user direct entry vs corrección de extracted value, mejora trazabilidad) |
| `simulate_personality` | `SimulateInput(profile_partial, scenario, tenant_id) → SimulateResponse` | `SimulatePersonalityInput(tenant_id, profile_partial: dict, scenario: str)` → `str` (con prefix "Sample for '{scenario}'(from cache)? {sample_text}"). Throttle 5/min + cache 10min TTL implementados en service | **MATCH** |
| `complete_onboarding` | `CompleteInput(draft_id, tenant_id, user_id) → CompleteResponse` | `CompleteOnboardingInput(draft_id, tenant_id, user_id)` → `str` summary. Service orquesta compile_full → brand_studio commit → tenant.is_onboarded=True → audit_log SYNC → outbox `TenantOnboardedEvent` | **MATCH** |

**Cross-check Extension SDK registration:** los 4 tools ya están registrados en `vitalia/backend/src/modules/vitalia/extensions.py` (líneas 351-456 inspeccionadas) bajo `tool_groups=("wizard", "copilot", "onboarding")` (o `"personality_preview"` para simulate). El handler real (`extract_tenant_context`, `confirm_slot`, etc.) reemplaza el placeholder `_not_implemented_yet` original.

**Conclusión:** los tools shipped son **funcionalmente equivalentes** al spec con input schemas refinados (tool surface más thin, business logic en service layer per DDD). T-onboarding-4 ya no necesita crear los tools — solo verificar wiring y eval coverage.

## Check 3 — Slot architecture / prompt cache drift

**Status: MATCH funcional con relabeling cosmético (1-indexed vs 0-indexed).**

| Capa | Inherited spec (03-arch-agentic § 5.3) | Shipped reality (`workflows/wizard_prompt_compiler.py`) | Verdict |
|---|---|---|---|
| Slot 1 | System role (cacheable) | SLOT 0 — `_SLOT_0_SYSTEM_ROLE` (cacheable) | **MATCH** (renumbered 0-indexed) |
| Slot 2 | Wizard role + Vitalia onboarding context (cacheable per-brand) | SLOT 1 — Wizard role + Vitalia onboarding ctx (cacheable per-brand) — lives en `prompts/wizard_role_vitalia.md` | **MATCH** |
| Slot 3 | Tools manifest (cacheable per-graph) | SLOT 2 — Tools manifest (`_SLOT_2_TOOLS_MANIFEST` 4 wizard tools cacheable static literal) | **MATCH** |
| Slot 4 | Valeria persona prompt (cacheable per-brand) ↑ cache_control marker AQUÍ ↑ | SLOT 3 — Valeria persona (`prompts/valeria_persona.md` cacheable per-brand) ↑ `_CACHE_BREAKPOINT_INDEX = 3` ↑ | **MATCH** (cache_control marker en el último slot cacheable, semánticamente idéntico) |
| Slot 5 | Conversation + current slots state + user turn (variable, NOT cached) | SLOT 4 — Conversation + slot state + user turn (variable, NOT cached) | **MATCH** |
| TTL | 5min default per spec (10-20 min wizard session) | TTL 5min documented en compiler header comment | **MATCH** |
| Cache validation | `cache_creation_input_tokens` + `cache_read_input_tokens` logged cada LLM call | `VitaliaCopilotCallbackHandler` (capability `vitalia_callback_subclasses` live) emite ambos via inherited `BaseAgentCallbackHandler` | **MATCH** |

**Drift cosmético:** 1-indexed (spec) vs 0-indexed (shipped). Slots cacheable cuentan 4 en ambos (slots 1-4 en spec, slots 0-3 en shipped); slot variable = 1 (slot 5 en spec, slot 4 en shipped). **Sin impacto runtime.** Si auditor pide alineación cosmética, opcionalmente renumerar comentarios en `wizard_prompt_compiler.py` (no es bloqueante).

**Anti-duplication §0 compliance:** wizard compiler es brand-specific (Valeria onboarding no tiene equivalente en engine). Sales_agent compiler v2 (6-slot) vive en engine `core/luana-core-sales-agent/` consumido por Adrián directo. NO se mirror. ✅ Audit cross-module clean (no path duplication).

## Check 4 — Validators feasibility re-check

**Status: feasible AS-IS con 3 adjustes menores.**

Validators inherited en `vitalia-ux-discovery/04-validators.yaml` que targetean T-onboarding-1..7:

| Validator ID | Path/Command | Estado vs shipped reality | Adjuste needed |
|---|---|---|---|
| `be_arch_fitness_brand` | `pytest vitalia/backend/tests/architecture/` | ✅ Already 245/245 PASS post-2026-05-18 merges. T-onboarding tickets agregarán nuevos tests que deben sumarse al ratchet sin shrink. | None. |
| `be_pytest_unit` (referenced) | `pytest vitalia/backend/tests/` | ✅ Already 510 PASS unit + 49 integration GREEN. Onboarding-specific tests bajo `vitalia/backend/tests/modules/vitalia/copilot/{tools,workflows}/` parcialmente shipped por copilot-tools-impl. T-onboarding-1..7 amplía pero no requiere nuevo path. | None. |
| `agentic_wizard_goldens` | `pytest vitalia/backend/tests/agentic_evals/copilot/test_wizard_pass_k_evaluation.py -v` | ✅ Ya implementado en copilot-tools-impl (4 wizard goldens YAML + pass^k runner k=3 threshold 0.5). Recap merge artifact § 1 SC-W1..W4 PASS. | T-onboarding-7 ahora es **OBSOLETE en su scope original** (los goldens ya están escritos). Re-purpose a "smoke regression + drift detector" en refresh. |
| `agentic_cost_canonicalization` | `pytest <tests for cost_recorder canonical>` | ✅ Heredado de PI-12 S1 T-1 fix (2026-05-02 commit 5856be4d). Test fixtures usan `litellm_call_id` en `response_metadata`. | None. |
| `e2e_smoke_wizard_onboarding` | `cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test e2e/specs/smoke/wizard-onboarding.smoke.spec.ts` | ❌ FE feature `vitalia/frontend/src/features/onboarding/` NO existe (confirmed via `find`). E2E spec por construir como parte de T-onboarding-6 + smoke nuevo. | NEW — T-onboarding-6 produce `wizard-onboarding.smoke.spec.ts` + `pages/wizard-onboarding.page.ts` POM. Port `3002` correcto (vitalia FE). |
| `fe_arch_fitness` | `cd vitalia/frontend && npx vitest run src/__tests__/architecture/` | ✅ 38/38 PASS post-2026-05-18 merge. T-onboarding-6 agregará feature + components nuevos que deben respetar boundaries (FSD `features/onboarding/`). | None. |
| `spanish_neutro_voseo_check` | `pytest scripts/check_spanish_neutro.py` o equivalente | ✅ Pre-commit hook activo. Wizard `copy.ts` debe ser tuteo. | None. |
| `fe_test_onboarding` | `cd vitalia/frontend && npx vitest run src/features/onboarding/__tests__/` | ❌ No existe — T-onboarding-6 crea feature + tests. | None (NEW work expected). |

**Adjustes recomendados:**

1. **agentic_wizard_goldens** — ya validada por copilot-tools-impl. T-onboarding-7 puede consumir el mismo runner agregando edge cases adicionales si surgen del FE wizard QA.
2. **agentic_cost_canonicalization** — heredado y vigente. Wizard tools ya tracean `cost_usd` via `pop_cost(litellm_call_id)` (test fixture pattern PI-12 S1 T-1).
3. **e2e_smoke_wizard_onboarding** — NUEVO. T-onboarding-6 debe escribir y satisfacer. Port 3002 (vitalia). Confirm `Clerk JWT testing token` lifecycle per `playwright-expert`.

## Check 5 — Tickets T-onboarding-1..7 scope drift

| Ticket | Verdict | Delta concreto |
|---|---|---|
| **T-onboarding-1** | **SCOPE_REDUCED** | Spec creaba `vitalia/backend/src/modules/vitalia/onboarding/{domain,infrastructure}/` independiente. Shipped: módulo `onboarding/` no existe; entidades `OnboardingDraft` + `WizardSlot` viven en `copilot/domain/entities/`. Repositorios shipped vía `OnboardingDraftService` (uso de `draft_repo` AsyncMock placeholder). **Refresh scope:** crear `OnboardingProgressRepository` + `BrandStudioDraftRepository` SQLAlchemy 2.0 reales (reemplazar `AsyncMock` placeholders en `wizard_onboarding_routes.py` DI), backed by tablas 011 + 012 ya migradas. Domain entities reutilizar shipped (no recrear). LOC actual: ~400 (vs estimado 600 spec). |
| **T-onboarding-2** | **SCOPE_REDUCED** | Spec creaba 6 services nuevos. Shipped: 5 services ya construidos (`extract_tenant_context_service`, `onboarding_draft_service`, `simulate_personality_service`, `complete_onboarding_service`, `wizard_orchestrator_service`). **Refresh scope:** WIRE-UP only — adapters bajo `infrastructure/providers/` (website_scraper, document_extractor, audio_transcriber) shipped por copilot-tools-impl (verificar via grep + arch test). Si audio_transcriber Whisper aún placeholder → wire real. Si `LivePreviewService` faltante (no veo path explícito) → crear vía `simulate_personality_service` cache layer ya shipped. LOC actual estimado: ~400 (vs 1200 spec). |
| **T-onboarding-3** | **SCOPE_REDUCED** | Spec creaba 5 endpoints. Shipped: 7 endpoints ya en `copilot/api/routes/wizard_onboarding_routes.py` (start draft / get draft / extract / confirm slot / simulate / complete / SSE stream). **Refresh scope:** reemplazar DI mocks (`AsyncMock()`) por servicios reales conectados a repos reales (Postgres-backed). Verificar `response_model=` en todos los routes excepto SSE stream (per arch fitness V-AE-2). LOC actual estimado: ~150 (DI wiring + 2 endpoint test fixes vs 500 spec). |
| **T-onboarding-4** | **SCOPE_OBSOLETE → SCOPE_REDUCED** | Spec creaba 4 Valeria tools R23 production-code Opus 4.7. Shipped por **copilot-tools-impl** (commits 3331151..427b0f3, ratificado APPROVED 2026-05-18). Los 4 tools (`extract_tenant_context`, `confirm_slot`, `simulate_personality`, `complete_onboarding`) viven en `copilot/tools/` con `@tool` decorator + Pydantic v2 args_schema + service-call pattern + tenant_id mandatory. Registrados via EP-3 en `extensions.py`. **Refresh scope:** WIRE-UP only — verificar tools están registered + handlers reales en `extensions.py` (líneas 351-456 confirmed). Eval `cost_canonicalization` validator already covers. **R23 NO aplica** al refresh — no es production_code nuevo, es smoke regression (Sonnet OK). LOC actual estimado: ~50 (smoke test regression + grep verification vs 800 spec). |
| **T-onboarding-5** | **SCOPE_OBSOLETE → SCOPE_REDUCED** | Spec creaba LangGraph supervisor topology Opus production. Shipped por copilot-tools-impl: `wizard_onboarding_state.py` + `wizard_onboarding_graph.py` (supervisor + extract_subagent deepagents) + `wizard_prompt_compiler.py` (5-slot cache layout — slots 0-3 cacheable + slot 4 variable) + `wizard_checkpoint_config.py` (AsyncPostgresSaver, table `vitalia_wizard_onboarding_checkpoints` migrated 020) + max-iter guard 25 + `WizardOrchestratorService`. **Refresh scope:** WIRE-UP only — integration test re-run + verify cost target ≤$0.10 USD per wizard session + verify cache_read_input_tokens > 0 en iter 2+. R23 NO aplica — no new production code agentic. LOC actual estimado: ~80 (regression + observability assertion vs 1000 spec). |
| **T-onboarding-6** | **SCOPE_UNCHANGED** | FE wizard `vitalia/frontend/src/features/onboarding/` NO existe en shipped. Spec scope completo aplica: WizardOnboardingLayout + WizardChatThread adapter + SlotTrackerSticky + ModeSelector + SlotConfirmInline + LiveWhatsAppPreview + LiveLandingSnippetPreview + CloseSetupWarningModal + WizardCompletionTransition + 6 hooks + URL state nuqs + copy.ts LatAm neutro + morph transition 400ms (Batch 1 ratificado). LOC estimate spec 2200 vigente. Sonnet builder-frontend default per R23 (production_code=false). |
| **T-onboarding-7** | **SCOPE_REDUCED → SMOKE_REGRESSION_ONLY** | Spec creaba 4 wizard goldens YAML + pass^k runner. Shipped por copilot-tools-impl: 4 goldens (`happy_url_extraction`, `negative_incomplete`, `edge_browser_close_resume`, `adversarial_url_malicious_pii_xss`) + `test_wizard_pass_k_evaluation.py` runner k=3 threshold 0.5 (merge artifact § 1 SC-W1..W4 todos PASS). **Refresh scope:** WIRE-UP only — verify runner pasa post-FE wizard wire (T-onboarding-6) sin regression de los 4 goldens existentes. Si emergen edge cases nuevos durante QA FE → agregar como goldens incrementales (sub-scope). R23 NO aplica (production_code=false). LOC actual estimado: ~100 (verification + posible 1 golden adicional vs 500 spec). |

**Reduction summary:**

- 5 tickets vuelven SCOPE_REDUCED (1, 2, 3, 4, 5, 7): ~770 LOC en lugar de ~5400 LOC originales (estimación gross).
- 1 ticket SCOPE_UNCHANGED (6 — FE wizard): 2200 LOC.
- 0 tickets SCOPE_EXPANDED.
- 0 tickets totalmente OBSOLETE (todos siguen aportando algo: wire-up de servicios reales + tests regression + arch invariant check).

**R23 impact:** dado que tools (T-4) + workflow (T-5) ya están shipped en copilot-tools-impl con APPROVED audit, el refresh **no requiere R23 Opus 4.7 mandatory** — son verification + integration work, no production_code agentic nuevo. Esto baja costo build esperado.

## Engine boundary check

Diff `wip/vitalia` vs `main` sobre `core/luana-core-*/src/**`:

```bash
git diff main...HEAD -- 'core/luana-core-*/src/**'  # → empty (verified via copilot-tools-impl 07-merge.md § 5)
```

Cero modificaciones engine ratificadas. Si refresh requiere engine change → escalate `/pm-luana` promotion proposal. **Detección actual:** ninguna modificación engine prevista por refresh.

**Promotion proposals ya migrated (per `vitalia/docs/product/checkpoint.md::ratified_promotion_proposals`):**
- `docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md` → state=migrated (luana-core-platform 0.2.0)
- `docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md` → state=migrated (luana-core-offer-studio 0.2.0)

Sin promotion blockers vivos.

## Cross-brand mirror scan

Per `.claude/rules/anti-duplication.md` cardinal:

```bash
for tool in extract_tenant_context confirm_slot simulate_personality complete_onboarding; do
  for B in nicolify comunify lupulo; do
    find ${WS}/$B/backend/src -name "${tool}.py" 2>/dev/null
  done
done  # → empty (verified by copilot-tools-impl 07-merge.md § 5 verify step 11)
```

Sin cross-brand mirror. Wizard onboarding pattern es brand-specific Vitalia. Si emerge segundo brand con onboarding agentic similar (ej. SaaSora future) → lift candidate via `/pm-luana` promotion. Documentado en checkpoint `promotion_candidates`.

## Recommended action

**MINOR_DRIFT — refresh package via override targeted.**

1. Producir `06-tickets-refresh.yaml` (acotado, sólo overrides para tickets con SCOPE_REDUCED).
   - T-onboarding-1: REDUCED → repos reales + DI wire-up (~400 LOC).
   - T-onboarding-2: REDUCED → adapter wire-up + LivePreviewService verificación (~400 LOC).
   - T-onboarding-3: REDUCED → DI mock→real swap + response_model audit (~150 LOC).
   - T-onboarding-4: REDUCED → wiring + smoke regression (~50 LOC). R23 OPT OUT (Sonnet OK).
   - T-onboarding-5: REDUCED → integration test re-run + cache validation (~80 LOC). R23 OPT OUT (Sonnet OK).
   - T-onboarding-6: UNCHANGED — referenciar parent verbatim.
   - T-onboarding-7: REDUCED → smoke + verify wizard goldens still pass post-FE (~100 LOC).
2. NO producir `03-arch-refresh.md` (drift no toca arquitectura — sólo scope de implementación).
3. NO producir `04-validators-refresh.yaml` (validators feasibles AS-IS; T-onboarding-6 introduce `e2e_smoke_wizard_onboarding` que ya está declarado en parent yaml).
4. Spawn `/dev-team` con tickets parent + override refresh local.

## Open Questions for PM (raised pre-ratification — now CLOSED)

> Ratified verbatim by Chris on 2026-05-18. Decisions folded into `06-tickets-refresh.yaml`.

1. **R23 OPT-OUT confirmation:** ¿/pm-vitalia ratifica que T-onboarding-4 + T-onboarding-5 dejan de ser Opus mandatory (production_code=true) y bajan a Sonnet (production_code=false, wire-up + regression only)? Esto baja cost esperado ~70%. Si rechaza → mantener Opus pero scope sigue REDUCED.

   ✅ **RATIFIED 2026-05-18:** YES → Sonnet OK (production_code=false, wire-up + regression only). owner_eligibility=[qwen-opencode, claude-sonnet] aplicado en T-4 + T-5. Tools (T-4) + graph (T-5) shipped APPROVED en copilot-tools-impl no son production code agentic nuevo — refresh es smoke regression + integration regression. ~70% cost reduction vs keeping Opus mandatory.

2. **AsyncMock → real repo migration:** los routes en `wizard_onboarding_routes.py` actualmente usan `AsyncMock` (líneas 75-78 inspeccionadas). T-onboarding-1 introduce `OnboardingProgressRepository` + `BrandStudioDraftRepository` SQLAlchemy 2.0 reales. ¿Architect deja diseño concreto (Inside-Out DDD per `backend-ddd.md`) o pasa free hand al builder? Recomiendo Architect produce un PR mini-arch (~30 líneas) inline en `06-tickets-refresh.yaml::T-onboarding-1::scope` con signatures repo + ORM models.

   ✅ **RATIFIED 2026-05-18:** YES → Architect produces mini-arch inline en `06-tickets-refresh.yaml::T-onboarding-1::scope`. Folded: SQLAlchemy 2.0 ORM models (OnboardingProgressModel + BrandStudioDraftModel con mapped_column, types, indexes, FKs), repository signatures async (OnboardingProgressRepository.create/get_by_tenant_user/update_step/mark_completed + BrandStudioDraftRepository.create/get_by_id_tenant/append_payload_patch/mark_committed), DI binding (provider functions yield repos backed by AsyncSession reemplazando AsyncMock líneas 75-78). Builder Sonnet consumes verbatim para velocidad GREEN-first iter.

3. **Whisper STT audio_transcriber:** spec `03-arch-agentic.md § 4.1` menciona Whisper STT como external call con timeout+fallback (`tessl__graceful-degradation`). Shipped `extract_tenant_context_service` actualmente accepta `url` + `text_content` pero NO `audio` (per tool args_schema inspected). ¿Slice 1 difiere audio path a Slice 2 (ratificar con Chris) o se cablea ahora?

   ✅ **RATIFIED 2026-05-18:** DEFER to Slice 2 → Whisper STT audio path removed from T-onboarding-2 scope. extract_tenant_context_service ships Slice 1 con URL + text_content únicamente. Audio adapter ratificado deferido (re-evaluate post Slice 1 + tenant feedback). audio_transcriber.py adapter wire-up REMOVED del scope. Tests audio path → SKIP con pytest.mark.skip. FE ModeSelector mostrará 3 opciones pero "Audio" DISABLED con tooltip "Disponible próximamente". LOC T-2 down ~80 LOC (400 → 320).

4. **FE feature naming:** spec 06-tickets.yaml::T-onboarding-6::scope dice `vitalia/frontend/src/features/onboarding/`. Confirmar — frontend FE shipped tiene `vitalia/frontend/src/features/vitalia/` placeholder (verified via ls). ¿Crear NEW `features/onboarding/` (per spec) o nest bajo `features/vitalia/onboarding/` (per FSD-Lite brand pattern)? Recomendación: parent spec stand — usar `features/onboarding/` para alinear con FSD boundary matrix.

   ✅ **RATIFIED 2026-05-18:** features/onboarding/ verbatim per spec (NOT nested under features/vitalia/). FSD boundary matrix raw — vitalia/frontend ya está brand-scoped por path. Cada brand tiene su propio {brand}/frontend/, los features/ dentro son flat per .claude/rules/frontend-fsd.md tabla boundary matrix. T-onboarding-6 override añadido a `06-tickets-refresh.yaml` con estructura target verbatim.

## Pre-merge checklist (`/pm-vitalia` post Phase F antes done)

Cuando esta sub-story (vitalia-slice-1-onboarding-wizard) cierre `reviewing → done`:
- [ ] gherkin matrix § 1 de `07-merge.md` mapea SC-W1..W4 a tests reales (heredables de copilot-tools-impl artifact)
- [ ] Playwright E2E run `wizard-onboarding.smoke.spec.ts` verde
- [ ] Capabilities new/updated: `vitalia/docs/product/capabilities/onboarding/wizard_brand_studio_slice_1.yaml` (NEW, status=live)
- [ ] Modules MD refresh: `vitalia/docs/product/modules/onboarding.md` (NEW module)
- [ ] How-to-verify commands reproducibles per template `07-merge-template.md`

## Final summary

| Dimension | Status |
|---|---|
| DB schema drift | NO_DRIFT (caller hint sobre lat/lng era inexacto) |
| Valeria tools contract | NO_DRIFT (signatures funcional equivalente) |
| Slot architecture / cache | NO_DRIFT (relabeling cosmético 0/1-indexed) |
| Validators feasibility | feasible AS-IS, 0 adjustes mandatory |
| Tickets scope | 5 REDUCED, 1 UNCHANGED, 1 REDUCED-to-smoke (was creation) |
| Engine boundary | clean (0 core/ modifications) |
| Cross-brand mirror | clean (0 mirrors) |
| Anti-duplication §0 | compliant (no observability mirror) |
| Action verdict | **MINOR_DRIFT** → `06-tickets-refresh.yaml` override |

## On close — checkpoint update

```yaml
state: refined
phase: READY_PACKAGE_REFRESHED
last_artifact: delta-arch-refresh.md
last_modified: 2026-05-18
next_action: "Spawn /dev-team con tickets T-onboarding-1..7 del parent 06-tickets.yaml + overrides en 06-tickets-refresh.yaml local. Resolver Open Questions §1-§4 con /pm-vitalia (R23 OPT-OUT + repo design + audio scope + FE feature path) antes de pick T-onboarding-1."
```

