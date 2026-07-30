# T-FE-bio-docs — Result

**Ticket:** T-FE-bio-docs (vitalia-fase2-lisa-doctores, delta v3 D3-B)
**Commit:** `937c7a5e`
**Branch:** `wip/vitalia`
**Date:** 2026-06-12

## Deliverables

### 1. `staff.types.ts`

Added:
- `BioFile` interface (camelCase mirror of `BioFileDTO`):
  - `id: string` (UUID)
  - `filename: string`
  - `sizeBytes: number`
  - `contentType: string`
  - `uploadedAt: string` (ISO 8601)
- `DoctorDetail.bioFiles?: BioFile[]`

### 2. `api/staff.ts`

Four new hooks added after `useDeleteBlock`:

| Hook | Pattern |
|---|---|
| `useBioFiles(doctorId)` | `useQuery` · GET `/{id}/bio-files` · key `staffKeys.bioFiles(id)` |
| `useBioFileUpload(doctorId)` | `useMutation` · 2-step: POST `/assets/upload` (kind=`bio_doc`) → POST `/{id}/bio-files` with `{storageKey,filename,sizeBytes,contentType}` |
| `useDeleteBioFile(doctorId)` | `useMutation` · DELETE `/{id}/bio-files/{file_id}` · invalidates `staffKeys.bioFiles` |
| `useBioFileDownload(doctorId)` | `useMutation` · GET stream → blob → `URL.createObjectURL` + anchor click (D-1: no presigned URL) |

Also added `staffKeys.bioFiles` to the key factory.

All hooks use:
- `useStaffActorHeaders()` for X-User-Role + X-User-ID (bug#3/bug#4 fix pattern)
- `API_BASE = ""` (relative, bug#2 CORS fix pattern)
- 60s AbortController timeout on raw fetch calls
- 503 detection → `"STORAGE_UNAVAILABLE"` error code

### 3. `BioRepoInputs.tsx` — Full Rewrite

**Canon homologations:**
- `Textarea` atom replaces raw `<textarea>` (D1 §§ design-system-first)
- `Button` atom (`variant="outline"`) replaces raw `<button>` for link add
- Inline emoji autosave indicators (`⏳/✓/⚠️`) KILLED — page-level `FloatingAutosaveIndicator` covers (canon §2.6)
- Card with `border-l-2 border-[--agent-lisa]` accent + section header

**File rows per mockup:**
- Icon by content-type: `📄` PDF · `🖼️` image · `📝` DOCX · `📎` other
- Name truncated + size formatted + date formatted
- Download button (⬇) → `useBioFileDownload` mutation
- Delete button (✕) → inline confirm prompt (`¿Eliminar?` + Sí/No) → `useDeleteBioFile`

**States:**
- Loading: Skeleton list with `aria-busy`
- Uploading: `UploadingRow` sub-component showing file name + "Subiendo…"
- Upload error: `UploadingRow` with error message + Reintentar + Quitar buttons
- Storage 503: maps to "Almacenamiento no disponible" message
- Error loading list: alert paragraph
- Empty: soft message "Sin archivos adjuntos. Sube documentos para enriquecer la bio."

**Link validation:**
- Zod URL schema (`z.string().url()`) on add
- Error shown as `role="alert"` paragraph (`aria-invalid` on input)
- Chips display with `aria-label` per link

**Architecture:**
- 0 raw `<div flex-col gap->` or `<div grid-cols->` violations (arch test clean)
- All `useId()` for accessible `htmlFor` → `id` pairings

### 4. Tests

**`api/__tests__/bio-docs-api.test.ts`** (10 tests):
- `staffKeys.bioFiles` key shape + distinctness from blocks key
- `BioFile` interface shape (runtime assertion)
- SC-D3B-3: validate file type + size client-side (5 assertions)
- SC-D3B-5: 503 → `STORAGE_UNAVAILABLE` error code detection

**`components/.../BioRepoInputs.test.tsx`** (11 tests):
- Renders Textarea atom (data-slot=textarea, not raw textarea)
- Initial notes value hydrated
- Existing links rendered
- File dropzone present
- Empty state when no bio files
- Loading skeleton with aria-busy
- File row renders existing BioFile data
- Canon §2.6: NO inline emoji indicators
- SC-D3B-3: invalid URL → Zod error + link not added + error cleared on valid input
- Confirm delete flow (shows/hides on cancel)
- Button atom for Agregar link (cursor-pointer class)

**`e2e/regression/vitalia-fase2-lisa-doctores/bio-docs-d3b.spec.ts`**:
- SC-D3B-3: invalid file type → error inline, upload endpoint NOT called (page.route mock)
- SC-D3B-5: 503 response → error row + Reintentar button visible

## Quality Gates

| Gate | Result |
|---|---|
| `tsc --noEmit` | ✅ 0 errors |
| `eslint src/features/lisa/` | ✅ 0 errors |
| `vitest run src/features/lisa/` | ✅ 461/461 pass |
| arch fitness (`test-no-div-layout`) | ⚠️ PRE-EXISTING failure (MonthCalendar.tsx from parallel session adds 5 violations — my code contributes 0) |
| coverage threshold (20%) | ⚠️ PRE-EXISTING failure (project-wide 2.15% vs 20% global threshold — not caused by this ticket) |

## Live Verification

**Status: PENDING — Escalate Chris staging gate**

- BE `:8002` is UP (`/health` 200)
- FE `:3002` is UP (redirects unauthenticated to `/sign-in`)
- Clerk auth required for live-verify
- Chrome DevTools MCP not available in this bash session
- Live-verify evidence will be recorded when Chris exercises the golden path:

**Manual golden path (for Chris):**
1. Navigate to `http://localhost:3002/{tenant_id}/lisa/staff/{doctor_id}/perfil`
2. Upload a real PDF → row appears (name/size/date) → `curl GET /{id}/bio-files` lists it
3. Click ⬇ → file downloads in browser
4. Click ✕ → confirm Sí → row disappears + DELETE 200
5. Upload invalid file (.exe) → error inline, no row in the list
6. Enter invalid URL → Zod error appears, link NOT added
7. Enter valid URL → link chip appears

```yaml
# dod_evidence (to be filled by Chris after live-verify):
dod_live_verified: null  # pending Chris gate
dod_env: "make dev-vitalia → http://localhost:3002 (Chrome DevTools MCP)"
dod_evidence:
  - action: "PENDING"
    observed: "PENDING"
    backend_log: "PENDING"
verified_at: null
```

## Files Changed

| File | Change |
|---|---|
| `vitalia/frontend/src/features/lisa/types/staff.types.ts` | `BioFile` interface + `bioFiles?` on `DoctorDetail` |
| `vitalia/frontend/src/features/lisa/api/staff.ts` | `staffKeys.bioFiles` + 4 new hooks |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/perfil/BioRepoInputs.tsx` | Full rewrite (203 → 619 lines) |
| `vitalia/frontend/src/features/lisa/api/__tests__/bio-docs-api.test.ts` | NEW — 10 tests |
| `vitalia/frontend/src/features/lisa/components/staff/workspace/perfil/BioRepoInputs.test.tsx` | NEW — 11 tests |
| `vitalia/frontend/e2e/regression/vitalia-fase2-lisa-doctores/bio-docs-d3b.spec.ts` | NEW — SC-D3B-3 + SC-D3B-5 (PENDING-LIVE-VERIFICATION) |

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| `frontend-expert` | FSD-Lite boundary matrix, canon §2.6 autosave, Vitest patterns | Killed inline emoji badges; used page-level FloatingAutosaveIndicator per canon §2.6 |
| React patterns baseline | Error boundaries, loading/error/empty states, accessible markup, stable keys | Applied: aria-busy, aria-label, aria-invalid, aria-live, aria-describedby, useId() for htmlFor |
| Shadcn UI conventions | `Textarea`, `Button`, `Skeleton` atoms | Replaced raw `<textarea>` + `<button>` with atoms; added Skeleton for loading state |
| Zod validation | Link URL validation | `z.string().url()` schema, error displayed as role=alert paragraph |
| Next.js Server/Client split | File is fully client interactive (hooks, state, mutations) | `"use client"` directive, no Server Component split needed (already client) |
| Graceful-degradation | Upload + download HTTP calls | AbortController 60s timeout on raw fetch; 503 detection → `STORAGE_UNAVAILABLE`; retry UI |

<!-- @pm: build phase done (state: tests-passing). Commit: 937c7a5e. Files: 6. Native ticket tests: 461/461 PASS. Awaiting orchestrator → gate-runner → auditor-frontend (independent verdict). Live-verify pending Chris staging gate (Clerk auth required). -->
