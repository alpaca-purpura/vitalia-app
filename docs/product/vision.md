# Luana Platform — Vision

**Fecha snapshot:** 2026-05-27 (regenerado post-multibrand reorg).
**Owner:** `/pm-vitalia` (fusión pm-vitalia+pm-luana, repo standalone 2026-07-31).

> ★ **Nota 2026-07-31 (vitalia-app standalone):** este file describe la visión del monorepo multimarca `luana-platform` del que se extrajo este repo. La filosofía engine-como-acumulador-de-aprendizajes sigue válida; la maquinaria cross-brand referenciada (portfolio, promotion gate, otras marcas) quedó archivada en `docs/archive/2026/multibrand-legacy/`. Visión viva de la marca: `vitalia/docs/product/vision.md`. Vista master: `vitalia/docs/product/checkpoint.md`.

> Luana es una plataforma multimarca multitenant SaaS que **multiplica el ROI por marca** consolidando engine compartido (`core/luana-core-*`, 26 paquetes) + verticales brand-specific (10 brands). Cada brand aprende independiente, **el engine acumula los aprendizajes técnicos transversales**, las brands acumulan los aprendizajes de negocio per-vertical. Resultado: lift+expand más rápido + costos infra-ingeniería compartidos.

## Filosofía cross-brand learning

Una brand que descubre un pattern técnico (ej: cómo manejar storage state freshness con Clerk en E2E) → ese aprendizaje vive en `docs/learnings/` (core engine root) → otras brands aplican sin redescubrir. Una brand que descubre un pattern de negocio (ej: cómo Vitalia maneja consentimiento digital paciente) → vive en `vitalia/docs/learnings/`, otras brands lo consultan si aplica (probablemente no — es brand-specific).

**Esta filosofía dicta arquitectura.** Engine compartido NO es shortcut DRY — es **mecanismo de transferencia de conocimiento técnico verificado a través de N verticales**.

## 10 Brand verticals (mapeo high-level)

| Brand | Vertical | Stage | Cross-brand learning rol |
|---|---|---|---|
| **Nicolify** | Agencias + Servicios B2B | 🔵 frozen snapshot post-reorg 2026-05-15 | **Referencia arqueológica** (24 stories shipped pre-reorg viven en `docs/archive/2026/snapshot-pre-multibrand-pm-redesign/`). NO live work post-reorg. Code consolidado en `core/luana-core-*/` |
| **Vitalia** | Salud + Bienestar electivo (HIPAA-lite LatAm) | ✅ brand más activa | 27 archived done + Fase 1 shell complete + Fase 2 in-progress + 71 capabilities + 21 learnings. **Source principal LIVE** para cross-brand prior-art |
| **Comunify** | Creator Economy + Educación | ✅ shipped | 2 archived done + 18 capabilities. **Source live secundario** (especialmente creator economy patterns) |
| **Lupulo Labs** | Gastronomía (KDS + reservas) | 🟡 placeholder | TBD — aprenderá real-time KDS + reservas industria-específica |
| **SaaSora** | SaaS + Productos Digitales | ⏳ bootstrap | TBD — aprenderá Churn/MRR/changelog engineering |
| **InmoFlow** | Real Estate / Inmobiliaria | ⏳ bootstrap | TBD — aprenderá portales (MercadoLibre Inmuebles, ZonaProp) |
| **Retailly** | E-commerce / D2C | ⏳ bootstrap | TBD — aprenderá Shopify/Woo + cart recovery |
| **Fixia** | Servicios Hogar + Oficios | ⏳ bootstrap | TBD — aprenderá despacho técnicos + cotización on-site mobile |
| **Guestly** | Turismo + Hotelería | ⏳ bootstrap | TBD — aprenderá channel manager + revenue management |
| **FitFlow** | Fitness + Deporte | ⏳ bootstrap | TBD — aprenderá membresías Stripe + aforo + waivers |

## Engine compartido (`core/luana-core-*`)

26 paquetes Python (uv workspace) que encapsulan abstracciones cross-brand:

- **Identity + multi-tenancy:** iam, platform, locale, currency
- **Agentic infrastructure:** llm router, prompt cache, observability, langgraph state, deepagents
- **Module foundations:** brand-studio, offer-studio, landing, analytics-engine, scheduling, connections, campaigns, copilot, sales-agent, compliance (planned)
- **Cross-cutting:** events, idempotency, billing, channels, extraction, observability

**Brands NUNCA importan código de otras brands** — sólo consumen engine via `from luana_core_X import Y`. Mirror cross-brand prohibido (anti-duplication.md + anti-duplication-refining.md).

## Flujo engine (ex promotion gate brand→core — retirado 2026-07-31)

Cuando la marca descubre un pattern que pertenece al engine:
1. `/pm-vitalia` evalúa el lift (flujo engine — repo standalone, sin promotion gate cross-brand)
2. Cambio directo en `core/luana-core-{pkg}` gateado por: arch tests del paquete + arch tests de vitalia en verde
3. Bump semver + CHANGELOG del paquete; breaking change de contrato (Extension SDK EP-1..EP-18) → ADR + ratificación de Chris ANTES

Detalle: `CLAUDE.md § Engine` + `docs/core-modules/README.md`. El promotion protocol multibrand quedó archivado en `docs/archive/2026/multibrand-legacy/`.

## Paradigm 3 conversaciones (paradigm v4)

Cada story atraviesa 3 conversaciones autónomas:

1. **Conv 1 — Refinamiento (idea→ready):** `/pm-{brand}` + `/po-ux`|`/po`|`/ux-agentico` + `/architect`. Output: ready package (01-spec + 02-design + 03-arch + 04-validators + 05-guidelines + 06-tickets).
2. **Conv 2 — Autonomous build (ready→developed):** `/dev-team` itera tickets vs validators GREEN.
3. **Conv 3 — Audit + merge (developed→done):** `/auditor` review + AUTO-HANDOFF `/pm-{brand}` merge.

Estados macro 10 (idea, refining, refined, ready, developing, developed, reviewing, done, parked, dropped) cross-nivel (idea/outcome/story/capability).

Detalle: `docs/process/pm-redesign-2026-05.md`.

## Cost routing

| Tipo trabajo | Modelo preferido | Rationale |
|---|---|---|
| Git workflow (commit/push) | Haiku 4.5 | Mecánico — Opus waste |
| BE/FE no-agentic build | Sonnet 4.6 / opencode | Sweet spot código repetitivo + tests |
| Architect orchestrator | Opus 4.7 | Decisión arquitectónica multi-surface |
| AGENTIC production code | Opus 4.7 (R23 HARD) | Calidad voice + reasoning |
| Auditor self-fix triviales | Sonnet/Opus auditor | Whitelist verbatim |
| Tests + docs (cualquier surface) | Sonnet | No-prod code |
| Context-builder + gate-runner | Haiku 4.5 | Worker reading + parsing |

Detalle: `.claude/rules/auditor-self-fix-policy.md` + `docs/process/pm-redesign-2026-05.md`.

## Cross-brand learning artefactos

| Path | Contenido | Scope |
|---|---|---|
| `docs/learnings/` | Aprendizajes técnicos transversales | Cross-brand (aplica ≥2) |
| `{brand}/docs/learnings/` | Aprendizajes negocio brand-specific | Solo esa brand |
| `docs/process/learnings.md` | Process/paradigm changes históricos | Cross-platform |
| `MEMORY.md` (~/.claude/...) | Índice pointer-first, ≤200 líneas | Modelo session memory |

Sistema cementado: `.claude/rules/learning-capture.md`. Trigger Chris: "aprendamos de esto".

## Filosofía técnica

- **Modular Monolith DDD** (Inside-Out: domain → infrastructure → application → api)
- **Async-first** (FastAPI async + SQLAlchemy 2.0 async + AsyncSession)
- **Multitenancy enforced** en cada query (`tenant_id` filter — `.claude/rules/tenant-isolation.md`)
- **Spanish neutro LatAm** UI (excepto sales_agent que respeta voz tenant)
- **Compliance-first** (PII sanitization, audit logs, retention policies — HIPAA-lite Vitalia drives this hard)
- **TDD obligatorio** (`.claude/rules/tdd-mandatory.md`)
- **Migrations idempotentes** (`IF NOT EXISTS` / `IF EXISTS` siempre)
- **Engine packages tests-first** + cada brand consumer revalidates (`.claude/rules/auditor-downstream-regression.md`)

## Filosofía agentic

- **LangGraph 2.0** como state machine para conversational agents (sales_agent, copilot)
- **DeepAgents** middleware (SubAgentMiddleware) para isolation de subtasks
- **Anthropic prompt caching** (5min/1h TTL) — slots architecture documentada per agent
- **Eval suite obligatorio** (sales_agent goldens, copilot trace events)
- **Voice fidelity grader** per tenant brand voice
- **Observabilidad ground-truth** (`copilot_trace_event` + `copilot_llm_call` tables — brand-mirror schema via backend-ddd.md exception)

## Filosofía git

- **Triple-branch:** `wip/{slug}` (autosave per worktree) → `main` (integración) → `release/{brand}-vX.Y.Z` (prod)
- **Worktrees obligatorios** para sesiones paralelas (Chris opera 2-3 simultáneas)
- **Worktree dual:** refine lane (`wip/{brand}-refine`) + build canónico (`wip/{brand}`) para refinar próximas mientras se construye actual (`.claude/rules/worktree-dual-strategy.md`)
- **GitHub Actions deferred** hasta deploy server materialice (`.claude/rules/github-actions-deferred.md`)
- **Pre-commit/pre-push hooks** SSoT (native Linux, no Docker)

## Filosofía Claude Code

- **Root CLAUDE.md** liviano (~200 líneas) + brand overlays auto-cargados (`.claude/rules/claude-md-overlay.md`)
- **Skills cargados on-demand** (no monolítico)
- **PM skill chaining** programático (`.claude/rules/pm-skill-chaining.md`)
- **Subagent return contract**: 1 línea final `<verdict> -> <artifact>` (anti-telephone-game)
- **MEMORY pointer-first** (`.claude/rules/learning-capture.md`)
- **Architect autonomous mode** opcional con explicit agent_assignment per ticket (`.claude/rules/architect-autonomous-mode.md`)
- **Anti-duplication refining**: PM/PO/Architect grep cross-brand antes refinar (`.claude/rules/anti-duplication-refining.md`)

## Vision evolución 2026-2027

Q3 2026: Vitalia MVP shipped en 3 verticales Tier 1 (dental + estética + oftalmología). Comunify estable. Nicolify continues. Lupulo bootstrap real.
Q4 2026: HIPAA-lite multi-país consolidado en engine. SaaSora bootstrap. Voice agent omnichannel (H5 Vitalia) shipped.
Q1 2027: Mid-market expansion Vitalia + Nicolify (multi-doctor, multi-org). Promotion gates frecuentes (cada vertical contribuye al engine).
Q2 2027: Tier 2 verticales Vitalia. InmoFlow/Retailly bootstrap.

## Vision NO

- NO competimos en emergencias / salud obligatoria
- NO somos directorio (no Doctoralia, no Yelp)
- NO somos one-size-fits-all genérico (no Notion/Monday/Asana clones)
- NO sacrificamos compliance por velocity (Vitalia drives this hard cross-brand)
- NO replicamos código entre brands (engine SSoT + Extension SDK)
- NO escala vía monolito mega-app (modular monolith DDD + posibles futuros carve-outs per brand)

## Referencias

- `CLAUDE.md` (root) — paradigm + topology
- `vitalia/docs/product/vision.md` — vertical-specific deep dive
- `nicolify/docs/product/vision.md` (TBD si no existe) — vertical más madura
- `docs/portfolio/PORTFOLIO.md` — vista master auto-gen cross-brand
- `docs/promotion-protocol/README.md` — workflow brand→core lift
- `docs/process/pm-redesign-2026-05.md` — paradigm v4 detalle
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` — EP-1..EP-18 contracts
- `.claude/rules/learning-capture.md` — sistema aprendizajes cross-brand
- `.claude/rules/anti-duplication-refining.md` — prior-art scan obligatorio
