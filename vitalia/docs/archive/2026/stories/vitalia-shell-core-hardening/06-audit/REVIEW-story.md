<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review (story-wide) — vitalia-shell-core-hardening

**Date:** 2026-06-11
**Brand:** vitalia
**Story folder:** `vitalia/docs/product/stories/vitalia-shell-core-hardening/`
**Tickets:** T-1..T-8 (8 FE tickets, superficie única — chrome del shell-organism)
**Files reviewed:** 75 (vitalia/frontend FE + 2 core/@luana/ui-kit additive)
**Domains touched:** shell-organism (chrome), clinics (lisa/staff N3), crm (adrian/embudo N3) — FE chrome only, NO BE, NO agentic
**Skills consulted:** frontend-expert · vitalia-design-system · playwright-expert (e2e) · chrome-devtools-verify (live-verify rule #37). Domain agentic skills (copilot/sales-agent/brand/offer/metrics) = N/A (no se tocó comportamiento de agente — Decisión confirmada CONTEXT-BRIEF §2).
**Live-verified:** YES — dod_live_verified=true, dod_evidence 5 entries (Playwright authenticated real-backend, fixture base.ts anti-burbuja + backend log limpio) + 2 rondas live de Chris (000/001.png @1920) → chris_verify.signoff = SATISFIED verbatim "ya quedó bien, continúa con el cierre hasta el done".
**Verdict:** **PASS**

---

## /test-frontend Gate Status (re-run by auditor — gate-output.json era STALE)

> **gate-output.json (iter-2) reportaba vitest FAIL (3)** pero predataba el commit `2867d10d` (Carril R, 23:44 local) que alineó esos 3 tests stale. El gate-output empezó 04:39 UTC = 23:39 local (5 min ANTES del fix). Per `consume_gate_output` (gate older than latest commit) → **re-corrí los gates yo mismo (verificación independiente):**

| Gate | Step | Result | Detail |
|---|---|---|---|
| QUALITY | `tsc --noEmit` | ✅ PASS | 0 errors strict (re-run auditor) |
| QUALITY | ESLint (60+ rules) | ✅ PASS | 0 errors, 0 warnings (re-run auditor) |
| QUALITY | Arch fitness (FE) | ✅ PASS | 210/210 (30 files; cross-brand-shell-mirror 31/31) |
| FUNCTIONAL | Vitest (full suite) | ✅ PASS | **255 files / 2664 tests / 0 fail** (re-run auditor, 20.18s) |
| FUNCTIONAL | E2E shell-core-hardening | ✅ PASS | 68/68 (0 flaky final) + resizer-matrix 7/7 + race 8/8 (T-7 + chris rounds) |
| HEALTH | jscpd / knip / madge | ℹ️ n/a | no se reportó growth; suite verde |

**Los 3 "fails" del gate-output.json STALE están RESUELTOS:** re-corrí `agent-catalog.test.ts` + `audited-section.test.tsx` → 118/118 PASS. Commit `2867d10d` los alineó a conducta shipped (adrian tiene 5 sub-tabs por la story embudo `recuperar`; audited-section requería clinicId válido para que el dual-filter hipaa-lite dispare el fetch — intención del test preservada). Pre-existentes destapados por la primera corrida FULL, NO regresión del PR.

## Warning Baseline Movement

ESLint reportó 0 errors / 0 warnings en la corrida del auditor → ningún baseline creció. (vitalia FE no usa los baselines numerados de la plataforma; gate es 0-errors HARD.)

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | FSD-Lite | PASS | 0 |
| 2 | Server/Client | PASS | 0 |
| 3 | React Patterns | PASS | 0 |
| 4 | Code Quality | PASS | 0 |
| 5 | Accessibility | PASS | 0 |
| 6 | Forms (RHF+Zod) | PASS | 0 (n/a — chrome, sin forms nuevos) |
| 7 | Multitenancy | PASS | 0 |
| 8 | Master Data / Spanish | PASS | 0 |
| 9 | Security / Deps | PASS | 0 |
| 10 | Tests / TDD | PASS | 0 |
| 11 | Domain Alignment / Agentic UI | PASS | 0 (n/a — sin comportamiento de agente) |
| 12 | Architecture Fitness (FE) | PASS | 0 |
| 13 | Mirror detection | PASS | 0 (N3 brand-local RETIRADO → encoge mirror) |
| 14 | Decisions honored cite (R6) | PASS | A/B/C honored (commits + result files) |
| 15 | Connectivity (anti-isla) | PASS | 0 |
| 16 | Visual fidelity (canon+scope+states) | PASS | 0 |

## Findings

Cero FAIL. Cero WARN bloqueante. Observaciones (no-bloqueantes, ruteadas a CIL):

### INFO: gate-output.json stale (proceso, no código)
**Category:** 4 (proceso)
**Detalle:** el gate-runner corrió 5 min antes del fix Carril R `2867d10d`. El auditor re-corrió los gates (verificación independiente, todo verde). → CIL L1 candidato: gate-runner debe re-disparar tras commits Carril R del propio auditor (freshness gate).

### INFO: SC-19 2 flaky pass-on-retry (timing theme-hydration)
**Category:** 10
**File:** `e2e/regression/shell-core-hardening/regression-cross-tab.spec.ts`
**Detalle:** [dark] lisa/marca render + agent-colors flaky en CI por timing de hidratación de tema (NO lógica del shell). Documentado por el builder, NO enmascarado. Las 2 rondas live de Chris @1920 + toggle dark en 3 sub-tabs (dod_evidence) confirman dark estable live. → CIL L3 candidato (estabilizar `await` de theme-hydration en el spec).

## Engine boundary (core/@luana/ui-kit)

- **Único edit a `core/`:** `EntityWorkspaceLayout.tsx` (commit `d3b06b11`) — prop opcional `activeLeaf?: string | null`. **ADITIVO + backward-compatible** (ausente → comportamiento URL-derivation sin cambio; presente → override para rutas con leaf segments estáticos `/perfil`,`/resumen`). 3 tests nuevos en `__tests__/EntityWorkspaceLayout.test.tsx` (10/10).
- **Proposals accepted** (checkpoint `core_lift.proposals_status: accepted`, commit `256517a3` + `2026-06-01-lift-shell-organism`). Edit no-additivo NO ocurrió (default = consumir N3 ya shipped v0.3.0). **NO requiere escalación /pm-luana** (additive-minimal dentro del pause-point del dispatch-plan).
- **Cero otros edits a core/.** `core/luana-core-*/src/` (Python engine) NO tocado.

## Contract / Decisions Compliance (Cat 14 — R6)

| Decisión (CONTEXT-BRIEF §2) | Honored? | Evidencia |
|---|---|---|
| A — soft-nav edge-redirect 307 + revertir band-aid → next/link | ✅ | `EmbudoMetrics.tsx` `<a href>`→`<Link>` (T-4 `523fe7c8`); proxy.ts coverage documentada (matcher NO expandido, ssr:false conservado); Next NO bumpeado |
| B — N3 CONSUMIR @luana/ui-kit + RETIRAR brand-local mirror | ✅ | StaffWorkspaceShell + LeadWorkspace + NewLeadPage importan `@luana/ui-kit` (T-5 `8d62c958`/`a042e1df`); `EntitySubNavBar.tsx` brand-local DELETED (258 líneas) |
| C — dark hardcoded→token (no wholesale) | ✅ | 2 ocurrencias migradas (`bg-white`→`bg-background`, amber `dark:` variant); 0 variantes nuevas innecesarias (T-6 `a3a63802`) |

## Scope discipline + Connectivity

- **AC-1** (web-mode eliminado): `ShellModeToggle.tsx` + `ValeriaRail.tsx` físicamente borrados; grep prod `shellMode`=0 (solo comentarios de remoción + `LegacyPersistedShape.shellMode?` del migrate — intencional).
- **AC-10** (no regresión): board/KanbanBoard/stage API del embudo NO tocados (`git diff` board=∅). Embudo `developed`+`defer_audit:true` preservado.
- **Cat 15 anti-isla:** `ValeriaCollapsedStrip` (NEW) enchufado en `ShellOrganismLayoutClient` (estado A); chat-store `newConversation` consumido por `ChatHeader [+]`. Sin islas.
- **Cat 16 canon:** N3 = `EntityWorkspaceLayout` core (NUNCA cableado a mano); 0 hardcoded hex/rgb en producción; 0 arbitrary-values nuevos; estados (default/loading/empty/error) cubiertos por SC-13/SC-15. CSS-gate desktop↔mobile (`hidden md:flex`, `<Group>` siempre montado) — D4 "Rendered more hooks" evitado.

## Cross-brand pollution / mirror (Cat 13)

- **nicolify NO tocada** (`git diff nicolify/`=∅). Verificado.
- **N3 brand-local mirror RETIRADO** → encoge el sistema, no lo crece. `test-no-cross-brand-shell-mirror` 31/31 PASS.
- **nicolify cross-brand mirror del N3 (M1):** existe pero NO se toca acá (forbidden, otra brand). Convergencia nicolify→core = story /pm-luana post-merge (ya en plan, `cross_brand_consumers: [vitalia, nicolify]`). Flag heredado, no acción del PR.
- `ValeriaCollapsedStrip` + máquina nueva = NEW justificado documentado (lift candidate /pm-luana, header en componente).

## Native-First + Live Verification Audit

- ✅ Gates corridos NATIVE (npx tsc/eslint/vitest host); e2e real-backend NATIVE (E2E_BASE_URL localhost:3002, NUNCA `make e2e`).
- ✅ Commits por pathspec (no `git add .`); Conventional Commits.
- ✅ Live-verify #37 satisfecho: dod_evidence 5 acciones reales + backend log (`verify-no-backend-errors.sh` existe) + 2 rondas Chris. dod_env documenta honestamente Chrome MCP no disponible esta sesión → Playwright-autenticado como 2ª herramienta válida (precedente embudo board-live). **Surface chrome FE-only sin writes BE por diseño** (GUARD HARD: "+"/historial = UI-local Zustand mock); los "writes" = mutaciones de estado UI-local + persistencia localStorage + efecto DOM, ejercidos live. demo-script.md presente.

## Verdict Math

- Cero FAIL en categorías 1/2/3/7/11/12/14/16 → no FAIL.
- Cat 16 sin reinvención de primitiva / scope-creep / token hardcodeado / estados ausentes → no FAIL.
- Allowlists: NO crecieron sin justificación. Carril R `e4ab797c` = corrección de paths stale post-rename inbox→adrian (net violations sin cambio, documentado) + `2867d10d` = 3 tests stale alineados a conducta shipped. Shrink-only respetado (EntitySubNavBar brand-local borrado encoge el mirror).
- Gates blocker (tsc/eslint/vitest/arch) → todos PASS (re-run auditor).
- Downstream regression: cross-feature N3 surface (staff/embudo consumen ui-kit) cubierto por full vitest suite + n3-*.spec real-backend → PASS.
- LIVE_VERIFY_MISSING → NO (dod_evidence + chris_verify.signoff presentes).
- UX_HANDOFF_MISSING → NO (mockup heredado firmado backbone + ratified_visual_by_chris).
- A lo sumo 0 WARN bloqueantes; 2 INFO ruteados a CIL.
- → **PASS**

## Self-fix log (Carril R)

Ninguno nuevo requerido por el auditor en esta corrida final. Los 2 commits Carril R (`e4ab797c` allowlists post-rename + `2867d10d` 3 tests stale) ya estaban aplicados por la sesión orquestadora pre-pickup y verificados aquí (re-run gates ALL GREEN). Documentados en sus commit bodies con root-cause.

## Upstream deficiency

Ninguna del architect. El ready package (6 artifacts + dispatch-plan) estaba completo, las 3 decisiones cerradas con código, pause-points respetados. **Process HB candidato (L1):** gate-runner debió re-disparar tras los commits Carril R del cierre (gate-output.json quedó stale 5 min) — capturar en harness-backlog para que el freshness gate del gate-runner contemple Carril R commits del propio cierre autonomous.
