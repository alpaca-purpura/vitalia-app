# Vitalia — Audit doc-vs-código + replan Slice 1 (2026-05-20)

> Producido por `/pm-vitalia` post-bootstrap step 0 GREEN, en respuesta al pedido Chris 2026-05-20:
> "audita cada story del backlog vs código real, re-evalúa ux-discovery con mockups + design-system,
> verifica core para reuso, revisa learnings, valida Clerk + Playwright, deja todo construible."
>
> **Verdict global:** ✅ Foundation sólida shipped (auth + infra + onboarding + copilot tools + agentes).
> Slice 1 UI (5 rutas operativas) no construido. Hay base de reuso fuerte en `core/luana-core-*` +
> `nicolify/frontend` (15 features espejo del legacy `ap_sales_agent` excepto growth-studio).
> Pre-flight Clerk/Playwright tiene gaps específicos identificados (Q2 Chris ratificó bloquear hasta verde).

---

## § 1 — Auditoría doc-vs-código (cada story)

### ✅ Stories shipped (done) — verificadas en código + tests + capabilities

| Story | Estado real | Capability YAMLs | Notas |
|---|---|---|---|
| `luana-vitalia-bootstrap` (Story 11) | ✅ shipped | 16 caps en 13 módulos | BE completo + FE dashboard + 3 fixtures LATAM + widget UMD + 3 KB médicos. Test coverage: 86 BE + 22 FE + 24 E2E + 1 widget |
| `vitalia-dev-stack-functional` | ✅ shipped | n/a (receta operativa) | 12-step bootstrap recipe en archive 07-merge.md |
| `vitalia-adopt-luana-core-iam` | ✅ shipped | iam-scaffold-slice-1 | IAM engine package consumido + tabla `tenants` + 022 migration |
| `vitalia-auth-base-functional` | ✅ shipped (commit `9e7351f`) | auth/clerk-middleware + sign-in-sign-up-pages | LIVE en dev-app.vitalialat.com. Auditor APPROVED tier PENDING_DEPLOY |
| `vitalia-slice-1-infra-cross-cutting` | ✅ shipped (squash `50143d57`+`cc4fcd68`) | 8 caps live (compliance/hipaa-lite-defensive-stack + iam + crm + observability + workers + connections/registries + platform/design-tokens + platform/migrations) | 23 alembic migrations + 5 Extension SDK registries + HIPAA-lite dual filter + audit log + pgcrypto + OTel + Sentry + ARQ cron + AppShell + Storybook |
| `vitalia-copilot-tools-impl` | ✅ shipped (commits `3331151..427b0f3`) | 7 caps NEW + 3 modules MD refreshed | Valeria wizard + Adrián 3 tools + Lucas 3 daily tools + medical guardrails + 16 goldens. 1363/1363 tests GREEN |
| `vitalia-slice-1-onboarding-wizard` | ✅ shipped (commit `4191371`+`38ab9bd`) | onboarding/clinic-onboarding-3step + wizard_brand_studio_slice_1 | Playwright E2E PASS_5_OF_5 |

### 🟢 Stories ready/refined con SSoT completo (no shipped, listos build)

| Story | State | Surface code existente | Surface code faltante |
|---|---|---|---|
| `vitalia-ux-discovery` | **ready** (parent) | 6 mockups HTML + design-system.md + 03-arch (consolidated + 3 sub) + 04-validators (29 validators × 4 categorías) + 05-guidelines + 06-tickets (56 tickets, 17 done por sub-stories ya shipped) | n/a — es parent SSoT |
| `vitalia-slice-1-inbox` | **refined** | inherit ticket subset T-inbox-1..T-inbox-9 (9 tickets). Components dir `shared/contact-sidebar` 2 tsx stubs + `shared/activity-stream` 2 tsx | Route `/inbox` (FE), BE module `inbox`, conexión `crm-hub` Nicolify reuse |
| `vitalia-slice-1-pipeline` | **refined** | inherit T-pipeline-1..T-pipeline-7 (7). Component `shared/deposits` 2 tsx | Route `/pipeline`, BE module `pipeline`, conexión `closer-studio` Nicolify reuse, depende side payment-adapter-mvp |
| `vitalia-slice-1-agenda` | **refined** | inherit T-agenda-1..T-agenda-9 (9). Migrations 002 appointments + 003 payment_events + 004 fiscal_receipts ya aplicadas | Route `/agenda`, BE module `agenda`, depende side payment-adapter-mvp + fiscal-emission-pe |
| `vitalia-slice-1-fidelizacion` | **refined** | inherit T-fidelizacion-1..T-fidelizacion-7 (7). Components `shared/nps` 1 tsx + `shared/agents` 4 tsx (Lucas avatar/cards) | Route `/fidelizacion`, BE module `fidelizacion` (re-engagement workflows usando idempotent_cron ya en `_shared/workers/`) |
| `vitalia-slice-1-marketing` | **refined** | inherit T-marketing-1..T-marketing-8 (8). Components `shared/marketing` 2 tsx + `shared/lucas-recommendations` 2 tsx + `shared/channels` 2 tsx + `shared/attribution` 2 tsx + Lucas tools (compute_attribution_matrix + compute_referrals_leaderboard) | Route `/marketing`, BE module `marketing`. **Growth-studio Nicolify NO reusa** (arch diferente per Chris) |

### 🟡 Side stories refining (bloquean Slice 1 agenda + pipeline)

| Story | State | Bloqueo | Próximo paso |
|---|---|---|---|
| `vitalia-payment-adapter-mvp` | **refining** (AWAITING_PO_DRAFT) | bloquea agenda + pipeline (depósito 30% + cobranza saldo) | Chris ratifica 4 open questions → `/po` produce 01-spec.md |
| `vitalia-fiscal-emission-pe` | **refining** (AWAITING_PO_DRAFT) | bloquea agenda (Capa 2 fiscal Nubefact PE) | Chris ratifica 4 open questions → `/po` produce 01-spec.md |
| `vitalia-pricing-decision` | **idea** | NO bloquea Slice 1 | Chris postergó decisión, sigue postergada hasta MVP UI estable |

### Total shipped vs faltante

- **17 tickets shipped** del 06-tickets.yaml parent (T-arch-1 + T-infra-1..9 + T-onboarding-1..7)
- **40 tickets faltantes** distribuidos: T-inbox(9) + T-pipeline(7) + T-agenda(9) + T-fidelizacion(7) + T-marketing(8)
- **3 T-agentic-* tickets** absorbidos por sibling `vitalia-copilot-tools-impl` (shipped)
- **39 capabilities live** en 24 módulos vitalia

---

## § 2 — Core Luana reusable (verify-first per Chris)

### Patterns que Chris asumió "para promover" — verificación cruzada

| Pattern vitalia | Existe en core ya? | Verdict | Acción |
|---|---|---|---|
| `@idempotent_cron` decorator (`vitalia/_shared/workers/base.py`) | **PARCIAL** — `@idempotent` ya existe en `core/luana-core-idempotency/`. El decorator vitalia es CONVENIENCE WRAPPER que añade: cron_span (OTel) + audit log + Sentry capture sobre el `@idempotent` ya en core | Reframe lift candidate como "cron envelope wrapper" (no idempotency check) | Proposal `/pm-luana`: lift `cron_envelope` → `core/luana-core-platform/workers/cron_envelope.py` consumiendo `core/luana-core-idempotency` |
| `PhiRepositoryBase` (`vitalia/_shared/repositories/phi_repository.py`) | **NO existe** en core. Grep cross-`core/` returns vacío | Genuine lift candidate | Proposal `/pm-luana`: lift `PhiRepositoryBase → CompoundScopeRepositoryBase` → `core/luana-core-platform/repositories/` (sustrae axis names: tenant_id + scope_id en lugar de tenant_id + clinic_id, abre puerta a brands futuros como fitflow `tenant+studio_id` o retailly `tenant+store_id`) |
| Dual filter tenant+clinic | NO existe genérico en core | Subsumido en CompoundScopeRepositoryBase ↑ | Mismo proposal |

### Core packages YA consumidos por vitalia (no requiere acción)

```
luana-core-extension-sdk      → 18 EPs registry, register_all en vitalia/extensions.py
luana-core-platform           → TenantLocationContract (proposal aceptada 2026-05-17)
luana-core-iam                → tenants engine (022_vitalia_add_engine_iam_tables)
luana-core-idempotency        → @idempotent decorator (consumido por @idempotent_cron vitalia)
luana-core-observability      → callback handler base + cost recorder + trace event repo
luana-core-copilot            → workflows + extractors base
luana-core-sales-agent        → LangGraph orchestrator + persona compiler
luana-core-channels           → format_for_channel + intent_detector + payment adapters
luana-core-compliance         → ComplianceService channel guard
luana-core-events             → outbox pattern + domain events
luana-core-extraction         → BaseExtractionOrchestrator
luana-core-brand-studio       → schema + extraction prompts (consumed vía EP-2)
luana-core-offer-studio       → 7 catalogs DAG + MaintenanceScheduleEnum (proposal 2026-05-17)
luana-core-landing            → landing templates
luana-core-billing            → BudgetGuard + RateLimiter
```

### Core packages potenciales para Slice 1 (BE + FE)

| Slice 1 ruta | Core BE consumibles | FE reuse pattern (nicolify) |
|---|---|---|
| `/inbox` | `luana-core-crm` (Lead + Customer + Conversation domain) · `luana-core-channels` (intent_detector + format_for_channel) · `luana-core-observability` (trace_event) | `nicolify/frontend/src/features/crm-hub/` + `nicolify/frontend/src/features/copilot/` rail (65+ components) |
| `/pipeline` | `luana-core-crm` (Sale + Lead stages) · `luana-core-billing` (rate limiter) · `luana-core-events` (StageAdvanced event) | `nicolify/frontend/src/features/closer-studio/` (board kanban + detail panel) + copilot rail |
| `/agenda` | `luana-core-scheduling` (Appointment + AvailabilitySchema + EventTypeSchema) · `luana-core-channels.payment.*` (mercadopago_adapter + stripe_connect_adapter + tokenized_recurring) · `luana-core-idempotency` (webhook dedup) | Construir nuevo combinando patterns crm-hub (list+detail) + payment Nicolify campaigns-lite |
| `/fidelización` | `luana-core-campaigns` (workers: scheduler_tick + execution_task + segment_refresh + audit_retention) · `luana-core-events` (NPSCollected event) | `nicolify/frontend/src/features/campaigns-lite/` + `nicolify/frontend/src/features/notifications/` |
| `/marketing` | `luana-core-campaigns` workers · vitalia Lucas tools (compute_attribution_matrix + compute_referrals_leaderboard + compute_stage_recommendation) | **NO usar growth-studio Nicolify** (arch diferente per Chris). Construir simple: cards Lucas recommendations + dashboard Lucas analysis + channel_metrics consumption |

---

## § 3 — Learnings impact sobre Slice 1

### Learnings vitalia activos

| Learning | Promotable | Impacto Slice 1 |
|---|---|---|
| `2026-05-16-capabilities-inventory-gap.md` | **yes** | Process learning — `/pm-vitalia` ya enforza R32 capability inventory al merge. Aplicar igual a las 5 stories Slice 1 |
| `2026-05-17-tooling-auto-regen-backlog.md` | **candidate** | Tooling — al cerrar cada story Slice 1, regen BACKLOG.md auto |
| `2026-05-18-phi-repository-base.md` | **candidate** | inbox + pipeline + fidelización LEEN PHI → usar `PhiRepositoryBase` (post lift = `CompoundScopeRepositoryBase` desde core) |
| `2026-05-18-idempotent-cron-pattern.md` | **candidate** | agenda recordatorios + fidelización re-engagement + marketing ETL → usar `@idempotent_cron` (post lift = `cron_envelope` desde core) |

### Re-encuadre stories post-learnings

- **inbox + pipeline + fidelización + agenda + marketing** todas tocan tabla PHI (consultas dual-filter tenant+clinic). Refresh /architect debe REQUERIR consumo `PhiRepositoryBase` (o engine equivalente post lift).
- **agenda + fidelización + marketing** tienen cron jobs. Refresh /architect debe REQUERIR consumo `@idempotent_cron` envelope.

---

## § 4 — Clerk + Playwright pre-flight gate

### Estado actual

| Item | Estado |
|---|---|
| Clerk publishable + secret keys | ✅ presentes en `vitalia/.env.dev` (`moral-gator-27.clerk.accounts.dev` test instance) |
| Clerk testing token | ✅ `CLERK_TESTING_TOKEN_VITALIA` configurado |
| Clerk Organizations feature | ❌ DISABLED en dashboard (vitalia es B2B multi-tenant, NEEDS enabled) |
| Test users existentes | ❌ vacío (Clerk API users list = `[]`) |
| Playwright storage state | ❌ NO existe `vitalia/frontend/playwright/.clerk/user.json` |
| Stack vitalia corriendo | ✅ BE 8002 OK · FE 3002 OK · postgres 5435 OK · alembic head=023 · 30+ tablas vitalia_* |
| 4 bugs handoff auth-base-functional | 3 fixed/mitigated · Bug #4 (phantom `vitalia_clinics`) RESUELTO (migration 023 crea `vitalia_clinic_branches` real) · Bug #5 (Redis) no crítico |
| Playwright suite smoke | 23 specs (auth + admin + dashboard + visual + mobile + a11y + vitalia/*) — 12 quedaron PENDING_DEPLOY tras auth-base-functional shipping |

### Pre-flight checklist (Q2 Chris ratificó Opción A — bloquear hasta verde)

```
1. Habilitar Organizations en Clerk dashboard `moral-gator-27.clerk.accounts.dev`
2. Crear 3 test users via Clerk API:
   - dr.demo@vitalia.test         (rol: owner+doctor)
   - recepcion@vitalia.test       (rol: recepcion)
   - admin@vitalia.test           (rol: super_admin)
3. Crear 1 test organization "Clínica Demo Vitalia" + assignar 3 users
4. Bootstrap Playwright storage state:
   cd vitalia/frontend && npx playwright test --grep "@auth-setup" (genera /clerk/user.json)
5. Correr suite smoke completa: 23 specs en green local + LIVE (dev-app.vitalialat.com)
6. Sólo entonces empezar build Slice 1
```

---

## § 5 — Plan propuesto Slice 1 — olas 2+2+1 (Q1 Chris)

### Pre-flight (Fase 0)

- ✅ Clerk dashboard Organizations enabled + 3 test users + test org
- ✅ Playwright storage state generado + suite smoke 23 specs GREEN
- ✅ 2 promotion proposals refrescados con verify-first:
  - `cron-envelope` → `core/luana-core-platform/workers/` (wrap `@idempotent` already in core)
  - `compound-scope-repository-base` → `core/luana-core-platform/repositories/`
  - Ambos accepted + migrated antes Slice 1

### Stories restructure

- `vitalia-ux-discovery` state ready → **done** (parent SSoT cumplido: mockups + design-system + 03-arch consolidated quedan como referencia visual inmutable)
- Cada uno de los 5 sub-stories refined recibe `/architect` refresh ligero produciendo SU PROPIO ready package (no inherit del parent):
  - `01-spec-extract.md` — recorte mega 01-spec.md acotado a la ruta
  - `02-design-ui.md` — link al mockup HTML como SSoT visual + component breakdown
  - `03-arch-extract.md` — BE+FE+agentic sub-arch propio
  - `04-validators.yaml` — Playwright spec + tests específicos ruta (must_pass:true)
  - `05-guidelines.md` — reuso explícito (`luana-core-*` packages + `nicolify/frontend/src/features/{crm-hub|closer-studio|campaigns-lite|copilot|notifications}/` patterns)
  - `06-tickets.yaml` — tickets atómicos propios (no inherit del parent)
  - ★ `HANDOFF-cross-story.md` — comunicación inter-story (tipos TS compartidos, schemas Zod, API endpoints comunes, side-effects esperados de otras stories en paralelo)

### Olas build (paralelas end-to-end developing → developed → reviewing → done)

**Ola 1 (paralela, dependencies más livianas):**
- `/inbox` — reuso fuerte `crm-hub` + `copilot` rail · BE consume `luana-core-crm` + `luana-core-channels` + `PhiRepositoryBase` core
- `/fidelización` — reuso `campaigns-lite` + `notifications` · BE consume `luana-core-campaigns` workers + `cron_envelope` core + `PhiRepositoryBase` core

**Ola 2 (paralela, deps shipping):**
- `/pipeline` — reuso `closer-studio` board · BE consume `luana-core-crm.Sale` + side payment-adapter-mvp ya shipped · `PhiRepositoryBase` core
- `/marketing` — sin growth-studio reuse · construye nuevo simple Lucas recommendations + channel_metrics dashboard · BE consume Lucas tools ya shipped + `luana-core-campaigns` workers · `cron_envelope` core

**Ola 3 (sola, más compleja):**
- `/agenda` — combina patterns crm-hub list+detail + payment Nicolify · BE consume `luana-core-scheduling` + `luana-core-channels.payment.*` + `cron_envelope` core para recordatorios · depende side payment-adapter-mvp + fiscal-emission-pe ya shipped

### Side stories paralelas (necesarias para Olas 2 + 3)

- `vitalia-payment-adapter-mvp` refining → refined → ready → developing → done
- `vitalia-fiscal-emission-pe` refining → refined → ready → developing → done

Trigger: Chris ratifica las 4 open questions de cada → `/po` produce 01-spec.md → `/architect` ready → `/dev-team` build → `/auditor` review → `/pm-vitalia` merge.

### Auto-handoff (paradigm v4.1)

Cada story de cada ola:
- `/dev-team` cierra `developed` → auto-handoff `/auditor`
- `/auditor` APPROVED → auto-handoff `/pm-vitalia` merge
- `/pm-vitalia` merge → state=done + archive + capability inventory update

### Estimación wall clock

| Ola | Stories | Estimated dev weeks |
|---|---|---|
| Pre-flight (Fase 0) | Clerk + Playwright + promotions | 0.5-1 sem |
| Ola 1 | inbox + fidelización (paralelas) | 2-3 sem |
| Ola 2 | pipeline + marketing (paralelas) + 2 side stories paralelas | 3-4 sem |
| Ola 3 | agenda | 2-3 sem |
| **Total Slice 1** | 5 rutas + 2 side stories | **7-11 sem** |

---

## § 6 — Validators externos cross-story

Cada ola termina con verificación Playwright LIVE contra `dev-app.vitalialat.com`:

1. Cada ruta nueva renderiza con los 3 test users (dr.demo + recepcion + admin) → roles correctos visible/hidden per RBAC
2. Datos PHI nunca leak en response (cross-tenant test) → SC-11 cumplido
3. Audit log row creado post cada acción sensible → SC-13 cumplido
4. Mobile viewport renderable + tappable → SC-15 cumplido
5. A11y axe critical+serious cero → SC-14 cumplido
6. Cobertura visual baseline regenerada → SC-16 cumplido

---

## § 7 — Decisiones pendientes Chris

Estas 3 son decisiones que pueden esperar a momento de cada ola, pero conviene anotarlas ahora:

1. **¿Promovemos 2 proposals como UN solo proposal "core-platform-extensions-slice-1"** que incluya `cron_envelope` + `CompoundScopeRepositoryBase`, o **dos proposals separados**?
2. **¿Side stories payment-adapter-mvp + fiscal-emission-pe arrancan refining ANTES o EN PARALELO con Ola 1?** (Ola 1 no depende de ellas, pero Ola 2-3 sí)
3. **¿Mockup wizard-brand-studio.html aplica para Slice 1 onboarding-wizard ya shipped?** Si Chris ratifica que el mockup es la referencia visual a respetar en build (no re-redesign), confirmar que el wizard shipped no necesita refresh.

---

## § 8 — Próximo paso natural (`/pm-vitalia` espera Chris)

Antes de mover ningún state, necesito Chris ratifique:

- (A) Plan en olas 2+2+1 con archivos `HANDOFF-cross-story.md` para coordinar paralelas
- (B) Pre-flight gate Clerk+Playwright como hard gate antes empezar
- (C) Verify-first sobre `@idempotent` ya en core (cron_envelope re-encuadre) + `PhiRepositoryBase` genuine lift
- (D) Las 3 decisiones pendientes § 7

Si Chris ratifica → `/pm-vitalia` ejecuta Fase 0 (pre-flight gates):
1. Habilitar Organizations Clerk dashboard (manual Chris) + crear 3 test users (via API)
2. Bootstrap Playwright storage state + verify suite smoke verde
3. `/pm-luana` proposal cron_envelope + CompoundScopeRepositoryBase
4. Cuando ratified+migrated → `/architect` refresh Ola 1 stories (inbox + fidelización en paralelo)
5. `/dev-team` build paralelo Ola 1
6. Iterar olas 2 + 3 según secuencia
