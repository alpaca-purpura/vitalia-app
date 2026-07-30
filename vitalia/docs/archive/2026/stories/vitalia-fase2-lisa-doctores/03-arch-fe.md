---
story_id: vitalia-fase2-lisa-doctores
surface: frontend
architecture_pattern: ADR-vitalia-004
adr_004_compliance: full
---

# 03-arch-fe · Frontend contract — Staff (features/lisa EXTEND + shell-organism EntitySubNavBar)

> Owner: `builder-frontend` (Sonnet). Auditor: `auditor-frontend` (Opus).
> Skills: `frontend-expert` + `vitalia-design-system` (★ FE SSoT). FSD-Lite. Next.js 16 Server-First. React Query SSoT data, Zustand UI-only. RHF+Zod autosave 600ms (NO save button). Spanish neutro. Columna ANGOSTA (chat Valeria ~320px al costado) -> todo full-width-de-columna, cards 1-col, calendario compacto.

## § Routing (route group, rutas-hoja reales — NO Shadcn Tabs)

```
app/[tenantId]/(shell-organism)/lisa/staff/
  page.tsx                          MODIFY  (directorio; Server Component; getStaffInitialState)
  [doctor-id]/
    layout.tsx                      NEW     (StaffWorkspaceShell — monta EntitySubNavBar)
    page.tsx                        NEW     (redirect -> ./perfil)
    perfil/page.tsx                 NEW     (Server -> DoctorPerfilView client)
    horarios/page.tsx               NEW     (Server -> DoctorHorariosView client)
    servicios/page.tsx              NEW     (Server -> DoctorServiciosView "pendiente")
```
- Server Component default; `params`/`searchParams` are `Promise` (Next 16). PHI NEVER in URL/searchParams (gate `test_no_phi_in_url_params`). `[doctor-id]` is a UUID, not PHI.
- Each hoja = its own URL (deep-link + back/forward respected — SC-1c Playwright). NO `<Tabs>` (gate `test-ribbon-no-shadcn-tabs`).

## § EntitySubNavBar (NEW shell-organism component — D-1)

`components/shared/shell-organism/EntitySubNavBar.tsx` (+ `.test.tsx`). Props per `03-arch.md § D-1`. Sticky full-width N3-dynamic bar: `[‹ Staff] | [avatar+nombre] | [Perfil][Horarios][Servicios]`. In directory: `entity=null` -> leaves disabled (opacity .45, aria-disabled, tabIndex=-1). In workspace: entity populated -> leaves enabled, active derived from URL. WAI-ARIA tablist + roving tabindex + Arrow nav (port from `SubSubTabsBar.tsx`). Tint active = `--agent-lisa`. Named export (no default). `// cap: clinics.lisa.doctores` header.

> NOT registered in `AGENT_SUBSUBTABS` catalog (that's for N3-static). EntitySubNavBar is rendered imperatively by the `[doctor-id]/layout.tsx` and `StaffDirectoryView` — driven by entity prop, not catalog. Arch test `test-agent-subsubtabs-ssot` unaffected (staff has no static subsubtab entry).

## § FSD-Lite layout (`features/lisa/`)

```
features/lisa/
  components/staff/
    LisaStaffView.tsx                NEW  "use client" root (directorio)
    StaffDirectoryView.tsx           NEW  grid + filters + pagination + EntitySubNavBar(entity=null)
    StaffCard.tsx                    NEW  avatar + name + specialty badge + stats + Ver perfil
    StaffDirectoryHeader.tsx         NEW  + Nuevo integrante + search + specialty/active filters
    NuevoIntegranteModal.tsx         NEW  RHF+Zod submit-driven (focus trap, Escape)
    StaffEmptyState.tsx              NEW  SC-8
    StaffErrorBanner.tsx             NEW  SC-7 retry
    AvatarUploader.tsx               NEW  Dropzone -> POST assets/upload -> PATCH avatar_key
    workspace/
      StaffWorkspaceShell.tsx        NEW  layout wrapper (header + EntitySubNavBar)
      perfil/
        DoctorPerfilView.tsx         NEW  "use client" autosave form
        BioRepoInputs.tsx            NEW  notes textarea + Dropzone files + links chips
        GeneratedBioSections.tsx     NEW  Generar bio btn + 3 contenteditable sections
      horarios/
        DoctorHorariosView.tsx       NEW  "use client"
        AvailabilityCalendar.tsx     NEW  week grid day x hour, drag-to-create, ‹/› nav, 24h toggle
        BloquePopover.tsx            NEW  repeat weekly/biweekly + end_date/N-iter/one-off + edit/delete
      servicios/
        DoctorServiciosView.tsx      NEW  "pendiente" placeholder
    __tests__/                       NEW  Vitest co-located
  api/
    staff.ts                         NEW  React Query hooks
    staff-server.ts                  NEW  getStaffInitialState, getDoctorInitialState (SSR)
    __tests__/
  hooks/
    use-autosave.ts                  NEW  debounce 600ms flush (or reuse existing if present)
    use-staff-filters.ts             NEW  URL params persist (q/specialty/active/page)
  store/
    staff-ui-store.ts                NEW  Zustand UI-only (modal open, selected leaf, calendar week)
  types/
    staff.types.ts                   NEW  mirror Pydantic DTOs (camelCase)
    staff-schema.ts                  NEW  Zod (doctorCreate, bio, availabilityBlock discriminated union)
```
Boundaries: `features/lisa` no importa de otra feature. Shadcn primitives solo en `components/ui/`. EntitySubNavBar en `components/shared/shell-organism/` (NO en features).

## § TypeScript Types (mirror Pydantic, camelCase)

```ts
interface DoctorListItem { id; firstName; lastName; specialty; avatarUrl?; yearsExperience?; patientsCount?; npsScore?; dniMasked; active }
interface DoctorDetail { id; firstName; lastName; dni; email; phone?; specialty?; credential; credentialCountry; yearsExperience?; languages: string[]; bioInputsNotes?; bioLinks: string[]; bioPublic?: BioPublic; avatarKey?; avatarUrl?; visibleEnLanding; active }
interface BioPublic { resumen?; formacion?; enfoque? }
type AvailabilityBlock =
  | { id; kind: "recurrent"; dayOfWeek; startTime; endTime; freq: "weekly"|"biweekly"; endConditionKind: "end_date"|"occurrences"|"open_ended"; endDate?; occurrences? }
  | { id; kind: "one_off"; specificDate; startTime; endTime }
interface AssetUploadResponse { key; url }
```
Datetimes ISO 8601 `string`. Optional fields explicit `?`.

## § Data layer (React Query + Zustand split)

| State | Storage | Key |
|---|---|---|
| doctors list | RQ `useStaffList(filters)` | `['lisa','staff','list',filters]` |
| doctor detail | RQ `useDoctor(id)` | `['lisa','staff',id]` |
| availability blocks | RQ `useAvailabilityBlocks(id)` | `['lisa','staff',id,'blocks']` |
| create/patch/delete | RQ mutations -> invalidate keys | — |
| modal open, active leaf, calendar week, drag draft | Zustand `staff-ui-store` | — |
| filters (q/specialty/active/page) | URL searchParams | — |
| forms | RHF + Zod | — |

Mutations invalidate explicitly. SSR hydrates RQ cache via `initialData` from server page (no refetch on mount).

## § Forms (RHF + Zod + autosave)

- **NuevoIntegranteModal:** submit-driven (atomic create). Zod `doctorCreateSchema` (credential validation client-side mirror per country). 422 -> inline `<FormMessage>` + focus field (SC-2). 409 dni -> error toast.
- **DoctorPerfilView:** autosave on-change debounce 600ms (`autosave-no-save-button`). Hint "Los cambios se guardan automaticamente". NO save button. Each field -> PATCH. Bio sections contenteditable -> autosave.
- **AvailabilityCalendar/BloquePopover:** drag-to-create -> popover -> POST block (creates + materializes). Edit/delete via popover. Delete with confirmed appts -> warning modal (SC-3b).
- Toasts via `sonner`. Never `alert()`/`window.confirm()` (use Dialog).

## § Calendar decision (research-backed)

**Recommendation: custom week grid + `@dnd-kit/core` for drag-to-create.** Rationale:
- Columna ANGOSTA (chat al costado ~320px) -> FullCalendar/react-big-calendar son anchos, no optimizados para ~600px de ancho; su CSS pelea con el shell.
- Necesitamos popover de recurrencia custom (weekly/biweekly + end_date/N-iter/one-off) — librerias generic no lo dan; tendriamos que override pesado.
- `@dnd-kit` (accessible, headless) da drag-to-create con control total + a11y (SC-10). Grid = CSS grid 7col x N-hour rows, base 07:00–21:00, toggle "Mostrar 24 horas" (00:00–23:00). Bloques recurrentes en cada semana; puntuales solo en la suya. ‹/› week nav (Zustand week state). 24h format (no AM/PM, no `toLocaleDateString`).
- Fallback si `@dnd-kit` no instalable: click-start + click-end interaction (no drag). Flag in ticket.

## § Dropzone install

**Install `diragb/shadcn-dropzone`** (over `react-dropzone`) into `components/ui/dropzone.tsx`. Used by `AvatarUploader` (image/* 10MB) + `BioRepoInputs` (PDF/JPG/PNG/DOCX 10MB). Lists name/size/remove + multi-file. Ticket `T-FE-3` deliverable: install + wire. Spanish copy: "Arrastra o haz clic para subir · PDF, JPG, PNG, DOCX · hasta 10 MB".

## § Estados visuales (spec § Estados)

loading (skeleton ×6 cards) · success (grid+filters+pagination) · empty (SC-8 illustration+CTA) · error (SC-7 banner+Reintentar) · saving (autosave hint) · save-error (toast + form intact).

## § Telemetría (FE)

`useTelemetry({event, payload})` -> POST `/api/v1/telemetry/event`. Events: `lisa_doctores_list_viewed`, `lisa_doctor_created`, `lisa_doctor_horarios_saved`, `lisa_doctor_deactivated` (per spec § Telemetría). Best-effort.

## § Accessibility

ARIA labels all inputs + `aria-invalid` errors. Focus ring `focus:ring-2 focus:ring-primary`. Modal focus trap + Escape. EntitySubNavBar `role=tablist`/`tab` + Arrow + `aria-selected`/`aria-disabled`. Calendar keyboard-operable (axe wcag2aa — SC-10). Contrast >=4.5:1 text, >=3:1 UI.

## § Responsive (spec § Responsive)

Mobile <768: grid 1col, workspace nav scroll-x, modal full-screen. Tablet 768-1024: grid 2col. Desktop >1024: grid 3-4col (but within angosta column -> auto-fit minmax keeps 1-2col when chat open).

## § MSW + tests

MSW handlers `vitalia/frontend/src/mocks/handlers/staff.ts` mock all endpoints. Vitest co-located per component w/ logic. Playwright specs (see 04-validators). Visual goldens: directorio + perfil + horarios × light/dark (6 PNG) + servicios-pendiente (1). `maxDiffPixelRatio: 0.001`.

## § File Structure (FE) — see FSD-Lite block above. Routing block above. NEW vs MODIFY marked.
