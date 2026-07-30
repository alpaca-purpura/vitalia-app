# vitalia-slice-1-fidelizacion — Guidelines (patterns required + forbidden + files + skills)

> **Consumer:** `/dev-team` build loop + each builder agent + auditors.
> **Schema:** post pm-redesign-2026-05 v4 + cement v4.1 2026-05-19 (must_load_skills enforceable).

## § A — Patterns REQUIRED

### A.1 Backend

| # | Pattern | SSoT |
|---|---|---|
| A1.1 | DDD Inside-Out: `domain/` (pure) → `infrastructure/` (impl) → `application/` (services + DTOs) → `api/` (FastAPI thin) | `.claude/rules/backend-ddd.md` |
| A1.2 | Tenant + Clinic dual filter en TODA query PHI (`.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)`) incluyendo `get_by_id` | `vitalia/.claude/rules/hipaa-lite.md` § Tenant isolation refuerzo |
| A1.3 | Repositorios PHI subclase `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` con `scope_field='clinic_id'` (post lift core 2026-05-20) | promotion proposal `2026-05-20-core-platform-extensions-slice-1` |
| A1.4 | Cron jobs wrap `@cron_envelope` engine (idempotency + OTel + audit + sentry) — NUNCA bypass | `luana_core_platform.workers.cron_envelope` |
| A1.5 | Audit log sync write pre-response en TODA mutación/lectura PHI | `vitalia/.claude/rules/hipaa-lite.md` § Audit log |
| A1.6 | PII sanitization en traces: `sanitize_payload(payload, compliance_level="hipaa_lite")` antes writes a observability tables | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` |
| A1.7 | PHI columns encrypted con pgcrypto symmetric (KEK rotated yearly) | `treatment_plans.notes`, `re_engagement_events.payload_phi`, `nps_responses.comment`, `audit_log.payload_redacted` |
| A1.8 | RBAC strict: `@require_phi_access(roles=["doctor", "nurse", "admin_clinic"])` en TODOS endpoints PHI | `vitalia/.claude/rules/hipaa-lite.md` § Access control |
| A1.9 | Channel guard `ComplianceService.validate_outbound_message(template, channel)` antes send WA template | `core/luana-core-compliance/` |
| A1.10 | Domain events emit via `luana_core_events.outbox.adapter_bus.publish(event, session=...)` (USE_OUTBOX_PATTERN_*=True default post 2026-04-30) | `core/luana-core-events/outbox/` |
| A1.11 | Idempotency natural key `(tenant_id, clinic_id, patient_id, pattern, sweep_date)` para crons + Idempotency-Key header for POST writes | `core/luana-core-idempotency/` |
| A1.12 | SQLAlchemy 2.0: `mapped_column()`, `select(...).where(...)`. NUNCA `Column()` o `session.query()` | `.claude/rules/backend-ddd.md` |
| A1.13 | Pydantic v2: `model_config = ConfigDict(from_attributes=True)`. NUNCA inner `class Config` | `.claude/rules/backend-ddd.md` |
| A1.14 | `response_model=` mandatory every route + FastAPI `redirect_slashes=False` (main.py) | `.claude/rules/architectural-fitness.md` |
| A1.15 | `structlog` mandatory `logger.bind(tenant_id=..., clinic_id=..., pattern=..., trace_id=...)`. NUNCA `print()` o stdlib `logging` | `.claude/rules/backend-quality.md` |
| A1.16 | Async-first: repos, services, route handlers all `async def`. AsyncSession only | `.claude/rules/backend-ddd.md` |
| A1.17 | Migrations idempotent raw SQL `IF NOT EXISTS` only. NUNCA `op.create_table()` / `sa.Enum(create_type=True)` | `.claude/rules/backend-migrations.md` |
| A1.18 | TenantLocale VO from `core/luana-core-platform/` for timezone display. NUNCA `datetime.utcnow()` — `utc_now()` helper | `.claude/rules/master-data.md` |
| A1.19 | Currency per data source — DTOs include `currency: str \| None`. NUNCA hardcoded 'USD' | `.claude/rules/currency-handling.md` (NPS no monetary, pero lifetime_value en future Slice 2) |
| A1.20 | Spanish neutro LatAm strict en BE catalogs + DTOs messages + templates Meta-approved scaffold (variables substitution preserve tenant voice) | `.claude/rules/spanish-text.md` |
| A1.21 | Throttle template MARKETING 1 reminder per pattern per 7d MINIMUM (regulación Meta + UX) | (this story rule cementada per `re_engagement_repo.check_throttle()`) |

### A.2 Frontend

| # | Pattern | SSoT |
|---|---|---|
| A2.1 | FSD-Lite per `vitalia/frontend/src/features/fidelizacion/` (api/components/hooks/store/types/copy.ts) | `.claude/rules/frontend-fsd.md` |
| A2.2 | Server-First default RSC. `"use client"` solo en nodos hoja con state/event handlers | `.claude/rules/frontend-fsd.md` |
| A2.3 | `fetchClient` auto-inyecta `X-Tenant-ID + X-Clinic-ID` from Clerk JWT — NUNCA hardcode header | `vitalia/frontend/src/lib/api/fetchClient.ts` |
| A2.4 | nuqs URL state SSoT — push history para inter-route, replace para intra-state (filter/selected/modal) | `vitalia/frontend/src/features/fidelizacion/types/url-state.ts` |
| A2.5 | React Query (TanStack v5): cache key `['fidelizacion', pattern, filters]` + invalidate on mutation success | `vitalia/frontend/src/lib/api/react-query-client.ts` |
| A2.6 | Tokens-only HEX literales en CSS variables (`vitalia/frontend/src/app/globals.css`). Resto consume via Tailwind classes `bg-[hsl(var(--vitalia-cian))]` | `vitalia/docs/architecture/design-system.md` |
| A2.7 | Copy SSoT en `vitalia/frontend/src/features/fidelizacion/copy.ts` — TODAS user-facing strings consumidas via `useCopy(FIDELIZACION_COPY)` helper | `.claude/rules/spanish-text.md` |
| A2.8 | PHI guarded: `<RequireRole roles={['doctor','nurse','admin_clinic']}>` + `<PiiMaskedSpan>` en patient name + lifetime_value + dates históricas + diagnóstico/notes | `vitalia/frontend/src/components/shared/phi/` (Story 11 cement) |
| A2.9 | Cross-feature import via Public API (`index.ts`) only. NUNCA deep import `@/features/other/components/X` | `.claude/rules/frontend-fsd.md` |
| A2.10 | Shared components (`<NPSTagBadge>`) viven en `vitalia/frontend/src/components/shared/nps/` con `index.ts` Public API | `.claude/rules/frontend-fsd.md` |
| A2.11 | TS types camelCase mirror Pydantic snake_case BE. ISO 8601 datetimes as `string` | (this story types/) |
| A2.12 | Storybook coverage mandatory: cada componente NEW tiene `.stories.tsx` cubriendo default + loading + error + empty + variants | `.claude/rules/frontend-quality.md` |
| A2.13 | a11y WCAG 2.1 AA: `role`, `aria-label`, `aria-describedby` (disabled tooltips), focus trap modals, keyboard nav cards | `.claude/rules/e2e-testing.md` § a11y |
| A2.14 | Spanish neutro LatAm strict en `copy.ts` — tuteo `tú`. Voseo prohibido (arch fitness enforces) | `.claude/rules/spanish-text.md` |
| A2.15 | Master data display via `useTenantLocale()` + `formatTenantDate*()` + `formatMoney(amount, currency)` — NUNCA hardcoded timezone/currency | `.claude/rules/master-data.md` |

### A.3 Agentic (Adrián + Lucas)

| # | Pattern | SSoT |
|---|---|---|
| A3.1 | EXTEND engine observability (`core/luana-core-observability/`) — NEVER mirror per `.claude/rules/anti-duplication.md` §0 | `.claude/rules/anti-duplication.md` cardinal |
| A3.2 | Adrián consume engine `core/luana-core-sales-agent/` runtime via DI/service inject. NUNCA modify engine | `sales-agent-expert::§3 NO se toca` |
| A3.3 | New tool `send_proactive_reengagement` wraps existing `send_template_confirmation` (cementado side story `vitalia-copilot-tools-impl` Ola 0) | `vitalia/backend/src/modules/vitalia/sales_agent/tools/` |
| A3.4 | Adrián slot 5 BRAND_VOICE cache prefix from `personality_profiles.system_instruction` — NUNCA inject `{tenant_name}` mid-block | `.claude/rules/sales-agent-brand-voice.md` |
| A3.5 | Lucas re-engagement recommendation tool: simple ReAct (1 aggregate DB tool + 1 LLM reasoning Kimi) — NO supervisor | `tessl__langgraph` |
| A3.6 | Lucas cache prefix slot 1-2 cacheable per-domain/per-graph (1h TTL) — cache_read >= 60% post-deploy | `claude-api` prompt caching |
| A3.7 | All LLM calls log `cache_creation_input_tokens` + `cache_read_input_tokens` + `provider` + `model` + `cost_usd` via engine `cost_recorder.pop_cost(litellm_call_id)` bridge (per PI-12 S1 T-1 cost canonicalization) | `.claude/rules/copilot-observability.md` |
| A3.8 | Eval goldens YAML schema cementado Story B PI-12 evals foundation 2026-05-08 (cost_bucket=evals_only enforced via arch fitness) | `tests/agentic_evals/*/goldens/**` |
| A3.9 | Voice fidelity grader Adrián threshold `grader_score >= 0.85` cada scenario re-engagement | `.claude/rules/sales-agent-brand-voice.md` |
| A3.10 | Trials threshold 0.66 (2/3 trials per scenario must pass) per eval golden batch | (validators §) |
| A3.11 | External calls wrap timeout + fallback (WhatsApp Business API 10s timeout + retry queue persistente) per `tessl__graceful-degradation` | per skill |
| A3.12 | Cost target: Lucas ≤ $0.05/invocation. Adrián turn ≤ $0.05. Cache hit rate ≥ 60%. | (validators §) |
| A3.13 | Tools async `@tool` decorated, call SERVICES (never raw repos), `tenant_id + clinic_id` mandatory en input schema | `.claude/rules/backend-ddd.md` |
| A3.14 | Schema mirror SQLAlchemy models `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/persistence/models/` allowed for engine migration ripple (schema-mirror exception) | `.claude/rules/backend-ddd.md` § Schema-mirror exception |
| A3.15 | R23 production_code routing: AGENTIC runtime tools = Opus 4.7 ONLY. Tests/goldens/docs about agentic = Sonnet OK | `.claude/rules/auditor-downstream-regression.md` + R23 |
| A3.16 | Trace recorder honest: `acc.obs.set_turn_error(error_kind, error_message)` en cada except antes SSE error yield | `copilot-expert` |

## § B — Patterns FORBIDDEN

| # | Anti-pattern | Reason |
|---|---|---|
| B.1 | Mirror engine observability/cost/pricing/turn_envelope/callback_handler en `vitalia/backend/src/modules/vitalia/{sales_agent,copilot}/observability/recording/` | `.claude/rules/anti-duplication.md` §0 cardinal — observability shared inventory |
| B.2 | Cross-brand import (vitalia importa nicolify/comunify/lupulo) | `.claude/rules/anti-duplication.md` § cross-brand mirror ban |
| B.3 | Cross-module SQL JOIN (fidelizacion ↔ otro módulo via JOIN) | `.claude/rules/backend-ddd.md` — store foreign IDs, resolve at application layer |
| B.4 | Modificar engine `core/luana-core-*/src/` sin promotion proposal `/pm-luana` | `.claude/rules/auditor-downstream-regression.md` § Engine edit detection |
| B.5 | Skip dual filter `clinic_id` "porque single-tenant clinic" | `vitalia/.claude/rules/hipaa-lite.md` cardinal |
| B.6 | PHI en URLs GET query params (`?dni=12345678`) — usar POST body siempre | `vitalia/.claude/rules/hipaa-lite.md` § Anti-patterns |
| B.7 | PHI en logs sin `sanitize_payload` | `vitalia/.claude/rules/hipaa-lite.md` |
| B.8 | PHI en email plaintext (debe linkear portal, no incluir diagnóstico body) | idem |
| B.9 | Skip throttle template WA 7d (compliance Meta + UX) | (this story rule) |
| B.10 | Send template MARKETING sin opt-in checkbox firmado consentimiento | Meta sanciona cuenta + regulación local LATAM |
| B.11 | Atribución falsa "Adrián decidió enviar autónomo" cuando cron disparó — origin debe ser `proactive_outbound` con sub-attribution "Adrián abrió conv · solicitado por sistema (cron X) confirmado operador {user_id}" | parent spec § Batch 4 cementado |
| B.12 | Skip `opt_out=true` flag en queries cron — paciente que dijo STOP nunca debe re-aparecer | this story rule cardinal |
| B.13 | Hardcoded strings JSX `vitalia/frontend/src/features/fidelizacion/*.tsx` — todo via `FIDELIZACION_COPY` | `.claude/rules/spanish-text.md` + arch fitness |
| B.14 | Cron sin `@cron_envelope` (bypass idempotent + OTel + audit + sentry centralizado) | `.claude/rules/architectural-fitness.md` (NEW gate `test_cron_envelope_used.py`) |
| B.15 | Repositorios PHI sin subclase `CompoundScopeRepositoryBase` con `scope_field='clinic_id'` | `.claude/rules/architectural-fitness.md` (NEW gate `test_compound_scope_repository_used.py`) |
| B.16 | NPS detractor visible sin masking comentario (no usar PHI en preview ni hover) | `vitalia/.claude/rules/hipaa-lite.md` |
| B.17 | Tag NPS en `/inbox` sin role check (PHI cruza rutas — respetar hipaa-lite RBAC) | idem |
| B.18 | Follow-up captured campo libre sin parsing duration robusto ("3 meses" → 90d backend) | parent spec |
| B.19 | Maintenance config offer sin migration retroactiva (offers existentes default NONE) | (this story rule) |
| B.20 | Cron timing en server-local TZ vs UTC (TZ confusion → cron disparo a hora inesperada) | `.claude/rules/master-data.md` |
| B.21 | Re-engagement count contaminando `/pipeline` ventas analytics (cohort separado obligatorio) | parent spec |
| B.22 | Templates Meta sin submit pre-aprobación (Meta rechaza envío templates no aprobados) | Meta Platform Terms |
| B.23 | Skip throttle template WA Business cost (limit per tenant per día — Slice 1 200 MARKETING/día default) | (this story rule) |
| B.24 | `send_medical_summary` por WhatsApp tier free (ComplianceService canal seguro guard) | `vitalia/.claude/rules/hipaa-lite.md` + `core/luana-core-compliance/` |
| B.25 | LangGraph `MemorySaver` (tutorials only) — use `AsyncPostgresSaver` for any agentic state | `tessl__langgraph` (No aplica esta story — no NEW LangGraph) |
| B.26 | Default flag flip side-effect sin Step 1 grep tests + Step 3 run AMBOS valores + Step 4 doc commit body | `.claude/rules/anti-default-flip-audit.md` (No aplica esta story — no flips) |
| B.27 | Builder editing SSoT files (learnings.md, BACKLOG, MEMORY, PORTFOLIO) — solo `/pm-{brand}` o `/pm-luana` | `.claude/rules/parallel-safety.md` M2 |
| B.28 | `git pull` / `git fetch && merge` / `--force` / `--no-verify` / `git add .` / `git add -A` | `.claude/rules/git-safety.md` |
| B.29 | Auditor self-fix tests (cualquier `.test.*` o `test_*.py`) — TDD discipline vive en dev-team | `.claude/rules/auditor-self-fix-policy.md` § NUNCA |

## § C — Files in scope (whitelist for builders)

### C.1 Backend builder may CREATE/MODIFY

```
vitalia/backend/src/modules/vitalia/fidelizacion/**
vitalia/backend/src/modules/vitalia/crm/{api,application/services/patient_consent_service.py,infrastructure/models/patient_model.py}  ← extend ONLY (opt_in/opt_out columns + endpoint)
vitalia/backend/src/modules/vitalia/connections/whatsapp/templates/fidelizacion/**  ← 5 Meta-approved JSON config files
vitalia/backend/src/modules/vitalia/extensions.py  ← register fidelización templates via EP-8 (pre-existing pattern)
vitalia/backend/src/modules/vitalia/persistence/migrations/{020,021,022,023}_slice1_*.py  ← idempotent raw SQL only
vitalia/backend/tests/modules/vitalia/fidelizacion/**
vitalia/backend/tests/modules/vitalia/crm/test_patient_consent*.py
vitalia/backend/tests/migrations/test_slice1_fidelizacion_migrations.py
vitalia/backend/tests/integration/test_cross_story_contracts.py  ← extend (add reengagement + nps tests)
vitalia/backend/tests/architecture/test_cron_envelope_used.py  ← NEW arch fitness gate
vitalia/backend/tests/architecture/test_compound_scope_repository_used.py  ← NEW arch fitness gate
vitalia/backend/tests/fixtures/{sanare_mx_tenant,patients_dental_cohort,offers_dental_catalog,appointments_completed_with_followup,re_engagement_events_seed,whatsapp_templates_meta_approved}.py
```

### C.2 Frontend builder may CREATE/MODIFY

```
vitalia/frontend/src/features/fidelizacion/**
vitalia/frontend/src/components/shared/nps/**
vitalia/frontend/src/lib/zod-schemas/{nps,re-engagement-event}.ts  ← NEW shared cross-feature Zod schemas
vitalia/frontend/src/app/(app)/fidelizacion/page.tsx  ← NEW Next.js route mount
vitalia/frontend/e2e/pages/fidelizacion.page.ts  ← POM
vitalia/frontend/e2e/specs/smoke/fidelizacion.smoke.spec.ts
vitalia/frontend/e2e/specs/regression/fidelizacion-*.spec.ts  ← 4 scenarios
vitalia/frontend/e2e/fixtures/{fidelizacion-seed,clinic-context}.fixture.ts
```

### C.3 Agentic builder may CREATE/MODIFY

```
vitalia/backend/src/modules/vitalia/sales_agent/tools/send_proactive_reengagement.py  ← NEW
vitalia/backend/src/modules/vitalia/agentic/lucas/tools/compute_re_engagement_recommendation.py  ← NEW
vitalia/backend/src/modules/vitalia/agentic/lucas/{__init__.py,services/lucas_re_engagement_service.py}  ← NEW
vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_send_proactive_reengagement.py
vitalia/backend/tests/modules/vitalia/agentic/lucas/tools/test_compute_re_engagement_recommendation.py
vitalia/backend/tests/agentic_evals/sales_agent/goldens/reengagement/**  ← 4 YAML golden scenarios
vitalia/backend/tests/agentic_evals/lucas/re_engagement_recommendation/**  ← 3 YAML golden scenarios
vitalia/backend/tests/agentic_evals/sales_agent/test_voice_fidelity_reengagement.py
vitalia/backend/tests/agentic_evals/lucas/test_prompt_cache_hit_rate.py
```

### C.4 FORBIDDEN (out of scope this story)

```
core/luana-core-*/src/**  ← engine modifications require /pm-luana promotion proposal
nicolify/**, comunify/**, lupulo/**  ← cross-brand FORBIDDEN
backend/src/shared/**  ← LEGACY pre-multibrand path (post 2026-05-15 deprecated)
vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/observability/recording/**  ← anti-duplication §0 cardinal (consume engine direct)
vitalia/frontend/src/features/agenda/**  ← OWNED by /agenda Ola 3 story
vitalia/frontend/src/features/inbox/**  ← OWNED by /inbox Ola 1 paralela story (consumer only via Public API)
vitalia/frontend/src/features/offer-studio/components/MaintenanceScheduleField.tsx  ← parent spec mention but defer Slice 2 wizard /offer-studio full
```

## § D — Skills MUST load (per surface) — v4.1 cement 2026-05-19

| Surface | Skills must_load | Resolution context |
|---|---|---|
| Backend fidelización module | `backend-expert`, `metrics-expert` (NPS aggregates) | DDD + arch fitness + master-data + currency + ETL contract (no ETL touched, but NPS metric pattern future) |
| Frontend fidelización feature | `frontend-expert`, `playwright-expert` (E2E) | FSD + tokens + form-runtime (no aplica directly esta story) + a11y |
| Backend cron jobs | `backend-expert` | cron_envelope pattern + idempotency |
| Backend opt-in/opt-out CRM extension | `backend-expert` | DDD + master-data |
| Agentic Adrián tool wrapper | `sales-agent-expert`, `copilot-expert` (anti-duplication §0), `tessl__langgraph`, `tessl__graceful-degradation` | Adrián §3 NO se toca + observability shared + WhatsApp tool wrap timeout+fallback |
| Agentic Lucas tool | `copilot-expert` (anti-duplication §0), `tessl__langgraph`, `metrics-expert` (aggregate queries) | Lucas growth pattern + observability shared + simple ReAct |
| Eval goldens | `sales-agent-expert` (voice fidelity grader threshold) | goldens schema cementado Story B PI-12 |
| Migrations Slice 1 | `backend-expert` | idempotent raw SQL + pgcrypto |
| Architecture fitness new gates | `backend-expert` (arch fitness ratchet) | shrink-only allowlists + new test_cron_envelope_used + test_compound_scope_repository_used |
| FE shared NPS component | `frontend-expert`, `brand-expert` (cross-feature shared abstraction lift candidate) | Public API + cross-feature import boundary |
| E2E Playwright | `playwright-expert` | Clerk auth fixture + POM + smoke/regression structure |
| Git workflow + commit | (orchestrator Opus) → `commit-push` (Haiku delegation) | `.claude/rules/git-haiku-delegation.md` |

## § E — Rules MUST load (universal + brand overlay)

| Rule | Scope |
|---|---|
| `.claude/rules/tenant-isolation.md` | universal cardinal |
| `vitalia/.claude/rules/hipaa-lite.md` | brand overlay cardinal (dual filter tenant+clinic + audit_log + pgcrypto + RBAC + channel guard) |
| `.claude/rules/backend-ddd.md` | backend DDD Inside-Out + schema-mirror exception |
| `.claude/rules/backend-migrations.md` | migrations idempotent IF NOT EXISTS raw SQL |
| `.claude/rules/backend-quality.md` | Ruff 70+ rules + arch fitness |
| `.claude/rules/frontend-fsd.md` | FSD-Lite boundary matrix |
| `.claude/rules/frontend-quality.md` | ESLint 60+ + TS strict + Vitest |
| `.claude/rules/architectural-fitness.md` | ratchet allowlists shrink-only |
| `.claude/rules/anti-duplication.md` | observability/cost/pricing shared inventory + cross-brand mirror ban |
| `.claude/rules/tdd-mandatory.md` | RED first per layer |
| `.claude/rules/spanish-text.md` | Latam neutro tuteo + magic comment escape |
| `.claude/rules/master-data.md` | UTC store + timezone tenant + DateTime(timezone=True) + utc_now() |
| `.claude/rules/currency-handling.md` | DTOs `currency: str \| None`, formatMoney(amount, currency) |
| `.claude/rules/copilot-observability.md` | trace events recorder + LLM call recording + best-effort |
| `.claude/rules/copilot-resilience.md` | copilot debug pattern (no direct Slice 1 — Lucas observability) |
| `.claude/rules/sales-agent-brand-voice.md` | Adrián slot 5 BRAND_VOICE compiler v2 |
| `.claude/rules/auditor-downstream-regression.md` | engine edit detection + cross-brand mirror scan + downstream test scope |
| `.claude/rules/auditor-self-fix-policy.md` | auditor never writes tests + whitelist self-fix categories |
| `.claude/rules/story-closure-gate.md` | 6 phases A-F + auto-handoff + 07-merge 5 secciones + archive at done |
| `.claude/rules/brand-docs-schema.md` | R1 no MD sueltos en `{brand}/docs/` raíz + R2 stories done auto-move archive + R3 auto-gen markers |
| `.claude/rules/e2e-testing.md` | Playwright native + Clerk auth fixture + POMs |
| `.claude/rules/debugging.md` | Docker per-brand + native lint/tests + top patterns 80% bugs |
| `.claude/rules/parallel-safety.md` | worktree D1-D14 + scope per branch + N sesiones bucket lock |
| `.claude/rules/step-0-worktree.md` | skill step 0 sync + brand detect |
| `.claude/rules/git-safety.md` | triple-branch policy + no pull/force/revert |
| `.claude/rules/git-haiku-delegation.md` | commit+push delegation orchestrator → Haiku |
| `.claude/rules/hotfix-repro-mandatory.md` | repro_verified field hot-fix tickets (no aplica esta story — no hotfix) |
| `.claude/rules/anti-default-flip-audit.md` | default flips side-effect (no aplica esta story — no flips) |
| `.claude/rules/data-reliability.md` | 4-layer verification ETL (no aplica directly Slice 1 — NPS not ETL'd to analytics-engine) |

## § F — Conditional rules by ticket surface

| Ticket type | Additional rules to load |
|---|---|
| Backend module DDD ticket | A1.* + B.3 + B.4 + B.5 + B.7 + B.12 + B.14 + B.15 |
| Migration ticket | A1.17 + B.4 (engine column extensions require proposal — but esta story pre-flight gate ya cubrió eso) |
| Cron worker ticket | A1.4 + A1.10 + A1.11 + B.14 + B.20 |
| API endpoint ticket | A1.8 + A1.9 + A1.14 + A1.21 + B.5 + B.6 + B.9 + B.10 |
| Frontend component ticket | A2.2 + A2.6 + A2.7 + A2.8 + A2.12 + A2.13 + B.13 + B.16 + B.17 |
| Agentic tool ticket | A3.* + B.1 + B.2 + B.4 + B.11 + B.25 |
| Eval goldens ticket | A3.8 + A3.9 + A3.10 + A3.15 |
| E2E ticket | A2.13 (a11y) + `playwright-expert` skill |

## § G — Decision IDs ratificados (decisions_applicable for tickets per R6)

| ID | Decision | Source |
|---|---|---|
| **D1** | DDD Inside-Out strict per fidelización module | parent arch + `.claude/rules/backend-ddd.md` |
| **D2** | PHI dual filter `tenant_id + clinic_id` cardinal | `vitalia/.claude/rules/hipaa-lite.md` |
| **D3** | Audit log sync write pre-response en PHI mutations | idem |
| **D4** | pgcrypto encryption PHI columns at-rest | idem |
| **D5** | RBAC strict `@require_phi_access` decorator | idem |
| **D6** | Compliance channel guard `ComplianceService.validate_outbound_message` | `core/luana-core-compliance/` |
| **D7** | Cron envelope engine wrap `@cron_envelope` (post lift core 2026-05-20) | promotion proposal `2026-05-20-core-platform-extensions-slice-1` |
| **D8** | CompoundScopeRepositoryBase subclass scope_field=clinic_id (post lift) | idem |
| **D9** | NPS schema tabla separada `vitalia_nps_responses` (NOT denormalized column) — § 7 Open Questions arch resolution | this arch § 7 |
| **D10** | Lucas re-engagement tool on-demand pull (no cron — Slice 1) — § 7 idem | idem |
| **D11** | Throttle template MARKETING 7d minimum per pattern per patient | spec + this story rule |
| **D12** | Templates Meta-approved 5 (3 UTILITY + 2 MARKETING) JSON config in `connections/whatsapp/templates/fidelizacion/` | spec § 3 |
| **D13** | Activity footer React Query polling 10s Slice 1 (defer SSE Slice 2) | § 7 idem |
| **D14** | Reuse Nicolify campaigns-lite + notifications token adapter (NO direct deep import) | spec § Reuse + arch § Reuse |
| **D15** | `NPSScoreCollected` + `ReEngagementTriggered` outbox events via `adapter_bus.publish()` (default post 2026-04-30) | `.claude/rules/anti-default-flip-audit.md` |
| **D16** | Adrián `send_proactive_reengagement` wraps existing `send_template_confirmation` (no new core graph) | `sales-agent-expert::§3 NO se toca` |
| **D17** | Lucas tool simple ReAct (1 aggregate + 1 LLM reasoning) — no supervisor | `tessl__langgraph` |
| **D18** | Cache prefix Lucas 1h TTL + 60% hit rate target | `claude-api` |
| **D19** | Voice fidelity grader threshold 0.85 + trials threshold 0.66 | `sales-agent-expert` |
| **D20** | R23 production_code routing: agentic runtime tools = Opus 4.7. tests/goldens = Sonnet OK | `.claude/rules/auditor-downstream-regression.md` |
| **D21** | TS types camelCase + Zod schemas shared en `vitalia/frontend/src/lib/zod-schemas/{nps,re-engagement-event}.ts` | this arch + HANDOFF |
| **D22** | Cross-feature `<NPSTagBadge>` shared en `vitalia/frontend/src/components/shared/nps/` (not feature-scoped) | this arch |
| **D23** | URL state nuqs 11 params (tab, period, vertical, doctor, urgency, selectedPatient, 4 modals) | this arch FE § 5 |
| **D24** | Storybook mandatory cada componente NEW (visual regression source + dev productivity) | universal cross-cutting |
| **D25** | Patient `opt_out=true` cascade cancel pending re_engagement_events (consent_service) | this story rule |

Builders MUST cite decisions_applicable list en commit body sección "Decisions honored".
