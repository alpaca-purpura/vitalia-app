# BUILD-LOG — vitalia-bugfix-shell-nav-scroll-errors (T-1..T-6)

> Conv 2 autonomous build. 6 tickets FE-only. Owner: builder-frontend (sonnet) + orchestrator recovery.

## Build narrative

1. Spawned `builder-frontend` (sonnet) with the full 6-fix spec (verbatim from 03-arch.md) in the prompt.
2. The agent ran in an isolated worktree and **implemented all 6 tickets** (incl. 6 e2e specs) but
   **stalled mid-T-3** (truncated while refining the Bug #7 e2e spec) — no clean `done ->`.
3. **Recovery (orchestrator):** the agent worktree branched off `09e12ae9` (shares ancestor `7b9f7289`
   with `wip/vitalia`; divergence is cockpit/docs only — **touches zero `vitalia/frontend/src` files**).
   Generated a scoped FE patch (`vitalia/frontend/src` + `e2e`, excluding node_modules), dry-run
   `git apply --check` = clean, applied into the canonical `luana-vitalia` worktree, removed the stale
   agent worktree + branch. Fixed one stale comment the agent missed (`not-found.tsx:16`).

## The 6 fixes (applied + verified)

| Ticket | Bug | Fix | Verified |
|---|---|---|---|
| T-1 | #1 routing 404 | `DEFAULT_LANDING_SUBPATH="mateo/agenda"` SSoT in `shell-routes.ts:47`; consumed in 3 redirects (`app/page.tsx:51`, `(shell-organism)/page.tsx:37`, `layout.tsx:79`); stale comments updated; `not-found.test.tsx` + `SubSubTabsBar.test.tsx` coverage_update | tsc/eslint/vitest ✓ |
| T-2 | #4 scroll (ALTA) | `AppPanelSlot.tsx:65` content wrapper `overflow-hidden → overflow-y-auto` (frame `<main>`/`<section>` stay overflow-hidden) | tsc/eslint/vitest ✓ |
| T-3 | #7 error boundary (ALTA) | NEW generic `(shell-organism)/[agent]/error.tsx` (`"use client"` + default export; renders inside ShellOrganismLayout → chrome/nav stay alive + Reintentar) | tsc/eslint/vitest ✓ |
| T-4 | #2 tenant selector | `useStoreHydration(useTenantStore)` added in `ShellOrganismLayoutClient.tsx:108` (was never called — root cause); TenantSwitcher trigger visible with ≥1 tenant | tsc/eslint/vitest ✓ · **live confirm pending** |
| T-5 | #5 landing banner | removed `<InfoBannerLandingDescoped>` render+import in PresenciaView; removed exports in `presencia/index.ts`; **deleted** `InfoBannerLandingDescoped.tsx` | tsc/eslint/vitest ✓ · no dangling refs |
| T-6 | #3 redundant titles | removed `<SubTabHeader>` from `SubTabContent.tsx` (echo for ~17 placeholder routes + double-title Servicios/Conexiones); removed top echo-h2 in Identidad/VozTono/Presencia views (kept AutosaveBadge); **deleted** orphaned `SubTabHeader.tsx`+test; intra-content section headings preserved | tsc/eslint/full vitest ✓ |

## Gate results (orchestrator-run, native)

| Gate | Result |
|---|---|
| `tsc --noEmit` | **0 source errors** (only `.next/dev/types` noise for `lisa/staff/[doctor-id]` route — pre-existing, out of scope) |
| `eslint --max-warnings 0` (changed paths) | **clean** |
| `vitest run` (FULL) | **2493 / 2493 passed** (226 files) — regression_guard intact (SubTabHeader removal broke nothing) |
| arch fitness (`__tests__/architecture/`) | **171 / 171 passed** |
| knip | n/a — not installed in this repo (04-validators over-specified; manual dead-ref check = 0 dangling imports) |

## Pending (verification phase — orchestrator)

- **DoD #37 live-verify (dev-app, Chrome DevTools MCP):** exercise each bug authenticated
  (`dr.demo@vitalialat.com`) + read console (0 red) + confirm effect → `dod_evidence`. Stack is UP.
- **Bug #2 live confirmation:** the rehydration fix is the confirmed *contributing* cause; live repro
  must confirm whether `/api/tenants` returns the single tenant for the dev-app user (if empty → that's
  a separate data/endpoint finding, not the switcher).
- **runtime_error_gate e2e** (`e2e/regression/shell-nav-scroll/`): specs written; run against stack
  (Clerk auth) in auditor gate phase.

## Cross-story observed bugs (non-egoísmo · NOT fixed here)

- **lisa/staff `StaffDirectoryHeader.tsx:70` `<h1>Staff</h1>`** is the same redundant-title pattern as
  Bug #3, but lives in `features/lisa/components/staff/**` = surface of `vitalia-fase2-lisa-doctores`
  (developing, bucket `clinics`). Left untouched per scope discipline → flag for lisa-doctores to absorb.
