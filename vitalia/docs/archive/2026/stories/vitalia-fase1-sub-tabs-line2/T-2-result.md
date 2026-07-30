# T-2 Result — agentTextClassSubTab Tailwind helper

**Story:** vitalia-fase1-sub-tabs-line2 (F1-S8)
**Ticket:** T-2 — _agent-tw-classes.ts EXTEND: agentTextClassSubTab with Lucas + Config exceptions
**Date:** 2026-05-25
**State:** pushed

## Summary

Extended `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` in-place
with `agentTextClassSubTab(slug: RibbonTabSlug): string` helper consumed by SubTab molecule (T-3).

Exceptions per 03-arch.md D18/D19:
- `lucas` → `"text-foreground"` (hex #111111 near-black causes poor contrast on bg-agent-lucas-soft)
- `config` → `"text-foreground"` (Config not an agent; bg-muted neutral per mockup)
- All other slugs → `"text-agent-{slug}"` (standard semantic tokens)

Also created `__tests__/_agent-tw-classes.test.ts` with 13 tests covering all cases + F1-S6 regression guard.

## Files Modified

| File | Type | Change |
|---|---|---|
| `vitalia/frontend/src/components/shared/shell-organism/_agent-tw-classes.ts` | Production | +35 lines (agentTextClassSubTab function) |
| `vitalia/frontend/src/components/shared/shell-organism/__tests__/_agent-tw-classes.test.ts` | Test | NEW — 13 tests |

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint` (modified files) | PASS (0 errors) |
| `vitest run` (test file) | PASS (13 tests, 13 passed) |
| Prettier | PASS |

## Design Decisions

- Import widened from `AgentSlug` to `RibbonTabSlug` — `agentTextClassSubTab` accepts `config` slug
  (which is not an AgentSlug). TypeScript exhaustiveness default branch uses `never` assertion.
- Kept `agentTextClass` (F1-S6) unchanged — different semantic (TypingIndicator/DelegateMarker
  text color uses full saturation agent color, SubTab active state uses exception-aware version).
- No dynamic class construction per Tailwind v4 JIT constraint.
