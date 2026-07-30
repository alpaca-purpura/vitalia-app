# T-FE-obs4 — success/warning semantic tokens (Badge) · RESULT

**Story:** vitalia-fase2-mateo-nueva-cita · state `developed` · phase `AWAIT_CHRIS_VERIFY` (NO transition)
**Commit:** `d9b57128` (pushed wip/vitalia)
**Scope:** tokens only — `globals.css` + `tailwind.config.ts` + 1 arch-test. Zero kit, zero BE, zero other modules/brands.

## Root cause (verified)

`@luana/ui-kit` Badge (`core/@luana/ui-kit/src/badge.tsx`) `success`/`warning` variants emit
`bg-success text-success-foreground` / `bg-warning text-warning-foreground`. Vitalia defined only the
namespaced `--vitalia-success`/`--vitalia-warning` — NOT the bare `--success`/`--warning` the kit
consumes. So `bg-success`/`bg-warning` resolved to nothing → the `available` (success) and
`out_of_hours` (warning) chips of `AvailabilityChip` rendered as plain text. `destructive` (busy) and
`secondary` (no_schedule) painted because those tokens already exist → 2 of 4 chips mute.

Why unit tests missed it: `AvailabilityChip.test.tsx` asserts the variant is *applied*
(`data-variant="success"`) — orthogonal to whether the token *paints*. Token-vs-render gap. Cazado por
la live-verify del orchestrator (Chrome MCP).

## Diff summary

| File | Change |
|---|---|
| `vitalia/frontend/src/app/globals.css` | `:root`: `--success: 142 76% 36%` / `--success-foreground: 0 0% 98%` / `--warning: 33 91% 44%` / `--warning-foreground: 0 0% 98%` (values = existing `--vitalia-success` #16A34A / `--vitalia-warning` #D97706). `.dark`: same tokens dropped in lightness (`142 60% 30%` / `33 80% 38%`) following the destructive criterion, foreground near-white. |
| `vitalia/frontend/tailwind.config.ts` | `colors.success` / `colors.warning` with `DEFAULT` + `foreground` (mirror of `destructive`). |
| `vitalia/frontend/src/__tests__/architecture/test-semantic-badge-tokens.test.ts` | NEW regression gate (6 tests): asserts tailwind.config defines both keys (DEFAULT+foreground bound to the vars) + globals.css declares the 4 vars. Closes the gap deterministically — `bg-success`/`bg-warning` from the kit can never be dead in vitalia again. |

`AvailabilityChip.tsx` / `NuevaCitaView.tsx` untouched (already correct — the fix is purely tokens).

## Gate output (literal)

```
$ npx tsc --noEmit            → TSC_EXIT=0
$ npx eslint src/ --cache     → ESLINT_EXIT=0
$ npx vitest run src/features/mateo/ src/__tests__/architecture/
  test-semantic-badge-tokens.test.ts (6 tests)  ✓   ← new gate GREEN
  AvailabilityChip.test.tsx (12 tests)          ✓
  FreeDoctorsList.test.tsx (6 tests)            ✓
  Test Files  2 failed | 62 passed (64)
  Tests       2 failed | 593 passed (595)
```

### The 2 failures are PRE-EXISTING (out of scope — NOT my change)

Confirmed by stashing my edits + removing my test, then re-running the 2 tests in isolation: **both still fail**
without my change (6 passed / 2 failed). Neither relates to obs#4 tokens; my diff added zero TSX/components.

- `test-no-div-layout.test.ts` — ratchet `123 > 121` (canon §2.7 raw-`<div>` layout count). Drift from parallel
  sessions adding components; my diff = CSS + config + `.test.ts` only.
- `test-kit-shell-fixture-mirror.test.ts` — reads `core/@luana/ui-kit/stories/_shell-fixtures.tsx`
  (`DEMO_RIBBON_ORDER` not found). That kit file shows `M` in the session git status at start (modified by
  another session); my HARD scope is tokens-only, NO kit. Left untouched.

## Live-verify

NOT run here (no Chrome MCP in this session). The orchestrator runs the 4-chip live-verify with the already-driven
flow (available → success green pill · busy → destructive red pill · out_of_hours → warning amber pill ·
no_schedule → secondary gray pill). NOT claiming "verified live".

## Cross-brand note (NOT fixed — route to /pm-luana)

The same gap very likely exists in **nicolify** and **comunify**: `@luana/ui-kit` Badge `success`/`warning`
variants would be mute there too if those brands also lack the bare `--success`/`--warning` tokens (each brand
owns its own `globals.css` + `tailwind.config.ts`). Per HARD scope I did NOT touch those brands. Orchestrator →
**/pm-luana** to verify + (likely) replicate the token addition per brand, and/or consider an arch-test lift so
every kit-consumer brand asserts the bare semantic tokens.

## Skills consulted

- **frontend-expert** — FSD-Lite + arch-test location (`src/__tests__/architecture/`) + quality gates (tsc/eslint/vitest). Decision: new gate follows the existing `test-ds-single-token-source.test.ts` read-file-and-regex pattern (no component render needed — token presence is a static contract).
- **vitalia-design-system** (authority of tokens = globals.css + tailwind.config) — confirmed tokens of color live in `globals.css` (not `@luana/design-tokens`, which only exports z-index). Reused the existing brand green/amber values (`--vitalia-success` #16A34A / `--vitalia-warning` #D97706) per RN-5 (names shared, values per-brand) instead of inventing a new palette. Mirrored the `destructive` light+dark pattern exactly.
- **frontend-visual-fidelity rule** (D1 design-system-first) — fix composes from the existing kit Badge + brand tokens; no new primitive, no local CSS, no `<select>`/arbitrary-value introduced. The token is the missing brand binding the kit already expects.
