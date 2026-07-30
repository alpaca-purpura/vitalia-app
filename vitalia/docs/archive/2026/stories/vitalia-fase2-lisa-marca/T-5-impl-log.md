# T-5 Implementation Log — FE Identidad sub-sub-tab

**Ticket:** T-5 vitalia-fase2-lisa-marca  
**Surface:** FE  
**Date:** 2026-05-27  
**Brand:** vitalia

---

## Summary

Implemented the Identidad sub-sub-tab for Lisa's Marca section.
Delivered 8 components + 2 hooks + 1 API layer + 1 Zustand store + 4 unit tests.
Wired `IdentidadView` into the T-4 page.tsx placeholder.

---

## Deliverables

### Components created

| File | Role |
|---|---|
| `features/lisa/components/marca/identidad/IdentidadView.tsx` | Client root, composes all 8 sub-components |
| `features/lisa/components/marca/identidad/IdentityCard.tsx` | RHF + Zod identity form, autosave 600ms |
| `features/lisa/components/marca/identidad/ClinicVerticalReadOnly.tsx` | D3-clinic read-only (vertical + specialties) |
| `features/lisa/components/marca/identidad/LogoDropZone.tsx` | Drag-drop logo, 5MB validation, live preview |
| `features/lisa/components/marca/identidad/ColorTriadEditor.tsx` | 3 color swatches, WCAG contrast warning |
| `features/lisa/components/marca/identidad/TypographyEditor.tsx` | Heading + body font selectors, live preview |
| `features/lisa/components/marca/identidad/TeamPreviewRow.tsx` | Avatar stack max 3 + counter |
| `features/lisa/components/marca/identidad/ExtractFromWebsiteButton.tsx` | D4-extract STUB — disabled + tooltip |
| `features/lisa/components/marca/identidad/AutosaveBadge.tsx` | Re-export from `components/marca/shared/` |
| `components/marca/shared/AutosaveBadge.tsx` | Shared autosave badge (T-6, T-7 reuse) |

### API + hooks + store

| File | Role |
|---|---|
| `features/lisa/api/marca.ts` | React Query key factory + fetch functions |
| `features/lisa/hooks/useIdentityAutosave.ts` | Debounce 600ms → PUT identity |
| `features/lisa/hooks/useVisualsAutosave.ts` | Debounce 600ms → PUT visuals |
| `features/lisa/store/marca-identidad-store.ts` | Zustand UI state (logo uploading, color picker) |

### Routing + barrel

- Updated `app/[tenantId]/(shell-organism)/lisa/marca/identidad/page.tsx` — wired `<IdentidadView>` replacing T-4 placeholder
- Updated `features/lisa/index.ts` — added IdentidadView + AutosaveBadge + marcaKeys exports
- Created `features/lisa/components/marca/identidad/index.ts` — component barrel

### Tests (4 test files, 19 unit tests)

| File | Tests |
|---|---|
| `__tests__/AutosaveBadge.test.tsx` | 6 tests: idle/saving/saved/error/dirty states, role=status |
| `__tests__/LogoDropZone.test.tsx` | 5 tests: accessible button, preview, >5MB reject, bad format reject, valid upload |
| `__tests__/ExtractFromWebsiteButton.test.tsx` | 3 tests: disabled, tooltip aria-label, no navigation on click |
| `__tests__/IdentityCard.test.tsx` | 5 tests: renders inputs, validation, autosave call, website display |

---

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| `eslint src/` | PASS — 0 errors, 0 warnings |
| Vitest 187 files | PASS — 2021/2021 tests |
| Coverage | PASS — 82.66% stmts / 92.24% branches / 69.87% fns (threshold 20%) |
| Architecture fitness (24 files, 149 tests) | PASS — 0 violations |

---

## Architecture decisions

### D1 — ColorTriadEditor without Radix Popover
`@radix-ui/react-popover` is not installed in vitalia/frontend (only tooltip, dialog, dropdown-menu, tabs, accordion, avatar, label, scroll-area, separator, slot). Implemented inline swatch pickers using native `<input type="color">` + hex text input. Functionally equivalent, no extra dependency.

### D2 — "use client" placement
Architecture test (FE-A5) requires `"use client"` within the first 500 characters of the file (checks `source.slice(0, 500)`). Moved directive to line 1 of all client components, before the JSDoc block.

### D3 — Page imports IdentidadView via feature barrel
Architecture test (FE-A4) requires pages to import from the feature's public API (`@/features/lisa`), not internal paths. Fixed page.tsx to use barrel import.

### D4 — No hex literals in ColorTriadEditor
Architecture tests (FE-A1 no hardcoded colors, FE-A9 no agent hex colors) flag any hex literal. Replaced `#e5e7eb` fallback with `var(--border, currentColor)` CSS var + `bg-muted` Tailwind class. Changed placeholder from `01B2F8` to `RRGGBB` to avoid false positive on agent color pattern match (`01b2f8` is Adrian's agent color).

### D5 — IdentidadView uses useRef for stable onSave callback
`useIdentityAutosave.scheduleAutosave` is called from IdentityCard's `onSave` prop. To avoid stale closure and avoid spurious re-renders from non-stable function refs, `onSaveRef` pattern used in `IdentityCard` rather than including `onSave` in `useEffect` dependencies.

### D6 — Logo upload uses raw fetch
`uploadLogo` in `marca.ts` uses raw `fetch()` instead of `fetchClient` because FormData requires multipart `Content-Type` (browser sets boundary automatically). The function manually injects `Authorization`, `X-Tenant-ID`, and `X-Clinic-ID` headers to preserve HIPAA-lite dual filter compliance.

---

## §11 Faithfulness gaps (from CONTEXT-BRIEF.md review)

None identified. All architectural decisions are within scope or explicitly stubbed per CONTEXT-BRIEF constraints (D4-extract, D3-clinic).

---

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, ESLint ratchet, studio section pages pattern, `"use client"` placement rules | Confirmed barrel-only cross-feature imports; "use client" must be first line within 500 chars; no hex literals outside globals.css + agent catalog |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, accessible markup, stable keys, memoization | Applied: SectionSkeleton + ErrorBanner in IdentidadView; aria-busy on loading states; stable entity.id keys; useRef for stable onSave callback |
| `tessl__zod` | Form schema + RHF resolver | Confirmed: identitySchema (from T-8), RHF mode="onChange", Zod resolver |
| `tessl__shadcn-ui` | Component selection | No Popover available → inline native color picker pattern; reused Button, Badge, Avatar, Skeleton, Tooltip from components/ui/ |
| `tessl__tailwind` | Utility classes + no inline style | Applied cn() throughout; replaced hex fallback with CSS var + Tailwind class |
| `tessl__nextjs-app-router-modularization` | Server/Client split | page.tsx = Server Component (no hooks); IdentidadView = "use client" root |
| `brand-expert` | Brand Studio field shapes, form-runtime autosave invariant | Confirmed: NO save button (autosave on-change non-negotiable per form-runtime-array.md) |

---

## Live verification

`chrome-devtools-verify` skill is DEPRECATED for Linux Mint (see project context). Manual verification steps documented:

1. `make dev-vitalia` — start stack
2. Open `http://localhost:3002/[tenantId]/lisa/marca/identidad`
3. Verify: form renders, autosave badge appears on change, logo dropzone DnD works, color swatches update preview, typography selectors update live preview
4. Verify: disabled ExtractFromWebsiteButton shows tooltip on hover
5. Verify: TeamPreviewRow shows "Gestionar equipo" disabled tooltip when doctoresStoryDone=false
6. Escalated to Chris staging gate for live verification.
