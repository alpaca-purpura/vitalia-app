# Gherkin verification matrix — vitalia/vitalia-shell-state-persistence

> Auditor: Phase D (auditor-frontend consolidated)
> Date: 2026-05-28T22:05:00-05:00
> Source: 01-spec.md scenarios SC-1..SC-8 + SC-5b · gate-output.json · E2E run 28/28

| Scenario (Gherkin) | Test path | Status | Notes |
|---|---|---|---|
| SC-1 — valeriaState survives reload | e2e/regression/shell-state-persistence/valeria-state-survives-reload.spec.ts + resize-and-state.spec.ts (un-skipped) | ✅ PASS | reload preserves 'rail' |
| SC-2 — shellMode survives reload | e2e/regression/shell-state-persistence/valeria-state-survives-reload.spec.ts | ✅ PASS | 'web' preserved |
| SC-3 — NO spurious 'full' write during SSR+hydration (the bug) | src/stores/__tests__/shell-store-hydration.test.ts + e2e instrumentSetItem | ✅ PASS | adversarial: 'full' never written when 'rail' saved; setItem no-op pre-hydration verified |
| SC-4 — fresh mobile drawer CLOSED (independent of desktop full) | e2e/regression/shell-state-persistence/mobile-collapsed-default.spec.ts + mobile-collapse.spec.ts (un-skipped) | ✅ PASS | no role=dialog at mount; valeriaState='full' does NOT auto-open |
| SC-5 — burger opens mobile drawer | e2e/regression/shell-state-persistence/mobile-collapsed-default.spec.ts | ✅ PASS | tap burger → role=dialog + focus trap |
| SC-5b — mobile remembers open/closed across reload (independent slice) | e2e/regression/shell-state-persistence/mobile-collapsed-default.spec.ts | ✅ PASS | mobileDrawerOpen slice persists separate from valeriaState |
| SC-6 — first visit no persisted value → default | src/stores/__tests__/shell-store-hydration.test.ts | ✅ PASS | default full/agentic, single clean write |
| SC-7 — corrupt localStorage no crash | src/stores/__tests__/shell-store-hydration.test.ts | ✅ PASS | falls back to default, no throw |
| SC-8 — a11y wcag2aa keyboard + screen-reader | e2e/regression/shell-state-persistence/mobile-collapsed-default.spec.ts (@a11y) | ✅ PASS | axe wcag2aa + Tab→burger→Enter→Escape focus return; aria-expanded/label neutro |

**Verdict:** 9/9 scenarios PASS. No NO_COVERAGE, no FAIL. Phase D GREEN.
