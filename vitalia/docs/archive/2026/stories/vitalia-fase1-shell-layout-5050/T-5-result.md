# T-5 Result — ShellModeToggle disabled chip placeholder

**Story:** vitalia-fase1-shell-layout-5050  
**Ticket:** T-5  
**Surface:** frontend  
**Commit:** d81429de  
**Branch:** wip/vitalia  
**Date:** 2026-05-23

## Summary

Finalized `ShellModeToggle.tsx` with SVG icons and created full test suite `ShellModeToggle.test.tsx` covering all gherkin_coverage scenarios from 06-tickets.yaml.

## Files Changed

| File | Action |
|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.tsx` | MODIFY — added SVG icons, finalized classes |
| `vitalia/frontend/src/components/shared/shell-organism/ShellModeToggle.test.tsx` | NEW — 13 unit tests, TDD RED→GREEN |

Note: `ShellOrganismLayout.tsx` (modify: listed in T-5 ticket) was already updated in T-3 — import and overlay mount were already present. No additional modification needed.

## Component Changes (ShellModeToggle.tsx)

- Added SVG icon for agentic mode: two equal rect panels (14×14, aria-hidden)
- Added SVG icon for web mode: narrow rail + wider main panel (14×14, aria-hidden)
- Updated classes: `flex h-8 items-center gap-1.5 ... opacity-70` (from stub `inline-flex gap-1 opacity-60`)
- Extracted `label` variable for DRY SVG conditional + span
- Preserved: `disabled`, `aria-disabled="true"`, `data-testid`, `aria-label`, `title`, `cursor-not-allowed`

## Test Suite (ShellModeToggle.test.tsx)

13 tests, all PASS:

| # | Test | Gherkin coverage |
|---|---|---|
| 1 | renders a disabled button | `disabled attribute` |
| 2 | has aria-disabled='true' | `aria-disabled='true'` |
| 3 | renders 'Agéntico' label when shellMode='agentic' | `renders 'Agéntico' label when shellMode='agentic'` |
| 4 | renders 'Web' label when shellMode='web' | `renders 'Web' label when shellMode='web'` |
| 5 | has data-testid='shell-mode-toggle' | `data-testid='shell-mode-toggle'` |
| 6 | has title attribute present | title presence |
| 7 | has aria-label 'Modo de shell: agéntico activo' when mode is agentic | `aria-label='Modo de shell: agéntico activo'` |
| 8 | has aria-label containing 'web' when mode is web | aria-label web variant |
| 9 | renders icon svg with aria-hidden when mode is agentic | icon svg (aria-hidden) agentic |
| 10 | renders icon svg with aria-hidden when mode is web | icon svg (aria-hidden) web |
| 11 | uses Spanish neutro: 'Agéntico' with tilde (no voseo) | Spanish neutro correctness |
| 12 | has cursor-not-allowed class for visual UX | cursor-not-allowed class |
| 13 | click events not fired when disabled | `click events not fired when disabled` |

## Validators

```
tsc --noEmit        → 0 errors ✅
eslint --max-warnings=0 → 0 warnings ✅
vitest run          → 13/13 PASS ✅
```

## Cross-brand Mirror Check

```bash
grep -rn "ShellModeToggle" nicolify/frontend/src comunify/frontend/src lupulo/frontend/src 2>/dev/null
→ 0 matches ✅ (brand-local component, no cross-brand consumers)
```

## Skills Consulted

| Skill | Invoked | Decision |
|---|---|---|
| `frontend-expert` | Yes | runtime-quality-checklist: selector-based Zustand mock via `vi.fn().mockImplementation(selector => selector(state))` — correct pattern for `useShellStore((s) => s.shellMode)` |
| `tessl__react-patterns` | Yes | disabled button: `disabled` + `aria-disabled="true"` both required; SVG icons with `aria-hidden="true"` correct (decorative) |
| `tessl__vitest` | Yes | `vi.mock` hoisting + `beforeEach(vi.clearAllMocks)` pattern; `useShellStore as unknown as Mock` cast for typed mock |
| `tessl__tailwind` | Yes | `cursor-not-allowed` on disabled button; no inline `style={{}}` |

## TDD Process

1. **RED phase**: wrote test file first — 11 tests passed (existing stub), 2 failed (SVG tests: `expected null not to be null`)
2. **GREEN phase**: added SVG icons to component — all 13 tests pass
