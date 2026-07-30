# CLAUDE.md

> **★ REPO STANDALONE `vitalia-app`** (extraído de luana-platform 2026-07-30). Este repo contiene SOLO la marca **vitalia** + el engine `core/` (fork vendored, 27 paquetes `luana-core-*`) + el harness completo + el cockpit vendored (`tools/cockpit/`). Referencias a otras marcas (nicolify/comunify/lupulo/…) en docs/rules son HISTÓRICAS — esas marcas viven en el repo luana-platform, no aquí. SSoT single-brand: `project.config.yaml` (`brands.active = [vitalia]`). El promotion gate cross-brand NO aplica (no hay otras marcas); cambios al engine se hacen directo en `core/` con los arch tests como gate.

**vitalia-app** — SaaS multitenant Salud + Bienestar (HIPAA-lite). Modular Monolith DDD + uv/pnpm workspace + Docker-First. La marca consume el engine `core/` (27 paquetes `luana-core-*`, vendored en este repo).

**Objetivo agentic dev:** Chris orquesta /pm-{brand} → /po-ux|/po → /architect → /dev-team → /auditor. Paradigm v4 con auto-handoffs. Cross-brand learning automático. Cost-routing por TIERS — SSoT `project.config.yaml::models` (SLOT 12): `mechanical` (gates/context/grep) · `workhorse` (BE/FE no-agentic) · `flagship` (agentic prod + estratégico/refinamiento: `/architect`·`/auditor`·`/dev-team`·`/po`·`/po-ux`·`/ux-agentico` + `builder-agentic` + `auditor-{be,fe,agentic}`) · `coordinator` (PMs). Swap de modelo = editar el seam + `make models-sync` (NUNCA frontmatter a mano — machinery CHECK 31).

## ★ Brand overlay auto-load

**Cuando trabajés dentro de `{brand}/...` o worktree `~/Proyectos/luana-{brand}*/`, Claude Code carga AUTO el overlay `{brand}/CLAUDE.md`** (walking ancestors built-in). Root + overlay coexisten — NO duplicar contenido. Detalle: `.claude/rules/claude-md-overlay.md`.

| Brand | Overlay | Vision |
|---|---|---|
| vitalia | `vitalia/CLAUDE.md` | `vitalia/docs/product/vision.md` |

@AGENTS.md cubre stack/commands/native-first/skills/quality/constraints. Este file = overlay project-specific.

**Topología completa + workspace tooling + paradigm v4 detail + 10 brand verticals catalog + cost-routing + bootstrap completo + skills detail:** ver `docs/rules-detail/_CLAUDE-original-backup.md` (load con Read on-demand).

## ★ Paradigma de trabajo (norte arquitectónico — por encima de features y de la tech)

Luana = **equipo de trabajadores digitales** que operan un sistema de Go-To-Market (NO un SaaS-herramienta). **3 planos:** Sistema (capacidades de negocio) · Capa de acción (acción única, web + agentes comparten) · Trabajadores (supervisora **Valeria** + especialistas scoped, **UN engine**). El **mapa del producto = 3 zonas**: **Agentes** · **Plataforma** (Acceso · Onboarding · Configuración) · **Infraestructura** (no-funcional). Toda capability declara su **caja desde la idea** + la zona se **deriva** del registro `SYSTEM-MAP.yaml`. La tech (MCP/code-mode) es implementación **swappable**; el invariante es "acción única descubrible + un solo engine + cero isla". SSoT: `docs/architecture/luana-platform/PARADIGM.md` (+ `ADR-010-orquestacion-agentica.md` + rule `paradigm-arquitectura.md`).

## Topology (1-liner)

```
luana-platform/
├── core/luana-core-{27 paquetes}/   ← engine SSoT
├── {vitalia,nicolify,comunify,lupulo}/{backend,frontend,config}/   ← 4 brands activas
├── {saasora,inmoflow,retailly,fixia,guestly,fitflow}/   ← 6 brands pendientes bootstrap (template _pm-sistema-template)
├── docs/   ← transversales Luana (portfolio + promotion-protocol + core-modules + process + specs + architecture)
└── scripts/   ← framework
```

Por-brand: `{brand}/docs/` = SSoT autónomo. Vista master cross-brand: `docs/portfolio/PORTFOLIO.md` (auto-gen via `make portfolio`).

## Workspace tooling (esenciales)

| Stack | Manager | Workspace |
|---|---|---|
| Python 3.12 | **uv** | `[tool.uv.workspace]` en root `pyproject.toml` (27 members editable) |
| TypeScript | **pnpm 9.15.9** | `pnpm-workspace.yaml` (core + 4 brand frontends) |
| Runtime | **Docker Compose** per brand (`make dev-{brand}` o `make dev-all`) | postgres compartido :5435 |

**Venv at workspace root** — `.venv/bin/{python,pytest,ruff}`. NUNCA `cd {brand}/backend && python -m venv .venv` (rompe resolución `luana_core_*`).

**Port allocation:** nicolify=8001/3001, vitalia=8002/3002, comunify=8003/3003, lupulo=8004/3004. **Cockpit:** un solo multi-cockpit en `:4000`, prendido desde **chris-corp** (home base) — ver § Cockpit.

## Tools operativas

| Tool | Path | Trigger conversacional | Cómo levantar |
|---|---|---|---|
| **Cockpit SDD** (visualizer · **vendored en este repo**) | `tools/cockpit/` (source Go + UI Next.js embebida go:embed · binario `tools/cockpit/go/cockpit` · filesystem-as-DB · NO Docker · NO PG · NO node en runtime) | usuario pide "levantar cockpit", "abrir el cockpit" (variantes coloquiales aceptadas) | **`make cockpit-up`** (single-workspace · `:4002` · nohup, sobrevive cierre de terminal). Estado: `make cockpit-status` · bajar: `make cockpit-down` · rebuild: `make cockpit-build` (requiere go + pnpm). Proceso v5 visible: tab Proceso (gate G signoff · DoD · stepper G·R) + gates en Drift. |

### Cockpit · vendored single-workspace

El cockpit es **filesystem-as-DB**: lee/escribe directo de los `.md`/`.yaml` de ESTE workspace (stories, checkpoints, capabilities, releases). Vive vendored en `tools/cockpit/` (origen: prenter-harness `products/devhub`, snapshot 2026-07-30 — fork consciente ratificado por Chris; la rule `cockpit-boundary.md` quedó OBSOLETA en este repo). Corre en `:4002` con PID local `.cockpit-local/cockpit.pid` (no usa `~/.cockpit/` global — no choca con cockpits de otros proyectos).

```bash
make cockpit-up        # prende leyendo este workspace (:4002)
make cockpit-status    # proceso · listener
make cockpit-down      # baja
make cockpit-build     # rebuild binario (UI estática + go build + sidecar)
```

## SDD Level 3 — vocabulario v4 (cementado 2026-05-06)

10 estados macro unificados cross-nivel (idea/outcome/story/capability):

| # | Estado | Owner | WIP cap |
|---|---|---|---|
| 1 | `idea` | Chris + `/pm-*` | ∞ |
| 2 | `refining` | `/pm-*` + `/po-ux`/`/po`/`/ux-agentico` | ≤ 3 |
| 3 | `refined` | `/pm-*` cierra | ≤ 5 |
| 4 | `ready` | `/architect` cierra (paquete completo: 03-arch + 04-validators + 05-guidelines + 06-tickets) | ≤ 5 |
| 5 | `developing` | `/dev-team` (opencode/workhorse · flagship si agentic prod) | ≤ 3 |
| 6 | `developed` | `/dev-team` + AUTO-HANDOFF `/auditor` | ≤ 1 |
| 7 | `reviewing` | `/auditor` + AUTO-HANDOFF `/pm-{brand}` merge si APPROVED | ≤ 1 |
| 8 | `done` | `/pm-*` merge | rolling 90d |
| 9 | `parked` | Chris | ∞ |
| 10 | `dropped` | Chris (terminal) | ∞ |

Paradigm full + flujo 3 conversaciones + cost-routing + skills ejes + ready package schema: `docs/process/pm-redesign-2026-05.md` + `docs/rules-detail/_CLAUDE-original-backup.md` § "Vocabulary".

**★ Story closure gate** (post 2026-05-18): story en `state: developed`/`reviewing` NO puede abandonarse para arrancar otra. `/dev-team` cerrar `developed` → AUTO-HANDOFF `/auditor`. APPROVED → AUTO-HANDOFF `/pm-{brand}` merge. Escape valve: `checkpoint.md::defer_audit: true` con razón documentada + Chris ratify. SSoT: `.claude/rules/story-closure-gate.md`.

## 10 Brand verticals (quick reference)

| Brand | Vertical | Estado |
|---|---|---|
| **Nicolify** | Agencias + Servicios B2B | ✅ shipped |
| **Vitalia** | Salud + Bienestar (HIPAA-lite) | ✅ shipped |
| **Comunify** | Creator Economy + Educación | ✅ shipped |
| **Lupulo Labs** | Gastronomía (KDS + reservas) | 🟡 placeholder |
| **SaaSora** | SaaS/Productos digitales | ⏳ bootstrap pendiente |
| **InmoFlow** | Real Estate | ⏳ bootstrap pendiente |
| **Retailly** | E-commerce/D2C | ⏳ bootstrap pendiente |
| **Fixia** | Servicios Hogar + Oficios | ⏳ bootstrap pendiente |
| **Guestly** | Turismo + Hotelería | ⏳ bootstrap pendiente |
| **FitFlow** | Fitness + Deporte | ⏳ bootstrap pendiente |

Bootstrap brand nueva: pattern Story 11 (vitalia) o Story 12 (comunify) → ver `_pm-sistema-template/SKILL.md` + `docs/rules-detail/_CLAUDE-original-backup.md` § "Bootstrap pattern".

## Brand → Core mapping (Extension SDK)

3 categorías de módulo: **CORE-FULL** (idéntico cross-brand), **ENGINE + BRAND-EXTENSION** (copilot, sales_agent, scheduling, connections), **ENGINE + BRAND-CONFIG** (brand-studio, offer-studio, landing, analytics, campaigns). Tabla completa con paths: `docs/rules-detail/_CLAUDE-original-backup.md` § "Brand → Core mapping".

Extension SDK SSoT: `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry` (EP-1..EP-18). Cross-brand mirror prohibido — ver `.claude/rules/anti-duplication.md`.

## Git Workflow (1-liner)

**Triple-branch:** `wip/{slug}` (autosave per worktree) → `main` (integración, **staging deploy MANUAL**) → `release/{brand}-vX.Y.Z` (único auto-deploy prod).

**Single-hub por marca (default · ADR-009):** N sesiones paralelas (refinar + builds) corren sobre el **mismo worktree canónico** `~/Proyectos/luana-{brand}` coordinadas por bucket locks (`session-lock.sh acquire docs|code:{module}`). Un solo filesystem = un solo SSoT de estado = el cockpit ve TODO + builds ven refinadas al instante. Índice git compartido → commit por pathspec. Worktree dedicado (`new-session.sh`) = **excepción** (lift core, protocol, exp, hotfix, otra marca). Dashboard: `scripts/git/status-all.sh`. M11: nunca >30 min sin push.

**Forbidden:** `git pull`, `git fetch && merge`, `git push --force`, `git revert` sin aprobación, `git add .` / `-A`, `git commit --no-verify`. Push non-fast-forward → STOP.

Detail: `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md` + `.claude/rules/worktree-dual-strategy.md` + `docs/architecture/luana-platform/ADR-{004,005,009}*.md`.

## Critical Rules (auto-loaded de `.claude/rules/`)

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `docs/portfolio/PORTFOLIO.md` o `{brand}/docs/product/checkpoint.md` antes coding |
| 2 | Tenant isolation | `tenant-isolation.md` |
| 3 | BE DDD | `backend-ddd.md` |
| 4 | FE FSD | `frontend-fsd.md` |
| 5 | Migrations idempotentes | `backend-migrations.md` |
| 6 | Git/Conventional Commits | `git-safety.md` |
| 7 | Parallel safety multi-instancia | `parallel-safety.md` |
| 8 | TDD obligatorio | `tdd-mandatory.md` |
| 9 | Debugging | `debugging.md` |
| 10 | Spanish neutro LatAm | `spanish-text.md` |
| 11 | PII (`response_model=`) | `pii-sanitisation.md` |
| 12 | Anti-duplication (cross-brand mirror ban) | `anti-duplication.md` |
| 13 | Ticket states + checkpoint protocol | `docs/process/{ticket-states,checkpoint-protocol}.md` |
| 14 | Auditor downstream regression | `auditor-downstream-regression.md` |
| 15 | Hot-fix repro mandatory | `hotfix-repro-mandatory.md` |
| 16 | Git Haiku delegation | `git-haiku-delegation.md` |
| 17 | Story closure gate (developed→reviewing→done auto) | `story-closure-gate.md` |
| 18 | Brand docs schema (R1+R2+R3) | `sistema-docs-schema.md` |
| 19 | Auditor self-fix policy | `auditor-self-fix-policy.md` |
| 20 | Anti default-flip audit | `anti-default-flip-audit.md` |
| 21 | PM skill chaining (Skill tool inline) | `pm-skill-chaining.md` |
| 22 | Learning capture (técnicos→core, negocio→brand, MEMORY pointer-only) | `learning-capture.md` |
| 23 | Anti-duplication refining (PM/PO/Architect grep core+nicolify+brands) | `anti-duplication-refining.md` |
| 24 | Architect autonomous mode + explicit agent_assignment per ticket | `architect-autonomous-mode.md` |
| 25 | CLAUDE.md hierarchy (root liviano + brand overlay auto-load) | `claude-md-overlay.md` |
| 26 | Worktree dual strategy (refine+build paralelos sin egoísmo) | `worktree-dual-strategy.md` |
| 27 | GitHub Actions deferred (pre-commit/pre-push hooks SSoT) | `github-actions-deferred.md` |
| 28 | Capability protocol v3.2 (story↔cap doctrine + scenarios + access + business_rules + header `# cap:` en código) | `docs/process/capability-protocol.md` |
| 29 | Release protocol (entity SSoT · reemplaza outcome+phase legacy) | `docs/process/release-protocol.md` |
| 30 | chris-input.md protocol (output verbatim per skill) | `docs/process/chris-input-protocol.md` |
| 31 | Cockpit permissions (whitelist transitions Chris vs Claude) | `docs/process/cockpit-permissions.md` |
| 32 | Bidirectional code↔cap mapping (cockpit `/functionality` tab · validator 4 cross-checks · pre-commit/pre-push) | `docs/process/capability-protocol.md` § Sec 12-13 |
| 33 | Anti-orphan integration (CONN: nada llega a `done` como isla — Consumed/On-map/Navigable/Notarized) | `anti-orphan-integration.md` |
| 34 | Frontend visual fidelity (átomos/moléculas + mockup adherence + scope discipline + Playwright scoped) | `frontend-visual-fidelity.md` |
| 35 | Test design doctrine (naturaleza del ticket → batería de tests · jscpd+arch-fitness first-class) | `test-design-doctrine.md` |
| 36 | Paradigma arquitectura (3 planos · mapa = 3 zonas · trabajadores sobre un sistema · acción única · un engine) | `paradigm-arquitectura.md` + `docs/architecture/luana-platform/PARADIGM.md` |
| 37 | Definition of Done live-verify (ninguna story `done` sin que Claude la ejerza live en el stack dev real + `dod_evidence`) | `definition-of-done-live-verify.md` |
| 38 | Cockpit boundary (binario versionado · cero fork · cambios triage genérico/específico · prenter-source jamás en luana) | `cockpit-boundary.md` |

## Conditional Rules (stub → skill on-demand)

| Tocas | Skill | Stub rule |
|---|---|---|
| Vista portfolio / cross-brand / core / promotion gate | `/pm-luana` (alias `/pm`) | `docs/portfolio/` + `docs/promotion-protocol/` + `docs/core-modules/` |
| PM brand-specific (×4 + 6 templates) | `/pm-{brand}` | `{brand}/docs/product/` |
| Bootstrap brand nueva | `_pm-sistema-template/` | scaffold workflow |
| User story UI std | `/po-ux` | `docs/specs/templates/01-spec-template.md` |
| User story service | `/po` | idem |
| Conversational flow design | `/ux-agentico` | `docs/specs/templates/02-design-agentic-template.md` |
| Tech architecture + ready package | `/architect` | `03-arch + 04-validators + 05-guidelines + 06-tickets` templates |
| Autonomous build (Conv 2) | `/dev-team` | `T-handoff-template.md` |
| Code review (Conv 3) | `/auditor` | `T-review-template.md` |
| `core/luana-core-copilot/` o `{brand}/.../copilot/` | `copilot-expert` | `copilot-{resilience,observability}.md` |
| `core/luana-core-sales-agent/` o `{brand}/.../sales_agent/` | `sales-agent-expert` | `sales-agent-brand-voice.md` |
| `core/luana-core-offer-studio/` | `offer-expert` / `offer-type-preset-expert` | `offer-catalogs.md` |
| `core/luana-core-analytics-engine/` ETL | `metrics-expert` | `{etl-extraction-contract,analytics-metrics,data-reliability}.md` |
| `core/luana-core-brand-studio/` | `brand-expert` | — |
| BE quality/master-data/currency/arch-fitness | `backend-expert` | `{backend-quality,master-data,currency-handling,architectural-fitness}.md` |
| FE quality/form-runtime | `frontend-expert` / `brand-expert` | `{frontend-quality,form-runtime-array}.md` |
| Streamlit admin | `backend-expert` | `admin-panel.md` |
| E2E Playwright + Clerk | `playwright-expert` | `e2e-testing.md` |
| Worktree protocol (consulta/troubleshoot) | `worktree-protocol` | `parallel-safety.md` + `step-0-worktree.md` |
| Commit + push delegation Haiku | `commit-push` | `git-haiku-delegation.md` |

## Resume protocol

```bash
git status --short && git branch --show-current && git log --oneline -3
cat docs/portfolio/PORTFOLIO.md             # Vista master 11 universos
cat {brand}/docs/product/checkpoint.md      # State brand
cat {brand}/docs/product/stories/{id}/checkpoint.md   # Story específica
ls {brand}/docs/product/releases/           # 9 releases F0..F8 (vitalia)
cat {brand}/docs/product/releases/F2.yaml   # Release activo brand
```

Schema checkpoint: `docs/process/checkpoint-protocol.md`. Paradigma v4: `docs/process/pm-redesign-2026-05.md`. Promotion workflow: `docs/promotion-protocol/README.md`.

## Workspace bootstrap (fresh clone)

```bash
# 1. Toolchain
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install 20 && corepack enable && corepack prepare pnpm@9.15.9 --activate

# 2. Deps + hooks
uv sync && pnpm install && make install-hooks

# 3. Dev stack per brand
cp {brand}/.env.dev.template {brand}/.env.dev
make dev-{brand}    # o make dev-all

# 4. Verify
.venv/bin/python -c "import luana_core_extension_sdk, luana_core_platform; print('OK')"
curl http://127.0.0.1:8002/health   # vitalia ejemplo
```

Bootstrap detail completo + troubleshooting: `docs/process/docker-dev-multibrand.md` + `docs/architecture/luana-platform/ADR-003*.md`.

## Anti-telephone-game (subagent return contract)

Cada subagent (builder-*, auditor-*, gate-runner, context-builder) MUST devolver UNA línea final: `<verdict> -> <path-to-artifact>`. NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Vision

- Platform-level: `docs/product/vision.md` — qué es luana-platform multibrand + filosofía cross-brand learning.
- Per-brand: `{brand}/docs/product/vision.md` (auto-load via overlay) — vertical + verticales target + GTM + buyer personas.
- Glossary: `docs/product/glossary.md`.
- Plan multibrand: `docs/architecture/luana-platform/01-core-audit.md` + ADR-001.

## Learning capture (1-liner)

Trigger: Chris dice **"aprendamos de esto"** o el hook `learning-detect.sh` sugiere. Captura → archivo `.md` en path canónico (técnico→`docs/learnings/`, negocio→`{brand}/docs/learnings/`, process→`docs/process/learnings.md` append) + MEMORY.md pointer 1 línea. Detalle: `.claude/rules/learning-capture.md`.

@AGENTS.md
