# CLAUDE.md

**luana-platform** — Multi-brand multitenant SaaS platform. Modular Monolith DDD + uv/pnpm workspace + Docker-First runtime. **10 brand apps** consumen un engine compartido `core/` (Luana).

@AGENTS.md cubre stack/commands/architecture/git/quality/native-first/skills/constraints. Esto = overlay project-specific.

## Topology

```
luana-platform/                                  ← monorepo (pnpm + uv workspace)
├── core/                                        ← Luana engine SSoT (26 packages)
│   ├── luana-core-{iam,platform,observability,
│   │   events,extension-sdk,extraction,llm,
│   │   idempotency,channels,compliance,billing,
│   │   ...}/                                    ← FULL CORE packages
│   ├── luana-core-{copilot,sales-agent}/        ← CORE-ENGINE + BRAND-EXTENSION
│   ├── luana-core-{brand-studio,offer-studio,
│   │   landing,analytics-engine,campaigns}/     ← CORE-ENGINE + BRAND-CONFIG
│   └── luana-core-{crm,assets,social-proof,
│       commercial-calendar,tenant-{domains,profile}}/  ← FULL CORE
├── nicolify/{backend,frontend}/                 ← Brand vertical: Agencias + Servicios B2B (CRM ciclo largo, portal cliente, propuestas/contratos, horas facturables)
├── vitalia/{backend,frontend,deploy,config}/    ← Brand vertical: Salud + Bienestar (reservas prepagadas, HIPAA-lite, seguimiento post-tratamiento) — Story 11 done
├── comunify/{backend,frontend,deploy}/          ← Brand vertical: Creator Economy + Educación (escalera de valor, bóveda autoridad, motor comunidades) — Story 12 done + WIP recovery
├── lupulo/                                      ← Brand vertical: Gastronomía (reservas mesa, pedidos digitales, integración KDS) — placeholder
├── apps/test-brand/                             ← Reference brand for Extension SDK contracts
# Brand verticals PENDING bootstrap (4 ya existen + 6 nuevos = 10 total):
#   saasora/   ← SaaS + Productos Digitales (onboarding, subscriptions Stripe, dashboards Churn/MRR, changelogs)
#   inmoflow/  ← Real Estate (portales, mapas, lead routing por zona, calculadoras financieras)
#   retailly/  ← E-commerce/D2C (catálogos dinámicos, cart recovery, logística, cross-selling checkout)
#   fixia/     ← Servicios Hogar + Oficios (técnicos en campo, cotización on-site, reseñas locales SEO)
#   guestly/   ← Turismo + Hotelería (motor reservas, sync OTAs Airbnb/Booking, guest experience)
#   fitflow/   ← Fitness + Deporte (membresías recurrentes, aforo, calendario clases, waivers)
├── docs/                                        ← SSoT funcional + arquitectura + process + specs
└── scripts/                                     ← framework scripts (generate_backlog, reconcile_capabilities, validators, etc.)
```

**Migración status (2026-05-15 post-reorg multimarca).** Plan target: `docs/architecture/luana-platform/01-core-audit.md`. Audit purge: `docs/architecture/luana-platform/02-core-purge-audit.md`. Core packages ya extraídos como `luana-core-*` (Story 5+). Brand apps consumen via `luana_core_*` Python imports + `@luana/*` TS imports. Stories 11-12 shipped (vitalia + comunify); lupulo placeholder; **6 marcas nuevas (SaaSora, InmoFlow, Retailly, Fixia, Guestly, FitFlow) pendientes bootstrap** — usar `_pm-brand-template/` workflow.

**Topología docs federada (post reorg 2026-05-15):** SSoT distribuido — `docs/` raíz contiene transversales (Luana core), cada `{brand}/docs/` contiene SSoT autónomo del brand. Vista master en `docs/portfolio/PORTFOLIO.md` (auto-gen). Skills `/pm` unificado en `/pm-luana` (Modo Portfolio + Modo Core Engineering) + `/pm-{brand}` (×4 + 6 templates). `/pm` queda como alias retro-compat. Promotion gate brand→core en `docs/promotion-protocol/`.

## Workspace tooling

| Stack | Manager | Lock | Workspace |
|---|---|---|---|
| Python 3.12 | **uv** | `uv.lock` (root) + `comunify/backend/uv.lock`, `nicolify/backend/uv.lock` | `[tool.uv.workspace]` en `pyproject.toml` raíz (27 members) |
| TypeScript | **pnpm 9.15.9** | `pnpm-lock.yaml` (root) | `pnpm-workspace.yaml` (core + nicolify + vitalia + comunify + lupulo) |
| Runtime | **Docker Compose** (`docker-compose.dev.yml`) | — | postgres + redis + qdrant (cuando aplique) |

**Venv at workspace root** — `.venv/bin/{python,pytest,ruff}` (uv-managed editable installs de todos los workspace members). NUNCA `cd nicolify/backend && python -m venv .venv` — los `luana_core_*` packages no estarían resueltos.

## Spec-Driven Development (SDD Level 3) — paradigma actual

SSoT funcional federado (post reorg multimarca 2026-05-15). Vocabulario v4 (post pm-redesign 2026-05-06).

### Core (Luana — `docs/`)

| Carpeta | Significado | Owner |
|---|---|---|
| `docs/portfolio/` | Vista master 11 universos (auto-gen via `make portfolio`). 1-pagers per universo | `/pm-luana` (Modo Portfolio) |
| `docs/promotion-protocol/` | Workflow brand→core lift gate + proposals + scan-{date}.yaml | `/pm-luana` (Modo Core) |
| `docs/core-modules/` | Contracts públicos de los 26 paquetes `luana-core-*` | `/pm-luana` (Modo Core) |
| `docs/product/` | Outcomes platform (cross-brand) + capabilities core (cuando se pueblen) | `/pm-luana` (Modo Core) |
| `docs/process/` | Reglas transversales: ticket-states, checkpoint-protocol, parallel-sessions, learnings, pm-redesign | `/pm-luana` |
| `docs/specs/` | Templates + Rubrics + Personas (reusable cross-brands) | varios |
| `docs/architecture/` | ADR platform + carve-out plan + purge audit | `/architect` + `/pm-luana` |
| `docs/domains/` | DEPRECATED legacy single-brand snapshot (read-only) | — |
| `docs/archive/{year}/` | Stories `done` snapshot inmutable + snapshot-pre-multibrand-pm-redesign | `/pm-luana` (read-only) |

### Per-brand (`{brand}/docs/` + `{brand}/.claude/`)

| Carpeta | Significado | Owner |
|---|---|---|
| `{brand}/docs/product/{outcomes,stories,capabilities,modules}/` | SSoT funcional brand | `/pm-{brand}` |
| `{brand}/docs/product/{BACKLOG,checkpoint}.md` | Auto-gen + state global brand | `/pm-{brand}` |
| `{brand}/docs/domains/` | Tools/workflows/extractors registrados via Extension SDK | `/pm-{brand}` |
| `{brand}/docs/learnings/` | Insights brand-local (`promotable: candidate\|yes\|no`) | `/pm-{brand}` |
| `{brand}/docs/architecture/` | ADRs locales brand | `/pm-{brand}` |
| `{brand}/.claude/rules/` | Rules overlay brand-specific (extiende `.claude/` raíz) | `/pm-{brand}` |
| `{brand}/.claude/skills/` | Skills overlay brand-specific (raro, mayoría globales) | `/pm-{brand}` |
| `{brand}/config/brand.yaml` | Feature flags + opt-in core packages | `/pm-{brand}` |

### Vocabulary (10 estados macro unificados cross-nivel idea/outcome/story/capability)

Detalle completo: `docs/process/pm-redesign-2026-05.md` § Punto 4.

| # | Estado | Significado | Trigger entry | Owner | WIP cap |
|---|---|---|---|---|---|
| 1 | `idea` | Spark + research opcional (`00-research.md`). Puede nunca implementarse | Chris tira | Chris + `/pm-luana` o `/pm-{brand}` | ∞ |
| 2 | `refining` | Decompose stories + drafts spec/UX/agentic. Loop iterativo Chris | Chris dice "refinemos {x}" | `/pm-luana` o `/pm-{brand}` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | Spec + UX/diseño ratificados Chris. Listo para architects | Chris ratifica | `/pm-luana` o `/pm-{brand}` cierra | ≤ 5 |
| 4 | `ready` | Paquete autocontenido completo (`03-arch` + `04-validators` + `05-guidelines` + `06-tickets`) | `/architect` cierra | `/architect` Opus | ≤ 5 |
| 5 | `developing` | Autonomous build activo iterando vs validators | `/dev-team` picks | opencode/Sonnet (Opus si agentic prod) | ≤ 3 |
| 6 | `developed` | Validators GREEN. Build cerrado, **AUTO-HANDOFF a `/auditor`** (default) salvo `defer_audit: true` en checkpoint | `/dev-team` cierra + emite handoff `/auditor` | `/dev-team` | ≤ 1 |
| 7 | `reviewing` | Auditor QA en curso (Opus C1-C3 + Sonnet tests). **AUTO-HANDOFF a `/pm-{brand}` merge** al APPROVED | auto desde Step 6 (o Chris manual si defer_audit ratificado) | `/auditor` | ≤ 1 |
| 8 | `done` | Auditor APPROVED + merge + capability promovida + docs | auditor APPROVED → `/pm-luana` o `/pm-{brand}` merge | `/pm-luana` o `/pm-{brand}` | rolling 90d |
| 9 | `parked` | De-prioritized, NO abandonado | manual | Chris | ∞ |
| 10 | `dropped` | Won't do (terminal) | manual | Chris | ∞ |

**Legacy exempt:** stories pre-paradigma (PI-12 sales-agent-eval) NO violan caps al migrar; cap aplica forward-only post 2026-05-06.

**★ Story closure gate (post 2026-05-18 — caso vitalia auditor-no-disparado):** una story que entra a `state: developed` o `reviewing` NO PUEDE ser abandonada para arrancar trabajo en otra story. `/dev-team` cerrar `developed` dispara **AUTO-HANDOFF** a `/auditor`. `/auditor` APPROVED dispara **AUTO-HANDOFF** a `/pm-{brand}` merge. Escape valve explícita: `checkpoint.md::defer_audit: true` con razón documentada + ratificación Chris. SSoT: `.claude/rules/story-closure-gate.md` + `docs/process/story-closure-gate.md` + `docs/architecture/luana-platform/ADR-006-story-closure-gate.md`.

Outcome (epic) = agrupación semántica de stories por objetivo común. Story = work unit. Ticket = sub-unit. Outcome cierra event-driven (no time-driven). NO PI/Sprint.

### `ready` package (5 archivos autocontenidos por story)

```
docs/product/stories/{story-id}/
├── 01-spec.md              # /po-ux fusión: Gherkin + wireframes inline (UI std)
│                           # /po: service-stories (no UI)
│                           # /po + /ux-agentico: agentic-stories (spec.md + 02-design-agentic.md)
├── 03-arch.md              # /architect: technical design (incluye sub-arquitecturas BE/FE/AGENTIC)
├── 04-validators.yaml      # ★ CRITICAL ★ tests ejecutables, must_pass:true c/u
├── 05-guidelines.md        # patterns required/forbidden + files in scope + skills/rules a cargar
├── 06-tickets.yaml         # T-1, T-2, ... work units atómicos
└── checkpoint.md           # state + phase + next_action vivo
```

Tickets flat dentro: `T-{n}-impl-log.md`, `T-{n}-result.md`, `T-{n}-review.md`. Si > 10 tickets → story es demasiado grande, split.

### Flujo extremo-a-extremo (3 conversaciones)

```
Conv 1 — DISCOVERY + READY  (Chris + /pm-luana + /po-ux + /architect)
  → idea (ideas-pool.yaml + opcional 00-research.md)
  → [Chris "refinemos"] → refining (/po-ux | /po | /ux-agentico drafts 01-spec + 02-design-*)
  → [Chris ratifica] → refined
  → /architect spawna /architect-{be,fe,agentic} en paralelo → 03-arch.md
  → /architect emite 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml
  → state=ready

Conv 2 — AUTONOMOUS BUILD   (opencode + Sonnet iterando contra validators)
  → /dev-team toma 06-tickets.yaml ticket-por-ticket
  → loop: implement → run validators → fix targeted file → repeat hasta GREEN o cap_reached
  → on GREEN: state=developing→developed + AUTO-HANDOFF /auditor (default)
  → on defer_audit:true en checkpoint: STOP, pingear Chris en bootstrap /pm-{brand}
  → on cap reached: state=developing→blocked, escalate Chris

Conv 3 — REVIEW + MERGE     (auto-handoff cadena; manual opt-in via defer_audit)
  → state=developed → reviewing (auto desde Conv 2, salvo defer_audit ratificado)
  → /auditor spawna auditor-{be,fe,agentic}
  → Phase D: gherkin verification matrix (scenario → test → status)
  → CHECKPOINTS.md C1-C5 grid: Code | Spec | Architecture | Cross-cutting | Trace
  → APPROVED → AUTO-HANDOFF /pm-luana o /pm-{brand} merge
  → /pm-{brand} escribe 07-merge.md (5 secciones cementadas) + update capabilities/* + archive story
  → state=reviewing→done
```

### Cost-routing por phase (model split)

| Phase | Modelo | Razón |
|---|---|---|
| `idea`/`refining`/`refined` (research, decomposition, specs, designs) | **Opus 4.7** | Pensamiento estratégico, alto valor, baja frecuencia |
| `/architect` orchestrator + sub-architects | **Opus 4.7** | Decisiones arquitectónicas, ROI altísimo |
| `/dev-team` BE/FE no-agentic | **Sonnet/opencode** | Ejecución contra validators, barato |
| `/dev-team` agentic production code (R23) | **Opus 4.7** | Calidad agentic = experiencia usuario |
| `/auditor` C1-C3 (código + spec + arch) | **Opus 4.7** | Juicio cualitativo |
| `/auditor` tests/lint/format | **Sonnet** | Determinístico |
| `gate-runner` / `context-builder` / `commit-push` | **Haiku** | Ejecuta + parsea |

### Skills ejes

> **PM unificado (post fusión 2026-05-15 ratificada):** 2 niveles — PM Luana unificado (Modo Portfolio + Modo Core Engineering en un solo skill) + per-brand PMs. Pointer-first (carga ~5k tokens en bootstrap, drill-down on demand). Anti-creep rules dentro del skill protegen jurisdicción.

| Skill | Modelo | Rol |
|---|---|---|
| `/pm-luana` (alias `/pm`) | Opus 4.7 | **PM unificado.** Cubre Modo Portfolio (panorama cross-brand, routing) + Modo Core Engineering (promotion gate brand→core, semver core packages, EPs, outcomes platform). Carga `docs/portfolio/PORTFOLIO.md` + `docs/promotion-protocol/README.md` + `docs/core-modules/README.md`. NO edita `{brand}/docs/`. |
| `/pm-{brand}` (×4: nicolify, vitalia, comunify, lupulo) | Opus 4.7 | **Brand PM.** Hereda paradigm v4. Owner `{brand}/docs/product/`, learnings, architecture, domains. Promotion candidates ping `/pm-luana`. |
| `_pm-brand-template` | (no auto-load) | Scaffold para bootstrap brands futuras (saasora, inmoflow, retailly, fixia, guestly, fitflow). |
| `/po-ux` | Opus 4.7 | UI standard stories (CRUD/list/detail/form/dashboard). Produce 01-spec.md con Gherkin + wireframes inline. |
| `/po` | Opus 4.7 | Service-stories only (no UI). Spec gherkin AI-resistant. |
| `/ux-agentico` | Opus 4.7 | Agentic-story design. State machine + slot architecture + voice constraints. Produce 02-design-agentic.md. |
| `/architect` | Opus 4.7 | Orquesta /architect-{be,fe,agentic}. Produce 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml = `ready` package. |
| `/dev-team` | opencode + Sonnet (BE/FE no-agentic + tests/docs sobre agentic) o Opus 4.7 (agentic production code) | Conv 2 autonomous build. Toma 06-tickets.yaml → TDD → push. |
| `/auditor` | Opus 4.7 | Conv 3. Spawna auditor-{be,fe,agentic}. CHECKPOINTS.md C1-C5. Verdict APPROVED/CHANGES_REQUESTED/ESCALATED. |
| `/commit-push` | Haiku 4.5 | Stage + commit + push delegation pattern. Orchestrator (Opus) prepara plan, Haiku ejecuta git workflow con guardrails verbatim. |

### Filosofía pointer-first (cementada universalmente)

> *"Memoria, índices y skills lite cargan punteros, no contenido. El detalle vive en SSoT donde nace y se carga on-demand."*

Aplicada a: MEMORY.md, memorias individuales, /pm-luana unificado, per-brand PMs, portfolio, promotion proposals. Beneficio: PM Luana escala lineal con cantidad de brands sin degradar contexto.

**Hard rule (R23):** AGENTIC tickets con `production_code: true` (luana_core_copilot/luana_core_sales_agent runtime + brand vertical extensions tocando esos cores) → Opus 4.7 SIEMPRE. opencode/Sonnet ban absoluto. AGENTIC tickets con `production_code: false` (tests/docs sobre agentic) → Sonnet OK.

### Resume protocol (post reorg multimarca 2026-05-15)

```bash
git status --short && git branch --show-current && git log --oneline -3
cat docs/portfolio/PORTFOLIO.md     # Vista master 11 universos (auto-gen via make portfolio)
```

Drill-down según contexto:

```bash
# Brand específica:
cat {brand}/docs/product/checkpoint.md
cat {brand}/docs/product/BACKLOG.md

# Core (Luana):
cat docs/promotion-protocol/README.md
ls docs/promotion-protocol/proposals/
cat docs/architecture/luana-platform/01-core-audit.md
cat docs/architecture/luana-platform/02-core-purge-audit.md

# Story específica brand:
cat {brand}/docs/product/stories/{story-id}/checkpoint.md
```

Schema checkpoint: `docs/process/checkpoint-protocol.md`. Paradigma v4: `docs/process/pm-redesign-2026-05.md`. Promotion workflow: `docs/promotion-protocol/README.md`.

### Anti-telephone-game (subagent return contract)

Cada subagent (builder-*, auditor-*, gate-runner, context-builder) MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Ejemplos: `done -> docs/product/stories/foo/T-1-result.md`, `blocked -> docs/product/stories/foo/checkpoint.md`, `failed -> tests/scripts/test_x.py:42`.

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Brand → Core mapping (Extension SDK)

| Module conceptual | Verdict | Core package | Brand extension surface |
|---|---|---|---|
| `iam`, `core`, `crm`, `assets`, `commercial_calendar`, `tenant_domains`, `tenant_profile`, `social_proof`, `idempotency`, `events`, `compliance`, `billing`, `channels`, `llm`, `observability`, `extension-sdk`, `extraction` | **CORE-FULL** | `luana-core-{x}` | n/a (idéntico cross-brand) |
| `copilot` | **ENGINE + BRAND-EXTENSION** | `luana-core-copilot` | `{brand}/backend/src/modules/{brand}/copilot/{extractors,tools,workflows,kb}/` |
| `sales_agent` | **ENGINE + BRAND-EXTENSION** | `luana-core-sales-agent` | `{brand}/backend/src/modules/{brand}/sales_agent/tools/` + `personas/` + `goldens/` |
| `brand` | **ENGINE + BRAND-CONFIG** | `luana-core-brand-studio` | `{brand}/config/brand.yaml` (enabled_sections + field_overrides + preset_pack) |
| `offer` | **ENGINE + BRAND-CONFIG** | `luana-core-offer-studio` | preset packs registrados via Extension SDK EP-2 |
| `analytics` | **ENGINE + BRAND-CONFIG** | `luana-core-analytics-engine` | enabled_metrics + channel_groups per-brand |
| `campaigns` | **ENGINE + BRAND-CONFIG** | `luana-core-campaigns` | brand activa CampaignTemplateDefs via EP-7 |
| `landing` | **ENGINE + BRAND-CONFIG** | `luana-core-landing` | LandingTemplateDefs via EP-12 |
| `scheduling` | **ENGINE + BRAND-EXTENSION** | `luana-core-scheduling` (futuro, hoy en `luana-core-platform`) | BookingPolicyDef per-brand |
| `connections` | **ENGINE + BRAND-EXTENSION** | `luana-core-connections` | ChannelAdapterDef per-brand (Lupulo POS/KDS, Vitalia payment gateway, Retailly Shopify/WooCommerce, Guestly OTAs Airbnb/Booking, SaaSora Stripe subscriptions, etc.) |
| `advertising`, `social_media` | **DROP** | n/a | Placeholder, no implementación |

**Extension SDK SSoT:** `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry` (EP-1..EP-18). Cada brand monta sus extensiones via `modules/{brand}/extensions.py::register_all(registry)`. Per `.claude/rules/anti-duplication.md` § lift shared rule — mirroring de patrones cross-brand está prohibido.

## 10 Brand verticals catalog

| Brand | Vertical | Cliente objetivo | Diferenciación core | Estado |
|---|---|---|---|---|
| **Nicolify** | Agencias y Servicios B2B | Agencias marketing, software boutique, consultoras | CRM ciclo largo · portal cliente · propuestas/contratos · horas facturables | ✅ shipped |
| **Vitalia** | Salud y Bienestar | Clínicas médicas, dentales, estéticas | Reservas prepagadas · historial médico · HIPAA-lite · seguimiento post-tratamiento | ✅ shipped (Story 11) |
| **Comunify** | Creator Economy + Educación | Coaches, creadores contenido, infoproductores | Escalera valor · bóveda autoridad · motor comunidad · embudos venta | ✅ shipped (Story 12) + WIP recovery |
| **Lupulo Labs** | Gastronomía | Restaurantes, bares, cafeterías | Reservas mesa · pedidos digitales · integración KDS vía agentes IA | 🟡 placeholder (Story 13 pendiente) |
| **SaaSora** | SaaS y Productos Digitales | Startups tech, micro-SaaS, software | Onboarding automatizado · subscripciones Stripe · dashboards Churn/MRR · changelogs | ⏳ bootstrap pendiente |
| **InmoFlow** | Real Estate (Inmobiliaria) | Brokers, agencias bienes raíces | Integración portales · mapas interactivos · lead routing por zona · calculadoras financieras | ⏳ bootstrap pendiente |
| **Retailly** | E-commerce / D2C | Tiendas online, marcas productos físicos | Catálogos dinámicos · cart recovery · integración logística · cross-selling checkout | ⏳ bootstrap pendiente |
| **Fixia** | Servicios Hogar + Oficios | Plomeros, electricistas, HVAC, reformas | Técnicos en campo · cotización on-site · reseñas locales SEO automatizadas | ⏳ bootstrap pendiente |
| **Guestly** | Turismo + Hotelería | Hoteles boutique, rentas vacacionales, tours | Motor reservas por temporada · sync OTAs (Airbnb/Booking) · guest experience | ⏳ bootstrap pendiente |
| **FitFlow** | Fitness y Deporte | Gimnasios, estudios yoga, boxes | Facturación recurrente membresías · control aforo · calendario clases · waivers | ⏳ bootstrap pendiente |

**Bootstrap pattern para brand nueva:** seguir Story 11 (vitalia) o Story 12 (comunify):
1. Crear workspace dir `{brand}/{backend,frontend,config,deploy}/`
2. Brand config `{brand}/config/brand.yaml` (compliance_level, enabled_sections, preset_pack, feature flags)
3. Extension mount `{brand}/backend/src/modules/{brand}/extensions.py::register_all(registry)` montando EP-1..EP-18
4. Brand-specific extensions: copilot/{extractors,tools,workflows,kb}, sales_agent/{tools,personas,goldens}, channel adapters
5. Migrations idempotent en `{brand}/backend/src/modules/{brand}/persistence/migrations/`
6. Frontend en `{brand}/frontend/` (Next.js 16 + FSD-Lite)
7. Deploy K8s manifests en `{brand}/deploy/`

## Git Workflow

**Triple-branch policy** (post multibrand reorg 2026-05-15 — ADR-004):

| Branch | Rol | CI/CD |
|---|---|---|
| `wip/{slug}` | Autosave por sesion paralela. TTL 30d (cron cleanup). | `ci-wip.yml` (light gates) |
| `main` | Integracion estable. CI gates on push + PR. **Staging deploy MANUAL** (post 2026-05-19 ratificada Chris — ADR-004 § policy update). | `ci.yml` (full) — `cd-staging.yml` solo via `workflow_dispatch` |
| `release/{brand}-vX.Y.Z` | Produccion brand-especifica. Desde main validado. **Único auto-deploy.** | `cd-prod.yml` |

**Worktrees por sesion paralela** (ADR-004 revocó ban legacy 2026-05-15 · ADR-005 cementó modelo D1-D14 2026-05-18):

```bash
# Sesion nueva: worktree dedicado (mec. B — D2/D3/D8)
scripts/git/new-session.sh vitalia story copilot-tools-impl be
# crea ~/Proyectos/luana-vitalia-copilot-tools-impl-be/
# branch wip/vitalia-copilot-tools-impl-be · manifest .session.yaml · symlink venv

# Dashboard cross-worktree (mec. H)
scripts/git/status-all.sh

# Sync canónico con main (mec. A logic, runs auto en SessionStart hook)
scripts/git/check-sync.sh

# Push con advisory sync check (mec. L)
scripts/git/push-wip.sh [BRANCH]

# Terminar sesion
scripts/git/cleanup-session.sh vitalia-copilot-tools-impl-be [--delete-branch]
```

**Skill consultable:** `worktree-protocol` (`/worktree-protocol`) — troubleshoot, explicar, modificar reglas del modelo. Trigger: "worktree no funciona", "modificar step 0", "cambiar política sync", etc.

**Manual operativo Warp:** `docs/process/warp-multibrand-handbook.md`. **Modelo SSoT:** `docs/process/parallel-sessions-protocol.md` D1-D14 + `docs/architecture/luana-platform/ADR-005-worktree-policy.md`.

**Forbidden**: `git pull`, `git fetch && merge`, `git push --force`, `git revert` (sin aprobacion), `git add .` / `git add -A`, `git commit --no-verify`. Push non-fast-forward → STOP, reportar. No `git pull`.

**Required**: `git add <path>` por nombre exacto. M11: nunca >30 min sin push con cambios significativos en worktree activo.

Detail: `.claude/rules/git-safety.md` (full policy) + `.claude/rules/parallel-safety.md` (multi-sesion) + `docs/architecture/luana-platform/ADR-004-git-branching-and-environments.md` (rationale).

## Critical Rules (auto-loaded)

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `docs/portfolio/PORTFOLIO.md` (cross-brand) o `{brand}/docs/product/checkpoint.md` (brand-specific) antes coding. Legacy snapshot single-brand: `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/` (read-only) |
| 2 | Tenant isolation | `.claude/rules/tenant-isolation.md` |
| 3 | BE DDD | `.claude/rules/backend-ddd.md` |
| 4 | FE FSD | `.claude/rules/frontend-fsd.md` |
| 5 | Migrations idempotentes | `.claude/rules/backend-migrations.md` |
| 6 | Git/Conventional Commits | `.claude/rules/git-safety.md` |
| 7 | Parallel safety multi-instancia | `.claude/rules/parallel-safety.md` (canonical en `docs/process/parallel-sessions-protocol.md`) |
| 8 | TDD obligatorio | `.claude/rules/tdd-mandatory.md` |
| 9 | Debugging | `.claude/rules/debugging.md` |
| 10 | Spanish neutro LatAm | `.claude/rules/spanish-text.md` |
| 11 | PII (`response_model=`) | `@AGENTS.md` → Tessl pii-sanitisation |
| 12 | Anti-duplication (cross-brand mirror ban) | `.claude/rules/anti-duplication.md` |
| 13 | Ticket states + checkpoint protocol + crash recovery | `docs/process/{ticket-states,checkpoint-protocol}.md` |
| 14 | Auditor downstream regression scope | `.claude/rules/auditor-downstream-regression.md` |
| 15 | Hot-fix repro mandatory | `.claude/rules/hotfix-repro-mandatory.md` |
| 16 | Git Haiku delegation (commit+push pattern) | `.claude/rules/git-haiku-delegation.md` |

## Conditional Rules (stub → skill)

| Tocas | Skill | Stub |
|---|---|---|
| Vista portfolio / cross-brand / core / promotion gate | `/pm-luana` skill (alias `/pm`) | `docs/portfolio/PORTFOLIO.md` + `docs/promotion-protocol/` + `docs/core-modules/` |
| `core/luana-core-copilot/` o `{brand}/backend/src/modules/{brand}/copilot/` | `copilot-expert` | `rules/copilot-{resilience,observability}.md` |
| `core/luana-core-sales-agent/` o `{brand}/backend/src/modules/{brand}/sales_agent/` | `sales-agent-expert` | `rules/sales-agent-brand-voice.md` |
| `core/luana-core-offer-studio/` catalogs | `offer-expert` / `offer-type-preset-expert` | `rules/offer-catalogs.md` |
| `core/luana-core-analytics-engine/` ETL | `metrics-expert` | `rules/{etl-extraction-contract,analytics-metrics,data-reliability}.md` |
| `core/luana-core-brand-studio/` | `brand-expert` | — |
| BE quality/master-data/currency/arch-fitness | `backend-expert` | `rules/{backend-quality,master-data,currency-handling,architectural-fitness}.md` |
| FE quality/form-runtime | `frontend-expert` / `brand-expert` | `rules/{frontend-quality,form-runtime-array}.md` |
| Streamlit admin | `backend-expert` | `rules/admin-panel.md` |
| E2E Playwright + Clerk auth + smoke tests | `playwright-expert` | `rules/e2e-testing.md` |
| PM brand-specific (×4 + 6 templates pendientes) | `/pm-{brand}` skill | `{brand}/docs/product/` + `{brand}/docs/{learnings,architecture,domains}/` |
| Bootstrap brand nueva | `_pm-brand-template/` | scaffold workflow + `{brand}/{backend,frontend,config,deploy,docs,.claude}/` |
| BE config flag flips (`core/config.py` defaults) | (none — `/pm-luana` ratification) | `rules/anti-default-flip-audit.md` |
| User story redacción (UI std) | `po-ux` skill | `docs/specs/templates/01-spec-template.md` |
| User story redacción (service-only) | `po` skill | `docs/specs/templates/01-spec-template.md` |
| Conversational flow design | `ux-agentico` skill | `docs/specs/templates/02-design-agentic-template.md` |
| Tech architecture + ready package | `architect` skill | `docs/specs/templates/03-arch-template.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` |
| Code implementation (autonomous build) | `dev-team` skill | `docs/specs/templates/T-handoff-template.md` |
| Code review (Conv 3) | `auditor` skill | `docs/specs/templates/T-review-template.md` |
| Process metrics emission | `dev-team` + `auditor` | `scripts/emit_process_metric.py` + `docs/process/metrics/README.md` |
| Hot-fix ticket origen handoff doc | `dev-team` + `po` | `.claude/rules/hotfix-repro-mandatory.md` |
| Backlog freshness | `/pm-{brand}` skill | `scripts/generate_backlog.py` (legacy, per-brand) |
| Portfolio freshness (cross-brand) | `/pm-luana` (Modo Portfolio) | `scripts/generate_portfolio.py` + `make portfolio` |
| Promotion candidates scan | `/pm-luana` (Modo Core) | `scripts/scan_promotables.py` + `make scan-promotables` |
| Capability reconciliation | `/pm-{brand}` skill | `scripts/reconcile_capabilities.py` (legacy, per-brand) |
| Multibrand carve-out (extracción a luana-core) | `/architect` + `/pm-luana` | `docs/architecture/luana-platform/01-core-audit.md` + `02-core-purge-audit.md` |
| Promotion proposal brand→core | `/pm-luana` skill | `docs/promotion-protocol/README.md` + `template-proposal.md` |
| Worktree protocol (consulta/troubleshoot/modificar) | `worktree-protocol` skill | `docs/process/parallel-sessions-protocol.md` D1-D14 + `docs/architecture/luana-platform/ADR-005-worktree-policy.md` + `.claude/rules/{parallel-safety,step-0-worktree}.md` + `scripts/git/*.sh` |

## Vision

`docs/product/vision.md` (snapshot legacy hasta /pm-luana regenerar live). Glossary: `docs/product/glossary.md`. Story-map backbone: `docs/product/story-map/backbone.md`. Plan multibrand: `docs/architecture/luana-platform/01-core-audit.md` + ADR-001.

## Workspace bootstrap (fresh clone)

```bash
# 1. Toolchain (user-local)
curl -LsSf https://astral.sh/uv/install.sh | sh                                  # uv
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash  # nvm
nvm install 20 && corepack enable && corepack prepare pnpm@9.15.9 --activate    # node + pnpm

# 2. Deps
uv sync          # Python workspace (todos los luana-core-* + brand backends editables)
pnpm install     # TS workspace (todos los frontends + cores TS)

# 3. Instalar git hooks
make install-hooks   # symlinks scripts/git-hooks/pre-commit → .git/hooks/pre-commit

# 4. Docker dev stack — por brand (S-DOCKER-DEV-MULTIBRAND — 2026-05-15)
cp vitalia/.env.dev.template vitalia/.env.dev   # rellena con valores reales
make dev-vitalia      # levanta postgres (shared) + vitalia backend + frontend
# O para development en nicolify (brand principal):
cp nicolify/.env.dev.template nicolify/.env.dev
make dev-nicolify     # postgres + nicolify backend (8001) + frontend (3001)
# O todas las brands simultaneamente:
make dev-all

# Targets disponibles: make dev-{brand}, make dev-{brand}-tunnel, make dev-all,
#                      make dev-down-{brand}, make dev-clean-{brand}
# Port allocation: nicolify=8001/3001, vitalia=8002/3002, comunify=8003/3003, lupulo=8004/3004
# Postgres compartido: 127.0.0.1:5435

# 5. Verify
.venv/bin/python -c "import luana_core_extension_sdk, luana_core_platform; print('OK')"
curl http://127.0.0.1:8002/health   # vitalia backend (si make dev-vitalia esta corriendo)
```

User must be in `docker` group (`sudo usermod -aG docker $USER` + re-login).

**Runbook completo:** `docs/process/docker-dev-multibrand.md` (quick start, targets, hot-reload, troubleshooting, agregar nueva brand).
**ADR:** `docs/architecture/luana-platform/ADR-003-docker-dev-multibrand.md` (decisiones D1-D6).
**Infra matrix:** `docs/portfolio/INFRA-MATRIX.md` (auto-gen via `make infra-matrix`).

@AGENTS.md
