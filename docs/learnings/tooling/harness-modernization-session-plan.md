# Plan de sesión — Homologación técnica + modernización del harness (2026-06-01)

> SSoT vivo de esta línea de trabajo (sobrevive a context-rot / resúmenes). Solo-operador (Chris). Origen: sesión 2026-06-01 desde worktree `luana-vitalia` (`wip/vitalia`).

## Directivas vigentes de Chris (NO violar)

1. **Trabajar todo acá** (worktree vitalia / `wip/vitalia`). Commit por pathspec; cross-cutting (`.claude/`, `tools/`, `docs/`, `core/`) con `SCOPE_GATE_SKIP=1` + razón en el body. No entreverar con la story en vuelo `vitalia-fase2-lisa-doctores` (developing).
2. **Workflows JS de Claude = motor de trabajo** (auditorías, edits por lote, research). Optimizar calidad/precio + evitar saturar contexto + evitar rehacer por context-rot.
3. **Handoff por sesión:** al cerrar cada chunk → entregar el **prompt EXACTO** para arrancar una conversación nueva con contexto fresco. Iterar así hasta terminar.
4. **Catalog + propose:** NADA se edita en el harness sin ratificación explícita de Chris.
5. **Solo-operador:** no hay otros programadores; el proceso debe ser operable por una persona.

## Encuadre (ratificado)

- **Modernización del harness** (skills/agents/rules/hooks/cockpit) y **historia B** = **hermanos separados** (cómo construimos vs qué construimos). Enlazados: el harness habilita a B.

## Secuencia macro (ratificada)

```
B (motor agentico, core)  →  Vitalia (instanciar+validar)  →  A (homologación, gate de replicación)  →  nicolify/comunify (replicar)
```
La **modernización del harness** es enabler transversal que corre primero/al margen (esta línea de trabajo).

## Frente actual: modernización del harness

1. [done] Research CC junio-2026 → `docs/learnings/tooling/claude-code-2026-capabilities.md`
2. [done] Schemas verificados contra docs oficiales (skills/agents/hooks) — embebidos en el workflow
3. [running] **Workflow `harness-audit-2026`** (run `wf_1f1d1973-ac4`) → catálogo ratificable
4. [pending] Chris ratifica el catálogo → qué se aplica
5. [pending] Aplicar cambios por lotes vía workflow (con prompt de sesión fresca por lote)
6. [pending] **Diseñar el PROCESO de gestión del ciclo de vida de harnesses** (solo-operador, report+fix on-the-fly ordenado) ← pedido Chris 2026-06-01
7. [pending] Refinar la historia B con el plan completo

## Entregables abiertos

- [ ] Catálogo de auditoría → `docs/learnings/tooling/harness-audit-2026-06-01.md`
- [ ] Proceso de ciclo de vida de harnesses (deliverable final)
- [ ] Prompt(s) de próxima sesión (contexto fresco) por cada chunk
- [ ] Refinamiento de B (`empleados-ia-auto-extension`)

## Artefactos ya creados esta sesión

- `docs/product/outcomes/tech-baseline-homologation-platform.md` (homologación A, secuencia revisada)
- `docs/learnings/tooling/claude-code-2026-capabilities.md` (baseline CC junio-2026)
- este archivo (plan de sesión)
- appends a `docs/product/stories/empleados-ia-auto-extension/chris-input.md`

## Progreso aplicado en esta sesión (2026-06-01)

### Silent-killers (ratificados Chris, aplicados)
- QW-2: `contract-guard.js` worktree-agnostic (CLAUDE_PROJECT_DIR + regex `/luana-*/`) — hook revivido en worktrees ≠ luana-platform (verificado: dispara en vitalia).
- QW-1: `handoff` + `worktree-protocol` SKILL.md — comentario `voseo-allowed` movido debajo del frontmatter (línea 1 = `---`).
- QW-13: `grep-bot` → "Luana Grep Bot".

### Voseo descope (pedido Chris — "solo UI, no harness")
- `scripts/git-hooks/pre-commit` §1: markdown FUERA del scan + exclusión de `.claude/`, `docs/`, `scripts/`, `tools/`, tests. El voseo solo se enforce en código de producto `.py`/`.ts`/`.tsx` user-facing. Output agéntico → arch tests en `core/`.
- `.claude/rules/spanish-text.md`: alcance reescrito (UI/agentic only) + magic comment marcado obsoleto para internos.
- `.claude/skills/po/SKILL.md`: comentario línea 1 eliminado (último offender de registro).
- Pendiente Wave 3 (opcional): limpiar ~73 comentarios `voseo-allowed` heredados en docs/skills (ruido inofensivo).

### Clase B (tessl) — severidad corregida → D-11 (decisión Chris pendiente)

### Pendiente inmediato
- Ratificación D-1..D-11.
- Commit por pathspec de los fixes (sin commitear aún).
- Prompt de sesión fresca para Wave 1 workflow.
- Proceso de ciclo de vida de harnesses (deliverable final).

## D-1..D-11 — RATIFICADAS por Chris (2026-06-01, "todas como recomendaste")

| # | Resolución ratificada |
|---|---|
| D-1 | `model: opus` en skills → **mantener**, verificar campo contra doc en Wave 2 (no remover: campo desconocido se ignora) |
| D-2 | `git-manager` → **RETIRAR** (deprecar: `disable-model-invocation:true`+`user-invocable:false` + banner → `commit-push`) |
| D-3 | `ux-disruptivo` + `ux-flow-architect` + `02-design-ui-template.md` → **DEPRECAR los 3** (stub → `/po-ux`) |
| D-4 | GitHub Actions → **seguir DEFERRED** + banners en docs que asumen GA activo |
| D-5 | scripts faltantes → **HÍBRIDO**: crear los del DoD live-verify (`dev-app-up.sh`,`cloudflared-setup.sh`,`e2e-preflight.sh`) si faltan; resto `⏳ PENDING` honesto |
| D-6 | cap líneas CLAUDE.md → **bumpear caps a 270/165** ahora + trim oportunista Wave 3 |
| D-7 | migración paradigm ADR-010 (config/infra→cajas) → **DIFERIR** (pista B/Vitalia, NO harness) |
| D-8 | audit docs históricos post nicolify-reset → **banners HISTORICAL in-place** (Wave 3) |
| D-9 | dirs faltantes (observed-bugs, allowlist 6 brands) → **on-demand** |
| D-10 | self-fix policy → **v4.2 canónico** (self_fix≤5, audit≤4), tachar v4.1 en todos lados |
| D-11 | tessl `tessl__*` refs → **reemplazar por guía inline / `tessl-context`** (salvo que Chris decida instalar plugin/MCP Tessl) |

### Nuevo bug detectado esta sesión (agregar a Wave 1/2)
- `make install-hooks` ROTO en worktrees: asume `.git` directorio (`mkdir .git/hooks` falla). Fix: usar `git rev-parse --git-path hooks` para el dir común. Workaround usado hoy: `cp scripts/git-hooks/pre-commit "$(git rev-parse --git-path hooks)/"`.

### Estado: silent-killers + voseo descope = COMMITEADOS (17bf3c62). Hook nuevo instalado en dir común (todos los worktrees).

---

## Sesión 2026-06-01 (continuación) — Waves 1+2A+2B + DoD ENDURECIDA aplicadas

> Motor: workflows JS (catalog+propose → diff → ratify Chris → commit Haiku por pathspec, SCOPE_GATE_SKIP=1). Verify-first (varias findings del catálogo resultaron sobreestimadas: globs analytics/offer ya correctos, tessl HARD-GATE era graceful-ignore, `<nextjs-portal>` siempre existe en dev).

**Commits (todos en `wip/vitalia`, pushed):**

| # | SHA | Qué |
|---|---|---|
| 1 | `2388a13a` | **Wave 1 mecánico** QW-3..QW-20: overlay caps 270/165 (D-6), containers reales `luana-dev-{brand}_{service}_dev-1`, IDs Opus 4.7→4.8, 04-tickets→06-tickets, WIP caps developed/reviewing ≤1, audit_iterations cap 4, `_OVERLAY-template`→`vitalia/CLAUDE.md`, `lib/routing/shell-routes`→`lib/shell-routes`, LITELLM fuera de flags activos, grep-bot color cyan |
| 2 | `dc6a94fa` | **Wave 2A** gates: #37 DoD en 6 templates (07-merge §6 REFUSE, checkpoint dod_*, 04-validators live_verify, T-* + Cat 12/13/14 en T-review) + #33 CONN+Prior-art en 03-arch + 5 globs de rules a paths reales |
| 3 | `32c01fcd` | **DoD keystone**: rule #37 endurecida (6 secciones) + `vitalia/frontend/e2e/fixtures/base.ts` (gate anti-burbuja, **live-verified 4 passed** localhost:3002) + `scripts/verify-no-backend-errors.sh` |
| 4 | `4663371` | **DoD propagación**: 04-validators (bloque `verification:`) + checkpoint (`demo_signoff`) + `demo-script-template.md` (nuevo) + test-design-doctrine + skills architect/dev-team/auditor/pm-vitalia+template |
| 5 | `3a9c53f2` | **Wave 2B tessl cleanup** (D-11): refs muertas `tessl__*` → docs canónicos/patrón inline en 8 agents + 9 skills + 7 templates (gates preservados) + QW-15 (Cat 13/16 verdict math) + builder containers |

**DoD ENDURECIDA = el gran entregable de la sesión** (Chris detectó "digo listo y hay burbuja de Next"). Research 6 frentes web-grounded → 6-section model: (1) `/architect` clasifica naturaleza técnica/funcional en `04-validators § verification`; (2) gates técnicos baseline + opt-in por naturaleza (Schemathesis/Hypothesis/mutmut); (3) ★ gate anti-burbuja `base.ts` (pageerror/console/hidratación/`/api/`-4xx5xx/diálogo-Next) + `verify-no-backend-errors.sh`; (4) cobertura reglas-de-negocio (gherkin-matrix MISSING bloquea); (5) ★ demo manual Chris (`demo-script.md` → `demo_signoff` APPROVED/REJECTED → `/pm` Fase F REFUSE); (6) modificación `regression_guard`. SSoT `.claude/rules/definition-of-done-live-verify.md`. MEMORY `dod-live-verify` actualizado. 3 decisiones ratificadas Chris (demo toda story user-reachable · técnica avanzada opt-in · base.ts implementado).

**Pendiente (próximos chunks):**
- **Wave 3** — staleness masiva clases A+F: process docs (`checkpoint-protocol.md` resume protocol a `{brand}/docs/...`, `contributing.md`, `git-workflow-multibrand.md`, `cicd-multibrand-runbook.md`, `parallel-sessions-protocol.md`, `pm-redesign-2026-05.md` banner SUPERSEDED) + ADRs (ADR-001 addendum monorepo, ADR-005/007/008/012/013 status+bitácoras, 00-overview topology, audit docs HISTORICAL banners D-8) + skills domain-expert path remapping + story templates cap_target/state vocab.
- **D-2** retirar `git-manager` (deprecar → `commit-push`). **D-3** deprecar `ux-disruptivo`+`ux-flow-architect`+`02-design-ui-template` (stub → `/po-ux`).
- **Bug nuevo**: `auto-chain-detect.sh` false-positive (saltó "auto-chain /pm-vitalia+/dev-team" cuando Chris solo dijo "avanzá, ratificado" — el hook misfira; ver catálogo § hooks, fallback sed lossy sin jq).
- **base.ts rollout**: hoy es opt-in (specs nuevos importan de `base.ts`). Migrar specs autenticados existentes (compose `mergeTests(base, auth)`) cuando cierre la story lisa-doctores en vuelo (NO tocar mid-flight). El legacy `auth.fixture.ts::collectConsoleErrors` ignora Hydration/500/404 — reemplazar por base.ts al migrar.
- Wave 2 quick-wins NO aplicados aún: QW-14 version field (parte de D-2 git-manager retiro).

### Estado: 5 commits aplicados. DoD endurecida cementada punta a punta. Story en vuelo `vitalia-fase2-lisa-doctores` (developing) NO tocada en toda la sesión.

---

## Sesión 2026-06-01 (continuación 2) — Wave 3 + D-2/D-3 + bugs aplicados

> Motor: workflow JS `harness-wave3-retire-bugs` (run `wf_dceae010-5be`, 31 editores sonnet verify-first + 1 síntesis opus, lotes DISJUNTOS, sin commit). Catalog+propose → diff → ratify Chris → commit Haiku por pathspec (`SCOPE_GATE_SKIP=1`). Verificación independiente del orchestrator antes de presentar (frontmatter línea-1, bash -n + 3 casos funcionales del hook, make -n, **lift offer/analytics confirmado real en `core/luana-core-*`**).

**Commits (todos en `wip/vitalia`, pushed, origin 0/0):**

| # | SHA | Qué |
|---|---|---|
| 1 | `96aa9559` | **Wave 3 docs** (23 files): 6 process docs (paths multibrand `{brand}/docs/product/stories/` + triple-branch hub-first ADR-009 + GA deferred + sin `git pull`) · ADR-001 PROPOSED→ACCEPTED+addendum monorepo · ADR-005/007/008/012/013 status+bitácoras · 00-overview topology real (26 luana-core-* + @luana) · 6 audit docs banners HISTORICAL/SUPERSEDED/ARCHIVED (D-8) · story templates `state`/`cap_target`/`cap_change_type` · 02-design-ui DEPRECATED |
| 2 | `ab647839` | **Wave 3 skills + D-2/D-3** (10 files): 7 domain-expert skills remapeadas a paths multibrand+engine · **D-2** git-manager RETIRADO (stub→`/commit-push`, `disable-model-invocation`+`user-invocable:false`, `version` removido) · **D-3** ux-disruptivo + ux-flow-architect DEPRECADOS (stub→`/po-ux`) · copilot-expert seed KB corregido al pack real |
| 3 | `1a0dc598` | **Bugs** (2 files): auto-chain-detect.sh (intent-gate: verbo imperativo o ≥2 slash-commands + **cláusula anti-stale** "aplica solo al turno actual" + warning jq ausente) · Makefile install-hooks worktree-safe (`git rev-parse --git-path hooks` + instala pre-push) |

**Catalog overestimates confirmados contra FS** (lo que NO era real — Chris pidió capturarlo):
- `parallel-sessions-protocol`: mecanismos NO estaban "todos pending" — A,B,D,E,F,H,I,J,L,M,N implementados; solo G+K pendientes.
- `pm-redesign`: solo 1 `/architect`=Sonnet era incorrecto (los otros describen al builder).
- `copilot-expert`: `references/copilot-*.md` SÍ existen; `luana-dev-luana_postgres_dev-1` es correcto.
- `metrics-expert`: `visionarias_redis` ya no estaba. `ADR-001`: links ya marcados `(pending)`.
- **Lift offer/analytics SÍ ocurrió**: catálogos `*_catalog.py` en `core/luana-core-offer-studio/`, `metric_catalog.py`/`extraction_contract.py` en `core/luana-core-analytics-engine/` (ya NO en brand backend) → paths de offer/metrics-expert correctos.

**Follow-ups abiertos (NO aplicados — necesitan criterio Chris):**
- `offer-type-preset-expert` cita `test_offer_type_preset_catalog_completeness.py` (no existe; el real cargado es `core/luana-core-offer-studio/tests/test_catalogs_dag_smoke.py`). Staleness pre-existente preservada por el agente. El "187 arch tests" sugiere que ese test quizá nunca se lifteó. Decidir: apuntar a dag_smoke o nombre real.
- ADR-013 quedó coherente pero el pointer MEMORY `luana-empleados-ia-vision` aún dice "NO ADR/spec aún" — actualizar (archivo del orchestrator).

**Pendiente (próximos chunks):**
- **base.ts rollout** a specs autenticados existentes (`mergeTests(base, auth)` + reemplazar `auth.fixture.ts::collectConsoleErrors`) — SOLO cuando cierre la story `vitalia-fase2-lisa-doctores` (NO tocar mid-flight).
- **Wave 4 resto** — ADR-002/003/004/010/011 (minor: addenda, ports cockpit, M14, story-tracking) + PARADIGM.md §7 + decisiones D-1/D-4/D-5/D-7/D-9 (varias ya ratificadas/deferred).
- **Wave 5 CC-2026** (oportunidades, no defectos): `when_to_use` (reducir listing budget), `context: fork`, `isolation: worktree` (builders write-capable), `background: true` (gate-runner/grep-bot), `memory: project`, plugin packaging.
- **Deliverable final**: diseñar el PROCESO de gestión del ciclo de vida de harnesses (solo-operador, report+fix on-the-fly ordenado).
- Refinar historia B (`empleados-ia-auto-extension`).

### Estado: 8 commits aplicados en total esta línea de trabajo (5 previos + 3 esta sesión). Wave 3 + D-2/D-3 + 2 bugs CERRADOS. Story en vuelo `vitalia-fase2-lisa-doctores` (developing) NO tocada.

---

## Sesión 2026-06-01 (continuación 3) — Wave 4 + D-5 + Wave 5 + item 4 (HLP cerrado)

> Motor: workflow JS `harness-wave4-adr-reconcile` (8 editores sonnet verify-first + síntesis opus, lotes disjuntos, sin commit, sin worktree-isolation) + autoría directa opus para los scripts D-5 (infra-crítico, no parallel) + edits frontmatter Wave 5 + agente `claude-code-guide` (verificación de campos CC-2026 contra docs oficiales ANTES de mass-edit). Cadena: catalog+propose → diff → ratify Chris → commit Haiku por pathspec (`SCOPE_GATE_SKIP=1`). Verify-first confirmó overestimates (ADR-011 ya correcto) y findings reales (scripts D-5 SÍ faltaban aunque la rule decía "probado live" — `make dev-app-vitalia` estaba roto).

**Commits (todos en `wip/vitalia`, pushed, origin 0/0):**

| # | SHA | Qué |
|---|---|---|
| 1 | `cbc736ce` | **Wave 4** (7 files): ADR-002/003/004/010 addenda (GA-deferred + trigger real workflow_dispatch + cockpit ports 4000-4004 + M1-M14 + bitácora D-7) · PARADIGM §7 (SYSTEM-MAP `{brand}/` + fila Critical #37) · D-4 banner github-environments-setup · fix offer-preset test ref → `test_catalogs_dag_smoke.py` (8 funcs). ADR-011 = overestimate. **Reconciliación ADR COMPLETA** (001-013, el resto fue Wave 3) |
| 2 | `22dacb4c` | **D-5 scripts** (3 new): `dev-app-up.sh` + `cloudflared-setup.sh` + `e2e-preflight.sh` (referenciados, nunca existieron). Validados bash -n + shellcheck + `e2e-preflight` verde live. Fallback localhost honesto cuando falta credencial tunnel |
| 3 | `2119d0c1` | **Wave 5** (9 files): `isolation:worktree` (3 builders) + `background:true` (grep-bot) + `memory:user` (4 auditores/architect) + rule #37 honesty (vitalia tunnel credencial pendiente → localhost). Campos verificados vs docs oficiales |
| 4 | (este commit) | **item 4**: HLP endurecida (apply-pipeline + verify-first + cost-routing + `memory:user`) + backlog reconciliado HB-1..HB-22 + INDEX pointer. (2b MEMORY pointer empleados-ia = fuera del repo) |

**Decisiones cerradas:** D-1 (`model:` en skills = válido turn-scoped → mantener) · D-4 (banner) · D-5 (scripts creados) · D-7 (config/infra→cajas DEFERRED track B/Vitalia → bitácora ADR-010) · D-9 (dirs on-demand, sin acción).

**Verificación CC-2026 (`claude-code-guide` vs docs oficiales):** los 6 campos Wave 5 son REALES. Correcciones al catálogo: `memory: user` (NO `project` — clobber en hub compartido); `context:fork` NO es candidato limpio (handoff ya delega a Haiku, ai-docs es interactivo) → Wave 5b. `when_to_use` = campo separado real.

**Follow-ups:** 2a offer-preset test ref (cbc736ce). 2b MEMORY pointer empleados-ia actualizado (índice + detalle: ADR-013 accepted + story `empleados-ia-auto-extension` en `idea`).

**Abierto (drenar por cadencia HLP, NO urgente):** HB-17 (Wave 5b: context:fork análisis + when_to_use migración + activar memory:user con body-instructions) · HB-18 (PII scanners) · HB-19 (D-10 verify) · HB-11 (voseo cleanup) · HB-20 (workflow name inconsistency) · HB-22 (cola MEDIUM/LOW). **Operacional Chris:** HB-21 (provisión tunnel `cloudflared-setup.sh`). **Producto:** base.ts rollout (solo cuando cierre `vitalia-fase2-lisa-doctores`); refinar historia B.

### Estado: continuación 3 = 4 commits (cbc736ce, 22dacb4c, 2119d0c1 + item 4). **Item 4 (HLP) CERRADO** — proceso documentado + probado punta a punta + backlog reconciliado. Story en vuelo `vitalia-fase2-lisa-doctores` (developing) NO tocada en toda la línea de trabajo.

## Sesión 2026-06-02 (continuación 4) — drenaje backlog HB-17/18/19/20/22 por cadencia HLP

> Motor: apply-pipeline §6 verbatim. **Verify-first** (opus lee FS, confirma findings — catálogo sobreestima) → **autoría directa opus** para infra-crítico (PII scanners + pre-commit surgery, no-parallel, precedente D-5) + **workflow JS `harness-wave5b-apply`** (11 editores sonnet, lotes DISJUNTOS por fase-barrier, sin commit, sin worktree-isolation) para edits de docs/frontmatter → **verificación independiente opus** (git diff real + spot-check claims, NO confiar en reportes de sub-agents) → present-diff → **ratify Chris (PENDIENTE)** → commit Haiku por pathspec. Verificación de campos CC-2026 dudosos (`when_to_use`/`context:fork`) vía `claude-code-guide` ANTES de mass-edit.

**Cambios en working tree (uncommitted — esperando ratificación):**

| HB | Qué | Mecanismo | Verif |
|---|---|---|---|
| 17a | `context:fork` análisis | claude-code-guide vs docs CC | **DEFERRED** — 0 candidatos limpios (interactivos/Haiku-delegated/reference-sin-task) |
| 17b | `when_to_use` pilot ×4 skills (architect/auditor/dev-team/playwright) | workflow sonnet | registry re-renderizó OK, triggers preservados, playwright Nicolify→Luana en frontmatter |
| 17c | `memory:user` activación ×4 agents | workflow sonnet | `<memory>` body-instructions (read-start/write-recurring), tailored per role |
| 18 | PII scanners + rule stub + pre-commit §8/§9 + CLAUDE.md #11 | autoría opus | **live-tested** exit 0/1 + whitelist + ruff + `bash -n` |
| 19 | self-fix v4.2 propagación (auditor SKILL + rules-detail) | workflow sonnet | ADR-007 = overestimate (ya tenía bitácora) |
| 20 | workflow name align | autoría opus | comment → `harness-audit-2026` |
| 22 | cockpit README path absoluto | autoría opus | → pointer memory |
| 11 | voseo cleanup | — | **DEFERRED** count real 380 ≠ ~73 |

**Verificación CC-2026 (`claude-code-guide` vs code.claude.com/docs/en/skills.md):** `when_to_use` = campo válido, se **appendea** a `description` (combined truncado 1536 chars — el win es orden/claridad, NO reducción de budget). `context:fork` = válido pero el subagent **pierde acceso al historial de conversación** + reference-skill sin task retorna vacío → inadecuado para todo skill interactivo/ratify (= todos los del harness) → HB-17a deferred.

**Archivos:** NEW `scripts/{_pii_scan_lib,scan_seed_pii,scan_goldens_pii}.py` + `.claude/rules/pii-sanitisation.md`; MOD 4 skills + 4 agents + auditor SKILL + rules-detail/auditor-self-fix-policy + pre-commit + CLAUDE.md + workflows/harness-audit.js + cockpit README + backlog + este file.

### Estado: continuación 4 = committeada (`28eb797f` HB-18 + `b29a12b0` HB-17b/c/19/20/22). Story `vitalia-fase2-lisa-doctores` (developing) NO tocada.

---

## Sesión 2026-06-02 (continuación 5) — CIERRE B1-B6 (closeout ejecutado punta a punta)

> Motor: apply-pipeline §6 verbatim sobre el plan `harness-closeout-2026-06-02.md`. Cadena por batch: verify-first opus contra FS → editar (opus directo para comportamiento/hooks · workflows JS sonnet file-per-agent para mecánico/docs, sin commit, sin worktree-isolation) → verificación independiente opus del `git diff` (NO confiar en reportes de sub-agents) → commit Haiku por pathspec (`SCOPE_GATE_SKIP=1`). Re-audit final read-only antes de declarar cerrado. **Autonomía ratificada por Chris** ("resolve todo de forma autónoma") — commit por batch sin pausa interactiva; el contrapeso fue verify-first + verificación-de-diff + re-audit.

**7 commits (`wip/vitalia`, 0/0 origin):**

| # | SHA | Batch | Qué |
|---|---|---|---|
| 1 | `aaf1041e` | B1 | 10 bugs funcionales (incl. el plan closeout) — opus directo |
| 2 | `316f8ce8` | B2 | brand-overlay rules HB-23 (banners aspiracional + hipaa-lite paths) — opus |
| 3 | `42c52a78` | B3 | quick-wins + hooks — hooks opus + workflow sonnet (9 ag) |
| 4 | `ea9ad657` | B4a | 19 templates — workflow sonnet (16 ag) |
| 5 | `65e573fe` | B4b | 18 process+rules — workflow sonnet (18 ag) |
| 6 | `9cd049d6` | B5 | skills HIGH (pase-produccion/chrome-devtools/brand-offer-auditor + PM backport ×6) — opus + workflow (6 ag) |
| 7 | `1f162789` | B6-residual | 20 OPEN del re-audit cerrados — workflow sonnet (16 ag) |

**Re-audit (6 agentes read-only, 1 superficie c/u):** B1-B5 DONE-verified contra FS · **0 regresiones** · 47 skills frontmatter L1 OK · 20 OPEN residuales → 20/20 cerrados en B6 → **OPEN-count final = 0**.

**Aprendizaje del apply-pipeline a escala:** verify-first cazó ~12 overestimates/desviaciones del catálogo (8-gate mito · pre-push dynamic-brands sin beneficio · offer catalogs 6≠8 · dev-team ya parametrizado · varios "ya estaban" de waves previas · 17 Opus-4.7 = históricos). El catálogo sobreestima incluso a nivel finding individual — la verificación-de-diff opus (no el reporte del sub-agent) fue la red real. Workflows sonnet file-per-agent (un archivo = un agente) evitaron races en el working tree compartido del hub.

**Abierto (post-cierre):** HB-24 file-size extraction (deferred-dedicada) · HB-11 voseo (deferred) · HB-21/B6-Cloudflare + settings.json StopFailure (Chris). `/harness-audit-2026` fresco cuando "huela a drift".

### Estado: continuación 5 = **closeout B1-B6 CERRADO** (7 commits, re-audit verde, 0 regresiones, 0 OPEN). HLP probado end-to-end a escala (88 OPEN reconciliados → cerrados/deferred/overestimate). Story `vitalia-fase2-lisa-doctores` (developing) NO tocada en toda la línea. base.ts rollout NO ejecutado (espera cierre de esa story).
