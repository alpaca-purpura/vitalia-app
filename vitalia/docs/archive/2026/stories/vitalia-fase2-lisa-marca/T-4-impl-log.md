# T-4 IMPL-LOG — FE Routing N3-static + SubSubTabsBar + AGENT_SUBSUBTABS catalog

**Story:** vitalia-fase2-lisa-marca  
**Ticket:** T-4  
**Commit:** 88883702  
**Branch:** wip/vitalia  
**Date:** 2026-05-27  

## Summary

Implemented ADR-vitalia-004 v1.1 N3-static routing pattern for `lisa/marca`.

**Files created:**

1. **`vitalia/frontend/src/lib/shell-routes.ts`** — AGENT_SUBSUBTABS catalog (N3 SSoT):
   - `SubSubTabMeta` interface (id, label, icon)
   - `AGENT_SUBSUBTABS` partial record keyed by `{agent}.{subtab}`
   - Entry: `"lisa.marca"` → [identidad, voz-y-tono, presencia]
   - Helper functions: `getSubSubTabs()`, `getDefaultSubSubTab()`

2. **`vitalia/frontend/src/components/shared/shell-organism/SubSubTabsBar.tsx`** — Client Component:
   - Roving tabindex WAI-ARIA tablist pattern (mirrors SubTabsBar)
   - Returns null for non-N3 routes (AGENT_SUBSUBTABS has no entry)
   - URL-derived active state (segment[3] of pathname)
   - Keyboard nav: ArrowLeft/Right/Home/End + Enter/Space
   - aria-selected + aria-current on active tab

3. **`vitalia/frontend/src/app/[tenantId]/(shell-organism)/lisa/marca/page.tsx`** — Server redirect to `identidad` (default sub-sub-tab)

4. **Three N3 page.tsx stubs** (Server Components with Suspense + skeleton):
   - `lisa/marca/identidad/page.tsx` — data-testid="identidad-page"
   - `lisa/marca/voz-y-tono/page.tsx` — data-testid="voz-y-tono-page"
   - `lisa/marca/presencia/page.tsx` — data-testid="presencia-page"

**Files modified:**

5. **`AppPanelSlot.tsx`** — mount `<SubSubTabsBar />` between SubTabsBar and content children

6. **`agent-catalog.ts`** — SHIPPED_STATIC_SUBTABS += "lisa.marca"

7. **`SubTabContent.tsx`** — remove "lisa.marca" from PLACEHOLDER_MAP (now N3-static shadowed); remove MarcaPlaceholder import

**Tests created:**

8. **`SubSubTabsBar.test.tsx`** — 20 unit tests (SC-1..SC-7)
9. **`test-agent-subsubtabs-ssot.test.ts`** — 13 arch fitness tests

**Arch test fix:**

10. **`test_no_hardcoded_subtab_keys.test.ts`** — allowlist extended with `shell-routes.ts` + `test-agent-subsubtabs-ssot.test.ts` (legitimate N3 SSoT files)

**Fix in T-8 schema:**

11. **`visuals-schema.ts`** — hexColor error message changed from `#01B2F8` → `#RRGGBB` format description (arch test `test_no_hardcoded_colors` blocked hardcoded brand hex in non-comment strings)

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite structure, arch fitness, allowlist extension pattern | ALLOWED_FILES update follows ratchet comment pattern; N3 SSoT files belong in allowlist |
| `tessl__react-patterns` | Accessible tablist, keyboard nav, aria-selected/current, focusRef management | Roving tabindex with useRef array + focusedIdx state; returns null on no match |
| `tessl__nextjs-app-router-modularization` | Server/Client boundary for page.tsx vs SubSubTabsBar | page.tsx = Server, SubSubTabsBar = Client Component |
| `brand-expert` | ADR-vitalia-004 v1.1 N3-static routing pattern compliance | NEVER Shadcn Tabs body for sub-sections; SubSubTabsBar is header bar only |

## Key Decisions

1. **Shell-routes.ts as N3 SSoT**: Analogous to SubTabContent.tsx's role for N2. `AGENT_SUBSUBTABS` is the single registry for N3 routes. The arch test for no-hardcoded-subtab-keys was extended to allow this file.

2. **SubSubTabsBar returns null**: For all agent.subtab combos not in AGENT_SUBSUBTABS, the component renders nothing. This preserves backward compatibility for all existing routes.

3. **AppPanelSlot is Server Component**: It can import Client Component SubSubTabsBar without needing "use client" itself. Server → Client boundary is natural here.

4. **Page.tsx as stubs**: T-5/T-6/T-7 will replace the placeholder content with their respective `*View` client roots. The stubs include proper `data-testid`, `data-tenant-id`, Suspense boundary, and loading skeleton.

5. **`MarcaPlaceholder` kept in barrel**: Removing from SubTabContent.tsx is correct, but the export in `lisa/index.ts` stays as it doesn't cause errors and may serve as fallback.

## Quality Gate Results

```
tsc --noEmit:    0 errors
eslint src/:     0 errors, 0 warnings  
vitest run:      2002/2002 PASS (183 test files)
  - SubSubTabsBar.test.tsx: 20/20 PASS
  - test-agent-subsubtabs-ssot.test.ts: 13/13 PASS
  - test_subtab_content_uses_ribbon_subtabs_ssot.test.ts: 7/7 PASS (no regression)
```
