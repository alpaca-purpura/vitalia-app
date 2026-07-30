# T-4 Result — AppPanelSlot Integration + Arch Tests

**Story:** vitalia-fase1-ribbon-6-tabs
**Ticket:** T-4
**State:** pushed
**Surface:** frontend
**Builder:** claude-sonnet-4-6
**Date:** 2026-05-25

---

## Summary

T-4 implements the AppPanelSlot integration with the real `<Ribbon />` organism (built in T-3) and adds/extends arch fitness tests for the new Ribbon shell-organism pattern.

---

## Files Changed

| File | Action | Lines |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.tsx` | MODIFY | 89 |
| `vitalia/frontend/src/components/shared/shell-organism/AppPanelSlot.test.tsx` | MODIFY | 139 |
| `vitalia/frontend/src/__tests__/architecture/test-ribbon-no-shadcn-tabs.test.ts` | NEW | 89 |
| `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | EXTEND | +5 lines |
| `vitalia/frontend/src/__tests__/architecture/test-vitalia-ui-strings-no-voseo.test.ts` | EXTEND | +60 lines |
| `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/06-tickets.yaml` | MODIFY | state: pushed |
| `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/T-4-impl-log.md` | NEW | — |
| `vitalia/docs/product/stories/vitalia-fase1-ribbon-6-tabs/T-4-result.md` | NEW | — |

**Note:** `test_server_first.test.ts` — no changes needed. The test tracks `KNOWN_MISSING_USE_CLIENT` (files with hooks but missing "use client"). Since Ribbon/RibbonTab/ConfigTab already have "use client", no violations exist and no allowlist modification was required.

---

## Gherkin Coverage

| Scenario | Tests | Status |
|---|---|---|
| (integration) AppPanelSlot renders `<Ribbon />` real | 7 tests in AppPanelSlot.test.tsx | PASS |
| (arch) test-ribbon-no-shadcn-tabs.test.ts NEW invariant | 6 tests | PASS |
| (arch) test-no-cross-brand-shell-mirror.test.ts EXTEND | 21 tests total | PASS |
| SC-8 i18n voseo glossary EXTEND | 24 tests total | PASS |
| (arch) invariants heredados preserved | 107 arch tests total | PASS |

**Total: 1327 tests across 137 test files — ALL GREEN**

---

## Quality Gate Results

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| `eslint src/ --cache` (scoped) | PASS — 0 errors |
| `prettier --check` (scoped) | PASS — auto-fixed 4 files |
| `vitest run AppPanelSlot.test.tsx` | PASS — 11/11 |
| `vitest run src/__tests__/architecture/` | PASS — 107/107 (18 test files) |
| `vitest run --coverage` (full) | PASS — 1327/1327 (137 files) |

---

## Key Decisions

1. **Server/Client boundary preserved**: AppPanelSlot remains a Server Component. It imports `<Ribbon />` (Client Component) — correct Next.js App Router pattern. Client boundary lives at `Ribbon.tsx`.

2. **Arch invariant: no Shadcn Tabs in Ribbon**: `test-ribbon-no-shadcn-tabs.test.ts` enforces that Ribbon/RibbonTab/ConfigTab never import from `@/components/ui/tabs`. Route-based navigation requires `usePathname()` state, not internal Radix Tabs state.

3. **Cross-brand isolation**: All new shell-organism names (`Ribbon`, `RibbonTab`, `ConfigTab`, `AGENT_RIBBON_ORDER`, `extractAgentFromPath`) are brand-local vitalia. 0 cross-brand matches confirmed by `test-no-cross-brand-shell-mirror.test.ts`.

4. **Autosave children architecture**: Children rendered directly (not as absolute overlay), content skeleton shown when no children — cleaner F1-S10 integration point.

---

## Next Ticket

**T-5** — Playwright E2E suite (POM + 9 behavior specs + 11 visual goldens + axe + i18n). Depends on T-4 (this ticket). State: ready.
