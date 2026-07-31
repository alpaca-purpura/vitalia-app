# CLAUDE.md

> **★ REPO STANDALONE `vitalia-app`** (extraído de luana-platform 2026-07-30 · reestructurado 2026-07-31). Contiene SOLO la marca **vitalia** + el engine `core/` (fork vendored, 27 paquetes `luana-core-*`) + el harness **materializado** (archivos propios en `.claude/` — sin plugin, sin kit externo) + el cockpit vendored (`tools/cockpit/`). Referencias a otras marcas (nicolify/comunify/…) en docs son HISTÓRICAS — viven archivadas en `docs/archive/2026/multibrand-legacy/`. SSoT single-brand: `project.config.yaml` (`brands.active = [vitalia]`). El promotion gate cross-brand NO existe: cambios al engine se hacen directo en `core/` con arch tests como gate (ver § Engine).

**vitalia-app** — SaaS multitenant Salud + Bienestar (HIPAA-lite). Modular Monolith DDD + uv/pnpm workspace + Docker-First. La marca consume el engine `core/` vendored.

**Flujo agentic:** Chris (y el equipo) orquestan `/pm-vitalia` → `/po-ux`|`/po` (+`/ux-agentico` si agentic) → `/architect` → `/dev-team` → `/auditor`. Paradigm v4 con auto-handoffs. Cost-routing por TIERS — SSoT `project.config.yaml::models` (SLOT 12): `mechanical` · `workhorse` · `flagship` · `coordinator`. Swap de modelo = editar el seam + `make models-sync` (NUNCA frontmatter a mano — machinery CHECK 31).

**Onboarding developer nuevo:** `docs/onboarding/README.md` (setup local + cockpit + flujo git + flujo agentic).

## ★ Brand overlay auto-load

**Cuando trabajés dentro de `vitalia/...`, Claude Code carga AUTO el overlay `vitalia/CLAUDE.md`** (walking ancestors built-in). Root + overlay coexisten — NO duplicar contenido. Detalle: `.claude/rules/claude-md-overlay.md`. Vision de marca: `vitalia/docs/product/vision.md`.

@AGENTS.md cubre stack/commands/native-first/skills/quality/constraints. Este file = overlay project-specific.

## ★ Paradigma de trabajo (norte arquitectónico)

Vitalia = **equipo de trabajadores digitales** que operan un sistema de Go-To-Market (NO un SaaS-herramienta). **3 planos:** Sistema (capacidades de negocio) · Capa de acción (acción única, web + agentes comparten) · Trabajadores (supervisora **Valeria** + especialistas scoped, **UN engine**). El **mapa del producto = 3 zonas**: **Agentes** · **Plataforma** (Acceso · Onboarding · Configuración) · **Infraestructura** (no-funcional). Toda capability declara su **caja desde la idea** + la zona se **deriva** de `vitalia/docs/architecture/SYSTEM-MAP.yaml`. SSoT: `docs/architecture/luana-platform/PARADIGM.md` (+ `ADR-010` + rule `paradigm-arquitectura.md`).

## Topology

```
vitalia-app/
├── core/luana-core-{27 paquetes}/     ← engine vendored (naming luana-core se conserva)
├── core/@luana/{8 paquetes TS}/       ← ui-kit, design-tokens, extension-sdk, …
├── vitalia/{backend,frontend,config,docs}/   ← la marca (SSoT funcional: vitalia/docs/)
├── docs/                              ← transversal: process + architecture engine + learnings + archive
├── tools/cockpit/                     ← cockpit vendored (Go + UI embebida)
└── scripts/                           ← framework (hooks, machinery, git)
```

## Workspace tooling (esenciales)

| Stack | Manager | Workspace |
|---|---|---|
| Python 3.12 | **uv** | `[tool.uv.workspace]` en root `pyproject.toml` (27 members editable) |
| TypeScript | **pnpm 9.15.9** | `pnpm-workspace.yaml` (core + vitalia/frontend) |
| Runtime | **Docker Compose** (`make dev-vitalia`) | postgres :5435 |

**Venv at workspace root** — `.venv/bin/{python,pytest,ruff}`. NUNCA crear venv dentro de `vitalia/backend` (rompe resolución `luana_core_*`).

**Ports:** vitalia backend=8002 · frontend=3002 · cockpit=4002.

## Cockpit (visualizador SDD · vendored)

Filesystem-as-DB: lee/escribe directo los `.md`/`.yaml` de ESTE repo (stories, checkpoints, capabilities, releases). Source en `tools/cockpit/` (Go + UI Next.js embebida go:embed · binario `tools/cockpit/go/cockpit` · NO Docker · NO PG). Trigger conversacional: "levantar/abrir el cockpit".

```bash
make cockpit-up        # :4002 · setsid nohup, sobrevive cierre de terminal
make cockpit-status    # proceso · listener
make cockpit-down
make cockpit-build     # rebuild binario (requiere go + pnpm)
```

Tabs (`cockpit.config.yaml::nav`): roadmap · evolucion · board · map · drift · learnings · harness. Proceso v5 visible: gate G signoff · DoD · stepper G·R + gates en Drift.

## SDD Level 3 — vocabulario v4 (10 estados macro)

| # | Estado | Owner | WIP cap |
|---|---|---|---|
| 1 | `idea` | Chris + `/pm-vitalia` | ∞ |
| 2 | `refining` | `/pm-vitalia` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | `/pm-vitalia` cierra | ≤ 5 |
| 4 | `ready` | `/architect` cierra (paquete: 03-arch + 04-validators + 05-guidelines + 06-tickets) | ≤ 5 |
| 5 | `developing` | `/dev-team` | ≤ 3 |
| 6 | `developed` | `/dev-team` + gate G (Chris verify) + AUTO-HANDOFF `/auditor` | ≤ 1 |
| 7 | `reviewing` | `/auditor` + AUTO-HANDOFF `/pm-vitalia` merge si APPROVED | ≤ 1 |
| 8 | `done` | `/pm-vitalia` merge | rolling 90d |
| 9 | `parked` | Chris | ∞ |
| 10 | `dropped` | Chris (terminal) | ∞ |

Detalle flujo + ready package schema: `docs/process/pm-redesign-2026-05.md`.

**★ Story closure gate:** story en `developed`/`reviewing` NO puede abandonarse para arrancar otra (mismo módulo). Ciclo: `developed` → G (Chris-verify) → R (reconcile) → `/auditor` → APPROVED → `/pm-vitalia` merge. Escape valve: `defer_audit: true` ratificado. SSoT: `.claude/rules/story-closure-gate.md`.

## Engine (`core/luana-core-*`) — ex promotion gate

El engine es SSoT conceptual compartido: **NUNCA mirror en `vitalia/backend/` de lo que el engine ya tiene** (`anti-duplication.md`). Cambio de engine = edición directa en `core/luana-core-{pkg}` gateada por: arch tests del paquete + arch tests de vitalia en verde + bump semver + CHANGELOG del paquete. Breaking change de contrato (Extension SDK EP-1..EP-18) → ADR + ratificación de Chris ANTES. Owner: `/pm-vitalia`. Catálogo: `docs/core-modules/README.md`. Extension SDK SSoT: `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry`.

3 categorías de módulo: **CORE-FULL** (se consume tal cual) · **ENGINE + BRAND-EXTENSION** (copilot, sales_agent, scheduling, connections) · **ENGINE + BRAND-CONFIG** (brand-studio, offer-studio, landing, analytics, campaigns). Mapping completo: `project.config.yaml::domain_modules`.

## Git Workflow (trunk-based · SSoT `docs/process/git-workflow.md`)

**`main` = único branch permanente.** Por story: `story/{id}` de vida corta (horas) → squash-merge → borrar. Chris pushea directo a main docs/chores/config; stories llevan review IA contexto-fresco pre-merge; tier de riesgo (auth/tenant/migraciones/pagos/agentes) → PR + review humano. Dev nuevo: todo vía PR el primer mes. Releases: hoy `release/vitalia-vX.Y.Z` (cd-prod deferred) → objetivo tags `vX.Y.Z`.

**Forbidden:** `git pull` con merge/rebase (permitido SOLO `git pull --ff-only` sobre branch limpio) · `git push --force` · `git revert`/`reset --hard` sin aprobación · `git add .`/`-A`/`-u` (stage por pathspec exacto) · `git commit --no-verify` · amend de commits pusheados. Enforcement primario = hooks locales (`make install-hooks`).

## Critical Rules (auto-loaded de `.claude/rules/`)

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `vitalia/docs/product/checkpoint.md` antes de coding |
| 2 | Tenant isolation | `tenant-isolation.md` |
| 3 | BE DDD | `backend-ddd.md` |
| 4 | FE FSD | `frontend-fsd.md` |
| 5 | Migrations idempotentes | `backend-migrations.md` |
| 6 | Git/Conventional Commits | `git-safety.md` |
| 7 | TDD obligatorio | `tdd-mandatory.md` |
| 8 | Debugging | `debugging.md` |
| 9 | Spanish neutro LatAm (UI) | `spanish-text.md` |
| 10 | PII (`response_model=`) | `pii-sanitisation.md` |
| 11 | Anti-duplication (engine mirror ban) | `anti-duplication.md` |
| 12 | Ticket states + checkpoint protocol | `docs/process/{ticket-states,checkpoint-protocol}.md` |
| 13 | Auditor downstream regression | `auditor-downstream-regression.md` |
| 14 | Hot-fix repro mandatory | `hotfix-repro-mandatory.md` |
| 15 | Git Haiku delegation | `git-haiku-delegation.md` |
| 16 | Story closure gate | `story-closure-gate.md` |
| 17 | Brand docs schema (R1..R4) | `sistema-docs-schema.md` |
| 18 | Auditor self-fix policy (v5 Responsable) | `auditor-self-fix-policy.md` |
| 19 | Anti default-flip audit | `anti-default-flip-audit.md` |
| 20 | PM skill chaining (Skill tool inline) | `pm-skill-chaining.md` |
| 21 | Learning capture (MEMORY pointer-only) | `learning-capture.md` |
| 22 | Anti-duplication refining (prior-art scan) | `anti-duplication-refining.md` |
| 23 | Architect autonomous mode + agent_assignment | `architect-autonomous-mode.md` |
| 24 | CLAUDE.md hierarchy (root + overlay vitalia) | `claude-md-overlay.md` |
| 25 | GitHub Actions deferred (hooks locales SSoT) | `github-actions-deferred.md` |
| 26 | Capability protocol v3.2 | `docs/process/capability-protocol.md` |
| 27 | Release protocol | `docs/process/release-protocol.md` |
| 28 | chris-input.md protocol | `docs/process/chris-input-protocol.md` |
| 29 | Cockpit permissions (whitelist transitions) | `docs/process/cockpit-permissions.md` |
| 30 | Bidirectional code↔cap mapping | `docs/process/capability-protocol.md` § Sec 12-13 |
| 31 | Anti-orphan integration (CONN) | `anti-orphan-integration.md` |
| 32 | Frontend visual fidelity | `frontend-visual-fidelity.md` |
| 33 | Test design doctrine | `test-design-doctrine.md` |
| 34 | HIPAA-lite PHI (dual filter + audit log) | `hipaa-lite.md` (consolidada a root 2026-07-31) |
| 35 | Shell-feature architecture (ADR-vitalia-004) | `shell-feature-architecture-mandatory.md` (consolidada a root 2026-07-31) |
| 36 | Paradigma arquitectura (3 planos · 3 zonas) | `paradigm-arquitectura.md` + PARADIGM.md |
| 37 | DoD live-verify (`dod_evidence`) | `definition-of-done-live-verify.md` |

## Conditional Rules (stub → skill on-demand)

| Tocas | Skill | Stub rule |
|---|---|---|
| Estado marca / backlog / stories / releases / caps / engine governance | `/pm-vitalia` (alias `/pm`) | `vitalia/docs/product/` + `docs/core-modules/` |
| User story UI std | `/po-ux` | `docs/specs/templates/01-spec-template.md` |
| User story service | `/po` | idem |
| Conversational flow design | `/ux-agentico` | `docs/specs/templates/02-design-agentic-template.md` |
| Tech architecture + ready package | `/architect` | `03-arch + 04-validators + 05-guidelines + 06-tickets` templates |
| Autonomous build (Conv 2) | `/dev-team` | `T-handoff-template.md` |
| Code review (Conv 3) | `/auditor` | `T-review-template.md` |
| `core/luana-core-copilot/` o `vitalia/.../copilot/` | `copilot-expert` | `copilot-{resilience,observability}.md` |
| `core/luana-core-sales-agent/` o `vitalia/.../sales_agent/` | `sales-agent-expert` | `sales-agent-brand-voice.md` |
| `core/luana-core-offer-studio/` | `offer-expert` / `offer-type-preset-expert` | `offer-catalogs.md` |
| `core/luana-core-analytics-engine/` ETL | `metrics-expert` | `{etl-extraction-contract,analytics-metrics,data-reliability}.md` |
| `core/luana-core-brand-studio/` | `brand-expert` | — |
| BE quality/master-data/currency/arch-fitness | `backend-expert` | `{backend-quality,master-data,currency-handling,architectural-fitness}.md` |
| FE quality/form-runtime | `frontend-expert` / `brand-expert` | `{frontend-quality,form-runtime-array}.md` |
| UI vitalia (`vitalia/frontend/src/**`) | `vitalia-design-system` | `frontend-visual-fidelity.md` |
| Streamlit admin | `backend-expert` | `admin-panel.md` |
| E2E Playwright + Clerk | `playwright-expert` | `e2e-testing.md` |
| Commit + push delegation Haiku | `commit-push` | `git-haiku-delegation.md` |
| PHI (`patient_*`/`medical_*`/`treatment_*`/…) | `hipaa-check` | `hipaa-lite.md` |

## Resume protocol

```bash
git status --short && git branch --show-current && git log --oneline -3
cat vitalia/docs/product/checkpoint.md      # Vista master del producto
cat vitalia/docs/product/stories/{id}/checkpoint.md   # Story específica
ls vitalia/docs/product/releases/           # F0..F8
```

Schema checkpoint: `docs/process/checkpoint-protocol.md`. Paradigma v4: `docs/process/pm-redesign-2026-05.md`.

## Workspace bootstrap (fresh clone)

Guía completa paso a paso: **`docs/onboarding/README.md`**. Resumen:

```bash
uv sync && pnpm install && make install-hooks
cp vitalia/.env.dev.template vitalia/.env.dev   # valores reales: pedir a Chris
make dev-vitalia && curl http://127.0.0.1:8002/health
make cockpit-up   # :4002
```

## Anti-telephone-game (subagent return contract)

Cada subagent (builder-*, auditor-*, gate-runner, context-builder) MUST devolver UNA línea final: `<verdict> -> <path-to-artifact>`. NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Vision

- Marca: `vitalia/docs/product/vision.md` (auto-load via overlay) — vertical + GTM + buyer personas.
- Plataforma (histórico multibrand): `docs/product/vision.md`.

## Learning capture (1-liner)

Trigger: Chris dice **"aprendamos de esto"** o el hook `learning-detect.sh` sugiere. Captura → archivo `.md` en path canónico (técnico→`docs/learnings/`, negocio→`vitalia/docs/learnings/`, process→`docs/process/learnings.md` append) + MEMORY.md pointer 1 línea. Detalle: `.claude/rules/learning-capture.md`.

@AGENTS.md
