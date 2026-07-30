<!-- voseo-allowed: audit phase D gherkin matrix may cite spec scenarios verbatim -->

# Phase D — Gherkin Verification Matrix

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Auditor:** auditor-frontend (Opus, story-level review)
**Date:** 2026-05-24
**Mapping basis:** 01-spec.md § 1 Scenarios SC-1..SC-9 → Playwright spec files.

## Coverage table

| Scenario | Type | Spec file (Playwright) | Tests run | Status | Evidence |
|---|---|---|---|---|---|
| SC-1 happy keyboard cycle | happy | `keyboard-cycle.spec.ts` | 6 | ✅ PASS | press r/f/c/Esc/r + localStorage persist all green |
| SC-2 negative typing guard | negative | `typing-guard.spec.ts` | 4 | ✅ PASS | typing "COMPRAR" no state change + Cmd+K bypass |
| SC-3 edge IME composition | edge | `ime-composition.spec.ts` | 2 | ✅ PASS | `e.isComposing` skip + dispatchEvent(compositionstart) |
| SC-4 adversarial store tampering | adversarial | `store-tampering.spec.ts` | 3 | ✅ PASS | INVALID state → console.warn + fallback render no crash |
| SC-5 edge click PanelLeftClose | edge | `click-collapse.spec.ts` | N | ✅ PASS | collapsed + auto-coupling shellMode='web' |
| SC-6 empty_state search | empty_state | `history-empty-search.spec.ts` | 5 | ✅ PASS | EmptyStateInline rendered + groups hidden + Esc clear |
| SC-7 a11y keyboard + axe wcag2aa | accessibility | `a11y-keyboard.spec.ts` | 7 | ✅ PASS | aria-expanded + live region + axe 0 violations rail/full/collapsed |
| SC-8 a11y mobile drawer + axe wcag2aa | accessibility | `a11y-mobile-drawer.spec.ts` | 6 | ✅ PASS | role=dialog + aria-modal + backdrop close + Esc + axe 0 violations |
| SC-9 i18n Spanish neutro | i18n | `i18n-spanish-neutro.spec.ts` | 6 | ✅ PASS | 28 strings verbatim + zero voseo regex + zero English placeholders |

**Total Playwright functional tests:** 45/45 PASS (project=smoke, native Linux, port 3002).

**Visual goldens (separate spec):** 13/13 PASS (project=visual, ratchet iter 1 baseline established).

## Sub-categorías N/A justification verification

| Sub-cat | Applies? | Justification quoted from spec § 1 |
|---|---|---|
| race_condition | NO | "Story no crea/edita recursos persistentes con unique constraint. Mock data es read-only hardcoded; valeriaState transitions son setState local sin DB." ✓ |
| concurrent_users | NO | "Shell chrome per-user (zustand local + localStorage). No comparte estado entre tenants/users." ✓ |
| network_failure | NO | "F1-S5 no realiza fetch API alguno. Mock conversaciones son import estático desde _mock-conversations.ts." ✓ |
| large_dataset | NO | "Mock data = 8 items hardcoded. Pagination/virtualization queda para Fase 2." ✓ |

All N/A justifications are valid for FE-only shell organism story with mock data.

## Skill/rule coverage per scenario

| Skill / Rule | Validates scenarios | Status |
|---|---|---|
| tessl__react-patterns | SC-3 (IME), SC-4 (adversarial guard), SC-7 (keyboard), createPortal (T-5.bis) | ✅ |
| tessl__shadcn-ui | Button/Input/Tooltip in ValeriaRail/ValeriaHistory/ValeriaSidebar | ✅ |
| tessl__tailwind | Semantic tokens (zero hex) — arch test test_no_hardcoded_colors PASS | ✅ |
| tessl__vitest | 1080/1080 unit tests PASS, 16 arch test files (83 tests) PASS | ✅ |
| frontend-expert (runtime-quality-checklist) | useEffect deps stable, no stale closures, hooks contract | ✅ |
| playwright-expert | POM ValeriaSidebarPage + Clerk auth fixture reuse F1-S4 + addInitScript determinism | ✅ |
| spanish-text.md | SC-9 grep + arch test test-vitalia-ui-strings-no-voseo (18 tests) | ✅ |
| hipaa-lite.md (vitalia overlay) | Mock data zero PHI, scope=N/A documented in checkpoint | ✅ |
| shell-mockup-per-component.md (vitalia overlay) | mockups/valeria-rail.html + valeria-history.html ratificados Chris iter 1, 13 visual goldens generated | ✅ |
| anti-duplication.md | 0 cross-brand matches (8 NEW names verified via grep + arch test test-no-cross-brand-shell-mirror) | ✅ |

## Verdict

**Phase D Gherkin coverage:** 9/9 scenarios mapped 1:1 to Playwright specs, 100% PASS rate.

