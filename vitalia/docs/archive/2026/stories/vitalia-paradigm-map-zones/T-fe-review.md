<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review: vitalia-paradigm-map-zones (T-5 + T-6)

**Date:** 2026-05-30
**Brand:** vitalia
**Story:** vitalia-paradigm-map-zones — migración del mapa a 3 zonas (Ribbon realign)
**Tickets:** T-5 (shell UI realineado) · T-6 (e2e specs valeria→mateo)
**Commits:** 102d3a77 (T-5) · 026f796e (T-6) · 65b2e972 (build close)
**Files Reviewed:** 106 (FE only)
**Domains touched:** shell-organism (agent-catalog SSoT, Ribbon, ConfigTab), features/mateo (ex-valeria agenda), e2e regression
**Skills consulted:** frontend-expert · brand-expert (agent catalog/shell) · vitalia-design-system (per result.md) · tessl__react-patterns (baseline) · playwright-expert (e2e)
**Live-verified:** N/A (cambio mínimo Ribbon, mockup_gate WAIVED por Chris — checkpoint mockup_gate_waived:true; e2e escritos no ejecutados, CI corre)
**Verdict:** **APPROVED**

## /test-frontend Gate Status

Validators verificados verdes (orchestrator, pre-handoff):

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit (strict) | PASS | 0 errores |
| ESLint (60+ rules) | PASS | 0 errores |
| Vitest | PASS | 212 files / 2319 tests (incluye agent-catalog-ribbon-taxonomy.test.ts NEW + test-no-cross-brand-shell-mirror.test.ts NEW) |
| Arch fitness (agent-catalog/subtab SSoT) | PASS | taxonomy v1.2 + subtab SSoT + cross-brand mirror gate verdes |
| e2e Playwright | written, not run | stack down; CI corre. 2 specs nuevos typecheckan + ~20 actualizados |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | PASS | 0 |
| 4 | Code Quality | PASS | 0 (2 cosmetic WARN-noted) |
| 5 | Accessibility | PASS | 0 (ConfigTab aria-label→"Plataforma") |
| 6 | Forms (RHF+Zod) | PASS | n/a (no form changes) |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 (no voseo) |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment | PASS | 0 |
| 12 | Architecture Fitness | PASS | 0 |
| 13 | Mirror detection | PASS | 0 (cross-brand gate GREEN) |
| 15 | Connectivity (anti-isla) | PASS | 0 (ruta mateo/agenda alcanzable; Ribbon Operar wired) |
| 16 | Visual fidelity | PASS | 0 (tokens reused; mockup_gate WAIVED) |

## Critical nuance — Valeria supervisora PRESERVADA ✅

Verificado: los 4 componentes sidebar de Valeria existen y NO fueron eliminados:
- `components/shared/shell-organism/ValeriaChat.tsx` ✓
- `components/shared/shell-organism/ValeriaSidebar.tsx` ✓
- `components/shared/shell-organism/ValeriaRail.tsx` ✓
- `components/shared/shell-organism/ValeriaHistory.tsx` ✓

Referenciados en `ShellOrganismLayoutClient.tsx` (sidebar render path intacto). Valeria salió SOLO del Ribbon como TAB (`AGENT_RIBBON_ORDER` sin valeria; `RIBBON_SUBTABS.valeria = []`); su agenda migró a Mateo. `DEFAULT_CHAT_AGENT = "valeria"` preservado. Correcto per spec.

## agent-catalog SSoT coherente ✅

`vitalia/frontend/src/lib/agent-catalog.ts`:
- `AGENT_RIBBON_ORDER = [lisa, mateo, adrian, lucas, camila]` — sin valeria, con mateo ✓ (línea 145-151)
- `RIBBON_SUBTABS.mateo = [agenda, pacientes]` (migrados de valeria) ✓; `RIBBON_SUBTABS.valeria = []` ✓
- `SHIPPED_STATIC_SUBTABS` contiene `mateo.agenda`, NO `valeria.agenda` ✓ (línea 285-288)
- `isValidAgent("mateo")===true`, `isValidAgent("valeria")===false` (exclusión explícita línea 316-317) ✓
- `AGENT_CATALOG.mateo.tabLabel="Operar"`, `defaultSubtab="agenda"` ✓
Cubierto por `agent-catalog-ribbon-taxonomy.test.ts` (13 invariantes, NEW).

## FSD-Lite boundaries ✅

`git mv` completo `features/valeria → features/mateo` (api/components/hooks/store/types/lib). Barrel `features/mateo/index.ts` coherente. Routing `app/(shell-organism)/valeria/agenda → mateo/agenda` (Server Component, static-route precedence documentada). Cero import roto a `@/features/valeria` (grep limpio — solo quedan docstrings/run-instructions cosméticos). `mateo/agenda/page.tsx` = Server Component sin "use client", hidrata `ValeriaAgendaView` client root. Sin cross-feature imports rotos.

## Carril A self-fix (T-5) — verificado

`PacientesPlaceholder.tsx`: lookup `RIBBON_SUBTABS.valeria.find(...)` (ahora `[]` → crash `reading 'icon'`) → corregido a `.mateo`. Cubierto por test existente `mateo/pacientes` (no test nuevo → Carril A legítimo). Estado actual confirmado: `RIBBON_SUBTABS.mateo.find((s) => s.id === "pacientes")` (línea 21). FE surface only, gate-verified. Conforme a auditor-self-fix-policy v4.2.

## e2e coherence ✅

2 specs nuevos (`ribbon-realign.spec.ts`, `mateo-agenda-loads.spec.ts`) typecheckan; usan POM + auth.fixture + shell-theme.fixture. Specs existentes: rutas `valeria/agenda → mateo/agenda`. Refs `valeria/agenda` restantes = labels de describe-block documentando la migración + 1 assertion intencional (`mateo-agenda-loads.spec.ts:123` `expect(url).not.toContain("/valeria/agenda")`). Sin rutas valeria/agenda colgadas activas.

## Anti-duplication cross-brand ✅

`test-no-cross-brand-shell-mirror.test.ts` (NEW) — grep 0 en nicolify/comunify/lupulo para ShellOrganismLayout, shell-store, useShellStore, ValeriaSidebar/Rail/History. Cero mirror cross-brand.

## Surface scope ✅

Commits 102d3a77 + 026f796e tocan SOLO `vitalia/frontend/**` (+ sus propios T-N-result.md / chris-input.md docs de la story). Cero edits en `tools/luana-cockpit/`, `core/`, u otra brand. (`.sweep-findings.json` con ruta valeria/agenda = artefacto pre-existente live-reconciliation, NO en el diff.)

## WARN (non-blocking, cosmetic — no requiere fix para merge)

### WARN: dead metadata `AGENT_CATALOG.valeria.tabLabel="Operar"`
**Category:** 4
**File:** `vitalia/frontend/src/lib/agent-catalog.ts:75`
**Issue:** `valeria` descriptor conserva `tabLabel: "Operar"` + `defaultSubtab: "agenda"`, duplicando los de `mateo`. Valeria ya no es ribbon tab → este metadata nunca se renderiza (Ribbon itera `AGENT_RIBBON_ORDER`, que excluye valeria).
**Por qué no FAIL:** decisión deliberada "shape-complete" — el test `agent-catalog.test.ts:164-167` solo asserta truthiness (no el valor), documentando que es sidebar-only. No consumido por ningún render path (grep confirmó: solo tests lo leen).
**Sugerencia futura (no bloqueante):** poner `tabLabel: "—"` / `defaultSubtab: ""` o comentar que es N/A para reducir confusión.

### WARN: docstrings/run-instructions stale citan `features/valeria`
**Category:** 4
**Files:** `features/mateo/types/__tests__/agenda-schema.test.ts:9`, `features/mateo/lib/__tests__/telemetry.test.ts:2` (run-path comments)
**Issue:** 3 comentarios citan la ruta vieja `src/features/valeria/...` en instrucciones de ejecución. Cosmético — no afecta imports ni ejecución.

## Contract / UI-SPEC Compliance

- [x] agent-catalog v1.2 matches 03-arch-fe.md § F6 + 02-impact.md § 5
- [x] Server/Client boundaries correctas (mateo/agenda = Server, ValeriaAgendaView = Client)
- [x] Mockup gate WAIVED (checkpoint mockup_gate_waived:true, cambio mínimo Ribbon) — no exigido
- [x] Test surfaces (FE-1/FE-2/FE-3 validators) existen

## Allowlist / Baseline Movement

- No arch fitness allowlist GREW. Nuevos tests AGREGADOS (taxonomy + cross-brand mirror) — net tighten.
- ESLint warning baselines: sin growth reportado (0 errores; vitest/tsc/eslint green).

## Native-First Audit

- [x] Sin `docker exec ... tsc|eslint|vitest|playwright` en commits
- [x] Sin `make e2e` / `make e2e-smoke`
- [x] Commits por pathspec (sin `git add .`/`-A`/`-u`)

## Verdict Math

- 0 FAIL en cualquier categoría (1/2/3/7/11/12/15 todas PASS).
- 0 allowlist/baseline growth sin justificación.
- 0 blocker /test-frontend (tsc/eslint/vitest GREEN).
- Arch fitness verde.
- 2 WARN cosméticos non-blocking (dead metadata + stale comments) → NO suben a WARN global (no son issues de comportamiento ni stake-asimétricos; ambos documentados/cubiertos por tests).
- Valeria sidebar preservado ✓ · surface scope limpio ✓ · cross-brand mirror 0 ✓.

→ **APPROVED**
