# Harness Close-out — auditoría reconciliada contra FS (2026-06-02)

> **Estado:** ✅ **EJECUTADO** (cont. 5, 2026-06-02) — B1-B6 cerrados, 7 commits, re-audit verde (0 regresiones), 20/20 residuales cerrados. Ver § CIERRE EJECUTADO abajo.
> **Cómo se hizo:** 6 agentes read-only reconciliaron el catálogo (`harness-audit-2026-06-01.md`) + backlog (HB-1..22) + waves (1-5 + cont.2/3/4) contra el **filesystem real**. El catálogo sobreestima ~30% → cada finding verificado.
> **Lectura honesta:** el harness **root** quedó funcionalmente sólido tras Waves 1-5 (los silent-killers originales se cerraron). Lo que quedaba = **~10 bugs funcionales reales** que las waves saltearon + una **cola larga de staleness de docs** (MEDIUM/LOW) + la **capa brand-overlay** — TODO cerrado en B1-B6.

---

## ✅ CIERRE EJECUTADO (cont. 5 · 2026-06-02 · apply-pipeline §6 end-to-end)

7 commits en `wip/vitalia` (0/0 con origin), commit por pathspec (Haiku), `SCOPE_GATE_SKIP=1`:

| Batch | Commit | Qué | Motor |
|---|---|---|---|
| **B1** | `aaf1041e` | 10 bugs funcionales (commit-push branch · architect 03-arch.md+paths · content-hunter engine paths · eslint scope · anti-dup inventario · tenant Clerk-org · arch-test cmd · parallel-safety D4 · ideas-pool · live-verify {brand}) | opus directo (verify-first) |
| **B2** | `316f8ce8` | brand-overlay rules: banners ASPIRACIONAL (comunify/nicolify/lupulo) + vitalia hipaa-lite 5 path/cron fixes | opus directo |
| **B3** | `42c52a78` | quick-wins (model IDs 4.8 · 04→06 · maxTurns · cockpit counts · MCP guard) + hooks (contract-guard regex 6 catálogos · pre-commit Section 18+venv · pre-push comment) | hooks opus + texto workflow sonnet (9 ag) |
| **B4a** | `ea9ad657` | 19 templates (T-handoff/T-review/REVIEW-final/04-validators/story-*/banners DEPRECADO/etc.) | workflow sonnet (16 ag) |
| **B4b** | `65e573fe` | 18 process+rules (extension-points apps/→brand · warp ADR-009 · vocab · MISSING markers · analytics/offer paths) | workflow sonnet (18 ag) |
| **B5** | `9cd049d6` | skills HIGH: pase-produccion banner DEFERRED+QW-14 · chrome-devtools DoD #37 · brand-offer-auditor de-Nicolify+template creado · PM backport ×6 (Auto-chain+Fase F.3) | opus + workflow sonnet (6 ag) |
| **B6** | `1f162789` | residual: 20 OPEN del re-audit (playwright/metrics references/ de-Nicolify · data-reliability · story fields · stragglers 04→06/Opus-4.7 · banners) | workflow sonnet (16 ag) |

**RE-AUDIT (6 agentes read-only, una superficie c/u):** B1-B5 todos **DONE-verified contra FS**, **0 regresiones** en las 6 superficies, 47 skills frontmatter L1 OK. 20 OPEN residuales surfaceados (capa `references/` + stragglers fuera del file-list) → **20/20 cerrados en B6**.

**OPEN-count final por superficie:** Skills 0 · Agents+Hooks+Cockpit 0 · Rules+brand 0 · Process 0 · Templates+ADR 0 · Quick-wins 0 → **0 OPEN** (todo lo del catálogo/re-audit cerrado).

**Quedó FUERA (registrado, no es regresión):**
- **HB-24** (nuevo, deferred): skill file-size extraction (architect/auditor/dev-team/po-ux → references/) — refactor de skills core, riesgo de romper carga, sesión dedicada.
- **HB-11** (deferred): voseo cleanup (380 archivos, alto-churn/cero-beneficio).
- **HB-21 / B6-Cloudflare** (operacional Chris): provisión túnel + `DEV_APP_TEST_PASSWORD`. Live-verify hoy vía localhost (fallback válido).
- **settings.json StopFailure** (DECISIÓN Chris: cambia comportamiento).
- 17 "Opus 4.7" + menciones residuales = **históricos/append-only/explicativos** (metrics/runs.jsonl, learnings.md tombstone, process-improvement banner'd, ticket-template deprecated self-name, architect SKILL "antes era 04-tickets") — NO se reescribe historia.

**Overestimates del catálogo confirmados cont. 5:** "8-gate FE" mito · pre-push dynamic-brands sin beneficio · offer catalogs=6 no 8 · dev-team live-verify ya parametrizado · context-builder sin mcp__ · cockpit BrandSwitcher no implementado · T-impl-log/T-result/T-review-Cat12-14/REVIEW-final-Verif-live ya estaban · bidirectional dedup intencional.

---

## Tally por superficie (verificado FS)

| Superficie | DONE | OPEN | OVERESTIMATE |
|---|---|---|---|
| Quick wins + Decisions | 27 + 10 | 3 | 0 |
| Skills | 10 | 14 | 2 |
| Agents + Hooks + Cockpit | 15 | 17 | 5 |
| Rules (root + detail + brand) | 6 | 24 | 1 |
| Process docs | 14 | 18 | 3 |
| Templates + ADR | 30 | 12 | 4 |
| **TOTAL** | **~112** | **~88** | **~15** |

---

## P0 — Bugs FUNCIONALES (rompen comportamiento ahora · prioridad real)

| # | Item | Archivo(s) | Por qué es fuego | Effort |
|---|---|---|---|---|
| P0-1 | **`commit-push` hardcodea branch `development`** (7 líneas: L31/40/68/77/79/97/126) | `.claude/skills/commit-push/SKILL.md` | Cada `/commit-push` le dice a Haiku `push origin development` → branch inexistente. Silent-killer (hoy funciona solo porque yo paso el branch a mano) | bajo |
| P0-2 | **architect-orchestrator: hand-off paths sin `{brand}/` prefix + auto-contradicción CONTRACT.md vs 03-arch.md** | `.claude/agents/architect-orchestrator.md` L17-19/39/559 | El architect escribe artefactos a `docs/product/stories/...` (sin brand) y mezcla `CONTRACT.md`/`03-arch.md`; los builders no los encuentran. L559 dice que ese path "NO existe" → se contradice solo | bajo |
| P0-3 | **content-hunter Phase 1 HARD GATE lee paths single-brand** (`backend/src/modules/brand/...`) + body Nicolify | `.claude/skills/content-hunter/SKILL.md` L35/67-77 | Falla en vitalia/comunify/lupulo (path sin `{brand}/`) | medio |
| P0-4 | **ESLint scope mismatch** builder `eslint src/ --cache` vs gate-runner `eslint .` (+ test-fe-* omite jscpd/knip/madge/npm-audit) | `builder-frontend.md` L356 / `gate-runner.md` L52 | Verde parcial (3/8 gates) se reporta como 8/8 → falsa confianza | medio |
| P0-5 | **`anti-duplication.md` inventario con 2 paths falsos** (`tenant_billing_config_repository` dice billing→es observability; `_resolve_tenant_currency` no existe→`FXResolver.default()`) | `.claude/rules/anti-duplication.md` L24-25 | La rule existe para PREVENIR duplicación; paths rotos → el builder recrea en vez de importar | bajo |
| P0-6 | **`tenant-isolation.md` no captura la prohibición Clerk-org** (`useAuth().orgId` como tenant_id) | `.claude/rules/tenant-isolation.md` | La vuln sistémica de 35 archivos (fix 2026-06-01) puede repetirse en otras marcas sin arch-test | bajo |
| P0-7 | **`architectural-fitness.md` cita comandos deprecated** (`/test-backend`, `/test-all`, `make arch-test`) | `.claude/rules/architectural-fitness.md` L30 | Comandos CI inválidos; el real es `test-{brand}` (gate-runner) + `make ci-parity` | bajo |
| P0-8 | **`parallel-safety.md` (detail) D4 contradice M12/ADR-009** (CANÓNICO "rota" vs ESTABLE) | `docs/rules-detail/parallel-safety.md` L15 | Confunde sobre el branch canónico (rota story-by-story vs hub estable) | bajo |
| P0-9 | **po/po-ux bootstrap lee `ideas-pool.yaml` inexistente** | `po/SKILL.md` L86, `po-ux/SKILL.md` L138 | Step 1 de bootstrap falla en toda marca activa | bajo |
| P0-10 | **live-verify hardcoded vitalia** (`make dev-app-vitalia` + `dr.demo@vitalialat.com`) | dev-team, po, po-ux, auditor SKILLs | Verificación DoD rota para nicolify/comunify/lupulo | bajo |

## P1 — Brand-overlay rules (build-peligrosas · no entró en ninguna wave) → "HB-23"

| # | Item | Archivo | Effort |
|---|---|---|---|
| P1-1 | comunify creator-funnels: paths inexistentes (`voice_profile/`, `validators/ladder_integrity.py`, `elevenlabs/`) | `comunify/.claude/rules/creator-funnels.md` | medio |
| P1-2 | vitalia hipaa-lite: 2 paths `shared/` stale + `phi_fields.py` profundidad mal + cron name (`vitalia_phi_retention_sweep` vs real `audit_log_retention_sweep_monthly`) | `vitalia/.claude/rules/hipaa-lite.md` | medio |
| P1-3 | nicolify agent-revenue: describe módulos inexistentes como implementados (sin banner ASPIRACIONAL) | `nicolify/.claude/rules/agent-revenue-engine.md` | bajo |
| P1-4 | lupulo kds: describe módulos placeholder como operativos (sin banner ASPIRACIONAL) | `lupulo/.claude/rules/kds-integration.md` | bajo |

## P2 — Skills HIGH (latentes / calidad · no urgentes pero landmines)

| # | Item | Archivo | Nota |
|---|---|---|---|
| P2-1 | **pase-produccion** modelo de deploy entero roto (`development`, `deploy-prod.yml`→`cd-prod.yml`, `visionarias-*`, `/test-all` inexistente, `version:`) | `pase-produccion/SKILL.md` | GA deferred → no urgente, pero es una mina. Effort alto |
| P2-2 | PM bootstrap brands backport incompleto (pm-retailly el peor: 114 líneas, 0 secciones protocol; pm-fitflow/fixia/guestly/inmoflow/saasora sin Auto-chain+Output+Fase-F.3) | `pm-{retailly,fitflow,fixia,guestly,inmoflow,saasora}/SKILL.md` | latente (esas marcas no están bootstrapeadas) |
| P2-3 | brand-offer-auditor: `references/audit-report-template.md` MISSING (Step 7 roto) + Nicolify hardcoded | `brand-offer-auditor/SKILL.md` | medio |
| P2-4 | chrome-devtools-verify no referencia DoD gate (#37) | `chrome-devtools-verify/SKILL.md` | bajo |
| P2-5 | architect/auditor/dev-team/po-ux file-size (929/752/818/540 líneas) → extraer templates inline a `references/` | 4 skills | medio |
| P2-6 | manychat-expert sin fallback context7→WebSearch; pm-vitalia/nicolify gaps menores (R4 header, Sara en triggers) | varios | bajo |

## P3 — Templates: vocab/path/gate staleness

| Item | Archivo | Effort |
|---|---|---|
| T-handoff: paths `docs/projects/active/PI-N/`, `.venv/bin/` relativo, `make verify-migration-idempotency` inexistente | `T-handoff-template.md` | medio |
| T-review: falta árbol 3-carril v4.2 + campos `self_fix_iter`/`audit_iterations` (sigue cap 2 pre-v4.2) | `T-review-template.md` | medio |
| REVIEW-final: `make dev` (no dev-app), URL nicolify hardcoded, vocab `audit-passed`/`ready_to_merge`/`status: live` | `REVIEW-final-template.md` | bajo |
| PI-template + sprint-template + ticket-template: SIN banner DEPRECATED (paths `docs/projects/`, `visionarias_brain_dev`) | 3 templates | bajo |
| 04-validators: scripts inexistentes (`run_agent_evals`, `scan_cross_brand_mirror`, etc.) sin stub ni `# MISSING` | `04-validators-template.yaml` | medio |
| extension-points.md: paths `apps/{brand}/` (~1300 líneas) + CC-4 allowlist sin 6 bootstrap brands | `extension-points.md` | medio |
| story-{service,ui,agentic}.yaml `Vive en:` sin `{brand}/` prefix; 00-story PI/sprint relative links; 01-spec L331 `/ux-ui`→02-design-ui; dispatch-plan sin DoD + caps v4.1; 02-design-ui owner `/ux-ui`+paths; 05-guidelines sin chrome-devtools+DoD; 06-tickets `state: draft`; release-template sin `production_status`; 00-research Nicolify | varios | bajo c/u |

## P3b — Process docs: vocab/path staleness

| Item | Archivo | Effort |
|---|---|---|
| process-improvement-handoff-*: paths `docs/projects/active/PI-12/` + `/home/chris/AISALESHT/`, SIN banner HISTORICAL | `process-improvement-handoff-2026-05-05.md` | bajo |
| warp-multibrand-handbook: invierte ADR-009 ("CANÓNICO rota story") + `git fetch && merge` (prohibido) ×3, sin banner hub | `warp-multibrand-handbook.md` | medio |
| cockpit-permissions: `atomics/change_log` (muerto) + `type (func/tech)` no matchea story types ADR-011 | `cockpit-permissions.md` | bajo |
| ticket-states: `04-tickets.yaml`→`06-` ×2 + qwen-opencode/Opus 4.7 | `ticket-states.md` | bajo |
| lifecycle §9 punch-list ⏳ contradice §8 DONE; `generate_release_notes.py`/`validate_chris_input.py` MISSING | `lifecycle.md` | medio |
| docker-dev-multibrand paths `/home/chalreme/` hardcoded ×3 | `docker-dev-multibrand.md` | bajo |
| INDEX M1-M8→M1-M14 + índice incompleto; learnings.md sin tombstones + sin entries junio 2026; worktree-protocol-v2-plan sin banner IMPLEMENTADO + `test_no_subagent_worktree.sh` MISSING; chris-input-protocol L222 hardcode; release-procedure-v0.1.0 "33 packages" (real 26) sin banner; spec-mapa-funcional sin cross-link #37 | varios | bajo c/u |

## P3c — Rules root + detail (resto)

| Item | Archivo | Effort |
|---|---|---|
| backend-migrations cita `docs/domains/migrations.md` inexistente (Clone DB workflow) | `backend-migrations.md` | bajo |
| analytics-metrics body paths 1 nivel arriba + Growth Studio FE `growth-studio/` inexistente (real `marketing/`) | `analytics-metrics.md` | bajo |
| offer-catalogs body cita `biz_type_catalog.py`/`ladder_hints_catalog.py` inexistentes; glob pierde `offer_ladder_hints.py` | `offer-catalogs.md` | bajo |
| github-actions-deferred no menciona sentinel `.ci-parity-deferred` (ADVISORY behavior) | `github-actions-deferred.md` | bajo |
| auditor-downstream-regression (detail) cita `.claude/rules/references/` ×5 (dir inexistente) | `docs/rules-detail/auditor-downstream-regression.md` | bajo |
| anti-duplication-refining describe nicolify "frozen" (es skeleton rebuild); brand-docs-schema R3 cita `outcomes` (muerto); step-0-worktree sin fila EFÍMERO hotfix; etl-extraction-contract path; definition-of-done learning pointer stale; auditor-self-fix-policy v4.1 tree sin ~~OBSOLETO~~ | varios | bajo/trivial |

## P4 — Quick-win residuals + cosmético (LOW)

| Item | Archivo | Effort |
|---|---|---|
| QW-6: model IDs "Opus 4.7" en bodies de agents (architect-orch L60/72/171/519, auditor-agentic L24/37/379/427, builder-agentic L27/59/735) | `.claude/agents/*.md` | trivial batch |
| QW-7: refs residuales `04-tickets.yaml` (auditor-agentic L303/329, auditor-frontend L392/417, hotfix-repro-mandatory L11/30) | varios | trivial |
| QW-14: `pase-produccion` aún tiene `version: 1.0.0` | `pase-produccion/SKILL.md` L8 | trivial |
| Hooks: pre-commit doble "Section 13" + machinery usa `python3` sistema (no venv); contract-guard offer-catalogs regex 3/8 catálogos; pre-push brands hardcoded; bidirectional dedup | `scripts/git-hooks/*` | bajo |
| Cockpit README: counts stale (19→20 routes, 12→18 lib, 6→10 tests), v0.7 roadmap BrandSwitcher ya implementado, "Configurar" como 6º agente | `tools/luana-cockpit/README.md` | bajo |
| settings.json StopFailure + deny paths legacy single-brand + PreToolUse vacío | `.claude/settings.json` | **DECISIÓN Chris** (cambia comportamiento) |
| Agents: dev-app.vitalia.com→vitalialat.com; `docs/etl/extraction-contract.md` MISSING; MCP tools sin fallback guard; context-validator maxTurns 60→80 | varios | bajo |

## P5 — Operacional (Chris · no automatizable sin tus keys)

| Item | Detalle |
|---|---|
| HB-21 | Provisión túnel Cloudflare por marca. **Necesito tus keys en disco** (API token o tunnel token por marca). Hoy live-verify por `localhost:300X` (fallback válido). El script `cloudflared-setup.sh` actual es interactivo-only → si me das tokens lo reescribo a path no-interactive |

---

## Overestimates registrados (señal de calidad del catálogo)

`debugging.md` container naming (el bug está en AGENTS.md, no en debugging.md) · `00-overview.md` ya reescrito (6 broken pointers falsos) · ADR-003 cockpit ports ya estaban · ADR-011 ya correcto · gate-runner `test-frontend` (prosa, no comando) · `</output></output>` doble tag (balanceado) · tessl en agent frontmatter (ya limpio Wave 3) · tessl-context description (poblada) · varios voseo (descopeados HB-4) · metrics-expert paths (ya core engine) · ADR-007 bitácora (ya existía).

---

## Track SEPARADO — Build de arquitectura agéntica (NO es harness)

`docs/product/stories/empleados-ia-auto-extension/` está en **`state: idea`** (research bundle + 4 casos borde). Doctrina cementada (PARADIGM.md + ADR-010 + ADR-013 + rule #36) y dirección ratificada, pero **0 build**. Pendiente: decisión Chris sobre vía de promoción (refining normal vs ADR-evolution) → recién ahí arranca el ciclo refine→architect→build por marca. **Esto es un esfuerzo de PRODUCTO, no de cierre de harness** — escala distinta.

---

## Plan de cierre propuesto (batches ratificables · "una sesión = un batch")

| Batch | Contenido | Riesgo | Recomendación orden |
|---|---|---|---|
| **B1** | P0 bugs funcionales (10 items) | medio (toca skills/agents/rules de comportamiento) | **1º — son los fuegos reales** |
| **B2** | P1 brand-overlay rules (HB-23, 4 marcas) | bajo (docs) | 2º |
| **B3** | P4 quick-win residuals + cosmético LOW (model IDs, 04-tickets refs, version, cockpit counts, hooks numbering) | bajo (mecánico, workflow sonnet) | 3º — barato y rápido |
| **B4** | P3 + P3b + P3c templates/process/rules staleness | bajo (docs, alto volumen → workflow) | 4º — la cola larga |
| **B5** | P2 skills HIGH (pase-produccion, PM bootstrap backport, brand-offer-auditor, file-size) | medio-alto | 5º — latentes, por valor |
| **B6** | P5 HB-21 Cloudflare | — | cuando Chris dé tokens |
| **—** | settings.json StopFailure + cualquier "decisión" | — | requiere criterio Chris (no batch) |

**Cost-routing:** B3+B4 (mecánico/docs, alto volumen) → workflow JS sonnet disjunto. B1+B2+B5 (comportamiento) → verify-first opus + sonnet edita + opus verifica. Todo bajo apply-pipeline §6 (catalog+propose → ratify → Haiku commit).
