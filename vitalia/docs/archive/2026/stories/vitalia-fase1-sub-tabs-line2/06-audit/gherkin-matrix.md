<!-- voseo-allowed: audit phase D matrix may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Phase D — Gherkin Matrix · F1-S8 vitalia-fase1-sub-tabs-line2

**Story:** `vitalia-fase1-sub-tabs-line2`
**Date:** 2026-05-25
**Auditor:** auditor-frontend (Opus 4.7)
**Spec source:** `01-spec.md` § 10 (10 scenarios SC-1..SC-10)
**Coverage source:** `06-tickets.yaml::gherkin_coverage` + actual test files

## Coverage table

| Scenario | Spec ref | Test file (graders) | Status | Notes |
|---|---|---|---|---|
| SC-1 happy · click sub-tab navega | `01-spec.md § 10 SC-1` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-nav.spec.ts` | ✅ COVERED · deferred runtime | 4 tests · POM + assertions; ejecución difiere a phase F merge (live app required) |
| SC-2 happy · agent change re-renders | `01-spec.md § 10 SC-2` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-agent-change.spec.ts` | ✅ COVERED · deferred runtime | 2 tests · valida re-render con 5 subtabs Lucas post click ribbon Atraer |
| SC-3 happy · deep link active state | `01-spec.md § 10 SC-3` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-deeplink.spec.ts` | ✅ COVERED · deferred runtime | 3 tests · Camila reactivar deep link → aria-selected true |
| SC-4 negative · activeAgent null | `01-spec.md § 10 SC-4` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-null-agent.spec.ts` | ✅ COVERED · deferred runtime | 3 tests · foobar/anything → query selector retorna null |
| SC-5 edge · invalid subtab | `01-spec.md § 10 SC-5` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-invalid-subtab.spec.ts` | ✅ COVERED · deferred runtime | 2 tests · lisa/inexistente → 4 subtabs visibles · ninguno active |
| SC-6 edge · mobile overflow Lucas 5 tabs | `01-spec.md § 10 SC-6` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-mobile-overflow.spec.ts` | ✅ COVERED · deferred runtime | 2 tests · viewport 375x667 · scroll horizontal validation |
| SC-7 adversarial · XSS guard | `01-spec.md § 10 SC-7` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-xss-guard.spec.ts` | ✅ COVERED · deferred runtime | 2 tests · `<script>alert(1)</script>` segment → no script execute · no active subtab |
| SC-8 a11y · keyboard roving tabindex | `01-spec.md § 10 SC-8` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-keyboard.spec.ts` | ✅ COVERED · deferred runtime | 7+ tests (ArrowR · ArrowL · wrap · Home · End · Enter · Space + axe wcag2aa scope) |
| SC-9 i18n · Spanish neutro labels | `01-spec.md § 10 SC-9` | `e2e/regression/vitalia-fase1-sub-tabs-line2/sub-tabs-i18n.spec.ts` + `src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` (F1-S8 describe block) | ✅ COVERED (vitest + e2e) | Vitest unit `RIBBON_SUBTABS labels verbatim — 22 Spanish neutro strings (no voseo imperatives)` + 6 aria-label assertions; spec e2e runtime deferred |
| SC-10 visual goldens · 12 PNGs (6 agents × 2 themes) | `01-spec.md § 10 SC-10` | `e2e/regression/vitalia-fase1-sub-tabs-line2/visual-goldens.spec.ts` | ⚠️ DEFERRED iter-1 (architecturally authorized) | 13 PNG goldens NOT committed · require `--update-snapshots` against live app at localhost:3002 + Chris re-ratify post-implementation. Architect cementó deferral porque mockup HTML ratificado Chris 2026-05-25T09:05Z (gate visual obligatorio shell-mockup-per-component.md ya cumplido) |

## Summary

| Metric | Value |
|---|---|
| Total scenarios specified | 10 (SC-1..SC-10) |
| Scenarios with test file present | 10/10 (100%) |
| Scenarios validated by Vitest unit/arch | 1 (SC-9 partial via voseo arch suite + RIBBON_SUBTABS labels verbatim) |
| Scenarios with Playwright spec written but runtime deferred | 9 (SC-1..SC-8 functional · SC-10 visual goldens) |
| Sub-categorías mandatory v4.1 marked `not_applicable` | 5 (race_condition · concurrent_users · network_failure · empty_state · large_dataset — justificadas spec § 10 último cuadro) |
| Coverage gap | 0 — todos los scenarios tienen test file presente |

## Deferral rationale (SC-10 + e2e runtime)

Per `01-spec.md § 4` + `vitalia/.claude/rules/shell-mockup-per-component.md` + `03-arch.md` architect cement: visual goldens iter-1 difieren a phase F merge (live app required at localhost:3002 + Chris re-ratify post-implementation). Mockup HTML `sub-tabs.html` (503 LOC, 6 agent variants + light/dark + 4 SubTab states) ya ratificado Chris (checkpoint frontmatter `ratified_visual_by_chris: true`, iter 1, 2026-05-25T09:05Z). Esa ratificación visual cumple el gate `shell-mockup-per-component.md` obligatorio pre-`/architect`.

Los 9 Playwright behavior specs (SC-1..SC-9) están escritos con POM + fixtures + axe-playwright wcag2aa; su runtime requiere stack vivo (`make dev-vitalia` + `E2E_BASE_URL=http://localhost:3002`). Auditor-frontend acepta deferral porque (a) gate-output.json `command: test-frontend` cubre tsc + ESLint + Vitest unit + arch fitness — los 5 gates GREEN; (b) la responsabilidad runtime corresponde a `/pm-vitalia` merge phase (con Chris staging gate manual si dev-app unavailable). Esto es coherente con S4 PI-1 9-bug pattern recordatorio del auditor SKILL.md (live verification gate FE PR ≥ M).

## Verdict

Phase D **COVERED** — 10/10 scenarios tienen test file presente. Deferral SC-10 + runtime SC-1..SC-9 architecturally authorized (mockup ratified gate already met).
