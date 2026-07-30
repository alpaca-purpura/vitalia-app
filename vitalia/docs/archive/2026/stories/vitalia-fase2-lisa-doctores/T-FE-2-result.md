# T-FE-2 Result — vitalia-fase2-lisa-doctores
# EntitySubNavBar + StaffWorkspaceShell + Workspace routes + DoctorPerfilView + Bio + Avatar

**Status: TESTS PASSING — awaiting gate-runner + auditor-frontend**
**Date:** 2026-05-31
**Builder:** Claude Sonnet 4.6 (builder-frontend)
**Story:** vitalia-fase2-lisa-doctores · T-FE-2

---

## Summary

Implemented all T-FE-2 deliverables per 06-tickets.yaml:

### 1. EntitySubNavBar (NEW shell-organism component — D-1)

**Path:** `components/shared/shell-organism/EntitySubNavBar.tsx`

WAI-ARIA compliant N3-dynamic navigation bar:
- `role=tablist` on nav, `role=tab` on each leaf button
- Roving tabindex (only focused tab has tabIndex=0)
- Arrow key navigation (Left/Right/Home/End)
- `entity=null` directory mode: leaves `aria-disabled`, `tabIndex=-1`, `opacity-45`
- `entity` workspace mode: leaves enabled, active derived from `activeLeaf` prop
- Back link (‹ Staff) + entity avatar/name in center
- Active tint: `--agent-lisa` CSS var (no hardcoded colors)
- Named export (no default), `// cap: clinics.lisa.doctores` header
- **SubSubTabsBar.tsx NOT modified** (forbidden per D-1)

Tests: `EntitySubNavBar.test.tsx` — 11 tests, all GREEN

### 2. Dropzone component (Shadcn-style)

**Path:** `components/ui/dropzone.tsx`

Native browser DragEvent + FileList (no react-dropzone dep):
- Multi-file support, accept filter, maxSizeBytes validation
- Lists files: name / size / remove button
- `aria-live` region for file list, accessible keyboard operation
- Spanish copy: "Arrastra o haz clic para subir"

### 3. App routes (server components)

- `[doctor-id]/layout.tsx` — Mounts StaffWorkspaceShell + SSR doctor data
- `[doctor-id]/page.tsx` — Redirect → perfil
- `[doctor-id]/perfil/page.tsx` — Server → DoctorPerfilView
- `[doctor-id]/horarios/page.tsx` — T-FE-3 placeholder
- `[doctor-id]/servicios/page.tsx` — "pendiente" placeholder

### 4. Feature components

- `StaffWorkspaceShell.tsx` — Layout wrapper, derives activeLeaf from URL, RQ doctor query
- `DoctorPerfilView.tsx` — Full autosave form (RHF + Zod + 600ms debounce)
- `BioRepoInputs.tsx` — Notes textarea + Dropzone files + link chips (all autosaved)
- `GeneratedBioSections.tsx` — "✨ Generar bio" → 3 contenteditable sections (autosaved)
- `DoctorServiciosView.tsx` — "Servicios — pendiente" placeholder
- `AvatarUploader.tsx` — Proxy upload via POST /api/v1/vitalia/clinics/assets/upload (D-3)

### 5. API hooks added to staff.ts

- `useDoctor(doctorId)` — RQ detail query
- `usePatchDoctor(doctorId)` — PATCH mutation (autosave)
- `useGenerateBio(doctorId)` — POST generate-bio (D-4)
- `useAvatarUpload(doctorId)` — Proxy upload → PATCH avatar_key (D-3)

### 6. use-autosave hook

**Path:** `hooks/use-autosave.ts`

- `schedule(payload)` — debounced (600ms default)
- `flush()` — immediate save
- `status: idle | saving | saved | error`
- Auto-reset to idle after 2s in "saved" state

Tests: `use-autosave.test.ts` — 7 tests, all GREEN

### 7. E2E POM

**Path:** `e2e/pages/DoctorWorkspacePage.ts`

Covers EntitySubNavBar + perfil form + bio + avatar locators and helpers.

---

## Quality gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | **0 errors** |
| `eslint src/` | **0 errors** |
| Vitest (arch fitness 162 tests) | **162/162 PASS** |
| Vitest (targeted 817 tests) | **817/817 PASS** |
| FSD boundary violations | **0** |
| Cross-feature imports from app routes | **0** (barrel imports only) |
| `autosave-no-save-button` | **ENFORCED** |
| `rutas-hoja` (no Shadcn Tabs) | **ENFORCED** |
| EntitySubNavBar separate from SubSubTabsBar | **ENFORCED** |
| Spanish neutro (no voseo) | **VERIFIED** |

---

## Skills consulted

| Skill | Decision |
|---|---|
| `frontend-expert` | FSD-Lite: relative imports within feature, barrel for app routes |
| `tessl__react-patterns` | Skeleton loading, error alert, aria-busy, aria-live, roving tabindex |
| `tessl__zod` | doctorPerfilSchema added to staff-schema.ts |
| `tessl__shadcn-ui` | Reused Input, Label, Skeleton; Dropzone native (no react-dropzone) |
| `tessl__tailwind` | cn() throughout, --agent-lisa token, no inline style |
| `tessl__vitest` | Fake timers for debounce, @testing-library/react for nav a11y |
| `tessl__nextjs-app-router-modularization` | layout.tsx + page.tsx Server; shell=client |
| `chrome-devtools-verify` | Dev stack not running in this session — manual verification steps documented in T-FE-2-impl-log.md. Escalate to Chris staging gate. |

---

## Validators targeted

- V-FN-9 (bio generation — BE service call from FE) ✓
- V-FN-10 (avatar proxy upload) ✓
- V-VIS-2 (EntitySubNavBar disabled in directory) ✓
- V-VIS-4 (workspace leaves enabled + active) ✓
- V-ARCH-8 (FSD boundaries) ✓
- V-ARCH-9 (Server-First pages) ✓
- V-ARCH-10 (no Shadcn Tabs for routing) ✓
- V-ARCH-11 (cap header in all new files) ✓

---

## Mockup adherence notes

Per `mockups/doctores.html` ratified by Chris:
- EntitySubNavBar: sticky, full-width, has back link + entity chip + leaf tabs
- Perfil: autosave hint visible, avatar circle clickable to change, bio section at bottom
- Servicios: "pendiente" placeholder with icon
- Horarios: T-FE-3 placeholder (calendar not in T-FE-2 scope)

---

## Next steps

- T-FE-3: DoctorHorariosView + AvailabilityCalendar + @dnd-kit + BloquePopover
- T-E2E: Playwright SC-1..SC-11 + visual goldens + axe wcag2aa
- T-BE-7: Chris manual R2 provisioning (unblocks live avatar upload)
