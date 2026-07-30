# vitalia-ux-discovery — Guidelines

> **Consumer:** `/dev-team` builders + `/auditor` reviewers.
> **Index:** `03-arch.md` (read first).

## 1. Skills + Rules to load (per ticket type)

### 1.1 BE non-agentic tickets (most modules)

**Skills (Bash invocation per `.claude/skills/`):**
- `backend-expert` — DDD Inside-Out, SQLA 2.0, Pydantic v2, Alembic idempotent, arch fitness
- `metrics-expert` — when ticket touches `vitalia/backend/src/modules/vitalia/marketing/`
- `brand-expert` — when ticket touches `vitalia/backend/src/modules/vitalia/onboarding/` (brand_studio interaction)
- `offer-expert` — when ticket touches `vitalia/backend/src/modules/vitalia/offer/` (medical_services_v1)
- `offer-type-preset-expert` — when ticket modifies preset pack
- `playwright-expert` — when ticket needs E2E smoke (frontend-adjacent)

**Tessl knowledge tiles:**
- `tessl__fastapi` · `tessl__pytest-api-testing` · `tessl__sqlalchemy` · `tessl__alembic` · `tessl__graceful-degradation`

**Rules (.claude/rules/):**
- `tenant-isolation.md` (CARDINAL) · `backend-ddd.md` · `backend-migrations.md` · `backend-quality.md` · `master-data.md` · `currency-handling.md` · `architectural-fitness.md` · `auditor-downstream-regression.md` · `anti-duplication.md` · `tdd-mandatory.md` · `spanish-text.md` · `parallel-safety.md` · `git-safety.md` · `git-haiku-delegation.md`

**Brand overlay:**
- `vitalia/.claude/rules/hipaa-lite.md` (CARDINAL Vitalia)

### 1.2 FE tickets

**Skills:**
- `frontend-expert` — FSD-Lite, Server-First RSC, React Query, RHF+Zod, Tailwind + Shadcn
- `playwright-expert` — E2E smoke + visual regression
- `chrome-devtools-verify` — live verification pre-merge

**Tessl knowledge tiles:**
- `tessl__react-patterns` · `tessl__zod` · `tessl__shadcn-ui` · `tessl__tailwind` · `tessl__vitest` · `tessl__nextjs-app-router-modularization` · `tessl__nuqs` · `tessl__react-query` · `tessl__react-hook-form`

**Rules:**
- `frontend-fsd.md` · `frontend-quality.md` · `architectural-fitness.md` · `e2e-testing.md` · `spanish-text.md` · `tdd-mandatory.md` · `master-data.md` · `currency-handling.md` · `parallel-safety.md` · `git-safety.md`

**Brand overlay:**
- `vitalia/.claude/rules/hipaa-lite.md` (PHI surface conventions per design-system.md § 8)

### 1.3 Agentic tickets (R23 — production_code=true → Opus 4.7)

**Skills:**
- `sales-agent-expert` — Adrián compiler v2 slots, §3 NO toca, LiteLLM canonical, voice fidelity, cost canonicalization
- `copilot-expert` — Valeria observability, deepagents subagent, SSE v2, plan cards
- `brand-expert` — wizard onboarding voice infra engine consume
- `claude-api` — prompt cache + tool use + extended thinking patterns

**Tessl knowledge tiles:**
- `tessl__langgraph` (supervisor, AsyncPostgresSaver, 6 stream modes)
- `tessl__deepagents` (SubAgentMiddleware, task tool, isolation)
- `tessl__graceful-degradation` (external tool timeout+fallback)

**Rules:**
- `copilot-resilience.md` · `copilot-observability.md` · `sales-agent-brand-voice.md` · `anti-duplication.md` (CARDINAL §0) · `auditor-downstream-regression.md` · `tdd-mandatory.md` · `tenant-isolation.md` · `spanish-text.md`

**Brand overlay:**
- `vitalia/.claude/rules/hipaa-lite.md`

## 2. Required patterns (MUST follow)

### 2.1 Backend

1. **DDD Inside-Out** — domain pure (no framework), infrastructure implements ports, application orchestrates services, api thin
2. **Tenant + Clinic dual filter** — every PHI query `.where(Model.tenant_id == tenant_id, Model.clinic_id == clinic_id)`. Including `get_by_id`.
3. **Soft delete** — `deleted_at TIMESTAMPTZ NULL` mandatory. NEVER hard delete.
4. **SQLAlchemy 2.0 only** — `mapped_column()`, `select(Model).where(...)`. NEVER `Column()` or `session.query()`.
5. **Pydantic v2 ConfigDict** — `model_config = ConfigDict(from_attributes=True)`. NO inner `class Config`.
6. **response_model= on every route** — PII allowlist enforcement (arch fitness `test_response_model_required.py`).
7. **`FastAPI(redirect_slashes=False)`** in `main.py`.
8. **Cross-module via ports** — `shared/links/ports/...` for reads, domain events for writes. NEVER cross-module import directo.
9. **Migrations idempotent** — raw SQL `IF NOT EXISTS` / `IF EXISTS`. NEVER `op.create_table()` / `sa.Enum(create_type=True)`.
10. **`structlog`** mandatory. NEVER `print()` / stdlib `logging`. Bind context `tenant_id`, `clinic_id`, `trace_id`.
11. **Async-first** — all repos, services, route handlers `async def`. AsyncSession.
12. **Audit log sync write** — PHI access logs row BEFORE response sent. Sync, not fire-forget.
13. **pgcrypto encryption** — PHI columns (`diagnosis`, `treatment_plan`, `medical_notes`, `treatment_plans.notes`, `re_engagement_events.payload_phi`, `audit_log.payload_redacted`). KEK via Vault/KMS, not env vars.
14. **RBAC strict** — `@require_phi_access(roles=["doctor", "nurse", "admin_clinic"])` on every PHI endpoint.
15. **Idempotency keys** — POST/PUT routes with retry potential accept `Idempotency-Key` header → `core/luana-core-idempotency/` checks.
16. **Currency policy** — DTOs with monetary fields include `currency: str | None = None`. ETL keeps source currency. NO hardcoded 'USD'.
17. **TenantLocale VO** — `datetime` always UTC-aware (`DateTime(timezone=True)`). Display tenant timezone via `useTenantLocale()` (FE) or `TenantLocale` VO (BE).
18. **Spanish neutro UI strings** — tuteo, NO voseo. EXCEPTION: Adrián output respects tenant voice (`personality_profiles.system_instruction`).
19. **TDD** — RED test FIRST per layer (domain → infra → app → api). NEVER commit without test.
20. **Extension SDK only** — brand surfaces register via `extensions.py::register_all(registry)`. NEVER mirror engine functions in `vitalia/`.

### 2.2 Frontend

1. **FSD-Lite layers** — `app/` thin routing · `features/{m}/` autocontained · `components/shared/` cross-feature · `lib/` utils
2. **Server Components default** — `"use client"` ONLY on leaf nodes with `useState`/`useEffect`/event handlers
3. **Public API via `index.ts`** — feature exports via `features/{m}/index.ts`. NO deep imports cross-feature.
4. **`fetchClient`** auto-injects `X-Tenant-ID` + `X-Clinic-ID` from Clerk JWT. NEVER hardcode.
5. **nuqs URL state SSoT** — push for inter-route nav, replace for intra-state. Schemas per feature in `types/url-state.ts`.
6. **React Query (TanStack v5)** for data fetching. Mutations include Idempotency-Key.
7. **RHF + Zod** for forms. Zod schemas in `lib/zod-schemas/` or feature `schemas/`.
8. **Tokens-only HEX literales** — in `globals.css` `:root`. NEVER hex outside (arch fitness enforces).
9. **`cn()` from `lib/utils.ts`** for Tailwind class composition.
10. **Microcopy in `copy.ts`** — every user-facing string lives in `features/{m}/copy.ts` per feature. Spanish neutro LatAm.
11. **PHI wrappers** — `<PiiMaskedSpan>` / `<RequireRole>` / `<AuditedSection>` for every PHI surface.
12. **Agent attribution** — use `<AgentAvatar>` + `<AgentAttribution>` for all agent UI references (Adrián / Lucas / Valeria / Sistema).
13. **NO `any`** — `unknown` + type guards.
14. **NO default exports** (except Next.js pages).
15. **TDD** — RED test FIRST (hook → component → store → E2E smoke).
16. **Storybook stories obligatorios** for 12 critical components (per `04-validators.yaml::visual_storybook_build`).
17. **A11y WCAG 2.1 AA** — `aria-label`, keyboard nav, contrast ratios, `prefers-reduced-motion` fallback.

### 2.3 Agentic

1. **R23 cost-routing** — production_code=true → Opus 4.7 ONLY. Tests/docs → Sonnet OK.
2. **§3 NO TOCAR** Adrián engine surfaces (Closer Studio API+WS, SmartBufferService, OutputManager chunking, enrollment_*, agent_state_checkpoints, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup).
3. **Anti-duplication §0 cardinal** — engine observability/cost/pricing/turn_envelope/callback_handler/FX/tenant_billing/PII patterns viven en `core/luana-core-*/`. EXTEND via heredancia.
4. **LiteLLM Proxy canonical** post 2026-05-06. NEVER direct provider adapters.
5. **`AsyncPostgresSaver` checkpointer** — NEVER `MemorySaver` in production.
6. **Prompt cache slot order** — slots 1-5 cacheable (system + domain + tools + persona + BRAND_VOICE) with `cache_control` marker. Slot 6 variable.
7. **Forbidden in cache prefix** — timestamps, conversation IDs, turn counters, random IDs, `{tenant_name}` mid-block.
8. **`sanitize_payload(compliance_level="hipaa_lite")`** before writes to observability tables. Vitalia adds NEW PHI fields per `phi_fields.py`.
9. **Tool design** — `@tool` decorated, async, calls SERVICES (never raw repos), `tenant_id` + `clinic_id` mandatory params, external calls wrap timeout+fallback.
10. **deepagents subagent isolation** — `SubAgentMiddleware.allowed_keys_to_subagent` + `allowed_keys_from_subagent` explicit.
11. **Cost canonicalization** — `cost_usd` via `pop_cost(litellm_call_id)` from CustomLogger bridge. Fixtures MUST include `litellm_call_id` in `response_metadata`.
12. **Max-iter guard** — `if state["iterations"] > 25: return END` per `COPILOT_RECURSION_LIMIT`.
13. **Medical guardrails** — register via EP-13 with real check callables (T-guards-1..3 implement).
14. **Channel guards** — PHI on non-encrypted channels (WhatsApp free/SMS/email plaintext) MUST be blocked + redirect to portal.
15. **Voice fidelity grader** — eval against `personality_profile.system_instruction` voice anchors per persona. Threshold ≥ 0.85.

### 2.4 Cross-cutting

1. **TDD mandatory** per `.claude/rules/tdd-mandatory.md`.
2. **Conventional Commits** — `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`.
3. **Git workflow** — wip/* branches per session, worktrees, never `git pull`, never force push. Per `.claude/rules/git-safety.md`.
4. **Commit+push delegation** Haiku via `/commit-push` skill per `.claude/rules/git-haiku-delegation.md` (when >2 files staged).
5. **Repro mandatory** on hot-fix tickets per `.claude/rules/hotfix-repro-mandatory.md` (NOT applicable Slice 1 — no hot-fix this story).
6. **Anti-default-flip audit** — Slice 1 introduces ZERO flips. Future Slice 2 flips → 4-step audit per `.claude/rules/anti-default-flip-audit.md`.
7. **Downstream regression scope** — auditors run downstream tests per `.claude/rules/auditor-downstream-regression.md` § A-I tables.

## 3. Forbidden patterns (NEVER do — per spec § Handoff #6 + cross-cutting)

### 3.1 Backend forbidden

- ❌ Cross-module SQL JOINs (use ports + application layer resolution)
- ❌ Cross-module direct imports outside `core/luana-core-*/` (use ports `shared/links/ports/`)
- ❌ Cross-brand mirror (NEVER `vitalia/backend/src/.../X.py` if `nicolify/backend/src/.../X.py` similar — lift to engine via `/pm-luana`)
- ❌ Engine direct edit (NEVER modify `core/luana-core-*/src/` — escalate promotion proposal)
- ❌ Hard delete (always soft delete `deleted_at`)
- ❌ `session.query()` (SQLA 1.x legacy) — use `select(...)`
- ❌ `Column()` definitions — use `mapped_column()`
- ❌ `class Config:` (Pydantic v1) — use `model_config = ConfigDict(...)`
- ❌ `print()` / stdlib `logging` — use `structlog`
- ❌ `datetime.utcnow()` — use `utc_now()` helper
- ❌ `DateTime()` without `timezone=True`
- ❌ Hardcoded `'USD'` in DTOs (use `currency: str | None`)
- ❌ Hardcoded timezone (use `TenantLocale` VO)
- ❌ PHI in URL query params (`GET /patients?dni=...`) — POST body always
- ❌ PHI in logs without `sanitize_payload` (`logger.info(f"Patient {patient.name}...")` PROHIBIDO)
- ❌ Audit log async fire-forget — sync write mandatory
- ❌ Bypass dual filter "porque single-tenant clinic" — siempre, sin excepción
- ❌ Reusar audit_log de raíz Luana — Vitalia tiene su propio audit_log (clinic_id + payload_redacted columns)
- ❌ `op.create_table()` / `op.add_column()` / `op.create_index()` (no idempotentes) — use raw SQL `IF NOT EXISTS`
- ❌ `sa.Enum(..., create_type=True)` (broken SA 2.0.27)
- ❌ `redirect_slashes=True` in `FastAPI(...)` (default broken for Next.js POST 307)
- ❌ Missing `response_model=` on route (arch fitness blocks)
- ❌ Missing `X-Tenant-ID` middleware on authenticated routes
- ❌ Cifrado simétrico app-level "rolled-our-own" — use `pgcrypto` or cloud KMS
- ❌ Default flag flip without 4-step audit (Slice 1 NO flips)
- ❌ docker exec ruff/pytest — native ONLY per `.claude/rules/backend-quality.md`

### 3.2 Frontend forbidden (13 anti-patterns Nicolify NO replicar — spec § Handoff #6)

- ❌ 4-tier loading sobre-ingeniero (1-2 tiers max Slice 1)
- ❌ Sidebar mega-detallada 8 tabs per channel (3 sections drill Vitalia)
- ❌ 13 hooks dispersos (consolidate ≤ 5 per feature)
- ❌ 8 endpoints separados (bundle 1-2 per resource)
- ❌ `ChannelGroupCard` artificial category (direct flat list Slice 1)
- ❌ `OfferLadder` demasiado abstracto (use `medical_services_v1` preset directly)
- ❌ `BenchmarkBadge` sin data (defer Slice 2 cuando benchmarks salud LATAM available)
- ❌ `LazyChannelGroup` tier loading (Suspense + intersection observer simpler)
- ❌ `_CATALOG_VERSION` bump manual (automated build script)
- ❌ `useCopilotOffset` coupling (Copilot rail self-contained)
- ❌ Lazy-loading sin error boundary (`<ErrorBoundary>` mandatory)
- ❌ Hard-coded slugs literales (use registries)
- ❌ Cross-feature imports sin port (Public API `index.ts` mandatory)
- ❌ Component naming por implementación (name by domain semantics)
- ❌ HEX literales outside `globals.css` (arch fitness `test_no_hardcoded_colors`)
- ❌ Hardcoded strings JSX (use `<feature>/copy.ts`)
- ❌ Voseo in user-facing copy (EXCEPTION: Adrián output backend)
- ❌ PHI in `localStorage`/`sessionStorage`
- ❌ PHI without `<PiiMaskedSpan>` / `<RequireRole>` / `<AuditedSection>` wrapper
- ❌ `any` types (use `unknown` + type guards)
- ❌ Default exports (except Next.js pages)
- ❌ `make e2e` / `make e2e-smoke` Docker (use NATIVE per `e2e-testing.md`)
- ❌ Spawn webServer dentro Playwright (use `E2E_BASE_URL`)
- ❌ Locators CSS/XPath (use Playwright role-based selectors)
- ❌ `test.skip` permanente
- ❌ Modal centrado para "Procesar pago saldo" (use sheet inline ContactSidebar per spec § Batch 4)
- ❌ `make dev` (Docker single-brand) — use `make dev-vitalia` per multibrand

### 3.3 Agentic forbidden

- ❌ Migrar StateGraph a deepagents wholesale (deepagents only subagent isolation)
- ❌ Eliminar Closer Studio + WS + SmartBufferService + OutputManager + follow_up_engine
- ❌ Subagents deepagents para Adrián especialistas (specialists viven en engine StateGraph)
- ❌ Hardcodear model wire-name strings en specialists (use `LLM_ROLE_BY_SITE` SSoT engine)
- ❌ Hardcodear canales literales en `OutputManager` (use `get_channel_format(channel_type)`)
- ❌ Import `copilot/` desde `sales_agent/` (o viceversa) — both consume `core/luana-core-*/`
- ❌ Tocar `PromptVersionModel`
- ❌ `from __future__ import annotations` en `*/orchestrator/graph.py` (rompe LangGraph runtime introspection)
- ❌ Bypass `sanitize_payload` en writes a `*_trace_event` / `*_llm_call`
- ❌ Duplicar plumbing `BaseAgentCallbackHandler` shared (only overrides agent-specific)
- ❌ Bypass channel registry shared
- ❌ Aliases DeepSeek retired (`deepseek-chat`, `deepseek-reasoner`) — use `deepseek-v4-flash` / `deepseek-v4-pro`
- ❌ Tier pricing >200k sin resolver (Kimi K2.6 split `TIER_THRESHOLD = 200_000`)
- ❌ `MemorySaver` checkpointer in production (use `AsyncPostgresSaver`)
- ❌ Inyectar `{tenant_name}` mid-block cache prefix slot 5 (use slot boundary)
- ❌ Crear archivo nuevo en `modules/{copilot,sales_agent}/observability/recording/<X>.py` o `cost/<X>.py` o `pricing/<X>.py` sin check `.claude/rules/anti-duplication.md` inventory first
- ❌ Tool sin `tenant_id` + `clinic_id` mandatory params
- ❌ Tool sin timeout+fallback wrap para external calls
- ❌ Mirror cross-brand tool (lift to engine via `/pm-luana` promotion)

## 4. Files in scope (per builder/auditor)

### 4.1 builder-backend scope

**Allowed paths:**
- `vitalia/backend/src/modules/vitalia/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding,connections,iam,crm,compliance,_shared}/{domain,application,api,infrastructure}/`
- `vitalia/backend/src/modules/vitalia/persistence/migrations/`
- `vitalia/backend/src/modules/vitalia/main.py`
- `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/persistence/models/` (SCHEMA-MIRROR EXCEPTION ONLY per `backend-ddd.md`)
- `vitalia/backend/tests/{modules,architecture,migrations,workers}/`

**Forbidden paths:**
- `core/luana-core-*/` (READ-ONLY consult — modifications require `/pm-luana` promotion)
- `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/{tools,extractors,workflows,kb,personas,goldens}/` (builder-agentic jurisdiction)
- `vitalia/frontend/src/`
- Other brands' code (`nicolify/`, `comunify/`, `lupulo/`)

### 4.2 builder-agentic scope

**Allowed paths:**
- `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/{tools,extractors,workflows,kb,personas,goldens,prompts}/`
- `vitalia/backend/src/modules/vitalia/agentic/`
- `vitalia/backend/src/modules/vitalia/extensions.py`
- `vitalia/backend/tests/{modules,agentic_evals}/{copilot,sales_agent}/`
- `vitalia/backend/tests/test_extensions.py`

**Forbidden paths:**
- `core/luana-core-*/` (READ-ONLY)
- Schema mirror persistence (builder-backend jurisdiction per schema-mirror exception)
- `vitalia/frontend/src/`
- Other brands' code

### 4.3 builder-frontend scope

**Allowed paths:**
- `vitalia/frontend/src/**`
- `vitalia/frontend/tailwind.config.ts`
- `vitalia/frontend/.storybook/`
- `vitalia/frontend/e2e/`
- `vitalia/frontend/playwright.config.ts`
- `vitalia/frontend/package.json` (deps additions)

**Forbidden paths:**
- `vitalia/backend/src/`
- `core/`
- Other brands' frontend

## 5. Validator dependencies (per ticket consumption)

Each ticket in `06-tickets.yaml` declares `acceptance.validator_ids` — subset of `04-validators.yaml` categories. Builder runs ONLY those validators per iteration loop (cost optimization).

Auditor consumes ALL validators in final review (C1-C5 grid).

## 6. Cross-cutting open questions deferred to /dev-team

Per `03-arch.md § 7` table — non-blocking, resolutions provided.

## 7. Performance budget enforcement

Per `04-validators.yaml::visual::visual_perf_budget_lighthouse`. If budget exceeded → CHANGES_REQUESTED.

## 8. A11y enforcement

Per `04-validators.yaml::visual::visual_a11y_axe`. WCAG 2.1 AA minimum.

## 9. Spanish neutro enforcement

Per `04-validators.yaml::non_functional::spanish_neutro_voseo_check`. Magic comment escape `<!-- voseo-allowed -->` permitted ONLY for technical glossary references (per `.claude/rules/spanish-text.md` R25).

## 10. Capability YAML + modules/{m}.md updates (post-merge SSoT reconciliation per pm-redesign-2026-05)

Story merge to `main` triggers `/pm-vitalia` to:
1. Run `scripts/reconcile_capabilities.py vitalia` (per `04-validators.yaml::capability_yaml_freshness_post_merge`)
2. Update/create `vitalia/docs/product/capabilities/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding}/<cap>.yaml`
3. Update/create `vitalia/docs/product/modules/{inbox,pipeline,agenda,fidelizacion,marketing,onboarding}.md` (SSoT funcional viva)
4. Move 01-spec scenarios to capability YAML scenarios field
5. Archive story to `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/`
6. State transition done

## 11. Side-story dependency tracking

Per `03-arch.md § 4` — tickets `blocked_by`:
- `vitalia-payment-adapter-mvp` (Mercado Pago) — `/dev-team` waits state≥developed
- `vitalia-copilot-tools-impl` (Valeria tools) — idem
- `vitalia-fiscal-emission-pe` (Nubefact PE) — idem

`/pm-vitalia` tracks via `vitalia/docs/product/BACKLOG.md` cross-reference.

## 12. Engine modifications NOT in scope (escalate to `/pm-luana`)

Per `03-arch-be.md § 2.13-2.14` — column additions to engine tables `tenants` + `offers` require promotion proposals:
- `docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md` (NEW)
- `docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md` (NEW)

`/pm-luana` ratifies BEFORE `/dev-team` picks `T-be-migration-014` / `T-be-migration-015`.

## 13. Lift candidates Slice 2 documented (NOT in this story scope)

Per `delta-arch-notes.md` — captured for `/pm-luana` retrospective post-Slice 1 merge.
