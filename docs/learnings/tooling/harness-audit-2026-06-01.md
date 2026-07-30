# (provenance)
> Generado por workflow `harness-audit-2026` (run wf_1f1d1973-ac4) · 2026-06-01 · 39 agentes · read-only.
> Estado: PROPUESTA — pendiente ratificación de Chris (catalog+propose). NADA aplicado aún.
> Línea base de schemas: `claude-code-2026-capabilities.md`. Plan: `harness-modernization-session-plan.md`.

---

# Catálogo de Auditoría del Harness Claude Code — luana-platform

> **Estado:** RATIFICABLE (pre-edit). Síntesis de 37 lotes cubriendo skills · agents · rules · hooks · cockpit · process · templates · adr.
> **Fecha:** 2026-06-01 · **Lead de síntesis:** subagente de consolidación.
> **Cómo leer:** Quick wins primero (aplicar sin discusión) → catálogo por superficie (severity-ordered) → decisiones que requieren criterio de Chris → roadmap CC-2026.
> **Verificación spot:** 8 claims de mayor impacto confirmados contra el filesystem real del worktree `luana-vitalia` (ver notas inline marcadas ✅ VERIFICADO).

---

## Resumen ejecutivo (patrones transversales)

Hay **6 clases de defecto recurrentes** que explican ~70% de los hallazgos. Atacar la clase, no el síntoma individual:

| # | Clase de defecto | Dónde aparece | Causa raíz |
|---|---|---|---|
| **A** | **Paths pre-reorg single-brand** (`backend/`, `frontend/`, `shared/`, `docs/product/stories/`) | ~18 skills, ~6 rules, ~12 templates, varios agents | El reorg multibrand (2026-05-15) no actualizó docs/skills downstream |
| **B** | **`tessl__*` skills + `.tessl/` directorio inexistentes** | 6 agents (HARD GATE Step 0), ~5 skills/templates | `.tessl/` nunca existió en este worktree → todo Step 0 que los exige se auto-aborta ✅ VERIFICADO |
| **C** | **Containers legacy `visionarias_*`** | 5 agents/skills, debugging refs | Naming pre-reorg; containers reales = `luana-{brand}-*` / `luana-dev-{brand}_*` |
| **D** | **Branch `development` + `git pull` + auto-deploy GA** | commit-push, git-manager, pase-produccion, varios process docs | Modelo pre-triple-branch + GA deferred no propagado |
| **E** | **Model IDs stale `Opus 4.7` / `Haiku 4.5` corto** | ~15 archivos (agents, rules, templates, learnings) | Modelo actual = `claude-opus-4-8` / `claude-haiku-4-5-20251001` |
| **F** | **Vocabulario muerto `outcomes`/`atomics`/`PI`/`sprint`/`04-tickets`** | checkpoint-protocol, PI/sprint templates, ticket-template, varios ADR | Consolidación SDD 4-ejes (2026-05-28) no propagada |

Y **2 gaps sistémicos de gate** (Critical Rules nuevas no cableadas en templates):
- **Critical Rule #37 (DoD live-verify)** ausente de: `07-merge-template.md`, `04-validators-template.yaml`, `checkpoint-template.md`, `T-result-template.md`, `T-review-template.md`. Es el vector exacto del caso `nicolify-r0-shell` reabierto.
- **Critical Rule #33 (anti-orphan CONN)** ausente de `03-arch-template.md`.

---

## Quick wins (bajo riesgo, alto impacto)

Cambios mecánicos, sin criterio de negocio, alto payoff. Aplicables en batch.

| # | Issue | Archivo(s) | Cambio concreto | Risk | Effort |
|---|---|---|---|---|---|
| QW-1 | **Comment antes de `---` rompe registro silencioso de skill** ("Agent type not found") | `.claude/skills/handoff/SKILL.md`, `.claude/skills/worktree-protocol/SKILL.md` | Mover `<!-- voseo-allowed -->` a DESPUÉS del cierre del frontmatter; `---` debe ser línea 1 absoluta ✅ VERIFICADO (ambos tienen comment en línea 1) | Bajo (fix) / Alto (estado actual) | trivial |
| QW-2 | **contract-guard.js no-operativo en worktree `luana-vitalia`** | `.claude/hooks/contract-guard.js` línea 162 | Reemplazar `repoMarker = '/luana-platform/'` por normalización agnóstica: `process.env.CLAUDE_PROJECT_DIR \|\| git rev-parse --show-toplevel` ✅ VERIFICADO (hardcode confirmado; el hook está silencioso en este worktree) | Alto (estado actual) | bajo |
| QW-3 | **Cap de líneas overlay incorrecto (200 vs 150)** | `.claude/hooks/claude-md-overlay-check.sh` línea 83 | Cambiar `-gt 200` → `-gt 150` (cap real del brand overlay) | Medio | trivial |
| QW-4 | **Instrucción bootstrap cita template inexistente** | `.claude/hooks/claude-md-overlay-check.sh` L74, `.claude/rules/claude-md-overlay.md` L33, `docs/rules-detail/claude-md-overlay.md` L104 | Corregir `_pm-brand-template/_OVERLAY-template.md` → `.claude/skills/_pm-brand-template/SKILL.md` (template no existe ✅ VERIFICADO) | Alto (bootstrap) | bajo |
| QW-5 | **Cobertura BE inconsistente 60% vs 43%** | `docs/specs/templates/03-arch-template.md` L90 | `60% del módulo` → `43% workspace threshold` (alinear con AGENTS.md) | Medio | trivial |
| QW-6 | **Model IDs stale `Opus 4.7`/`Haiku 4.5`** (batch global) | 5 agents (architect-orch, auditor-{agentic,backend}, builder-{agentic,backend}), `git-haiku-delegation.md` + ref, `commit-push`, `pase-produccion`, templates `T-{handoff,result,review}`, `REVIEW-final`, ADR-001/004/007 bitácoras, `_CLAUDE-original-backup` (13 ocurrencias) | Replace `Opus 4.7`→`claude-opus-4-8`, `Haiku 4.5`→`claude-haiku-4-5-20251001`; Co-Authored-By footers → `Claude Opus 4.8 (1M context)` | Bajo | bajo |
| QW-7 | **`04-tickets-template.yaml` no existe — citado como SSoT** | `hotfix-repro-mandatory.md` (stub+detail), `story-closure-gate.md` (detail), ADR-006, `auditor-{backend,agentic,frontend}.md`, architect-agentic, ticket-states.md | Reemplazar todas las citas por `06-tickets-template.yaml` (el real ✅ VERIFICADO) | Medio | bajo |
| QW-8 | **Container legacy `visionarias_*`** | builder-{backend,agentic}, copilot-expert, metrics-expert (`visionarias_redis`→`luana_redis_dev`), data-storyteller, debugging refs, T-handoff/ticket templates | Replace por `luana-{brand}-backend-dev` / `luana-dev-{brand}_backend_dev-1` / `luana_redis_dev` según convención real | Alto (commands fallan) | bajo-medio |
| QW-9 | **`LITELLM_PROXY_ENABLED` citado como flag activo (removido PI-12 S1 T-5)** | `tdd-mandatory.md` L20, `anti-default-flip-audit.md` L7 (cardinal), `architect-agentic` L211, `architect-be`, `auditor-agentic` L250 | Quitar de la lista de flags activos (mantener solo en tabla histórica) | Bajo | bajo |
| QW-10 | **Typo `### Stado`** | `docs/specs/templates/03-arch-template.md` L113 | `Stado` → `Estado` | Nulo | trivial |
| QW-11 | **`shell-routes.ts` path con subdir `routing/` inexistente** | `.claude/skills/nicolify-design-system/SKILL.md` L151, `vitalia-design-system/SKILL.md` L66, `vitalia/CLAUDE.md` L81 | `lib/routing/shell-routes.ts` → `lib/shell-routes.ts` (✅ VERIFICADO: existe sin `routing/`) | Medio | trivial |
| QW-12 | **WIP cap divergente developed/reviewing (≤2 vs ≤1 canónico)** | `checkpoint-template.md` L47-48, pm-comunify, pm-lupulo, pm-inmoflow, pm-retailly, pm-saasora (todos ≤2) | Cambiar a ≤1 (CLAUDE.md SDD Level 3 + story-closure-gate WIP cap v2 son SSoT) | Medio | bajo |
| QW-13 | **`grep-bot` se auto-identifica "Nicolify Grep Bot"** | `.claude/agents/grep-bot.md` L22 | `Nicolify Grep Bot` → `Luana Grep Bot` | Alto (brand confusion) | trivial |
| QW-14 | **`version: 1.0.0` frontmatter inválido CC-2026** | `.claude/skills/git-manager/SKILL.md`, `pase-produccion/SKILL.md` | Eliminar campo `version` del frontmatter | Bajo | trivial |
| QW-15 | **Verdict math omite categorías nuevas (CHANGES_REQUESTED no auto-fire)** | `auditor-agentic.md` (Cat 16 Connectivity), `auditor-backend.md` (Cat 13 Connectivity), `auditor-frontend.md` (Cat 16 Visual fidelity) | Agregar las categorías a sus bloques FAIL conditions | Medio | bajo |
| QW-16 | **Glob frontmatter nunca matchea (rules no auto-cargan)** | `master-data.md` (5 globs), `currency-handling.md`, `sales-agent-brand-voice.md`, `form-runtime-array.md`, `analytics-metrics.md`, `backend-migrations.md`, `offer-catalogs.md` | Prefijar con `**/` y corregir paths a layout multibrand/core real | Medio-Alto (rule silenciosa) | bajo |
| QW-17 | **INDEX.md `migration-plan.md` roto** | `docs/process/INDEX.md` L9 | Eliminar fila o apuntar a `lifecycle.md § 8 Roadmap` | Medio | trivial |
| QW-18 | **ADR-006 `04-tickets-template` → en realidad apunta a artefacto distinto** | `docs/architecture/luana-platform/ADR-006-story-closure-gate.md` | `04-tickets-template.yaml` → `06-tickets-template.yaml` | Medio | trivial |
| QW-19 | **ADR-011 cita `00-checkpoint-template.md` (no existe)** | `ADR-011-bugfix-story-type.md` L38 | `00-checkpoint-template.md` → `checkpoint-template.md` | Bajo | trivial |
| QW-20 | **Color duplicado `orange` (grep-bot = builder-frontend)** | `.claude/agents/grep-bot.md` | Cambiar a `cyan`/`gray` para distinguir en cockpit session map | Bajo | trivial |

---

## Skills (`.claude/skills/`)

### HIGH

| Issue | Archivo(s) | Cambio propuesto | Risk | Effort |
|---|---|---|---|---|
| **`git-manager` apunta a OTRO repo (`alpacapurpura/ap_sales_agent`) + usa branch `development` + `git pull`/`--force-with-lease` (viola git-safety.md)** | `git-manager/SKILL.md` | Retirar el skill (preferido) o reescribir completo para triple-branch + sync-from-main.sh. Mapear triggers git a `commit-push` vía skillOverrides | Alto | medio |
| **`pase-produccion` deployment model entero roto: merge `development`, `git fetch && merge` (prohibido), `deploy-prod.yml` inexistente (real: `cd-prod.yml`), imágenes `visionarias-*` legacy, `cd frontend` sin brand, `/test-all` skill inexistente** | `pase-produccion/SKILL.md` | Reescribir para triple-branch squash-merge + `.ci-parity-deferred` awareness + brands específicas + correct image names. Banner GA-deferred | Alto | alto |
| **`commit-push` branch `development` (no existe en triple-branch) en 7 líneas** | `commit-push/SKILL.md` | Replace `development` → `wip/{brand}` / `$(git branch --show-current)`; backtick-cmd injection para auto-detección | Alto (Haiku worker recibe constraint inválido) | bajo |
| **Paths single-brand pre-reorg masivos** (`backend/`, `shared/`, `cd backend && .venv/bin/...`) | `backend-expert`, `brand-expert`, `copilot-expert`, `metrics-expert`, `offer-expert`, `offer-type-preset-expert`, `sales-agent-expert`, `content-hunter`, `brand-offer-auditor` | Reemplazar por `cd {brand}/backend && ${WS}/.venv/bin/...` y core paths (`core/luana-core-*`, `luana_core_*` imports). Tabla remapping al top de cada skill | Alto | medio |
| **`tessl__*` HARD GATE auto-aborta** (`.tessl/` no existe ✅ VERIFICADO) | po-ux (L50-51), ux-agentico (L77-79), architect-fe (frontend-visual-fidelity § D0 inexistente), todos los que listan `tessl__` en `must_load_skills` | Reemplazar por `tessl-context` skill real + WebFetch fallback, o stubs. Aclarar que son tiles Tessl (CLI), no skills invocables | Alto | medio |
| **`brand-offer-auditor` referencia `references/audit-report-template.md` inexistente (Step 7 roto) + hardcoded Nicolify** | `brand-offer-auditor/SKILL.md` | Crear el template o inline; parametrizar brand con Step 0 detection | Alto | medio |
| **Hardcoded `Nicolify` cross-brand** (rompe vitalia/comunify/lupulo) | `brand-offer-auditor`, `content-hunter`, `data-storyteller` (título + Bowtie funnel), `playwright-expert` (título + body), `manychat-expert`, `git-manager`, `ux-disruptivo`, `ux-flow-architect` | Parametrizar `{brand}` o detección por worktree (`basename $(git rev-parse --show-toplevel)`) | Alto | medio |
| **`content-hunter` Phase 1 HARD GATE lee Python domain files inexistentes** | `content-hunter/SKILL.md` | Rediseñar Phase 1: pedir data al usuario o llamar Brand Studio API; quitar code-archaeology de skill de marketing | Alto | medio |
| **`ux-flow-architect` DEPRECATED banner + body 525 líneas activo + apunta a `/ux-ui` inexistente + agents nicolify-* inexistentes + paths sin brand** | `ux-flow-architect/SKILL.md` | `user-invocable: false` + stub redirect a `/po-ux`. No mezclar deprecated banner con body activo | Alto | medio |
| **Agents inexistentes referenciados** (`nicolify-ux-designer`, `nicolify-feature`, `nicolify-frontend`, `nicolify-ux-designer`) | `ux-disruptivo`, `ux-flow-architect`, `data-storyteller` | Reemplazar por `po-ux`/`builder-frontend` o eliminar Integration Notes | Alto | bajo |
| **PM bootstrap brands: faltan secciones protocol** (Auto-chain rule, Fase F.3 cap ledger, Brand docs schema R1+R2+R3, Capability inventory post-merge, Output protocol chris-input) | `pm-comunify`, `pm-fitflow`, `pm-fixia`, `pm-guestly`, `pm-inmoflow`, `pm-retailly`, `pm-saasora` (severidad variable; pm-retailly más severo: sin tabla de Comandos completa) | Backport desde `pm-vitalia` (referencia mantenida) sustituyendo brand slug. Considerar script de sincronización cross-brand | Alto (handoffs textuales, merges sin cap update, docs schema sin enforcement) | medio |
| **`metrics-expert` paths analytics todos a `backend/src/modules/analytics/` (real: `core/luana-core-analytics-engine/`) + `visionarias_redis`** | `metrics-expert/SKILL.md` | Header multibrand + remapping a core engine paths + `luana_redis_dev` | Alto | medio |
| **`po`/`po-ux` bootstrap lee `ideas-pool.yaml` inexistente en brands activas** | `po/SKILL.md` L87, `po-ux/SKILL.md` L138 | Reemplazar por `ls {brand}/docs/product/stories/` (state=idea) | Medio | bajo |

### MEDIUM / LOW (agrupados)

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`architect/SKILL.md` 916 líneas (~2x guía 500); auditor 738; dev-team 810; po-ux 540** | architect, auditor, dev-team, po-ux | Extraer templates inline (04-validators, 05-guidelines, dispatch-plan, CHECKPOINTS, self-fix table, builder prompts) a `references/` | Medio (refactor) | medio |
| **Live-verify hardcoded vitalia** | dev-team (L806-811), po (L354), po-ux (L540), auditor (live-verify section) | Parametrizar `make dev-app-{brand}` + ref a `definition-of-done-live-verify.md` | Medio (nicolify falla auth) | bajo |
| **`audit_iterations`/`self_fix_iter` caps inconsistentes (3/4/5 mezclados)** | `auditor/SKILL.md` (L244/285/330/408/636) | Resolver a audit_iterations=4, self_fix_iter=5; auditar contra `auditor-self-fix-policy.md` SSoT | HIGH (escalación impredecible) | bajo |
| **`chrome-devtools-verify` no referencia DoD gate (Critical #37)** | chrome-devtools-verify/SKILL.md | Sección "DoD Live Verification Gate" + requerir `dod_evidence` | Medio | bajo |
| **`_pm-brand-template` status nicolify stale + skill-name placeholder hardcoded + Auto-chain rule solo en comentario** | `_pm-brand-template/SKILL.md` | Pointer a PORTFOLIO; `{{PM_SKILL_NAME}}` placeholder; embeber Auto-chain verbatim | Medio | bajo |
| **Voseo sin magic comment** | brand-expert (L372-377), nicolify-design-system, README brands | Agregar `<!-- voseo-allowed -->` o convertir a tuteo | Bajo (hook flag) | trivial |
| **`tessl-context` description vacía en frontmatter** | tessl-context/SKILL.md | Agregar description para discovery/auto-trigger | Bajo | trivial |
| **Broken pointers varios** (`docs/mejoras-proceso/to-do.md`, `references/data-viz-conventions.md`, `references/audit-report-template.md`, `vitalia/.claude/skills/...` paths) | copilot-expert, data-storyteller, brand-offer-auditor, nicolify-design-system | Crear archivos o corregir paths | Medio | bajo |
| **`pm/SKILL.md` alias puro con overhead opus** | pm/SKILL.md | `context: fork` apuntando a pm-luana, body solo invocación | Bajo | bajo |
| **manychat-expert: paths nicolify rebuild inexistentes + context7 MCP sin fallback** | manychat-expert/SKILL.md | Marcar paths "(a crear en R0)"; fallback WebSearch si context7 ausente | Medio | bajo |
| **`pm-vitalia`/`pm-nicolify` gaps menores** (R4 ausente en header schema, `00-story.md`/`00-research.md` ambigüedad, Sara no en description nicolify, label "master orquestador" stale) | pm-vitalia, pm-nicolify | R1+R2+R3 → R1+R2+R3+R4; agregar Sara a triggers nicolify; corregir label alias | Medio | bajo |

---

## Agents (`.claude/agents/`)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`tessl__*` en `skills:` frontmatter = Step 0 HARD GATE auto-aborta cada invocación** (`.tessl/` no existe ✅ VERIFICADO) | builder-agentic, builder-backend, architect-orchestrator, auditor-agentic, auditor-backend, auditor-frontend (8 skills tessl distintos) | Crear stubs SKILL.md redirigiendo a WebFetch canónico, O fallback en prompt body cuando invocación falla. Sin esto, **ningún builder/auditor con tessl en skills arranca** | Alto | medio |
| **`.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` inexistente (gate PII mandatory)** | builder-backend L96, auditor-backend L88 | Crear `.claude/rules/pii-sanitisation.md` stub apuntando al patrón `response_model` de backend-ddd.md | Alto (Cat 7 PII sin referencia) | bajo |
| **Container legacy `visionarias_postgres`/`visionarias_brain_dev`/`visionarias_logs` en migration step** | builder-backend L277-280, builder-agentic L277-280 | Replace por `luana-{brand}-backend-dev` + postgres brand-specific | Alto (migration test "container not found") | bajo |
| **Hand-off paths sin brand prefix** (`docs/product/stories/{id}/03-arch-*.md`) | architect-be (L135), architect-fe (L120), architect-agentic (Step 4) | Prefijar `{brand}/docs/product/stories/{id}/` — sub-agent escribe a path wrong, orchestrator Step 4 no encuentra artifact | Alto | bajo |
| **gate-runner spawn pasa `test-frontend` deprecated en vez de `test-fe-{brand}`** | builder-frontend.md L365 | `test-frontend` → `test-fe-${BRAND}` | Alto (gate-runner rehúsa/silencia) | bajo |
| **`grep-bot` self-id "Nicolify" + `Sonnet Explore` subagent inexistente** | grep-bot.md L4/19/22/26 | "Luana Grep Bot"; escalación → invocar skill `explore-module` | Alto | bajo |

### MEDIUM / LOW

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **Ningún agent tiene `isolation: worktree`** (✅ VERIFICADO) — write-capable builders en hub multi-sesión arriesgan contaminación de índice | builder-{backend,frontend,agentic} (HIGH para writers), auditores (Carril A escribe), architect, context-builder | Agregar `isolation: worktree` (prioridad: builder-agentic maxTurns:150 primero). Ver Roadmap CC-2026 | Bajo (aditivo) / resuelve hazard real | bajo |
| **Inconsistencia ESLint scope** (builder `eslint src/ --cache` vs gate-runner `eslint .`; gate-runner test-fe-* omite jscpd/knip/madge/npm-audit del spec 8-gate de builder) | builder-frontend.md, gate-runner.md | Alinear test-fe-{brand} al spec completo 8-gate o crear `test-fe-full-{brand}` | Alto (verde parcial 3/8 vs 8/8) | medio |
| **Broken pointers** (`scripts/e2e-preflight.sh` ✅ MISSING, `dev-app.vitalia.com`→`dev-app.vitalialat.com`, `docs/etl/extraction-contract.md` ✅ MISSING, `docs/core-modules/{module}.md`) | builder-frontend, context-builder, architect-orchestrator | Crear scripts/guards `if exists` o corregir dominio | Medio | bajo |
| **Verdict math omite categorías nuevas** (ver QW-15) | auditor-{agentic,backend,frontend} | Agregar Cat Connectivity/Visual a FAIL conditions | Medio | bajo |
| **`</output></output>` doble tag** | architect-orchestrator, auditor-agentic | Eliminar tag extra | Bajo | trivial |
| **Artifact naming conflict CONTRACT.md vs 03-arch.md** | architect-orchestrator.md | Alinear a `03-arch.md` (downstream auditors lo esperan) | Medio | bajo |
| **MCP tools referenciados sin server configurado** (`mcp__clerk__*`, `mcp__tessl__*`, `mcp__google-dev-knowledge__*`, `mcp__shopify-dev-mcp__*`) | architect-orchestrator L163-166, context-builder | Guard "if MCP available else WebFetch fallback" | Medio | bajo |
| **`context-validator` maxTurns:60 insuficiente para módulos grandes (copilot+analytics)** | context-validator.md | Subir a 80 | Bajo (verdict truncado) | trivial |
| **DoD live-verify generaliza solo vitalia** | auditor.md live-verify section | `make dev-app-{brand}` | Medio | bajo |

---

## Rules (`.claude/rules/` + brand rules + `docs/rules-detail/`)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`backend-migrations.md` cita `docs/domains/migrations.md` inexistente (Clone DB workflow roto)** | `.claude/rules/backend-migrations.md` L22 | Crear el runbook o corregir path | Alto | bajo |
| **`currency-handling.md` glob nunca matchea `format-money` (real en `core/@luana/format/`)** | `.claude/rules/currency-handling.md` | Fix glob a `core/@luana/format/src/format-money*` + `**/backend/src/modules/*/analytics/` | Alto (rule silenciosa en código crítico de display) | trivial |
| **`master-data.md` 5 globs single-brand nunca matchean** | `.claude/rules/master-data.md` | Globs multibrand-aware (`core/luana-core-platform/`, `**/frontend/src/hooks/useTenantLocale.ts`, `**/frontend/src/lib/format/`) | Alto | bajo |
| **`sales-agent-brand-voice.md` glob `backend/src/modules/sales_agent/` nunca matchea + personality path roto** | `.claude/rules/sales-agent-brand-voice.md` L2 | Globs a `**/backend/src/modules/*/sales_agent/` + `**/luana_core_brand_studio/domain/personality.py` | Alto | bajo |
| **`anti-duplication.md` inventario con paths erróneos** (`tenant_billing_config_repository` en billing→es observability; `_resolve_tenant_currency` no existe→`FXResolver.default()`) | `.claude/rules/anti-duplication.md` L24-25 | Corregir paths del inventario SSoT (la rule existe para PREVENIR duplicación; paths rotos causan recreación) | Alto | bajo |
| **`analytics-metrics.md` engine paths incompletos + Growth Studio FE path inexistente** | `.claude/rules/analytics-metrics.md` | Corregir `application/services/stage_services/constants.py` + `channel_registry.py` (1 nivel arriba); marcar growth-studio FE pendiente | Alto | bajo |
| **`architectural-fitness.md` cita `/test-backend`, `/test-all`, `make arch-test` DEPRECATED** | `.claude/rules/architectural-fitness.md` L30 | `test-{brand}` (gate-runner) + `make ci-parity`; agregar `core/tests/architecture/**` al glob | Alto (CI commands inválidos) | bajo |
| **`offer-catalogs.md` cita `biz_type_catalog.py`+`ladder_hints_catalog.py` inexistentes (glob falla)** | `.claude/rules/offer-catalogs.md` | Quitar `biz_type` (es enum en luana-core-platform), `ladder_hints`→`offer_ladder_hints`; corregir "7 catalogs" (son 8) | Alto | bajo |
| **`step-0-worktree.md`: enforcement matrix omite EFÍMERO hotfix → HARD REFUSE legítimo** | `.claude/rules/step-0-worktree.md` | Agregar fila EFÍMERO hotfix brand X = OK (NB: comment-before-`---` aquí es rule, no skill — menor severidad que handoff/worktree-protocol) | Medio | bajo |
| **brand rules con paths inexistentes** (comunify creator-funnels: `voice_profile/`→`brand/voice_cloning/`, `elevenlabs/`, `validators/ladder_integrity.py`; lupulo kds + nicolify agent-revenue: módulos placeholder descritos como implementados) | `comunify/.claude/rules/creator-funnels.md`, `lupulo/.claude/rules/kds-integration.md`, `nicolify/.claude/rules/agent-revenue-engine.md` | Corregir paths comunify; banner `> ASPIRACIONAL — bootstrap pendiente` para lupulo + nicolify | Alto | medio |
| **`vitalia/.claude/rules/hipaa-lite.md` 3 paths monolito stale** (`shared/agent_observability/`, `compliance/phi_fields.py` mal anidado, `shared/compliance/`) + cron name mismatch + voseo en string user-facing | vitalia/.claude/rules/hipaa-lite.md | Corregir a `core/luana-core-observability/`, `compliance/domain/phi_fields.py`, `core/luana-core-compliance/`; cron→`audit_log_retention_sweep_monthly`; tuteo | Alto | medio |
| **`docs/rules-detail/auditor-downstream-regression.md` cita `.claude/rules/references/` (dir inexistente) 5×** | docs/rules-detail/auditor-downstream-regression.md | Corregir a `docs/rules-detail/auditor-downstream-targets.md`; ADR-001 name fix | Alto (auditor no carga tabla SSoT A-I) | bajo |
| **`docs/rules-detail/auditor-self-fix-policy.md` dos versiones de caps en conflicto (v4.1 tabla 3/4 vs v4.2 sección 5/4) + árbol v4.1 obsoleto como principal** | docs/rules-detail/auditor-self-fix-policy.md | Marcar tabla/árbol v4.1 `~~OBSOLETO~~`; v4.2 como SSoT (self_fix=5, audit=4) | Alto | bajo |
| **`docs/rules-detail/parallel-safety.md` D4 contradice M12/ADR-009 (canónico "rota" vs "ESTABLE")** | docs/rules-detail/parallel-safety.md L15 | Corregir celda Branch CANÓNICO a `wip/{brand}` ESTABLE; quitar frontmatter `globs` residual | Alto (rota branch canónico) | bajo |

### MEDIUM / LOW (agrupados)

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`definition-of-done-live-verify.md`: scripts inexistentes** (`scripts/dev-app-up.sh` ✅ MISSING, `scripts/cloudflared-setup.sh` ✅ MISSING) + learning renombrado + layers 2/4/6 pendientes | `.claude/rules/definition-of-done-live-verify.md` L143/146/111 | Crear scripts o corregir refs; agregar frontmatter glob `**/07-merge.md,**/checkpoint.md`; implementar layers | Alto (gate live bloqueado) | medio |
| **`e2e-testing.md` + `definition-of-done-live-verify` citan `scripts/e2e-preflight.sh` ✅ MISSING** | e2e-testing.md L15, builder-frontend, playwright-expert | Crear script o reemplazar por checks inline (`curl localhost:300X/health`) | Alto | bajo |
| **`etl-extraction-contract.md` + `data-reliability.md` citan `docs/etl/extraction-contract.md` ✅ MISSING + make targets inexistentes** | etl-extraction-contract.md L16, data-reliability.md | Corregir a `core/luana-core-analytics-engine/docs/extraction-contract.md`; marcar make targets TBD | Alto | bajo |
| **`form-runtime-array.md` glob sin `**/` nunca auto-triggea** | form-runtime-array.md | Agregar `**/` prefix | Medio | trivial |
| **`debugging.md` container names `luana-{brand}-backend-dev` vs real `luana-dev-{brand}_backend_dev-1`** | debugging.md | Auditar naming real del compose y alinear (afecta también docker-dev-multibrand.md, AGENTS.md) | Alto (debug commands fallan) | bajo |
| **`github-actions-deferred.md` + `git-safety.md` no mencionan sentinel `.ci-parity-deferred` (✅ EXISTE)** | github-actions-deferred.md (stub+detail), git-safety.md | Documentar el sentinel + comportamiento ADVISORY dev-only + cross_check_3 sigue HARD + scripts test-{brand}.sh inexistentes | Alto (confunde gate activo) | medio |
| **`git-haiku-delegation.md` model IDs stale** (ver QW-6) | git-haiku-delegation.md + haiku-delegation.md ref | Update Opus 4.7→4.8, Co-Authored-By | Bajo | bajo |
| **`tenant-isolation.md` NO captura prohibición Clerk org como tenant_id (vuln sistémica 35 archivos fixed 2026-06-01)** | `.claude/rules/tenant-isolation.md` | Sección "FE: Clerk tenant source" prohibiendo `useAuth().orgId`, dirigir a `useTenantId()`; ref arch-test + learning. Restringir glob `**/*`→`**/*.{py,ts,tsx}` | Alto (otras brands sin arch-test pueden repetir) | bajo |
| **`copilot-{observability,resilience}.md` description genérica idéntica + glob overlap** | copilot-observability.md, copilot-resilience.md | Diferenciar descriptions (observabilidad vs runtime); documentar co-activación intencional | Bajo | trivial |
| **descriptions genéricas "Stub — invoca X skill"** | backend-quality, data-reliability, etl-extraction-contract, currency-handling | Enriquecer con keywords de trigger | Bajo (auto-trigger impreciso) | trivial |
| **`paradigm-arquitectura.md` sin frontmatter (no auto-attach pese a Critical #36)** | paradigm-arquitectura.md | Agregar frontmatter description | Bajo (carga vía CLAUDE.md igual) | bajo |
| **`anti-duplication-refining.md` describe nicolify "frozen" (es skeleton rebuild activo)** | anti-duplication-refining.md L18 | Actualizar a "skeleton post-reset, rebuild en curso" | Medio (prior-art scan descarta nicolify) | bajo |
| **`brand-docs-schema.md` R3 cita `outcomes` (muerto) + título "R1+R2+R3" pero documenta R4** | `.claude/rules/brand-docs-schema.md` L37, detail file | `outcomes`→`capabilities/stories`; título → R1+R2+R3+R4; agregar `releases/` al schema | Medio | bajo |
| **`docs/rules-detail/` model IDs + outcomes + Critical Rules table 21 reglas atrás + `.tessl/RULES.md` ref** | `_CLAUDE-original-backup.md`, `_AGENTS-original-backup.md` | Banner "⚠️ LEGACY BACKUP" + update Critical Rules table o pointer a CLAUDE.md | Medio (cargados on-demand) | medio |
| **`docs/rules-detail/anti-default-flip-audit.md` enforcement layers citan tests inexistentes** | docs/rules-detail/anti-default-flip-audit.md L112-113 | Marcar `⏳ PENDING` o crear tests | Medio | bajo |
| **`docs/rules-detail/{learning-capture,spanish-glossary,story-closure-gate,step-0-worktree}.md` broken pointers + frontmatter residual** | varios rules-detail | Hooks inexistentes → crear o marcar ⏳; eliminar frontmatter `globs` residual; `04-tickets`→`06-tickets`; clarificar MEMORY.md path | Medio | bajo |
| **`nicolify/.claude/rules/shell-feature-architecture.md` delega ADR-vitalia-003 sin ADR propio + omite tab `sara-*`** | nicolify shell-feature rule | Crear ADR-nicolify-003 o nota explícita de delegación; agregar `sara-*` al scope | Medio | bajo |
| **`vitalia/.claude/rules/shell-*` paths a stories archivadas + scope `config-*`/`plataforma-*` divergente + layer 5 TBD** | vitalia shell-feature-architecture-mandatory, shell-mockup-per-component | Corregir paths a `docs/archive/2026/stories/`; alinear scope a IDs reales | Medio | bajo |

---

## Hooks (`.claude/hooks/` + git-hooks + settings.json)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **contract-guard.js no-operativo en worktree (ver QW-2)** ✅ VERIFICADO | `.claude/hooks/contract-guard.js` L162 | Normalización agnóstica al nombre del worktree | Alto | bajo |
| **claude-md-overlay-check.sh bootstrap cita template inexistente (QW-4) + cap 200 vs 150 (QW-3)** | `.claude/hooks/claude-md-overlay-check.sh` | Ver quick wins | Alto/Medio | bajo |
| **pre-commit: PII scanners inexistentes degradan a WARNING** (`backend/scripts/scan_seed_pii.py`, `scan_goldens_pii.py`) | `scripts/git-hooks/pre-commit` §8-9 | Crear scanners o corregir path; PII gate de eval/goldens NO operativo | Alto | medio |
| **pre-commit: dos "Section 13" (collision) + machinery section usa `python3` sistema (no venv) + 15.5 sin guard `-x` venv** | `scripts/git-hooks/pre-commit` L1454/1988/1989/1807 | Renumerar a Section 18; usar `${REPO_ROOT}/.venv/bin/python`; agregar guard `-x` | Medio | bajo |

### MEDIUM / LOW

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **contract-guard offer-catalogs regex cubre 3/8 catálogos** | contract-guard.js | Expandir a `(archetype\|value_level\|format\|section\|variant\|biz_type\|ladder_hints\|preset)_catalog\.py$` | Medio (4 catálogos sin reminder bump version) | bajo |
| **settings.json: Stop hook sin análogo StopFailure; deny permissions paths legacy single-brand; PreToolUse vacío** | `.claude/settings.json` | Agregar StopFailure (mirror validate_session_close); deny `**/node_modules/**` etc.; documentar PreToolUse | Medio | bajo |
| **pre-push: brands hardcoded `vitalia nicolify comunify lupulo`; cross_check_4 sin TODO rastreable** | `scripts/git-hooks/pre-push` L124 | Dynamic brand discovery (find capabilities/); TODO con criterio Fase 5 | Bajo (las 6 brands sin caps se saltean igual) | bajo |
| **pre-commit/pre-push bidirectional code duplicado (§5d vs §4d)** | pre-commit, pre-push | Extraer a `scripts/validate_bidirectional_hook.sh` compartido | Bajo | medio |
| **auto-chain-detect.sh fallback sed lossy sin jq; learning-detect.sh voseo + ref a script legítimo como "prohibido"** | auto-chain-detect.sh, learning-detect.sh | Warning si jq ausente; tuteo; reformular advertencia capture.sh | Bajo | bajo |

---

## Cockpit (`tools/luana-cockpit/`)

### HIGH / MEDIUM

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **README path absoluto machine-specific `/home/chalreme/.claude/plans/...`** (contradice sección "portabilidad") | tools/luana-cockpit/README.md L303 | Reemplazar por pointer a memory `cockpit-luana-state.md` | Medio (404 en otra máquina) | trivial |
| **README staleness: 19 vs 20 routes (falta /api/sessions ADR-009), 12 vs 18 lib modules, ~67 vs 10 test files, "Configurar" como 6º agente, "7 agentes" en /arquitectura** | tools/luana-cockpit/README.md | Actualizar tablas API/lib/tests; aclarar Configurar=zona no agente; corregir conteos | Medio | bajo |
| **README "Pendiente Chris ratificación" mezcla resuelto/abierto; v0.7 roadmap lista feature ya implementada (BrandSwitcher)** | tools/luana-cockpit/README.md | Auditar items; remover implementados | Bajo | bajo |
| **Voseo sin magic comment (hook puede flaggear)** | tools/luana-cockpit/README.md | `<!-- voseo-allowed: internal tooling README -->` | Bajo | trivial |

---

## Process (`docs/process/`)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`checkpoint-protocol.md` resume protocol entero apunta a `docs/projects/active/PI-{N}/...` (estructura inexistente) + `git push origin development`** | docs/process/checkpoint-protocol.md L30-38/74-93/131/142-164 | Reescribir paths a `{brand}/docs/product/stories/{id}/`; eliminar niveles PI/sprint; `development`→`wip/{brand}` | Alto (resume falla silenciosamente) | medio |
| **`cicd-multibrand-runbook.md`: `git pull` "válido aquí" (viola git-safety SIN EXCEPCIÓN) + asume GA activo (deferred) + K8s aspiracional** | docs/process/cicd-multibrand-runbook.md L45 | Reemplazar git pull por fetch+reset; sección "0. Estado deferred"; disclaimer K8s vs Docker Compose+tunnel real | Alto | medio |
| **`contributing.md`: workflow PR multi-dev con reviews + branch `feat/` + `.claude-shared/` sync desde "AISALESHT" (paths inexistentes) + `core/shared/`** | docs/process/contributing.md | Reescribir para triple-branch solo-operador; eliminar `.claude-shared/` sync; `core/shared/`→`core/luana-core-*/` | Alto | medio |
| **`git-workflow-multibrand.md`: Workflow 1 invierte ADR-009 (worktrees default vs hub) + `# AUTO DEPLOY` falso (GA deferred) + paths `/home/chalreme/` hardcoded** | docs/process/git-workflow-multibrand.md | Reordenar hub-first; corregir comments deploy; `WS=$(git rev-parse...)` | Alto | medio |
| **`github-environments-setup.md`: presenta staging auto-deploy + K8s como operativos (GA deferred, infra real = VPS+docker-compose+CF tunnel)** | docs/process/github-environments-setup.md | Banner "⚠️ deferred"; nota arquitectura VPS-per-brand ratificada 2026-05-16 | Alto | bajo |
| **`parallel-sessions-protocol.md`: `new-session.v2.sh` inexistente (solo `new-session.sh`); D4/D9 contradicen ADR-009; mecanismos A-N "pending" pero implementados** | docs/process/parallel-sessions-protocol.md | Corregir filename; banner ADR-009 supersede; auditar status mecanismos | Alto/Medio | medio |
| **`pm-redesign-2026-05.md`: Punto 1 tabla 7-estados (superseded por Punto 4 10-estados) + `/architect`=Sonnet (debe Opus) + ADR-005 citado para closure-gate (es ADR-006) + paths sin brand** | docs/process/pm-redesign-2026-05.md | Banner SUPERSEDED en Punto 1; corregir model + ADR ref + paths | Alto (vocabulario + model routing contradictorios) | medio |
| **`process-improvement-handoff-2026-05-05.md` + `-investigation.md`: paths `docs/projects/active/PI-12/` + `/home/chris/AISALESHT/` inexistentes; Nicolify-scoped proposals** | docs/process/process-improvement-handoff-*.md | Banner "HISTORICAL — read-only archaeology"; notas de implementación (R3/R18 ya hechos) | Alto (mandatory reads fallan) | bajo |

### MEDIUM / LOW

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`lifecycle.md` §9 punch-list ⏳ contradice §8 Fases DONE; scripts `generate_release_notes.py`/`validate_chris_input.py` ✅ MISSING; F2.yaml refs stale; port 4002 vitalia-specific; "67 caps" snapshot stale** | docs/process/lifecycle.md | Auditar items vs estado; convertir abiertos a stories; generalizar port; reframe snapshot | Alto (false completion signal) | medio |
| **`learnings.md` model IDs/qwen legacy en entries pre-reorg + falta entries June 2026 (Clerk org fix, DoD cement, ci-parity)** | docs/process/learnings.md | Tombstone banners en entries legacy (append-only, NO editar); agregar entries June 2026 | Medio | bajo |
| **`release-protocol.md` cita `scripts/generate_release_notes.py` ✅ MISSING** | docs/process/release-protocol.md L178/253 | Marcar "(futuro — no implementado)" o crear stub | Medio | bajo |
| **`cockpit-permissions.md`: `type (func/tech)` no coincide con story types (ui/service/agentic/bugfix); 'atomics/change_log' (atomics muerto)** | docs/process/cockpit-permissions.md L78/121/154 | Actualizar a story types ADR-011; `atomics`→`scenarios[]` | Medio | bajo |
| **`ticket-states.md`: `04-tickets.yaml`→`06-`; qwen-opencode + Opus 4.7; 12 estados ticket vs 10 macro sin aclarar relación** | docs/process/ticket-states.md L4/105/94-101 | Corregir filename; model IDs; párrafo de contexto ticket-vs-story states | Medio | bajo |
| **`warp-multibrand-handbook.md`: §3.4/§0 multi-lane worktrees como default (ADR-009 = hub); git fetch+merge manual vs sync-from-main** | docs/process/warp-multibrand-handbook.md | Banner ADR-009; topología hub-first; usar sync script | Alto/Medio | medio |
| **`worktree-protocol-v2-plan.md`: "plan ejecutable" pero implementado (histórico); `scripts/test_no_subagent_worktree.sh` ✅ MISSING; branches obsoletas inexistentes** | docs/process/worktree-protocol-v2-plan.md | Banner "IMPLEMENTADO (histórico)"; crear test o nota | Medio | bajo |
| **`docker-dev-multibrand.md` container naming inconsistente + paths hardcoded** | docs/process/docker-dev-multibrand.md | Auditar naming real; `${WS}` | Medio | bajo |
| **`INDEX.md`: `migration-plan.md` roto (QW-17) + M1-M8 (real M1-M14) + índice incompleto** | docs/process/INDEX.md | Corregir + expandir tabla | Medio | bajo |
| **`spec-mapa-funcional.md` no cross-linkea Critical #37 / `story-closure-gate.md` minor staleness en line-number cites** | spec-mapa-funcional.md, story-closure-gate.md | Cross-link DoD gate; reformular cites de línea exacta | Bajo | bajo |
| **`chris-input-protocol.md` path plan hardcoded + lista skills incompleta** | chris-input-protocol.md L6/222 | Quitar path; `pm-vitalia,pm-luana`→`pm-{brand},pm-luana` | Bajo | trivial |
| **`release-procedure-v0.1.0.md` count 33 vs 27 + scope solo core (no brands)** | release-procedure-v0.1.0.md | Banner "v0.1.0 one-time, superseded by release-protocol.md" | Bajo | bajo |

---

## Templates (`docs/specs/templates/`)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **DoD live-verify (Critical #37) ausente de templates clave** | `07-merge-template.md` (§6 + REFUSE gate), `04-validators-template.yaml` (validator live_verify), `checkpoint-template.md` (campos dod_live_verified/dod_env/dod_evidence), `T-result-template.md`, `T-impl-log-template.md`, `T-review-template.md` (+ Cat 14) | Agregar sección/campos con schema de `definition-of-done-live-verify.md`. **Es el vector del caso nicolify-r0-shell reabierto** | Alto (stories llegan a done sin evidencia live) | medio |
| **Anti-orphan CONN (Critical #33) ausente de 03-arch + Prior art audit ausente** | `03-arch-template.md` | Agregar `## Integration design (CONN)` (reachability/consumers/registration/home_cap) + `## Prior art audit` | Alto (islas a done sin detección) | bajo |
| **`04-validators-template.yaml`: scripts inexistentes (run_agent_evals, run_trajectory_eval, check_cost_budget, check_voice_fidelity, run_adversarial_suite, scan_cross_brand_mirror ✅ MISSING) + cmds sin brand/venv + port 3000** | docs/specs/templates/04-validators-template.yaml | Crear stubs o marcar "# MISSING create before use"; `cd {brand}/backend && ${WS}/.venv/bin/`; port→{brand_port}; agregar playwright_visual_scope | Alto (validators no corren) | medio |
| **`02-design-ui-template.md` DEPRECATED (po-ux produce 01-spec unificado, lo prohíbe explícitamente) + owner `/ux-ui` inexistente + paths rotos** | docs/specs/templates/02-design-ui-template.md | Banner DEPRECATED; owner → po-ux histórico; corregir paths (5-level, `frontend/src/lib/tokens.ts`→`core/@luana/design-tokens`) | Alto | bajo |
| **`PI-template.md` + `sprint-template.md` metodología muerta** (`docs/projects/` inexistente; PI/Sprint reemplazado por Release) + vocab `live`/`audit-passed` + qwen | docs/specs/templates/{PI,sprint}-template.md | Banner [DEPRECADO] → release-protocol.md/release-template.yaml; considerar mover a archive | Alto | bajo |
| **`ticket-template.yaml` legacy: `docs/projects/` + `visionarias_brain_dev` + falta v4.1 fields (brand/schema_version/must_load_skills/assignment) + tessl__ naming** | docs/specs/templates/ticket-template.yaml | Banner DEPRECATED → `06-tickets-template.yaml`; o backport v4.1 fields | Alto | bajo |
| **`T-handoff-template.md` resume/output paths `docs/projects/active/...` + `docker exec visionarias_brain_dev` + venv relativo + `make verify-migration-idempotency` inexistente** | docs/specs/templates/T-handoff-template.md | Corregir paths a `{brand}/docs/product/stories/`; container real; `${WS}/.venv/`; script path real | Alto (resume + migration gate fallan) | medio |
| **`story-{service,ui,agentic}.yaml`: falta cap_target/cap_change_type (mandatory desde idea); `status` ambiguo (capability vs story); path `{module}/` subfolder inexistente** | docs/specs/templates/story-{service,ui,agentic}.yaml | Agregar cap_target/cap_change_type; renombrar a capability_status; corregir Vive-en path; story-agentic: `state:` (no `status: planned`), agregar agent_owner/map_zone/map_box/release | Alto | medio |
| **`REVIEW-final-template.md` model `claude-opus-4-7` 2× + falta §Verificación live + `make dev` stale + hardcoded nicolify URL + vocab `live`/`ready-to-merge`** | docs/specs/templates/REVIEW-final-template.md | Model→4-8; sección DoD live; `make dev-app-{brand}`; vocab `reviewing→done` | Alto | medio |
| **`T-review-template.md`: faltan Cat 12 (cross-brand mirror), Cat 13 (CONN), Cat 14 (DoD live); cap 2 contradice v4.2; self-fix pre-v4.2** | docs/specs/templates/T-review-template.md | Agregar Cat 12/13/14; caps v4.2; 3-carril decision tree; model 4-8; path con brand | Alto | medio |

### MEDIUM / LOW

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **`00-story-template.md` relative links 5-level resuelven fuera de brand + PI/sprint/opportunity links rotos** | docs/specs/templates/00-story-template.md | Corregir a `../../{module}/`; quitar pi/sprint/opportunity (modelo Release) | Alto | bajo |
| **`01-spec-template.md` "Próximo paso" cita `/ux-ui`→`02-design-ui.md` (deprecado) + changelog stale** | docs/specs/templates/01-spec-template.md L331 | Reemplazar por "ya producido por /po-ux"; actualizar changelog v3/v4 | Alto | bajo |
| **`02-design-agentic-template.md` personas inexistentes + brand_voice_ssot relative + voseo sin comment** | docs/specs/templates/02-design-agentic-template.md L129-131 | Corregir a `lead-frio-impaciente-pe.yaml` o wildcard; voseo-allowed comment | Medio | bajo |
| **`dispatch-plan-template.md` falta DoD live-verify + caps stale (3 vs 4/5) + no menciona bugfix** | docs/specs/templates/dispatch-plan-template.md | Sección DoD gate; caps v4.2; nota bugfix opcional | Alto/Medio | bajo |
| **`release-template.yaml` falta `production_status` (eje despliegue v4) + shipped_gate_evidence** | docs/specs/templates/release-template.yaml | Agregar campos | Medio | bajo |
| **`05-guidelines-template.md` tessl__ IDs inexistentes + falta chrome-devtools-verify/DoD rule** | docs/specs/templates/05-guidelines-template.md | tessl__→tessl-context; agregar chrome-devtools-verify + definition-of-done-live-verify.md | Medio | bajo |
| **`06-tickets-template.yaml` model Opus 4.7 + state `draft` vs 10-estados + sprint/pi legacy fields** | docs/specs/templates/06-tickets-template.yaml | Model 4-8; aclarar ticket-state vs story-state; marcar sprint/pi DEPRECATED | Medio | bajo |
| **`T-impl-log-template.md`/`T-result-template.md` model stale + tessl__ + falta DoD section** | T-impl-log, T-result | Model 4-8; tessl pattern; sección DoD live-verify | Medio | bajo |
| **`00-research-template.md` hardcoded Nicolify + owner `/pm` ambiguo + frontmatter embebido** | docs/specs/templates/00-research-template.md | Brand-neutral; aclarar owner; mover YAML al top | Bajo | bajo |
| **`00-chris-input-template.md` voseo "invocá"** | docs/specs/templates/00-chris-input-template.md L51 | `invocá`→`usa`/`ejecuta` | Bajo | trivial |

---

## ADR (`docs/architecture/luana-platform/`)

### HIGH

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **ADR-001 status PROPOSED desde 2026-05-09 + prescribe 5-repos (real: monorepo = Alternativa D que el ADR rechaza) sin addendum** | ADR-001-luana-platform.md | Status→ACCEPTED + §8 Addendum documentando adopción monorepo (la divergencia arquitectónica más crítica, sin registrar en ningún ADR); related docs rotos | Alto | medio |
| **`00-overview.md` topology pre-reorg (core/copilot, core/shared) + 6 broken pointers (ARCHITECTURE.md, CONTRIBUTING.md, RELEASES.md, ADR-001 path, AISALESHT external)** | docs/architecture/luana-platform/00-overview.md | Topology actual (26 luana-core-*); corregir/eliminar links | Alto (onboarding wrong model) | medio |
| **`05-cross-repo-tooling.md` premisa entera (5-repo GitHub Org) nunca ejecutada + `/home/chris/AISALESHT/` + Sunday Playbook re-bootstrap** | docs/architecture/luana-platform/05-cross-repo-tooling.md | Banner SUPERSEDED (monorepo retenido) | Alto (Playbook crea org/repos fantasma) | bajo |
| **`migration-from-nicolify.md` API SDK rota (`registry.lock()`→`.close()`, `brand_voice_seed_register` inexistente, EP numbering wrong) + AISALESHT source reseteado + Node 22 (real 20)** | docs/architecture/luana-platform/migration-from-nicolify.md | Banner ARCHIVED; corregir API a SDK real; o mover a archive | Alto (copy-paste → AttributeError) | medio |
| **`extension-points.md` todos los ejemplos usan `apps/{brand}/` (inexistente) + CC-4 allowlist sin 6 bootstrap brands** | docs/architecture/luana-platform/extension-points.md | `apps/{brand}/`→`{brand}/backend/src/modules/{brand}/`; allowlist → pointer a SDK source | Alto (path errors, bootstrap falla) | medio |
| **`ADR-008` status proposed + prescribe `core/luana-core-ui` + CLI inexistentes (real: `core/@luana/ui-kit` flat, sin CLI)** | ADR-008-luana-core-ui-shadcn-cli-pattern.md | Status→superseded/accepted-partial; documentar @luana/ui-kit como implementación real | Alto (builder scaffolea package que no debe existir) | bajo |
| **`01-core-audit.md` §7-§9 roadmap histórico + 5 docs prometidos con nombres incorrectos (02-extension-points etc.) + paths `apps/`** | docs/architecture/luana-platform/01-core-audit.md | Sección "Execution status"; mapear planned→actual names; corregir paths | Alto | medio |
| **`02-core-purge-audit.md` + `03-nicolify-carve-out-audit.md` + `04-pending-migrations.md`: estados stale post nicolify-reset 2026-05-29 (estructuras descritas no existen); `b2b-billable-hours.md` + `001_initial_snapshot.py` inexistentes; counts off-by-one** | 02/03/04 audit docs | Banners post-reset; bitácoras de waves ejecutados; corregir counts; marcar lifts COMPLETED | Alto (carve-out continuity) | medio |
| **`ADR-006` related `04-tickets-template` apunta a artefacto distinto (QW-18)** | ADR-006-story-closure-gate.md | `04-tickets`→`06-tickets`; qwen-opencode→opencode; nota 10-estados | Alto | bajo |

### MEDIUM / LOW

| Issue | Archivo(s) | Cambio | Risk | Effort |
|---|---|---|---|---|
| **ADR-002 cd-staging trigger stale (body dice push-a-main, real workflow_dispatch) + story refs no archivadas** | ADR-002-cicd-multibrand.md | Addendum 2026-05-19; corregir refs a `docs/archive/` | Alto | bajo |
| **ADR-004 parallel-safety "M1-M11" (real M1-M14) + ci-wip descripción stale + cleanup-wip deferred + model 4.7** | ADR-004-git-branching-and-environments.md | Nota M14 + ADR-005/009; trigger real; deferred note | Alto/Medio | bajo |
| **ADR-005 §2.1 tabla CANÓNICO "rota" (Addendum v2 corrige pero tabla no) + "Superseded by: none" (ADR-009 lo supersede parcialmente)** | ADR-005-worktree-policy.md | Corregir tabla §2.1 a ESTABLE; agregar "Superseded by: ADR-009 (canonical topology)" | Alto | bajo |
| **ADR-007 caps contradictorios (3/4) + sin forward pointer a v4.2** | ADR-007-paradigm-v4.1-autonomy.md | Bitácora v4.2 supersede (self_fix≤5, audit≤4) | Medio | bajo |
| **ADR-010 4 tareas derivadas sin stories de tracking** | ADR-010-orquestacion-agentica.md | Bitácora con story IDs/status (migración caps, MapView, índice acciones, SYSTEM-MAP) | Medio | bajo |
| **ADR-012 outcome refining pese a useAutosave shipped + adoption stories inexistentes + contract divergente (no `load`, no react-query interno)** | ADR-012-autosave-primitive-platform.md | Bitácora SHIPPED; contract as-built; abrir adoption stories | Medio (duplicados viejos persisten) | bajo |
| **ADR-013 MEMORY pointer contradice (dice "NO ADR aún") + story `idea` vs ADR accepted** | ADR-013 + MEMORY `luana-empleados-ia-vision` | Actualizar MEMORY; nota stories en idea | Medio | bajo |
| **ADR-003 port table sin cockpit (4000-4004); ADR-011 `00-checkpoint-template.md` (QW-19)** | ADR-003, ADR-011 | Agregar cockpit ports; corregir filename | Bajo | trivial |
| **PARADIGM.md SYSTEM-MAP vitalia-specific + falta DoD live-verify en §7 enforcement** | PARADIGM.md §7 | Generalizar `{brand}/docs/architecture/SYSTEM-MAP.yaml`; agregar fila Critical #37 | Bajo | bajo |

---

## Necesita decisión de Chris (stake/criterio)

Estos NO se aplican sin tu ratificación — implican criterio de negocio, retiro de superficies, o trade-offs de arquitectura.

| # | Decisión | Contexto | Opciones |
|---|---|---|---|
| **D-1** | **`model: opus` en frontmatter de skills — ¿es campo válido CC-2026?** | Aparece en ~15 PM skills + po/po-ux/ux-agentico/dev-team/handoff. El schema verificado de skills NO lo lista (válidos: description, when_to_use, allowed-tools, disable-model-invocation, user-invocable, context, agent). | (a) Confirmar con docs CC-2026 si se respeta en skills → mantener; (b) Eliminar de todos (routing por cost-routing externo); (c) Mover a `agent:` field |
| **D-2** | **Retirar `git-manager` skill** | Apunta a OTRO repo (ap_sales_agent), usa branch `development`, viola git-safety (`git pull`, `--force-with-lease`). `commit-push` ya cubre el workflow canónico. | (a) Retirar + skillOverrides→commit-push; (b) Reescritura completa |
| **D-3** | **Retirar/consolidar `ux-disruptivo` + `ux-flow-architect` + `02-design-ui-template.md`** | Todos nicolify-scoped legacy; `/po-ux` multibrand cubre el espacio. ux-flow-architect ya auto-marcado DEPRECATED. | (a) Deprecar los 3 (user-invocable:false + stubs); (b) Parametrizar ux-disruptivo para multibrand |
| **D-4** | **Reactivar GitHub Actions / provisionar staging** | Múltiples docs asumen GA activo; sentinel `.ci-parity-deferred` confirma deferred. Triggers de reactivación: servidor staging, 1ª release, 2º dev, customer-paying. | Confirmar si seguimos deferred (entonces banners en docs) o se provisiona infra (entonces fix workflows) |
| **D-5** | **¿Crear los scripts faltantes o marcarlos TBD?** | `e2e-preflight.sh`, `dev-app-up.sh`, `cloudflared-setup.sh`, `scan_cross_brand_mirror.sh`, agentic eval scripts, PII scanners, `generate_release_notes.py`, `test_no_subagent_worktree.sh`, `test-{brand}.sh` — todos citados como SSoT, ninguno existe. | (a) Crear stubs funcionales (resuelve gates rotos); (b) Marcar `⏳ PENDING` en cada referencia (honesto pero gates siguen inertes) |
| **D-6** | **Cumplir cap de líneas CLAUDE.md** | CLAUDE.md = 257 líneas (cap 200, +57); vitalia/CLAUDE.md = 159 (cap 150, +9) ✅ VERIFICADO. La rule la viola el propio proyecto. | (a) Trim a caps (mover detalle a rules-detail); (b) Actualizar caps a valores reales (270/160) |
| **D-7** | **Migración paradigm (ADR-010): caps config/infra → cajas + agent_owner deprecation** | ~71 caps vitalia con `agent_owner: infra` (deprecated v2.0) + MapView reorganization + índice de acciones. Sin stories. | Abrir story(s) de migración o ratificar deferral con fecha |
| **D-8** | **Archivar audit docs históricos post nicolify-reset** | 02/03/04-audit + migration-from-nicolify + 05-cross-repo + handoff docs son arqueología (estructuras descritas no existen). | (a) Banners HISTORICAL in-place; (b) Mover a `docs/archive/2026/` |
| **D-9** | **Bootstrap directorios faltantes** | `comunify/docs/observed-bugs/` + `lupulo/docs/observed-bugs/` inexistentes (rule asume); CC-4 allowlist sin 6 brands; `apps/client-simulator` fuera de uv workspace. | Bootstrappear on-demand o ahora |
| **D-10** | **Self-fix policy: resolver caps definitivos** | v4.1 (3/4) vs v4.2 (5/4) conviven en SSoT detail + ADR-007 + auditor SKILL con números mezclados. Necesita 1 valor canónico ratificado. | Ratificar v4.2 (self_fix≤5, audit≤4) como único + tachar v4.1 en todos lados |

---

## Roadmap de adopción priorizado (mapeado a features CC-2026)

### Wave 1 — Quick wins mecánicos (1 sesión, bajo riesgo)
Aplicar QW-1 a QW-20 en batch. **Prioridad absoluta QW-1 (frontmatter break) y QW-2 (contract-guard)** porque silencian funcionalidad sin error visible. Incluye fix global de model IDs (E), `04-tickets`→`06-tickets` (QW-7), containers `visionarias_*` (QW-8), WIP caps (QW-12).
- **CC-2026 hook events:** ninguno requerido; son edits de archivo.

### Wave 2 — Gates rotos / Critical Rules sin cablear (alto impacto operativo)
- **DoD live-verify (#37) en templates** (07-merge, 04-validators, checkpoint, T-result, T-review, dispatch-plan) + crear `dev-app-up.sh`/`cloudflared-setup.sh` (D-5).
- **Anti-orphan CONN (#33) en 03-arch-template** + Prior art audit.
- **`tessl__*` resolution** (clase B): stubs o fallback en 6 agents Step 0 GATE + skills. Sin esto los builders/auditors no arrancan.
- **PII scanners + `pii-sanitisation.md` stub** (pre-commit §8-9 + builder/auditor backend).
- **Globs rotos de rules** (clase: master-data, currency, sales-agent-voice, form-runtime, offer-catalogs, analytics) → rules auto-cargan de nuevo.
- **CC-2026 `SubagentStart` hook:** candidato para enforcement de model routing (opus para agentic) + WIP cap check + sub-agent worktree ban (reemplaza `test_no_subagent_worktree.sh` faltante).

### Wave 3 — Staleness masiva de paths/vocab (clases A + F)
- Reescritura de `checkpoint-protocol.md` resume protocol + process docs (cicd-runbook, contributing, git-workflow, parallel-sessions, pm-redesign) a triple-branch + hub + paths multibrand.
- Skills domain-expert path remapping (backend/brand/copilot/metrics/offer/sales-agent-expert).
- Templates legacy (PI/sprint/ticket/02-design-ui) → banners DEPRECATED.
- Story templates → cap_target/cap_change_type + state vocab.
- **CC-2026 `isolation: worktree`:** agregar a builders write-capable (builder-agentic primero, maxTurns:150) + auditores Carril A. Resuelve el hazard de índice compartido en hub multi-sesión.

### Wave 4 — ADR reconciliation + decisiones de Chris
- ADR-001 addendum monorepo (la divergencia más crítica sin registrar).
- ADR-005/007/008/012/013 status + bitácoras.
- Audit docs históricos → banners o archive (D-8).
- Decisiones D-1 a D-10.

### Wave 5 — Optimización CC-2026 (oportunidades, no defectos)
- **`when_to_use` field** para reducir presión del skill-listing budget (~59 skills comparten budget): mover triggers de description a when_to_use en ~20 skills verbosos (architect 999 chars, auditor 944, dev-team 1167, etc.). **Cost-routing / listing budget.**
- **`context: fork`** para skills que generan artefactos grandes sin contaminar contexto principal (ai-docs, architect, handoff, ux-*, vitalia/nicolify-design-system).
- **`background: true`** para gate-runner (determinístico) + grep-bot (paralelizable).
- **`memory: project`** para architect/auditor (acumular anti-patterns cross-story) + builder-frontend (decisiones de implementación).
- **CC-2026 `WorktreeRemove` hook:** auto-cleanup-session + liberar bucket locks huérfanos.
- **CC-2026 `PostCompact` hook:** recordar recargar checkpoint.md + MEMORY.md (anti context-rot).
- **CC-2026 `TaskCreated` hook:** validar assignment block en tickets (architect-autonomous-mode).
- **Plugin packaging:** consolidar el harness (.claude/) como plugin versionable una vez estabilizado.

---

*Fin del catálogo. 8 claims de mayor impacto verificados contra filesystem real. Esperando ratificación de Chris antes de cualquier edit.*