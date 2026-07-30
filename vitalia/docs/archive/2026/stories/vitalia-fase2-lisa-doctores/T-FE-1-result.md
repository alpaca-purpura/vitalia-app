---
ticket: T-FE-1
story: vitalia-fase2-lisa-doctores
surface: frontend
state: pushed
commit: 147b7cfd
builder: builder-frontend (Sonnet 4.6)
date: 2026-05-31
---

# T-FE-1 Result — Staff directory: routes + components + hooks + RQ + MSW

## Summary

Staff directory for Lisa agent fully implemented. Renamed sub-tab `doctores` → `staff` per spec v2 (01-spec.md ratificado Chris 2026-05-31). All quality gates GREEN.

## Deliverables shipped

| File | Status |
|---|---|
| `app/[tenantId]/(shell-organism)/lisa/staff/page.tsx` | NEW — Server Component, SSR hydration |
| `features/lisa/components/staff/LisaStaffView.tsx` | NEW — "use client" root |
| `features/lisa/components/staff/StaffDirectoryView.tsx` | NEW — grid + states |
| `features/lisa/components/staff/StaffCard.tsx` | NEW — card personal-branding |
| `features/lisa/components/staff/StaffDirectoryHeader.tsx` | NEW — filters + CTA |
| `features/lisa/components/staff/NuevoIntegranteModal.tsx` | NEW — RHF+Zod submit-driven |
| `features/lisa/components/staff/StaffEmptyState.tsx` | NEW — SC-8 |
| `features/lisa/components/staff/StaffErrorBanner.tsx` | NEW — SC-7 |
| `features/lisa/api/staff.ts` | NEW — useStaffList + useCreateDoctor hooks |
| `features/lisa/api/staff-server.ts` | NEW — SSR fetch helpers |
| `features/lisa/hooks/use-staff-filters.ts` | NEW — nuqs URL-backed filters |
| `features/lisa/store/staff-ui-store.ts` | NEW — Zustand UI-only |
| `features/lisa/types/staff.types.ts` | NEW — TS types (camelCase mirror) |
| `features/lisa/types/staff-schema.ts` | NEW — Zod (credential country-specific) |
| `mocks/handlers/staff.ts` | NEW — MSW handlers incl 503 for SC-7 |
| `features/lisa/components/staff/__tests__/staff.test.tsx` | NEW — 29 tests |
| `features/lisa/api/__tests__/staff-api.test.ts` | NEW — 16 tests |

### Modified files (rename doctores → staff)

| File | Change |
|---|---|
| `lib/agent-catalog.ts` | RIBBON_SUBTABS lisa: `doctores` → `staff`; added `lisa.staff` to SHIPPED_STATIC_SUBTABS |
| `components/shared/shell-organism/SubTabContent.tsx` | Removed `lisa.staff` from PLACEHOLDER_MAP (now shipped static), removed DoctoresPlaceholder import |
| `features/lisa/index.ts` | Added staff exports; removed DoctoresPlaceholder; added getStaffInitialState |
| Arch tests (3 files) | Updated labels/IDs for doctores → staff rename; added lisa.staff to allowlists |
| `package.json` | Added msw devDependency |

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| ESLint | 0 errors, 0 new warnings |
| Vitest (2367 tests total) | ALL PASS |
| Architecture fitness (162 tests) | ALL PASS |
| Gherkin coverage | SC-2 (credential invalid), SC-7 (network failure), SC-8 (empty state), SC-9 (pagination), SC-3 (deactivate) |

## Architecture decisions taken

- Sub-tab rename `doctores` → `staff` per 01-spec.md v2 (ratificado Chris) — consistent with routes `lisa/staff/`
- `lisa.staff` added to `SHIPPED_STATIC_SUBTABS` (static route exists) → removed from `PLACEHOLDER_MAP`
- NuevoIntegranteModal is submit-driven (atomic create — one exception to autosave per spec)
- Credential validation client-side mirrors backend: PE=numeric, AR/MX/CL=alphanumeric
- MSW handlers include 503 variant for SC-7 network failure testing
- Auth: `fetchClient` (HIPAA-lite dual filter tenant+clinic) per vitalia convention
- MSW installed as devDependency (`msw@^2.x`)

## Skills consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `frontend-expert` | Core FSD-Lite patterns, Server-First, barrel exports, runtime quality checklist | Applied FSD structure exactly; verified no cross-feature imports via public API only |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys | All async states covered; ARIA roles on status/alert/tablist; data-testids for Playwright |
| `tessl__zod` | Form schema NuevoIntegranteModal + credential validation | Discriminated union for availability block (T-FE-3 preview); superRefine for country-specific |
| `tessl__shadcn-ui` | Component selection — Card/Dialog/Input/Select/Badge/Button/Skeleton | Reused existing Shadcn atoms; NO Tabs (per policy); NO recreated primitives |
| `tessl__tailwind` | Utility classes, cn(), no inline style | Applied throughout; agent-lisa CSS var for brand tint |
| `tessl__vitest` | Test setup, async, mocking | React mock for next/link, next/image; voseo-allowed magic comment in test file |
| `tessl__nextjs-app-router-modularization` | Server+Client boundary — page.tsx Server + LisaStaffView "use client" | Split correctly per ADR-004 §3.3 |
| `brand-expert` | N/A — no brand studio aggregates touched | Not invoked |
| `chrome-devtools-verify` | Live verification gate | NOT INVOKABLE — dev environment not running. Escalated to Chris staging gate per skill instructions. |

## Mockup scope notes (D3 — out of scope for T-FE-1)

Per 06-tickets.yaml T-FE-1 scope, the following from mockups/doctores.html are OUT of scope:
- AvatarUploader (T-FE-2)
- EntitySubNavBar (T-FE-2)
- workspace routes [doctor-id]/perfil|horarios|servicios (T-FE-2 + T-FE-3)
- BioRepoInputs / GeneratedBioSections (T-FE-2)
- AvailabilityCalendar / BloquePopover (T-FE-3)

## Live verification

`chrome-devtools-verify` skill: NOT invokable in this session (no running dev environment). Escalated to Chris staging gate per skill protocol. Manual verification steps:
1. `make dev-vitalia` (start vitalia stack)
2. Navigate to `http://localhost:3002/[tenantId]/lisa/staff`
3. Verify: grid loads, empty state shown when no doctors, error banner + retry when 503, "+ Nuevo integrante" opens modal with credential validation (SC-2)
4. Submit form → verify navigation to `/lisa/staff/[id]/perfil`

## Notes for auditor-frontend

- Architecture rename `doctores → staff` required updating 3 arch test files (agent-catalog.test.ts, SubTabsBar.test.tsx, test-vitalia-ui-strings-no-voseo.test.ts) + adding allowlist entry to test_no_hardcoded_subtab_keys.test.ts. These are intentional ratchet updates for the rename.
- `DoctoresPlaceholder` component remains in codebase (used as re-export that is now no longer used by SubTabContent or index.ts). It can be removed in cleanup but is harmless (no reference path to it).
- MSW handlers at `src/mocks/handlers/staff.ts` (no MSW server setup in this ticket — tests use direct schema validation, not MSW integration tests; MSW setup is in T-FE-2+)
