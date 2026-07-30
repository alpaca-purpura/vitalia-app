# T-1 Result — SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath

**Story:** vitalia-fase1-sub-tabs-line2 (F1-S8)
**Ticket:** T-1 — Extend agent-catalog.ts with SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath
**Date:** 2026-05-25
**State:** pushed

## Summary

Extended `vitalia/frontend/src/lib/agent-catalog.ts` in-place (per Q1 cement / anti-duplication.md)
with F1-S8 catalog data:

- `SubTabMeta` interface (id: string, label: string, icon: string)
- `RIBBON_SUBTABS: Record<RibbonTabSlug, readonly SubTabMeta[]>` — 22 sub-tabs across
  lisa(4) / lucas(5) / adrian(4) / valeria(2) / camila(4) / config(3) / mateo(0 — transversal)
- `extractSubtabFromPath(pathname: string | null | undefined): string | null` helper

Also extended `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` with 30 new F1-S8 tests
covering SubTabMeta shape, RIBBON_SUBTABS distribution, labels (Spanish neutro), icons, and
extractSubtabFromPath valid/invalid/null paths.

## Files Modified

| File | Type | Change |
|---|---|---|
| `vitalia/frontend/src/lib/agent-catalog.ts` | Production | +72 lines (SubTabMeta + RIBBON_SUBTABS + extractSubtabFromPath) |
| `vitalia/frontend/src/lib/__tests__/agent-catalog.test.ts` | Test | +200 lines (30 new F1-S8 tests) |

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `eslint src/lib/agent-catalog.ts src/lib/__tests__/agent-catalog.test.ts` | PASS (0 errors) |
| `vitest run src/lib/__tests__/agent-catalog.test.ts` | PASS (83 tests, 83 passed) |
| Prettier | PASS |

## Design Decisions

- `RIBBON_SUBTABS.mateo = []` — RibbonTabSlug type includes mateo (AgentSlug union includes it).
  Empty array satisfies Record constraint. SubTabsBar Q5 guard (`return null` when subtabs.length === 0)
  handles mateo gracefully if ever routed there.
- `extractSubtabFromPath` returns raw segment without RIBBON_SUBTABS membership validation —
  consumer (SubTabsBar) does `.find()` validation per 03-arch.md D20.
- Mateo labeled "transversal agent" in JSDoc with empty subtabs (not 0 count in the 22 total).

## Acceptance Criteria

| Criterion | Status |
|---|---|
| SubTabMeta interface exported with id/label/icon | PASS |
| RIBBON_SUBTABS 22 sub-tabs distributed 4·5·4·2·4·3 | PASS |
| extractSubtabFromPath returns subtab segment or null | PASS |
| All test IDs match AGENT_CATALOG.{slug}.defaultSubtab | PASS |
| Spanish neutro labels (Reputación, Voz del paciente, Mi cuenta) | PASS |
| No new file created — EXTEND in-place per Q1 cement | PASS |
