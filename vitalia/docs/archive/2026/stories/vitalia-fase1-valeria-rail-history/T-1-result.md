# T-1 Result — useKeyboardShortcuts hook

**Story:** vitalia-fase1-valeria-rail-history (F1-S5)
**Ticket:** T-1
**Branch:** wip/vitalia
**Commit SHA:** 2ffb9200
**Date:** 2026-05-23

---

## Skills consulted (must_load enforcement v4.1)

| Skill | Status | When invoked | Decision taken |
|---|---|---|---|
| `frontend-expert` | LOADED | Pre-implementation | Hook location: `vitalia/frontend/src/hooks/` (per FSD-Lite hooks layer). Cleanup pattern: useEffect return with removeEventListener. `[shortcuts]` dep array — re-attach on identity change. Runtime quality checklist read. |
| `tessl__react-patterns` | LOADED | Pre-implementation | useEffect cleanup contract mandatory. No `useEffect` for data fetching (not applicable). Dependency array uses `[shortcuts]` only — stable module-level helpers excluded. |
| `tessl__vitest` | LOADED | Pre-test-writing | RTL `renderHook` pattern. `vi.spyOn(window, 'addEventListener')` for cleanup tests. `Object.defineProperty` for read-only event properties (`isComposing`, `target`). |

---

## Diff summary

**Files created (2 NEW):**

| File | LOC | Description |
|---|---|---|
| `vitalia/frontend/src/hooks/useKeyboardShortcuts.ts` | 144 | Generic hardened keyboard shortcuts hook — `ShortcutsMap` type + `useKeyboardShortcuts` function |
| `vitalia/frontend/src/hooks/__tests__/useKeyboardShortcuts.test.ts` | 295 | 11 Vitest tests (TDD RED → GREEN) |

**Total:** 439 LOC (2 files, 0 modified, 0 deleted)

---

## Validator gates output

### Vitest: 11/11 PASS

```
✓ src/hooks/__tests__/useKeyboardShortcuts.test.ts (11 tests) 21ms

Test Files  1 passed (1)
Tests  11 passed (11)
```

Tests covered:
1. dispatches bare lowercase key handler (`r` → handler called)
2. dispatches Escape exact match handler
3. dispatches `mod+k` via metaKey (Mac)
4. dispatches `mod+k` via ctrlKey (Windows/Linux cross-platform)
5. skips dispatch when focus in INPUT
6. skips dispatch when focus in TEXTAREA
7. skips dispatch when focus in `[contenteditable=true]`
8. modifier shortcuts (Cmd+K) BYPASS focus-in-input guard
9. skips dispatch when `e.isComposing=true` (IME composition)
10. removeEventListener on unmount (cleanup contract)
11. re-attaches handler when shortcuts dict identity changes

### TypeScript strict: 0 errors (hook files)

```
npx tsc --noEmit → 0 errors in src/hooks/useKeyboardShortcuts.ts
                   0 errors in src/hooks/__tests__/useKeyboardShortcuts.test.ts
```

Pre-existing tsc error in `ValeriaRail.test.tsx` (future ticket T-3, not T-1 scope).

### ESLint: 0 errors

```
npx eslint src/hooks/useKeyboardShortcuts.ts src/hooks/__tests__/useKeyboardShortcuts.test.ts --cache
→ (no output = 0 errors)
```

### Prettier: OK

```
npx prettier --check src/hooks/useKeyboardShortcuts.ts src/hooks/__tests__/useKeyboardShortcuts.test.ts
→ All matched files use Prettier code style!
```

---

## Anti-duplication scan (pre-write audit)

```bash
for b in nicolify comunify lupulo; do
  grep -rln "useKeyboardShortcuts" ${WS}/$b/frontend/src 2>/dev/null | wc -l
done
# Result: 0 / 0 / 0 — NO cross-brand mirror exists
```

Verdict: CLEAN. First consumer. LIFT CANDIDATE for `/pm-luana` promotion when second consumer (Nicolify/Comunify/Lupulo) needs keyboard shortcuts.

---

## LIFT CANDIDATE note

`useKeyboardShortcuts` has zero brand-specific logic (hardened guard: IME + input focus + modifier bypass). Promotable to `core/@luana/hooks/use-keyboard-shortcuts/` (or `@luana/ui-kit`) when a 2nd consumer exists. Action: `/pm-luana` lift story post F1-S5 merge. No action required in this ticket.

---

## Live verification

`chrome-devtools-verify` skill is DEPRECATED on Linux Mint (WSL2+Windows bridge). This PR touches only a new hook + tests (no route, no page, no UI component rendered). No Chrome DevTools verification required per runtime-quality-checklist.md § "Cuándo skip" — hook-only change with no `app/**/page.tsx` or component rendering.

---

## Implementation notes

The `useKeyboardShortcuts` signature is:

```typescript
export type ShortcutsMap = Record<string, () => void>;
export function useKeyboardShortcuts(shortcuts: ShortcutsMap): void;
```

Key format:
- Bare key: `"r"`, `"f"`, `"Escape"` — exact `e.key` match, no modifier
- Modifier: `"mod+k"` — `(e.metaKey || e.ctrlKey)` + `e.key === "k"`

Guard evaluation order (per D4 spec):
1. `e.isComposing` → skip always (IME)
2. Modifier shortcut → bypass input guard, fire
3. Bare shortcut + in editable context → skip

`passive: true` on the listener (no `preventDefault` called, safe for scroll performance).

---

## Arch tests

F1-S5 story arch tests (T-7 ticket scope) — not yet extended in T-1. The hook is brand-local, no FSD boundary violations, no hex colors, no cross-brand imports. Arch tests `test_server_first.test.ts` unaffected (no `"use client"` added — hook is a plain TS module, not a component).
