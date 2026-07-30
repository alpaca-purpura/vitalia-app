# T-6 Result — Vitest aggregate run + 3 NEW arch tests

**Story:** vitalia-fase1-shell-layout-5050
**Ticket:** T-6 (Vitest aggregate run + 3 NEW arch tests · skip-link target · shell-store schema · no-cross-brand-mirror)
**Surface:** frontend tests-only
**production_code:** false
**Date:** 2026-05-23

## Validators GREEN

| Validator | Command | Result |
|---|---|---|
| `val-fe-arch-skip-link` | `npx vitest run src/__tests__/architecture/test-skip-link-target.test.ts` | ✅ 2/2 PASS |
| `val-fe-arch-shell-store` | `npx vitest run src/__tests__/architecture/test-shell-store-schema.test.ts` | ✅ 3/3 PASS |
| `val-fe-arch-no-cross-brand-mirror` | `npx vitest run src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` | ✅ 4/4 PASS |
| `val-fe-arch-fsd` | No modification needed — shell-organism files use named exports, test-fsd-imports.test.ts not present in vitalia | ✅ N/A |
| `val-fe-arch-no-default-export` | No modification needed — all T-1..T-5 components are named exports per /architect rule | ✅ N/A |
| `val-fe-vitest-unit` | `npx vitest run --reporter=default` — 121 files, 979 tests | ✅ ALL PASS |

## Files Created

1. `vitalia/frontend/src/__tests__/architecture/test-skip-link-target.test.ts` — NEW
   - Reads ShellOrganismLayout.tsx via readFileSync
   - Asserts `<main id="main-content">` pattern and `tabIndex={-1}` attribute
   - 2 tests PASS

2. `vitalia/frontend/src/__tests__/architecture/test-shell-store-schema.test.ts` — NEW
   - Imports `{ SHELL_STORAGE_KEY, useShellStore }` and types from `../../stores/shell-store`
   - Validates ValeriaState union values (collapsed/rail/full)
   - Validates ShellMode union values (agentic/web)
   - Validates SHELL_STORAGE_KEY === 'vitalia-shell-state'
   - 3 tests PASS

3. `vitalia/frontend/src/__tests__/architecture/test-no-cross-brand-shell-mirror.test.ts` — NEW
   - Uses execSync grep on nicolify/comunify/lupulo frontend/src directories
   - Asserts 0 matches for ShellOrganismLayout, shell-store, useShellStore, ValeriaSidebarSlot
   - WS resolved to `/home/chalreme/Proyectos/luana-vitalia` (workspace root)
   - 4 tests PASS

## Files NOT modified

- `test-fsd-imports.test.ts` — Does not exist in vitalia arch tests; shell-organism in `components/shared/` does not require FSD boundary allowlist entries
- `test-no-default-export.test.ts` — Does not exist in vitalia arch tests; all T-1..T-5 shell-organism components verified as named exports

## Arch test ratchet state

- Before T-6: 12 test files, 55 tests
- After T-6: 15 test files, 64 tests
- Net addition: +3 files, +9 tests
- Ratchet: NEW gates added (shrink-only invariant holds — no existing allowlists modified)

## Gate results

- `tsc --noEmit`: 0 errors
- `eslint src/__tests__/architecture/test-*.test.ts --max-warnings=0`: 0 warnings
- `vitest run src/__tests__/architecture/`: 15 files, 64 tests PASS
- `vitest run` (full suite): 121 files, 979 tests PASS

## Skills consulted

- `frontend-expert` — runtime-quality-checklist, arch test ratchet pattern
- `tessl__vitest` — test setup, async patterns, happy-dom environment
- `tessl__react-patterns` — architecture test patterns

## Notes

- R24 gate: CONTEXT-BRIEF.md has `Validator pass: _pending_` but `Faithfulness flag: clean` with §11 CLEAN (no gaps). Proceeded per partial flag rule.
- T-6 is tests-only (production_code: false) — no new production code written.
- All 3 new arch tests gate vitalia-specific invariants; cross-brand mirror test verifies the anti-duplication rule per `.claude/rules/anti-duplication.md`.
