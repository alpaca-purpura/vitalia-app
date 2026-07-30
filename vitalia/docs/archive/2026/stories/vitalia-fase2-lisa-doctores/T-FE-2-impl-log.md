# T-FE-2 Implementation Log
# vitalia-fase2-lisa-doctores / EntitySubNavBar + Workspace + DoctorPerfilView + Bio + Avatar

## Status: GREEN — all gates passed

**Builder:** Claude Sonnet 4.6 (builder-frontend)
**Date:** 2026-05-31
**Gates:** tsc 0 errors · eslint 0 errors · 817 vitest tests passed (162 arch + 655 others) · FSD boundaries clean

---

## Plan

### Design-system-first (D1)
- Atoms reused: `Button`, `Input`, `Label`, `Skeleton`, `Textarea` from `components/ui/`
- Molecules: `Dropzone` (NEW — Shadcn-style, native DragEvent, no react-dropzone dep)
- Shell-organism: `EntitySubNavBar` (NEW sibling of `SubSubTabsBar`, NOT a modification)
- Tokens: `--agent-lisa` (CSS var from globals.css) for active tint + avatar initial bg

### Mockup scope notes
- Horarios page: T-FE-3 scope — rendered as placeholder only (per spec "pendiente" for horarios)
- DoctorHorariosView: out of T-FE-2 scope (belongs to T-FE-3 deliverables)
- Calendar grid/drag-to-create: out of T-FE-2 scope

### Integration (CONN)
- `StaffWorkspaceShell` mounted via `[doctor-id]/layout.tsx` (layout wraps all workspace pages)
- `EntitySubNavBar` registered in layout → reachable from all 3 leaf pages
- All 3 leaf routes registered under `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/`
- Back link points to `/{tenantId}/lisa/staff` (directory)

---

## Skills consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, Server-First pages, runtime-quality-checklist | Used relative paths within feature (not cross-feature @/features/lisa imports from within lisa components). Arch test enforcement confirmed. |
| `tessl__react-patterns` | Error boundaries, loading/error/empty states, aria, stable keys, memoization | Applied: loading skeleton on DoctorPerfilView, error alert, aria-busy, aria-live autosave hint, roving tabindex in EntitySubNavBar |
| `tessl__zod` | RHF + Zod for perfil form, doctorPerfilSchema | Added `doctorPerfilSchema` to existing staff-schema.ts |
| `tessl__shadcn-ui` | Reuse existing atoms, never recreate | Reused Input, Label, Skeleton. Dropzone created native (not reinstalling react-dropzone). |
| `tessl__tailwind` | Utility classes, cn(), no inline style | Used cn() from @/lib/utils throughout |
| `tessl__vitest` | Test patterns, async, mocking | Fake timers for debounce tests; @testing-library/react for EntitySubNavBar |
| `tessl__nextjs-app-router-modularization` | Page.tsx pure Server + *Client.tsx for interactivity | layout.tsx + page.tsx pure Server; StaffWorkspaceShell is "use client" |
| `chrome-devtools-verify` | Live verification | Not available in this session (dev stack not running). Manual steps documented below. |

---

## Files created/modified

### NEW — Shell organism
- `components/shared/shell-organism/EntitySubNavBar.tsx` — N3-dynamic entity nav bar
- `components/shared/shell-organism/EntitySubNavBar.test.tsx` — 11 a11y tests (RED→GREEN)

### NEW — UI component
- `components/ui/dropzone.tsx` — Native Shadcn-style dropzone (multi-file, accept, maxSize)

### NEW — App routes
- `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/layout.tsx` — StaffWorkspaceShell mount + SSR
- `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/page.tsx` — Redirect → perfil
- `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/perfil/page.tsx` — Server → DoctorPerfilView
- `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/horarios/page.tsx` — Placeholder (T-FE-3)
- `app/[tenantId]/(shell-organism)/lisa/staff/[doctor-id]/servicios/page.tsx` — Placeholder (pending)

### NEW — Feature components
- `features/lisa/components/staff/workspace/StaffWorkspaceShell.tsx` — Layout + RQ doctor query
- `features/lisa/components/staff/workspace/AvatarUploader.tsx` — Dropzone → proxy upload
- `features/lisa/components/staff/workspace/perfil/DoctorPerfilView.tsx` — Autosave form
- `features/lisa/components/staff/workspace/perfil/BioRepoInputs.tsx` — Notes + files + links
- `features/lisa/components/staff/workspace/perfil/GeneratedBioSections.tsx` — 3 contenteditable sections
- `features/lisa/components/staff/workspace/servicios/DoctorServiciosView.tsx` — Pending placeholder

### NEW — Hooks
- `hooks/use-autosave.ts` — Debounced autosave (600ms) with status lifecycle
- `hooks/use-autosave.test.ts` — 7 tests (RED→GREEN)

### MODIFIED — API + types + barrel
- `features/lisa/api/staff.ts` — Added: useDoctor, usePatchDoctor, useGenerateBio, useAvatarUpload
- `features/lisa/types/staff-schema.ts` — Added: doctorPerfilSchema + DoctorPerfilFormValues
- `features/lisa/index.ts` — Barrel exports for all new workspace components + hooks

### NEW — E2E POM
- `e2e/pages/DoctorWorkspacePage.ts` — Playwright POM for doctor workspace

### UPDATED — Story artifacts
- `06-tickets.yaml` — T-FE-2 state: pushed

---

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | 0 errors |
| `eslint src/` | 0 errors |
| `vitest run` (arch) | 162/162 PASS |
| `vitest run` (targeted) | 817/817 PASS |
| FSD boundary violations | 0 (arch test PASS) |
| Cross-feature imports | 0 (relative paths within lisa/) |
| Spanish neutro | Verified (no voseo in user-facing strings) |
| `autosave-no-save-button` | ENFORCED — no Guardar button present |
| `rutas-hoja` anti-Shadcn-Tabs | ENFORCED — separate page.tsx files |
| `EntitySubNavBar NOT SubSubTabsBar modify` | ENFORCED — new file, SubSubTabsBar untouched |

---

## Architecture decisions respected

- **D-1**: EntitySubNavBar is NEW sibling — `SubSubTabsBar.tsx` never touched
- **D-3**: Proxy upload via `useAvatarUpload` → `/api/v1/vitalia/clinics/assets/upload` (no presigned)
- **D-4**: GeneratedBioSections triggers POST to BE bio-gen service (extractive, no FE LLM)
- **ADR-vitalia-004**: rutas-hoja reales, no Shadcn Tabs for workspace navigation

---

## Manual live verification steps (Chrome DevTools — when dev stack available)

1. `make dev-vitalia` → http://localhost:3002
2. Navigate to a doctor workspace: `/{tenantId}/lisa/staff/{doctorId}/perfil`
3. Verify EntitySubNavBar renders sticky with back link + entity name + Perfil|Horarios|Servicios tabs
4. Verify ArrowLeft/Right moves focus between tabs (keyboard nav SC-10)
5. Edit specialty field → wait 600ms → check network (PATCH request fires)
6. Verify autosave hint shows "Los cambios se guardan automáticamente" (idle state)
7. Click avatar → dropzone appears → upload image → verify proxy POST + PATCH
8. Fill bio notes → click "✨ Generar bio" → verify POST to generate-bio endpoint
9. Edit contenteditable sections → verify autosave fires
10. Navigate to servicios → verify placeholder text
11. Navigate to horarios → verify "próximamente" placeholder

---

## Remaining scope (NOT in T-FE-2)

- DoctorHorariosView (calendar grid + @dnd-kit + BloquePopover) → T-FE-3
- Visual golden screenshots → T-E2E
- Real R2 provisioning → T-BE-7 (Chris manual action)
- Full E2E specs SC-1..SC-11 → T-E2E
