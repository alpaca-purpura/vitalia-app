# vitalia-slice-1-inbox — Guidelines

<!-- voseo-allowed: documenting anti-pattern examples in copy guidelines -->

> **Consumer:** `/dev-team` (Sonnet build per ticket) + `/auditor` (Opus audit C1-C5).
> **Index:** `03-arch.md` § 0-9 (read first).

## § 1 — Skills & rules to load on entry

`/dev-team` and builders MUST load these on session start:

### Skills (auto-load when touching these paths)

| Path | Skill |
|---|---|
| `vitalia/backend/src/modules/vitalia/inbox/` · `vitalia/backend/src/modules/vitalia/crm/` | `backend-expert` |
| `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` | `sales-agent-expert` + `tessl__langgraph` + `tessl__graceful-degradation` |
| `vitalia/backend/src/modules/vitalia/copilot/persistence/models/*` | `copilot-expert` (schema mirror exception per `.claude/rules/backend-ddd.md`) |
| `vitalia/frontend/src/features/inbox/` · `vitalia/frontend/src/features/crm-shared/` | `frontend-expert` |
| `vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts` · `e2e/pages/inbox.page.ts` | `playwright-expert` |
| Brand voice chip 🟢 + ContactSidebar PHI fields | `brand-expert` (read-only Slice 1) |
| Anything cross-brand or engine modification proposal | `/pm-luana` (escalate via checkpoint) |

### Rules (cardinals · auto-loaded)

- `.claude/rules/tenant-isolation.md` (tenant_id mandatory + clinic_id dual-filter via vitalia overlay)
- `.claude/rules/backend-ddd.md` (Inside-Out · async-first · SA 2.0 · Pydantic v2 · schema-mirror exception)
- `.claude/rules/frontend-fsd.md` (FSD-Lite · Server-First · boundary matrix)
- `.claude/rules/backend-migrations.md` (idempotent raw SQL `IF NOT EXISTS`)
- `.claude/rules/anti-duplication.md` (§ 0 cardinal — engine shared abstractions inventory)
- `.claude/rules/architectural-fitness.md` (allowlists shrink-only · ratchet)
- `.claude/rules/tdd-mandatory.md` (RED first per layer)
- `.claude/rules/spanish-text.md` (UI chrome neutro · sales_agent voice exemption)
- `.claude/rules/master-data.md` + `.claude/rules/currency-handling.md` (UTC store · TenantLocale VO)
- `.claude/rules/auditor-downstream-regression.md` (engine_edit_detection + cross_brand_mirror_scan)
- `.claude/rules/story-closure-gate.md` (gherkin_coverage field + 07-merge 5 sections)
- `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md` + `.claude/rules/step-0-worktree.md`

### Brand overlay rules (vitalia-specific)

- `vitalia/.claude/rules/hipaa-lite.md` (PHI cardinal: dual filter + audit log + sanitize + encryption + RBAC + channel guards)
- `vitalia/.claude/rules/README.md` (overlay extends root)

## § 2 — Files in scope (boundaries)

### Allowed to TOUCH (this story)

**Backend:**
- `vitalia/backend/src/modules/vitalia/inbox/{application,api}/**` (NEW Slice 1 — service orchestrator + 8 endpoints)
- `vitalia/backend/src/modules/vitalia/crm/{domain,infrastructure,application,api}/**` (EXTEND existing scaffold — add Conversation/Message/ActivityEvent/ActionReceipt + 2 endpoints)
- `vitalia/backend/src/modules/vitalia/connections/whisper/` (NEW Slice 1 — adapter Whisper STT)
- `vitalia/backend/src/modules/vitalia/connections/{whatsapp,instagram,email}/adapter.py` (EXTEND existing — add `retract_message_id` method)
- `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` (NEW R23 Opus)
- `vitalia/backend/src/modules/vitalia/extensions.py` (EXTEND — register new tool via EP-3)
- `vitalia/backend/src/modules/vitalia/persistence/migrations/024_inbox_tables.py` (NEW migration)
- `vitalia/backend/tests/modules/vitalia/{inbox,crm,sales_agent}/**` (NEW test files)
- `vitalia/backend/tests/integration/test_inbox_*.py` (NEW)
- `vitalia/backend/tests/architecture/test_no_hardcoded_strings_inbox.test.ts` (NEW arch gate? — N/A for backend)

**Frontend:**
- `vitalia/frontend/src/app/(app)/inbox/page.tsx` (NEW RSC entry)
- `vitalia/frontend/src/features/inbox/**` (NEW full feature)
- `vitalia/frontend/src/features/crm-shared/**` (NEW — producer for Olas 2+3)
- `vitalia/frontend/src/lib/zod-schemas/{lead,conversation}.ts` + `vitalia/frontend/src/lib/zod-schemas/index.ts` (NEW shared)
- `vitalia/frontend/src/lib/copy.ts` (NEW formatCopy helper — if not already present)
- `vitalia/frontend/src/__tests__/architecture/test_no_hardcoded_strings_inbox.test.ts` (NEW arch gate)
- `vitalia/frontend/e2e/specs/smoke/inbox.smoke.spec.ts` (NEW)
- `vitalia/frontend/e2e/pages/inbox.page.ts` (NEW POM)
- `vitalia/frontend/e2e/specs/a11y/inbox.a11y.spec.ts` (NEW a11y suite)

**Docs:**
- `vitalia/docs/product/stories/vitalia-slice-1-inbox/**` (this story folder)
- `vitalia/docs/product/capabilities/inbox/*.yaml` (NEW post-merge per `/pm-vitalia`)
- `vitalia/docs/product/modules/inbox.md` (NEW post-merge per `/pm-vitalia`)
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` (UPDATE § 10 Bitácora + § 3 cross-story contracts that this story produces)

### Forbidden to TOUCH (out of scope)

- **Engine packages** `core/luana-core-*/src/luana_core_*/` — READ-ONLY consultation. Modifications require `/pm-luana` promotion proposal. Esta story consume engines existentes only.
- **Other brands** `nicolify/**` · `comunify/**` · `lupulo/**` — NEVER. Cross-brand mirror prohibido (anti-duplication.md).
- **Root legacy paths** `backend/src/**` · `frontend/src/**` · `docs/product/stories/**` — NO existen post multibrand reorg 2026-05-15.
- **Other vitalia stories surfaces** (`vitalia/frontend/src/features/{pipeline,agenda,fidelizacion,marketing}/**`) — those are Olas 2+3 territory. Consumers MUST go via `crm-shared` Public API exposed by this story.
- **Engine `core/luana-core-{sales-agent,copilot,observability,llm,compliance}/` runtime** — Adrián turn pipeline is §3 NO se toca per sales-agent-expert (Closer Studio API+WS · SmartBufferService · OutputManager chunking · enrollment_* · agent_state_checkpoints · webhook adapters · follow_up_engine · PromptVersionModel · model_pricing_snapshot · tool_call_dedup).

## § 3 — Patterns REQUIRED (must-have)

### Backend

1. **Tenant + clinic dual filter cardinal** — every PHI query has `Model.tenant_id == tenant_id AND Model.clinic_id == clinic_id`. Inheritance via `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` con `scope_field="clinic_id"`. NO exceptions including `get_by_id`. Lead repo single-filter (Lead is non-PHI per existing scaffold).
2. **SQLAlchemy 2.0 syntax** — `mapped_column()` · `select(Model).where(...)` · async-first · `AsyncSession`. NEVER `Column()` or `session.query()`.
3. **Pydantic v2 ConfigDict** — `model_config = ConfigDict(from_attributes=True)`. NO inner `class Config`. Explicit types · NO `Any`.
4. **`response_model=` mandatory** on every route (PII allowlist enforcement · arch fitness gates).
5. **`X-Tenant-ID` + `X-Clinic-ID` headers** on every PHI authenticated route. Bearer Clerk JWT required.
6. **`FastAPI(redirect_slashes=False)`** in `main.py` (Story 11 cement · don't break).
7. **Idempotency-Key header** on `POST /messages` (SendMessage). Pattern: client-generated UUID consumed via `core/luana-core-idempotency`.
8. **Optimistic Concurrency Control** via `If-Match: <updated_at>` header on `POST /mode` + `POST /messages/{id}/revert`. 409 Conflict on stale.
9. **Audit log sync write pre-response** on every PHI mutation/access (Send · Retract · SetMode · Pause · ProactiveOutbound · ToolsState read). Use `vitalia/backend/src/modules/vitalia/audit/audit_writer.py`.
10. **PII sanitization** in observability writes via `core/luana-core-observability/recording/sanitization.py::sanitize_payload(compliance_level="hipaa_lite")`. Vitalia PHI fields list in `vitalia/backend/src/modules/vitalia/compliance/phi_fields.py`.
11. **Idempotent migrations raw SQL** — `IF NOT EXISTS` pattern. NEVER `op.create_table()` or `sa.Enum(create_type=True)`.
12. **`structlog` only** — NEVER `print` or `logging` direct.
13. **Async-first** — repositories · services · route handlers all `async`. `tessl__graceful-degradation` for external calls (Whisper 30s · WA/IG 15s · retract 5s).
14. **Domain events via outbox bus** — `MessageSent`, `MessageRetracted`, `ModeChanged`, `AdrianPaused`, `ConversationStarted`, `ProactiveOutboundSent`. Consumed via `core/luana-core-events.outbox.adapter_bus.publish` (post 2026-04-29 default True).
15. **DTOs with monetary fields include `currency: str | None = None`** — vitalia_messages.llm_cost_usd not user-facing, but follow pattern.

### Frontend

1. **Server-First** — RSC default. `"use client"` ONLY on leaf nodes with state/handlers (per arch fitness `test_server_first.test.ts`).
2. **`fetchClient` auto-injects `X-Tenant-ID` + `X-Clinic-ID`** from Clerk JWT (Story 11 cement).
3. **nuqs URL state SSoT** — `useQueryStates(INBOX_URL_SCHEMA, { history: 'replace' })` for sub-state intra-route. `push` only for inter-route P1 sidebar nav.
4. **React Query keys + invalidation** — patterns per `03-arch-fe.md` § 5.
5. **PHI components mandatory** — ContactSidebar wraps all PHI fields with `<PiiMaskedSpan>` + `<RequireRole>` + `<AuditedSection>`. Arch fitness `test_phi_pii_components_used.test.ts` enforces.
6. **Microcopy SSoT via copy.ts** — cero strings hardcoded en JSX. Single-locale tree-shakable const. Spanish neutro LatAm (NO voseo · arch fitness `test_no_voseo_in_copy.test.ts`).
7. **Tokens-only via CSS vars** — only HEX literals in `vitalia/frontend/src/app/globals.css`. TSX/CSS modules use `var(--vitalia-X)` or vt-* utility classes. Arch fitness `test_no_hardcoded_colors.test.ts`.
8. **FSD-Lite boundaries** — features/inbox doesn't import features/pipeline et al. crm-shared producer + components/shared consumers only. Public API via `index.ts`.
9. **TS types mirror Pydantic v2 DTOs** — camelCase NOT REQUIRED (this codebase mantiene snake_case en TS para alignment 1:1 con BE per HANDOFF § 3 type signatures). ISO 8601 datetimes as `string`. Optional fields explicit `T | null`.
10. **Reuse adapter (fork físico)** — copy components from `nicolify/frontend/src/features/{closer-studio,crm-hub,copilot}/` with token retoken (NEW files in vitalia, NOT re-export). ADR-vitalia-001 ratified.
11. **Storybook stories** for every NEW Slice 1 component (variants per `02-design-ui.md` § 9).
12. **Accessibility WCAG 2.1 AA** — Segmented control radiogroup · ActivityStream aria-expanded · ActionReceipt aria-live polite · ContactSidebar PHI reveal aria-label · keyboard nav Tab order. Contrast ≥ 4.5:1.
13. **Optimistic updates + rollback** — SetMode, SendMessage. OCC 409 → invalidate React Query + toast.

### Agentic (R23 Opus production code)

1. **`@tool` decorator + Pydantic input schema** on every tool. Async. Service-resolved (no raw DB access from tool).
2. **`tenant_id` + `clinic_id` mandatory** in tool input schema (HIPAA-lite dual filter).
3. **NEVER mirror engine observability** (anti-duplication.md § 0 cardinal). Consume `SalesAgentObservabilityContext` shipped.
4. **`tessl__graceful-degradation`** for external calls in tools. Timeout + fallback.
5. **PII sanitization** via engine `sanitize_payload(compliance_level="hipaa_lite")` before logging.
6. **Voice voseo exemption** — sales_agent output respects tenant voice config (`personality_profiles.system_instruction`). `.claude/rules/spanish-text.md` does NOT apply to Adrián output. Applies to UI chrome only.
7. **Eval goldens** when adding new tool — minimum 1 reinforcement golden (happy + 1 edge) if scenario significant.

## § 4 — Patterns FORBIDDEN (must-not-have)

### Backend
- ❌ `Column()` SA legacy syntax — use `mapped_column()`
- ❌ `session.query()` — use `select(Model).where(...)`
- ❌ Sync routes/services touching DB — async-first only
- ❌ `print()` / `logging` direct — use `structlog`
- ❌ Inner `class Config` Pydantic — use `model_config = ConfigDict(...)`
- ❌ `response_model` missing on route — arch fitness blocks
- ❌ `op.create_table()` migration — raw SQL `CREATE TABLE IF NOT EXISTS`
- ❌ `sa.Enum(..., create_type=True)` — raw SQL enum reuse
- ❌ Hardcoded `'USD'` currency — `currency: str | None = None` + resolve from `TenantLocale`
- ❌ `datetime.utcnow()` — use `utc_now()` helper · `DateTime(timezone=True)` columns
- ❌ Cross-brand import `from nicolify.*` / `from comunify.*` / `from lupulo.*` — NEVER. Compartir via `core/luana-core-*` engine.
- ❌ Mirror engine observability/cost/pricing/turn_envelope/callback_handler in `vitalia/.../observability/` — EXTEND via heredancia (anti-duplication.md § 0)
- ❌ Skip dual filter "porque single-tenant clinic" — siempre tenant_id + clinic_id
- ❌ PHI in URL query params (e.g., `GET /patients?dni=12345`) — POST body always
- ❌ PHI in plaintext email body — link to portal only
- ❌ `logging.info(f"Patient {patient.name}...")` — use sanitize_payload before logging
- ❌ Audit log async fire-and-forget — sync write pre-response mandatory
- ❌ Direct provider adapter calls bypassing connections module — must go through `connections.{channel}.adapter`
- ❌ Hardcoded model wire-name strings (e.g., `model="kimi-k2.6"`) in business code — use engine LLM router

### Frontend
- ❌ HEX literals in TSX/CSS modules — only `globals.css` · arch fitness blocks
- ❌ `hsl(198 99% 49%)` in TSX — use `var(--vitalia-cian)` or vt-bg-cian utility
- ❌ Cross-feature import `from "@/features/pipeline/..."` from inbox — Public API only via index.ts
- ❌ Deep imports `from "@/features/inbox/components/ConversationList"` from outside the feature — index.ts re-exports
- ❌ Hardcoded strings in JSX > 3 chars — `INBOX_COPY.xxx` always
- ❌ Voseo in copy.ts (`vos/tenés/podés/querés`) — tuteo neutro only
- ❌ `"use client"` on non-leaf components — split client/server boundary
- ❌ `useEffect` for data fetching — React Query hooks
- ❌ `useState` for URL state — nuqs only
- ❌ PHI fields in `localStorage` / `sessionStorage` — IDs only, fetch on-demand server-side
- ❌ ContactSidebar without PHI wrappers — `<PiiMaskedSpan>` mandatory
- ❌ Direct fetch (`await fetch(...)`) — use `fetchClient` (auto-injects headers)
- ❌ `any` type — `unknown` + type guards
- ❌ Default exports (except Next pages) — named exports for tree-shake
- ❌ Import from nicolify runtime — copy adapter pattern only (fork físico)
- ❌ Re-export Nicolify components — copy + retoken in vitalia

### Agentic
- ❌ Mirror engine `turn_envelope.py` / `callback_handler.py` / `cost_recorder.py` per-brand — REVERT obligatorio (anti-duplication.md § 0)
- ❌ Tool without `tenant_id` + `clinic_id` in input schema — HIPAA-lite breach
- ❌ Tool calling raw DB / repository directly — go through service layer
- ❌ External call without timeout + fallback (tessl__graceful-degradation)
- ❌ PII in tool error messages / log statements — sanitize_payload first
- ❌ Modify engine `core/luana-core-sales-agent/` runtime without `/pm-luana` promotion proposal
- ❌ Subagent without `tools=[]` explicit — sandbox via deepagents (engine cement)
- ❌ Hardcoded provider strings in specialist code — use `LLM_ROLE_BY_SITE` SSoT (engine)

### Cross-cutting
- ❌ `git add .` / `git add -A` — stage by exact filename
- ❌ `git pull` / `git push --force` — banned per parallel-safety
- ❌ `git commit --no-verify` — pre-commit hook mandatory
- ❌ Default flag flips without anti-default-flip-audit.md 4-step workflow — esta story has ZERO flag flips
- ❌ Capability YAML manual editing of auto-gen sections — modify source · `make portfolio` regenerates

## § 5 — Reuso explícito (mapping referenced parent + paths)

### Engine packages (CONSUME direct via Python imports)

| Engine package | Path | Usage in this story |
|---|---|---|
| `luana_core_platform.repositories.compound_scope_repository.CompoundScopeRepositoryBase` | `core/luana-core-platform/src/luana_core_platform/repositories/compound_scope_repository.py` | Inbox PHI repos heredan con `scope_field="clinic_id"` |
| `luana_core_platform.workers.cron_envelope.cron_envelope` | `core/luana-core-platform/src/luana_core_platform/workers/cron_envelope.py` | Opcional Slice 1: cron `cleanup_expired_action_receipts_5min_sweep` |
| `luana_core_crm.domain.{lead,customer}` | `core/luana-core-crm/src/luana_core_crm/domain/` | Consult-only — vitalia mantiene Lead local. Lift Slice 2. |
| `luana_core_channels.format_for_channel` + `luana_core_channels.intent_detector` | `core/luana-core-channels/src/luana_core_channels/` | Outbound message format dispatch · intent detection (WA quick replies, IG buttons) |
| `luana_core_observability.recording.sanitization.sanitize_payload` | `core/luana-core-observability/src/luana_core_observability/recording/sanitization.py` | PII sanitize en traces + audit log payload_redacted |
| `luana_core_observability.recording.turn_envelope.BaseObservabilityContext` | idem | Adrián turn envelope (engine shipped — consume via SalesAgentObservabilityContext) |
| `luana_core_compliance.ComplianceService` | `core/luana-core-compliance/` | Channel guards + marketing opt-in + medical guardrails |
| `luana_core_idempotency` | `core/luana-core-idempotency/` | `Idempotency-Key` header pattern en SendMessage |
| `luana_core_events.outbox.adapter_bus.publish` | `core/luana-core-events/src/luana_core_events/outbox/` | Domain events emission |
| `luana_core_sales_agent` runtime | `core/luana-core-sales-agent/` | Adrián turn pipeline (CONSUME · NO modify) |
| `luana_core_copilot` runtime | `core/luana-core-copilot/` | copilot_trace_event source for ActivityStream (CONSUME) |
| `luana_core_brand_studio.personality_service` (read-only) | `core/luana-core-brand-studio/` | Voice style chip lectura · personality_profiles.system_instruction |
| `luana_core_extension_sdk.ExtensionPointRegistry` | `core/luana-core-extension-sdk/` | Register `retract_last_message` tool via EP-3 |

### Nicolify FE reuso (REUSE adapter — fork físico Slice 1)

| Source | Destination | Token adapter |
|---|---|---|
| `nicolify/frontend/src/features/closer-studio/components/CloserLayout.tsx` | `vitalia/frontend/src/features/inbox/components/InboxLayout.tsx` | bg-amber-50 → vt-bg-azul-marino-8 · violet-* → vt-purpura-* |
| `nicolify/frontend/src/features/closer-studio/components/inbox/ConversationList.tsx` | `vitalia/frontend/src/features/inbox/components/ConversationList.tsx` | Temperature chips borrados · NEW chips 🔴 + 📎 + Stage decisión |
| `nicolify/frontend/src/features/closer-studio/components/inbox/ConversationItem.tsx` | idem | + badges + Stage chip |
| `nicolify/frontend/src/features/closer-studio/components/inbox/ConversationThread.tsx` | idem | header "AI Activo / Tienes el control" → SegmentedControl3Modes |
| `nicolify/frontend/src/features/closer-studio/components/inbox/MessageBubble.tsx` | idem | + audio + image stub + ActionReceiptUndoChip inline · Adrián avatar gradient_adrian |
| `nicolify/frontend/src/features/closer-studio/components/inbox/MessageInput.tsx` | idem | placeholder dinámico · attach/voice buttons |
| `nicolify/frontend/src/features/closer-studio/components/inbox/ContactSidebar.tsx` | idem | + `<PiiMaskedSpan>`/`<RequireRole>`/`<AuditedSection>` wrappers |
| `nicolify/frontend/src/features/copilot/components/composer/VoiceOverlay.tsx` | `vitalia/frontend/src/features/inbox/components/ComposerVoiceButton.tsx` | retoken · public API exposed |
| `nicolify/frontend/src/features/crm-hub/components/LifecycleStageChip.tsx` | reference only para FilterChips Stage decisión styling | retoken |
| `nicolify/frontend/src/features/crm-hub/components/ContactDetailContent.tsx` | reference only para ContactSidebar sections layout | retoken + PHI wrappers |

### vitalia/frontend/src/components/shared/ (Story 11 cement — REUSE direct)

- `phi/{PiiMaskedSpan,RequireRole,AuditedSection}` — PHI compliance wrappers
- `agents/{AgentAvatar,AgentAttribution}` + `agentNameByRole` — gradients per agent
- `activity-stream/ActivityStreamSticky` (base — extend per inbox needs)
- `contact-sidebar/ContactSidebar` (base — extend in inbox feature)
- `shell/{AppShell,Sidebar,TopBar}` (route shell)

## § 6 — Commit + push workflow

Per `.claude/rules/git-safety.md` triple-branch policy:

- Branch: `wip/vitalia` (canónico vitalia · NO rota por story per M12 cement 2026-05-18)
- Commits: Conventional Commits `<type>(scope): <desc>` — type ∈ {feat, fix, refactor, docs, test, chore, perf, ci, wip}
- Stage exact files: `git add path/to/file` (NEVER `git add .`)
- Pre-commit hook runs ruff on staged `.py` files (native, backend venv)
- Push frequency: NEVER >30min without push if significant changes (M11)
- Multi-file commit → delegate Haiku per `.claude/rules/git-haiku-delegation.md`
- Squash-merge to `main` at story `done` per `story-closure-gate.md` Fase F

Commit message template:
```
feat(vitalia/inbox): T-inbox-be-1 — Conversation + Message + ActivityEvent + ActionReceipt domain + repos

- 4 new domain entities (PHI dual-filter · tenant_id+clinic_id)
- Repositories heredan luana_core_platform.CompoundScopeRepositoryBase scope_field="clinic_id"
- Migration 024_inbox_tables (idempotent raw SQL · IF NOT EXISTS)
- Domain events ConversationStarted/MessageSent/MessageRetracted/ModeChanged/AdrianPaused/ProactiveOutboundSent

Tests RED first per layer (domain → infra → app).
gherkin_coverage: SC-01 SC-02 SC-03 SC-04

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## § 7 — Auditor checklist (Phase B / C1-C5 + Phase D Gherkin)

Per `.claude/skills/auditor/SKILL.md`:

- **C1 Code** — DDD layers correct · async-first · SQLAlchemy 2.0 syntax · Pydantic v2 ConfigDict · `response_model=` mandatory · structlog only · no cross-brand imports · no engine modifications (consulted READ-ONLY only)
- **C2 Spec** — Gherkin scenarios SC-01..04 mapped 1:1 to tests (Phase D · `06-audit/gherkin-matrix.md`)
- **C3 Architecture** — fitness gates green · allowlists shrunk · `CompoundScopeRepositoryBase` consumed via heredancia · `anti-duplication.md § 0` no mirrors
- **C4 Cross-cutting** — PHI dual filter applied · audit log sync write · `sanitize_payload(compliance_level="hipaa_lite")` · `currency: str | None` on monetary DTOs · UTC + TenantLocale · Spanish neutro UI · sales_agent voice exemption preserved · idempotency key + OCC patterns · downstream regression scope per `.claude/rules/auditor-downstream-regression.md` § E (brand extension + engine consume)
- **C5 Trace** — every ticket result references gherkin scenarios + validators run + production_code true/false correct (R23: agentic production_code → Opus required · non-production-code tickets → Sonnet OK)

Auditor self-fix policy: per `.claude/rules/auditor-self-fix-policy.md`. Whitelist self-fix (1-2 files · ≤10 lines) for lint/format/typo/missing response_model. NEVER self-fix structural (branch logic · refactor · tests).

## § 8 — Cross-story coordination (HANDOFF updates required)

When this story produces contracts that Olas 2+3 consume, MUST update `HANDOFF-cross-story-updates.md` (this story folder) AND `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md`.

Producer contracts this story emits (per HANDOFF § 3-6):
- TS types: `Lead`, `Conversation` in `vitalia/frontend/src/features/crm-shared/types.ts`
- Zod schemas: `leadSchema`, `conversationSchema` in `vitalia/frontend/src/lib/zod-schemas/`
- API endpoints: `GET /api/v1/vitalia/crm/leads`, `GET /api/v1/vitalia/crm/leads/{id}`, `GET /api/v1/vitalia/crm/conversations`, `GET /api/v1/vitalia/crm/conversations/{id}`
- Domain events emitted: `ConversationStarted`, `MessageSent`, `MessageRetracted`, `ModeChanged`, `AdrianPaused`, `ProactiveOutboundSent`
- BE module exports: `vitalia/backend/src/modules/vitalia/crm/` (extended) + `vitalia/backend/src/modules/vitalia/inbox/`

Detalle en `HANDOFF-cross-story-updates.md` this story.

## § 9 — Open questions deferred to /dev-team

| # | Question | Default decision |
|---|---|---|
| 1 | ActivityEvent projection (`vitalia_activity_events` table) vs direct query `copilot_trace_event`? | **Projection Slice 1** (read isolation + UI-tuned shape). Reconsider if drift detected post-Slice 1. |
| 2 | Whisper STT location (brand-local vs engine lift)? | **Brand-local Slice 1** (`vitalia/.../connections/whisper/adapter.py`). Lift candidate Slice 2. |
| 3 | ProactiveOutboundModal templates storage (hardcoded vs DB-backed)? | **Hardcoded 5 templates Slice 1** (`vitalia/.../inbox/application/services/_templates.py`). Templates registry → Slice 2 lift `core/luana-core-channels/templates/`. |
| 4 | Concurrent edit conflict (SC-03) — OCC strategy? | **`If-Match: <updated_at>` header + 409 Conflict** on stale. Client re-fetches via React Query invalidate + toast notification. |
| 5 | ContactSidebar PHI reveal default — masked vs revealed for `doctor` role? | **Masked by default for all roles**. Reveal triggers audit log row. (Stricter than HIPAA — explicit consent per access.) |
| 6 | retract_last_message tool — Slice 1 ship vs defer? | **SHIP Slice 1** as R23 Opus production_code=true ticket. 1 reinforcement golden opcional (`T-inbox-agentic-1`). Defer if scope tight. |

## § 10 — References

- `01-spec-extract.md` · `02-design-ui.md` · `02-design-ui-mockup.html` (SSoT visual)
- `03-arch.md` (index) · `03-arch-be.md` · `03-arch-fe.md` · `03-arch-agentic.md`
- `04-validators.yaml` (must_pass:true · 4 categorías)
- `06-tickets.yaml` (DAG atómicos)
- `HANDOFF-cross-story-updates.md` (contratos producidos Ola 1 inbox · consumed Olas 2+3)
- `vitalia/docs/product/outcomes/vitalia-mvp-ui-foundation-handoff-cross-story.md` (SSoT cross-story Slice 1)
- `vitalia/.claude/rules/{hipaa-lite,README}.md`
- `vitalia/config/brand.yaml`
- `.claude/rules/*.md` (cardinales root)
- `vitalia/docs/architecture/design-system.md`
- Parent archived: `vitalia/docs/archive/2026/stories/vitalia-ux-discovery/{01-spec.md, 03-arch*.md, 06-tickets.yaml}`
